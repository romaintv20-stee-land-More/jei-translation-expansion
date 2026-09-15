#!/usr/bin/env python3
"""Validate frozen G41 / Minecraft 1.21.5 source delta and locale ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_21_5 as g41

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_JA_MISSING = set(g41.g40.NEW_G40_KEYS) | set(g41.NEW_G41_KEYS)


def main() -> int:
    errors: list[str] = []
    base = g41.parse_json(g41.BASE_SOURCE)
    target = g41.parse_json(g41.TARGET_SOURCE)
    scope = json.loads(g41.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g41.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g41.POLICY_PATH.read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "upstream" / "minecraft-1.21.5-language-audit.json").read_text(encoding="utf-8"))
    previous_scope = json.loads(g41.g40.SCOPE_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g41.semantic_sets(base, target)
    normal_keys = {key for key in target if not key.startswith(g41.DEBUG_PREFIX)}
    if (len(base), len(target), len(normal_keys)) != (288, 290, 284):
        errors.append(f"source counts changed: base={len(base)} target={len(target)} normal={len(normal_keys)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (288, 2, 0, 0):
        errors.append("semantic partition differs from frozen 288/2/0/0")
    if added != g41.NEW_G41_KEYS:
        errors.append(f"added key set changed: {sorted(added)}")

    expected_diff = {
        "base_key_count": 288,
        "target_key_count": 290,
        "target_normal_key_count": 284,
        "target_debug_only_key_count": 6,
        "unchanged_key_and_value_count": 288,
        "added_key_count": 2,
        "removed_key_count": 0,
        "changed_english_value_count": 0,
        "changed_debug_only_key_count": 0,
        "review_required_normal_added_or_changed_key_count": 2,
    }
    for key, expected in expected_diff.items():
        if diff.get(key) != expected:
            errors.append(f"diff {key}: expected {expected!r}, got {diff.get(key)!r}")
    if set(diff.get("added_keys", [])) != g41.NEW_G41_KEYS:
        errors.append("diff added_keys differs from frozen G41 set")
    if diff.get("removed_keys") != [] or diff.get("changed_english_values") != {}:
        errors.append("G41 must have no removed or changed-English entries")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if len(full) != 65 or len(complete) != 1 or len(incomplete) != 24 or len(selected) != 90:
        errors.append(
            f"ownership counts changed: full={len(full)} complete={len(complete)} incomplete={len(incomplete)} selected={len(selected)}"
        )
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G41 locale ownership sets overlap")
    if complete != {"en_us"}:
        errors.append(f"G41 complete-upstream ownership must be en_us only, got {sorted(complete)}")
    if "uk_ua" not in full or "uk_ua" in incomplete:
        errors.append("uk_ua must be a full override and must not remain a supplement")
    if "ja_jp" not in incomplete:
        errors.append("ja_jp must remain a missing-key-only supplement")

    previous_selected = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )
    if selected != previous_selected:
        errors.append("G41 selected 90-language scope differs from G40")
    if full - {"uk_ua"} != set(previous_scope["addon_full_locales"]):
        errors.append("G41 full ownership except uk_ua differs from G40 addon-full ownership")
    if set(scope["documented_full_english_fallback_locales"]) != set(previous_scope["documented_full_english_fallback_locales"]):
        errors.append("G41 documented full-English fallback locale set differs from G40")
    if scope.get("malformed_upstream_full_override_locales") != ["uk_ua"]:
        errors.append("G41 scope must record uk_ua as the sole malformed upstream full override")

    if policy.get("pinned_commit") != g41.G41_COMMIT:
        errors.append("G41 policy pinned commit differs from reconstruct constant")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g40_semantics"):
        errors.append("G41 policy must allow exact unchanged G40 semantic reuse")
    if reuse.get("cross_key_reuse_allowed") is not False:
        errors.append("G41 policy must forbid cross-key reuse")
    if not reuse.get("runtime_literals_must_be_preserved"):
        errors.append("G41 policy must preserve runtime literals")
    override = policy.get("malformed_upstream_override", {})
    if override.get("locales") != ["uk_ua"] or not override.get("full_override_required"):
        errors.append("G41 policy must require a full uk_ua repair override")

    ownership = scope.get("ownership_changes_from_g40", {})
    if ownership.get("upstream_to_forced_full_override") != ["uk_ua"]:
        errors.append("G41 ownership manifest must record uk_ua upstream -> forced full override")
    if ownership.get("newly_complete_upstream") != [] or ownership.get("complete_to_incomplete") != []:
        errors.append("G41 must not otherwise change complete-upstream ownership")

    if audit.get("jei_upstream_commit") != g41.G41_COMMIT:
        errors.append("G41 audit pinned commit differs from reconstruction")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("first_1_21_5_commit") != "2cc5d1e8b7fb4f79c917804d7582bb7c48374499":
        errors.append("G41 first 1.21.5 port commit changed")
    if endpoint.get("next_minecraft_port_commit") != "2a57409c2af0ce9716749a0329166a41cbcf453f":
        errors.append("G41 next 1.21.6 port commit changed")
    build = audit.get("build_metadata", {})
    if build.get("neoforge") != "21.5.75" or build.get("neoforge_version_range") != "[21.5.74,)" or build.get("java_toolchain") != "21":
        errors.append("G41 frozen build metadata changed")
    if audit.get("malformed_selected_upstream_locales") != ["uk_ua"]:
        errors.append("G41 audit must freeze uk_ua as the sole malformed selected upstream locale")

    try:
        pinned_target = g41.fetch_g41_upstream("en_us")
        if pinned_target != target:
            errors.append("frozen G41 en_us source differs from pinned JEI endpoint")
    except Exception as exc:
        errors.append(f"could not verify frozen G41 en_us against pinned endpoint: {exc}")

    for locale in sorted(complete | incomplete):
        try:
            upstream = g41.fetch_g41_upstream(locale)
        except Exception as exc:
            errors.append(f"{locale}: failed to fetch pinned upstream locale: {exc}")
            continue
        missing = normal_keys - set(upstream)
        if locale in complete and missing:
            errors.append(f"{locale}: marked complete but missing {len(missing)} normal keys")
        if locale in incomplete and not missing:
            errors.append(f"{locale}: marked incomplete but has no missing normal keys")

    try:
        ja = g41.fetch_g41_upstream("ja_jp")
        if normal_keys - set(ja) != EXPECTED_JA_MISSING:
            errors.append(f"ja_jp must be missing exactly the five frozen G41 keys, got {sorted(normal_keys-set(ja))}")
    except Exception as exc:
        errors.append(f"ja_jp: failed pinned completeness check: {exc}")

    try:
        url = g41.RAW_JSON_TEMPLATE.format(commit=g41.G41_COMMIT, locale="uk_ua")
        request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G41-validate"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_uk = response.read().decode("utf-8")
        try:
            json.loads(raw_uk)
            errors.append("pinned uk_ua unexpectedly became valid JSON; frozen full-override assumption must be reviewed")
        except json.JSONDecodeError:
            repaired = g41.repair_uk_ua_text(raw_uk)
            repaired_values = {str(k): str(v) for k, v in json.loads(repaired).items() if not str(k).startswith("_")}
            if normal_keys - set(repaired_values) != EXPECTED_JA_MISSING:
                errors.append("repaired uk_ua must be missing exactly the same five normal keys as ja_jp")
    except Exception as exc:
        errors.append(f"uk_ua malformed-source verification failed: {exc}")

    if errors:
        print(f"FAIL: {len(errors)} G41 delta/source ownership error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.5 / JEI 21.4.0 frozen source delta and locale ownership")
    print("English delta: 288 unchanged / 2 added / 0 removed / 0 changed")
    print("Ownership: 65 full/override / 24 supplements / 1 complete upstream = 90 selected locales")
    print("uk_ua correctly moves to a full repair override; ja_jp remains a five-key supplement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

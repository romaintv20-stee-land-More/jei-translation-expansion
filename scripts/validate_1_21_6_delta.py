#!/usr/bin/env python3
"""Validate frozen G42 / Minecraft 1.21.6 source delta and locale ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_21_6 as g42

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.6-language-audit.json"


def main() -> int:
    errors: list[str] = []
    base = g42.parse_json(g42.BASE_SOURCE)
    target = g42.parse_json(g42.TARGET_SOURCE)
    scope = json.loads(g42.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g42.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g42.POLICY_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    previous_scope = json.loads(g42.g41.SCOPE_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g42.semantic_sets(base, target)
    normal_keys = {key for key in target if not key.startswith(g42.DEBUG_PREFIX)}
    if (len(base), len(target), len(normal_keys)) != (290, 289, 283):
        errors.append(f"source counts changed: base={len(base)} target={len(target)} normal={len(normal_keys)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (289, 0, 1, 0):
        errors.append("semantic partition differs from frozen 289/0/1/0")
    if removed != g42.REMOVED_G42_KEYS:
        errors.append(f"removed key set changed: {sorted(removed)}")

    expected_diff = {
        "base_key_count": 290,
        "target_key_count": 289,
        "target_normal_key_count": 283,
        "target_debug_only_key_count": 6,
        "unchanged_key_and_value_count": 289,
        "added_key_count": 0,
        "removed_key_count": 1,
        "changed_english_value_count": 0,
    }
    for key, expected in expected_diff.items():
        if diff.get(key) != expected:
            errors.append(f"diff {key}: expected {expected!r}, got {diff.get(key)!r}")
    if diff.get("added_keys") != [] or set(diff.get("removed_keys", [])) != g42.REMOVED_G42_KEYS:
        errors.append("G42 diff added/removed key sets differ from frozen removal-only delta")
    if diff.get("changed_english_values") != {}:
        errors.append("G42 must have no changed-English entries")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if len(selected) != 90:
        errors.append(f"selected ownership must total 90 locales, got {len(selected)}")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G42 locale ownership sets overlap")
    if "en_us" not in complete:
        errors.append("en_us must remain complete upstream")
    if "uk_ua" not in full or "uk_ua" in complete or "uk_ua" in incomplete:
        errors.append("uk_ua must remain exclusively a full repair override")

    previous_selected = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )
    if selected != previous_selected:
        errors.append("G42 selected 90-language scope differs from G41")
    if set(scope["documented_full_english_fallback_locales"]) != set(previous_scope["documented_full_english_fallback_locales"]):
        errors.append("G42 documented full-English fallback set differs from G41")
    if scope.get("malformed_upstream_full_override_locales") != ["uk_ua"]:
        errors.append("G42 scope must record uk_ua as the sole malformed upstream full override")

    if policy.get("pinned_commit") != g42.G42_COMMIT:
        errors.append("G42 policy pinned commit differs from reconstruction")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g41_semantics"):
        errors.append("G42 policy must allow exact unchanged G41 semantic reuse")
    if reuse.get("cross_key_reuse_allowed") is not False:
        errors.append("G42 policy must forbid cross-key reuse")
    if not reuse.get("runtime_literals_must_be_preserved"):
        errors.append("G42 policy must preserve runtime literals")
    removed_policy = policy.get("removed_semantics", {})
    if removed_policy.get("count") != 1 or set(removed_policy.get("keys", [])) != g42.REMOVED_G42_KEYS or not removed_policy.get("must_not_be_emitted"):
        errors.append("G42 policy must freeze the one removed semantic key and forbid emission")
    override = policy.get("malformed_upstream_override", {})
    if override.get("locales") != ["uk_ua"] or not override.get("full_override_required"):
        errors.append("G42 policy must require a full uk_ua repair override")

    if audit.get("jei_upstream_commit") != g42.G42_COMMIT:
        errors.append("G42 audit pinned commit differs from reconstruction")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("final_1_21_6_commit") != g42.G42_COMMIT:
        errors.append("G42 final endpoint changed")
    if endpoint.get("next_minecraft_port_commit") != "8a22d93e6e903142c9dbcdf699496f435d1c569d":
        errors.append("G42 next 1.21.7 port commit changed")
    build = audit.get("build_metadata", {})
    if build.get("neoforge") != "21.6.20-beta" or build.get("neoforge_version_range") != "[21.6.20-beta,)" or build.get("java_toolchain") != "21":
        errors.append("G42 frozen build metadata changed")
    if audit.get("malformed_selected_upstream_locales") != ["uk_ua"]:
        errors.append("G42 audit must freeze uk_ua as the sole malformed selected upstream locale")

    try:
        pinned_target = g42.fetch_g42_upstream("en_us")
        if pinned_target != target:
            errors.append("frozen G42 en_us source differs from pinned JEI endpoint")
    except Exception as exc:
        errors.append(f"could not verify frozen G42 en_us against pinned endpoint: {exc}")

    for locale in sorted(complete | incomplete):
        try:
            upstream = g42.fetch_g42_upstream(locale)
        except Exception as exc:
            errors.append(f"{locale}: failed to fetch pinned upstream locale: {exc}")
            continue
        missing = normal_keys - set(upstream)
        if locale in complete and missing:
            errors.append(f"{locale}: marked complete but missing {len(missing)} normal keys")
        if locale in incomplete and not missing:
            errors.append(f"{locale}: marked incomplete but has no missing normal keys")

    try:
        url = g42.RAW_JSON_TEMPLATE.format(commit=g42.G42_COMMIT, locale="uk_ua")
        request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G42-validate"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_uk = response.read().decode("utf-8")
        try:
            json.loads(raw_uk)
            errors.append("pinned uk_ua unexpectedly became valid JSON; full-override assumption requires review")
        except json.JSONDecodeError:
            repaired_values = {
                str(k): str(v)
                for k, v in json.loads(g42.g41.repair_uk_ua_text(raw_uk)).items()
                if not str(k).startswith("_")
            }
            if not (normal_keys - set(repaired_values)):
                errors.append("repaired uk_ua unexpectedly covers every G42 normal key")
    except Exception as exc:
        errors.append(f"uk_ua malformed-source verification failed: {exc}")

    if errors:
        print(f"FAIL: {len(errors)} G42 delta/source ownership error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.6 / JEI 22.0.0 frozen source delta and locale ownership")
    print("English delta: 289 unchanged / 0 added / 1 removed / 0 changed")
    print(f"Ownership: {len(full)} full/override / {len(incomplete)} supplements / {len(complete)} complete upstream = 90 selected locales")
    print("uk_ua remains a full repair override; removed G41 grindstone-experience semantics are not carried forward")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

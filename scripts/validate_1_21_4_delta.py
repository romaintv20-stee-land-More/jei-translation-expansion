#!/usr/bin/env python3
"""Validate frozen G40 / Minecraft 1.21.4 source delta and locale ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21_4 as g40

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    base = g40.parse_json(g40.BASE_SOURCE)
    target = g40.parse_json(g40.TARGET_SOURCE)
    scope = json.loads(g40.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g40.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g40.POLICY_PATH.read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "upstream" / "minecraft-1.21.4-language-audit.json").read_text(encoding="utf-8"))
    previous_scope = json.loads(g40.g39.SCOPE_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g40.semantic_sets(base, target)
    normal_keys = {key for key in target if not key.startswith(g40.DEBUG_PREFIX)}
    if (len(base), len(target), len(normal_keys)) != (286, 288, 282):
        errors.append(f"source counts changed: base={len(base)} target={len(target)} normal={len(normal_keys)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (285, 3, 1, 0):
        errors.append("semantic partition differs from frozen 285/3/1/0")
    if added != g40.NEW_G40_KEYS:
        errors.append(f"added key set changed: {sorted(added)}")
    if removed != g40.REMOVED_G40_KEYS:
        errors.append(f"removed key set changed: {sorted(removed)}")

    expected_diff = {
        "base_key_count": 286,
        "target_key_count": 288,
        "target_normal_key_count": 282,
        "target_debug_only_key_count": 6,
        "unchanged_key_and_value_count": 285,
        "added_key_count": 3,
        "removed_key_count": 1,
        "changed_english_value_count": 0,
        "changed_debug_only_key_count": 0,
        "review_required_normal_added_or_changed_key_count": 3,
    }
    for key, expected in expected_diff.items():
        if diff.get(key) != expected:
            errors.append(f"diff {key}: expected {expected!r}, got {diff.get(key)!r}")
    if set(diff.get("added_keys", [])) != g40.NEW_G40_KEYS:
        errors.append("diff added_keys differs from frozen G40 new fuel-category set")
    if set(diff.get("removed_keys", [])) != g40.REMOVED_G40_KEYS:
        errors.append("diff removed_keys differs from frozen generic Fuel removal")
    if diff.get("changed_english_values") != {}:
        errors.append("G40 must have no changed-English-value entries")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if len(full) != 64 or len(complete) != 1 or len(incomplete) != 25 or len(selected) != 90:
        errors.append(
            f"ownership counts changed: full={len(full)} complete={len(complete)} incomplete={len(incomplete)} selected={len(selected)}"
        )
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G40 locale ownership sets overlap")
    if complete != {"en_us"}:
        errors.append(f"G40 complete-upstream ownership must be en_us only, got {sorted(complete)}")
    if "ja_jp" not in incomplete:
        errors.append("ja_jp must move from complete G39 ownership to a G40 missing-key supplement")

    previous_selected = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )
    if selected != previous_selected:
        errors.append("G40 selected 90-language scope differs from G39")
    if full != set(previous_scope["addon_full_locales"]):
        errors.append("G40 addon-full ownership differs from G39")
    if set(scope["documented_full_english_fallback_locales"]) != set(previous_scope["documented_full_english_fallback_locales"]):
        errors.append("G40 documented full-English fallback locale set differs from G39")

    if policy.get("pinned_commit") != g40.G40_COMMIT:
        errors.append("G40 policy pinned commit differs from reconstruct constant")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g39_semantics"):
        errors.append("G40 policy must allow exact unchanged G39 semantic reuse")
    if reuse.get("cross_key_reuse_allowed") is not False:
        errors.append("G40 policy must forbid cross-key reuse")
    if not reuse.get("runtime_literals_must_be_preserved"):
        errors.append("G40 policy must preserve runtime literals")
    donor = policy.get("later_upstream_backport_policy", {})
    if donor.get("donor_snapshot") != g40.DONOR_COMMIT:
        errors.append("G40 policy donor snapshot differs from reconstruction")
    if not donor.get("allowed_only_if_same_key_and_exact_same_english_value"):
        errors.append("G40 donor policy must require exact same-key + same-English semantics")

    ownership = scope.get("ownership_changes_from_g39", {})
    if ownership.get("complete_to_incomplete") != ["ja_jp"]:
        errors.append("G40 ownership manifest must record ja_jp complete -> incomplete")
    if ownership.get("newly_upstream_from_addon_full") != [] or ownership.get("no_longer_upstream") != []:
        errors.append("G40 must not add/remove selected JEI upstream locale ownership")

    if audit.get("jei_upstream_commit") != g40.G40_COMMIT:
        errors.append("G40 audit pinned commit differs from reconstruction")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("first_1_21_4_commit") != "c0d0367841b16fa3a9567c3d93172cbd1f1b578c":
        errors.append("G40 first 1.21.4 port commit changed")
    if endpoint.get("next_minecraft_port_commit") != "2cc5d1e8b7fb4f79c917804d7582bb7c48374499":
        errors.append("G40 next 1.21.5 port commit changed")
    build = audit.get("build_metadata", {})
    if build.get("neoforge") != "21.4.136" or build.get("neoforge_version_range") != "[21.4.121,)" or build.get("java_toolchain") != "21":
        errors.append("G40 frozen build metadata changed")

    try:
        pinned_target = g40.fetch_upstream_json(g40.G40_COMMIT, "en_us")
        if pinned_target != target:
            errors.append("frozen G40 en_us source differs from pinned JEI endpoint")
    except Exception as exc:
        errors.append(f"could not verify frozen G40 en_us against pinned endpoint: {exc}")

    for locale in sorted(complete | incomplete):
        try:
            upstream = g40.fetch_upstream_json(g40.G40_COMMIT, locale)
        except Exception as exc:
            errors.append(f"{locale}: failed to fetch pinned upstream locale: {exc}")
            continue
        missing = normal_keys - set(upstream)
        if locale in complete and missing:
            errors.append(f"{locale}: marked complete but missing {len(missing)} normal keys")
        if locale in incomplete and not missing:
            errors.append(f"{locale}: marked incomplete but has no missing normal keys")
    if not errors:
        try:
            ja = g40.fetch_upstream_json(g40.G40_COMMIT, "ja_jp")
            if normal_keys - set(ja) != g40.NEW_G40_KEYS:
                errors.append("ja_jp must be missing exactly the three new G40 fuel-category keys")
        except Exception as exc:
            errors.append(f"ja_jp: failed pinned completeness check: {exc}")

    if errors:
        print(f"FAIL: {len(errors)} G40 delta/source ownership error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.4 / JEI 20.0.0 frozen source delta and locale ownership")
    print("English delta: 285 unchanged / 3 added / 1 removed / 0 changed")
    print("Ownership: 64 addon-full / 25 supplements / 1 complete upstream = 90 selected locales")
    print("ja_jp correctly moves to a three-key missing-only supplement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

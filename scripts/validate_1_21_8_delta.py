#!/usr/bin/env python3
"""Validate frozen G44 / Minecraft 1.21.8 source delta, ownership, and donor policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21_8 as g44

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.8-language-audit.json"


def main() -> int:
    errors: list[str] = []
    base = g44.parse_json(g44.BASE_SOURCE)
    target = g44.parse_json(g44.TARGET_SOURCE)
    scope = json.loads(g44.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g44.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g44.POLICY_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    previous_scope = json.loads(g44.g43.SCOPE_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g44.semantic_sets(base, target)
    normal = {k for k in target if not k.startswith(g44.DEBUG_PREFIX)}
    if (len(base), len(target), len(normal)) != (291, 305, 299):
        errors.append(f"source counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (290, 15, 1, 0):
        errors.append("semantic partition differs from frozen 290/15/1/0")
    if removed != g44.REMOVED_G44_KEYS:
        errors.append(f"removed key set changed: {sorted(removed)}")
    if set(diff.get("added_keys", [])) != added or set(diff.get("removed_keys", [])) != removed:
        errors.append("frozen diff added/removed key sets differ from source")
    if diff.get("changed_english_values") != {}:
        errors.append("G44 must have no changed-English entries")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(incomplete), len(complete), len(selected)) != (65, 24, 1, 90):
        errors.append(f"ownership counts changed: {len(full)}/{len(incomplete)}/{len(complete)}/{len(selected)}")
    if complete != {"en_us"}:
        errors.append(f"G44 complete upstream set changed: {sorted(complete)}")
    if full & incomplete or full & complete or incomplete & complete:
        errors.append("G44 ownership sets overlap")
    if "uk_ua" not in full or scope.get("malformed_upstream_full_override_locales") != ["uk_ua"]:
        errors.append("uk_ua must remain the sole malformed full repair override")

    previous_selected = set(previous_scope["addon_full_locales"]) | set(previous_scope["selected_upstream_complete_locales"]) | set(previous_scope["selected_upstream_incomplete_locales"])
    if selected != previous_selected:
        errors.append("G44 selected 90-language scope differs from G43")
    if set(scope["documented_full_english_fallback_locales"]) != set(previous_scope["documented_full_english_fallback_locales"]):
        errors.append("G44 documented full-English fallback set differs from G43")

    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g43_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        errors.append("G44 policy must permit exact unchanged G43 reuse and forbid cross-key reuse")
    if reuse.get("future_donor_commit") != g44.DONOR_COMMIT or not reuse.get("future_donor_allowed_only_for_exact_same_key_same_english"):
        errors.append("G44 exact future donor policy changed")
    donor_en = g44.donor_english()
    bad_donor = sorted(key for key in added if donor_en.get(key) != target[key])
    if bad_donor:
        errors.append(f"future donor English no longer exactly matches G44 added semantics: {bad_donor}")

    endpoint = audit.get("endpoint_resolution", {})
    if audit.get("jei_upstream_commit") != g44.G44_COMMIT or endpoint.get("final_1_21_8_commit") != g44.G44_COMMIT:
        errors.append("G44 pinned endpoint changed")
    if endpoint.get("next_minecraft_port_commit") != "1f0f90ee84bb771c25e8118b4cf25aeaf9d26726" or endpoint.get("next_minecraft_version") != "1.21.9":
        errors.append("G44 next Minecraft port metadata changed")
    build = audit.get("build_metadata", {})
    if build.get("neoforge") != "21.8.47" or build.get("neoforge_version_range") != "[21.8.9,)" or build.get("java_toolchain") != "21":
        errors.append("G44 frozen build metadata changed")
    if audit.get("malformed_selected_upstream_locales") != ["uk_ua"]:
        errors.append("G44 audit malformed-locale ownership changed")

    try:
        pinned_en = g44.fetch_g44_upstream("en_us")
        if pinned_en != target:
            errors.append("frozen G44 en_us differs from pinned endpoint")
    except Exception as exc:
        errors.append(f"could not verify pinned G44 en_us: {exc}")

    for locale in sorted(complete | incomplete):
        try:
            upstream = g44.fetch_g44_upstream(locale)
        except Exception as exc:
            errors.append(f"{locale}: failed to fetch pinned upstream locale: {exc}")
            continue
        missing = normal - set(upstream)
        if locale in complete and missing:
            errors.append(f"{locale}: marked complete but missing {len(missing)} normal keys")
        if locale in incomplete and not missing:
            errors.append(f"{locale}: marked incomplete but has no missing normal keys")

    if errors:
        print(f"FAIL: {len(errors)} G44 source/delta error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.8 / JEI 24.2.0 frozen source delta and ownership")
    print("English delta: 290 unchanged / 15 added / 1 removed / 0 changed")
    print("Ownership: 65 full/override / 24 supplements / 1 complete upstream = 90 selected locales")
    print(f"Exact same-key/same-English future donor pinned at {g44.DONOR_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

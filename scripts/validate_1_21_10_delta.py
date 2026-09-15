#!/usr/bin/env python3
"""Validate frozen Minecraft 1.21.10 / JEI 26.2.0 source, scope, ownership, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21_10 as g46

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.10-language-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g46.parse_json(g46.BASE_SOURCE)
    target = g46.parse_json(g46.TARGET_SOURCE)
    scope = load(g46.SCOPE_PATH)
    diff = load(g46.DIFF_PATH)
    policy = load(g46.POLICY_PATH)
    audit = load(AUDIT_PATH)
    unchanged, added, removed, changed = g46.semantic_partition()
    normal = {k for k in target if not k.startswith(g46.DEBUG_PREFIX)}

    if (len(base), len(target), len(normal), len(target)-len(normal)) != (305, 308, 302, 6):
        raise ValueError("G46 frozen English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (305, 3, 0, 0):
        raise ValueError("G46 frozen semantic partition changed")
    if added != g46.ADDED_G46_KEYS:
        raise ValueError("G46 added-key set changed")
    if any(base.get(k) != target[k] for k in unchanged):
        raise ValueError("G46 unchanged semantics are not exact")

    expected_diff = (305, 3, 0, 0)
    actual_diff = (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count"),
    )
    if actual_diff != expected_diff:
        raise ValueError(f"G46 diff counts changed: {actual_diff}")
    if set(diff.get("added_keys", [])) != g46.ADDED_G46_KEYS or diff.get("removed_keys") != [] or diff.get("changed_english_values") != {}:
        raise ValueError("G46 frozen diff key sets changed")

    selected_full = set(scope["addon_full_locales"])
    selected_supp = set(scope["selected_upstream_incomplete_locales"])
    selected_complete = set(scope["selected_upstream_complete_locales"])
    if (len(selected_full), len(selected_supp), len(selected_complete)) != (64, 25, 1):
        raise ValueError("G46 ownership counts changed")
    if selected_complete != {"en_us"}:
        raise ValueError("G46 complete-upstream ownership changed")
    if len(selected_full | selected_supp | selected_complete) != 90:
        raise ValueError("G46 selected scope union changed")
    if selected_full & selected_supp or selected_full & selected_complete or selected_supp & selected_complete:
        raise ValueError("G46 ownership sets overlap")
    if scope.get("malformed_upstream_full_override_locales") != [] or scope.get("malformed_upstream_full_override_locale_count") != 0:
        raise ValueError("G46 must not retain malformed full overrides")
    if "uk_ua" not in selected_supp or "uk_ua" in selected_full:
        raise ValueError("G46 uk_ua validity/ownership transition changed")
    transition = scope.get("upstream_validity_transition", {})
    if transition.get("uk_ua_is_valid_in_g46") is not True or transition.get("uk_ua_g46_ownership") != "missing-key-only supplement":
        raise ValueError("G46 uk_ua transition metadata changed")
    if set(transition.get("uk_ua_missing_keys", [])) != g46.ADDED_G46_KEYS:
        raise ValueError("G46 uk_ua missing-key transition changed")

    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= selected_full:
        raise ValueError("G46 fallback scope changed")

    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g45_semantics") or reuse.get("unchanged_key_count") != 305:
        raise ValueError("G46 unchanged reuse policy changed")
    if reuse.get("new_key_count") != 3 or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G46 new-key/cross-key policy changed")
    if reuse.get("future_donor_commit") != g46.DONOR_COMMIT or not reuse.get("future_donor_allowed_only_for_exact_same_key_same_english"):
        raise ValueError("G46 donor policy changed")
    if reuse.get("fallback_when_no_safe_translation") != "exact-target-English":
        raise ValueError("G46 fallback policy changed")

    donor_en = g46.donor_english()
    for key in g46.ADDED_G46_KEYS:
        if donor_en.get(key) != target[key]:
            raise ValueError(f"G46 donor English no longer exact for {key}")

    overrides = scope.get("upstream_literal_safety_overrides", {})
    if sum(len(v) for v in overrides.values()) != scope.get("upstream_literal_safety_override_count"):
        raise ValueError("G46 safety-override count mismatch")
    if set(overrides) - selected_supp:
        raise ValueError("G46 safety overrides exist outside supplement locales")

    if audit.get("jei_upstream_commit") != g46.G46_COMMIT:
        raise ValueError("G46 audit endpoint changed")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("final_1_21_10_commit") != g46.G46_COMMIT or endpoint.get("next_minecraft_port_commit") != "6b615d15ef776abf139339779985a91c59c9c324":
        raise ValueError("G46 endpoint resolution changed")
    metadata = audit.get("build_metadata", {})
    if metadata.get("neoforge") != "21.10.64" or metadata.get("java_toolchain") != "21" or metadata.get("specification_version") != "26.2.0":
        raise ValueError("G46 build metadata changed")

    print("PASS: Minecraft 1.21.10 frozen delta/scope/ownership validation")
    print("English: 308 total / 302 normal / 6 debug")
    print("G45 -> G46: 305 unchanged + 3 added + 0 removed + 0 changed")
    print("Ownership: 64 full + 25 supplements + 1 complete upstream = 90")
    print("uk_ua is valid upstream and supplement-owned in G46")
    print(f"Frozen upstream literal-safety override keys: {scope.get('upstream_literal_safety_override_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

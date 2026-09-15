#!/usr/bin/env python3
"""Validate frozen Minecraft 1.21.11 / JEI 27.3.0 source, scope, ownership, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21_11 as g47

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.11-language-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g47.parse_json(g47.BASE_SOURCE)
    target = g47.parse_json(g47.TARGET_SOURCE)
    scope = load(g47.SCOPE_PATH)
    diff = load(g47.DIFF_PATH)
    policy = load(g47.POLICY_PATH)
    audit = load(AUDIT_PATH)
    unchanged, added, removed, changed = g47.semantic_partition()
    normal = {k for k in target if not k.startswith(g47.DEBUG_PREFIX)}

    if (len(base), len(target), len(normal), len(target)-len(normal)) != (308, 308, 302, 6):
        raise ValueError("G47 frozen English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (306, 2, 2, 0):
        raise ValueError("G47 frozen semantic partition changed")
    if added != g47.ADDED_G47_KEYS or removed != g47.REMOVED_G46_KEYS or changed:
        raise ValueError("G47 renamed-key sets changed")
    if any(base.get(k) != target[k] for k in unchanged):
        raise ValueError("G47 unchanged semantics are not exact")

    actual_diff = (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count"),
    )
    if actual_diff != (306, 2, 2, 0):
        raise ValueError(f"G47 diff counts changed: {actual_diff}")
    if set(diff.get("added_keys", [])) != g47.ADDED_G47_KEYS or set(diff.get("removed_keys", [])) != g47.REMOVED_G46_KEYS:
        raise ValueError("G47 frozen diff key sets changed")

    selected_full = set(scope["addon_full_locales"])
    selected_supp = set(scope["selected_upstream_incomplete_locales"])
    selected_complete = set(scope["selected_upstream_complete_locales"])
    if (len(selected_full), len(selected_supp), len(selected_complete)) != (64, 25, 1):
        raise ValueError("G47 ownership counts changed")
    if selected_complete != {"en_us"} or len(selected_full | selected_supp | selected_complete) != 90:
        raise ValueError("G47 selected scope changed")
    if selected_full & selected_supp or selected_full & selected_complete or selected_supp & selected_complete:
        raise ValueError("G47 ownership sets overlap")
    if scope.get("malformed_upstream_full_override_locales") != [] or scope.get("malformed_upstream_full_override_locale_count") != 0:
        raise ValueError("G47 must have no malformed selected upstream locale")
    if "uk_ua" not in selected_supp:
        raise ValueError("G47 uk_ua must remain a valid upstream supplement locale")

    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= selected_full:
        raise ValueError("G47 fallback scope changed")

    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g46_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G47 unchanged/cross-key reuse policy changed")
    if not reuse.get("renamed_resource_location_to_identifier_keys_are_new_semantics_for_translation_ownership"):
        raise ValueError("G47 renamed-key policy changed")
    if not reuse.get("project_owned_added_keys_use_exact_target_english"):
        raise ValueError("G47 project-owned new-key policy changed")

    publication = scope.get("publication_context", {})
    if publication.get("upstream_jei_target_is_maven_only") is not True:
        raise ValueError("G47 Maven-only publication context was lost")

    overrides = scope.get("upstream_literal_safety_overrides", {})
    if sum(len(v) for v in overrides.values()) != scope.get("upstream_literal_safety_override_count"):
        raise ValueError("G47 safety-override count mismatch")
    if set(overrides) - selected_supp:
        raise ValueError("G47 safety overrides exist outside supplement locales")

    if audit.get("jei_upstream_commit") != g47.G47_COMMIT:
        raise ValueError("G47 audit endpoint changed")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("first_1_21_11_port_commit") != "6b615d15ef776abf139339779985a91c59c9c324":
        raise ValueError("G47 first-port endpoint changed")
    if endpoint.get("final_1_21_11_commit") != g47.G47_COMMIT or endpoint.get("next_minecraft_port_commit") != "d395fda29b10f09b860d5a6221b459050f5071d3":
        raise ValueError("G47 endpoint resolution changed")
    metadata = audit.get("build_metadata", {})
    if metadata.get("neoforge") != "21.11.13-beta" or metadata.get("java_toolchain") != "21" or metadata.get("specification_version") != "27.3.0":
        raise ValueError("G47 build metadata changed")

    print("PASS: Minecraft 1.21.11 frozen delta/scope/ownership validation")
    print("English: 308 total / 302 normal / 6 debug")
    print("G46 -> G47: 306 unchanged + 2 added + 2 removed + 0 changed")
    print("Ownership: 64 full + 25 supplements + 1 complete upstream = 90")
    print("No cross-key reuse from Resource Location IDs to Identifier IDs")
    print("Upstream JEI 1.21.11 publication context: Maven-only")
    print(f"Frozen upstream literal-safety override keys: {scope.get('upstream_literal_safety_override_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

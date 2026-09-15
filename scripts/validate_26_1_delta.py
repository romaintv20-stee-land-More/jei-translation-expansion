#!/usr/bin/env python3
"""Validate frozen Minecraft 26.1 / JEI 29.2.0 source, scope, ownership, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_26_1 as g48

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-26.1-language-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g48.parse_json(g48.BASE_SOURCE)
    target = g48.parse_json(g48.TARGET_SOURCE)
    scope = load(g48.SCOPE_PATH)
    diff = load(g48.DIFF_PATH)
    policy = load(g48.POLICY_PATH)
    audit = load(AUDIT_PATH)
    unchanged, added, removed, changed = g48.semantic_partition()
    normal = {k for k in target if not k.startswith(g48.DEBUG_PREFIX)}

    if (len(base), len(target), len(normal), len(target)-len(normal)) != (334, 309, 303, 6):
        raise ValueError("G48 frozen English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (294, 9, 34, 6):
        raise ValueError("G48 frozen semantic partition changed")
    if added != g48.ADDED_G48_KEYS or removed != g48.REMOVED_G47_KEYS or changed != g48.CHANGED_G48_KEYS:
        raise ValueError("G48 frozen semantic key sets changed")
    if any(base.get(k) != target[k] for k in unchanged):
        raise ValueError("G48 unchanged semantics are not exact")

    actual_diff = (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count"),
    )
    if actual_diff != (294, 9, 34, 6):
        raise ValueError(f"G48 diff counts changed: {actual_diff}")
    if set(diff.get("added_keys", [])) != g48.ADDED_G48_KEYS:
        raise ValueError("G48 frozen added-key set changed")
    if set(diff.get("removed_keys", [])) != g48.REMOVED_G47_KEYS:
        raise ValueError("G48 frozen removed-key set changed")
    if set(diff.get("changed_english_values", {})) != g48.CHANGED_G48_KEYS:
        raise ValueError("G48 frozen changed-English key set changed")

    selected_full = set(scope["addon_full_locales"])
    selected_supp = set(scope["selected_upstream_incomplete_locales"])
    selected_complete = set(scope["selected_upstream_complete_locales"])
    if (len(selected_full), len(selected_supp), len(selected_complete)) != (64, 25, 1):
        raise ValueError("G48 ownership counts changed")
    if selected_complete != {"en_us"} or len(selected_full | selected_supp | selected_complete) != 90:
        raise ValueError("G48 selected scope changed")
    if selected_full & selected_supp or selected_full & selected_complete or selected_supp & selected_complete:
        raise ValueError("G48 ownership sets overlap")
    if scope.get("malformed_upstream_full_override_locales") != [] or scope.get("malformed_upstream_full_override_locale_count") != 0:
        raise ValueError("G48 must have no malformed selected upstream locale")
    if "uk_ua" not in selected_supp:
        raise ValueError("G48 uk_ua must be a valid upstream supplement locale")

    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= selected_full:
        raise ValueError("G48 fallback scope changed")

    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g47_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G48 unchanged/cross-key reuse policy changed")
    if not reuse.get("same_key_required") or not reuse.get("same_english_required"):
        raise ValueError("G48 exact semantic reuse requirements changed")
    if not reuse.get("project_owned_added_or_changed_keys_use_exact_target_english"):
        raise ValueError("G48 project-owned added/changed-key policy changed")
    if not reuse.get("removed_keys_must_not_be_emitted"):
        raise ValueError("G48 removed-key policy changed")

    publication = scope.get("publication_context", {})
    if publication.get("public_distribution_configured") is not True:
        raise ValueError("G48 public-distribution context was lost")
    if publication.get("curse_project_id") != "238222" or publication.get("modrinth_id") != "u6dRKJwZ":
        raise ValueError("G48 publication identifiers changed")

    overrides = scope.get("upstream_literal_safety_overrides", {})
    if sum(len(v) for v in overrides.values()) != scope.get("upstream_literal_safety_override_count"):
        raise ValueError("G48 safety-override count mismatch")
    if set(overrides) - selected_supp:
        raise ValueError("G48 safety overrides exist outside supplement locales")

    if audit.get("jei_upstream_commit") != g48.G48_COMMIT:
        raise ValueError("G48 audit endpoint changed")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("first_26_1_release_commit") != "9de18f504f357be537c5de24cac408b51ca9d8b1":
        raise ValueError("G48 first-release endpoint changed")
    if endpoint.get("final_26_1_endpoint") != g48.G48_COMMIT:
        raise ValueError("G48 final endpoint changed")
    if endpoint.get("next_patch_commit") != "b1ebe15147adb0bded6f3e5ccf86b35124fa5929":
        raise ValueError("G48 next-patch boundary changed")
    if endpoint.get("next_minecraft_version") != "26.1.1":
        raise ValueError("G48 next Minecraft boundary changed")
    metadata = audit.get("build_metadata", {})
    if metadata.get("neoforge") != "26.1.0.8-beta" or metadata.get("neoforge_version_range") != "[26.1.0.8-beta,)":
        raise ValueError("G48 NeoForge metadata changed")
    if metadata.get("java_toolchain") != "25" or metadata.get("specification_version") != "29.2.0":
        raise ValueError("G48 Java/specification metadata changed")

    completeness = audit.get("selected_upstream_completeness", {})
    if completeness.get("uk_ua", {}).get("missing_normal_key_count") != 4:
        raise ValueError("G48 uk_ua missing-key count changed")

    print("PASS: Minecraft 26.1 frozen delta/scope/ownership validation")
    print("English: 309 total / 303 normal / 6 debug")
    print("G47 -> G48: 294 unchanged + 9 added + 34 removed + 6 changed")
    print("Ownership: 64 full + 25 supplements + 1 complete upstream = 90")
    print("Only exact same-key/same-English G47 semantics may be reused")
    print("Build: JEI 29.2.0 / NeoForge 26.1.0.8-beta / Java 25")
    print(f"Frozen upstream literal-safety override keys: {scope.get('upstream_literal_safety_override_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

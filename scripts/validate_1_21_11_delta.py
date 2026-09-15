#!/usr/bin/env python3
"""Validate frozen maintained Minecraft 1.21.11 / JEI 27.38.0 source, scope, ownership, and reuse policy."""
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

    if (len(base), len(target), len(normal), len(target)-len(normal)) != (308, 334, 328, 6):
        raise ValueError("G47 frozen English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (291, 37, 11, 6):
        raise ValueError("G47 frozen semantic partition changed")
    if added != g47.ADDED_G47_KEYS or removed != g47.REMOVED_G46_KEYS or changed != g47.CHANGED_G47_KEYS:
        raise ValueError("G47 frozen semantic key sets changed")
    if any(base.get(k) != target[k] for k in unchanged):
        raise ValueError("G47 unchanged semantics are not exact")

    actual_diff = (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count"),
    )
    if actual_diff != (291, 37, 11, 6):
        raise ValueError(f"G47 diff counts changed: {actual_diff}")
    if set(diff.get("added_keys", [])) != g47.ADDED_G47_KEYS:
        raise ValueError("G47 frozen added-key set changed")
    if set(diff.get("removed_keys", [])) != g47.REMOVED_G46_KEYS:
        raise ValueError("G47 frozen removed-key set changed")
    if set(diff.get("changed_english_values", {})) != g47.CHANGED_G47_KEYS:
        raise ValueError("G47 frozen changed-English key set changed")

    selected_full = set(scope["addon_full_locales"])
    selected_supp = set(scope["selected_upstream_incomplete_locales"])
    selected_complete = set(scope["selected_upstream_complete_locales"])
    if (len(selected_full), len(selected_supp), len(selected_complete)) != (63, 26, 1):
        raise ValueError("G47 ownership counts changed")
    if selected_complete != {"en_us"} or len(selected_full | selected_supp | selected_complete) != 90:
        raise ValueError("G47 selected scope changed")
    if selected_full & selected_supp or selected_full & selected_complete or selected_supp & selected_complete:
        raise ValueError("G47 ownership sets overlap")
    if scope.get("malformed_upstream_full_override_locales") != [] or scope.get("malformed_upstream_full_override_locale_count") != 0:
        raise ValueError("G47 must have no malformed selected upstream locale")
    if not {"uk_ua", "fil_ph"} <= selected_supp:
        raise ValueError("G47 uk_ua and fil_ph must be valid upstream supplement locales")

    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= selected_full:
        raise ValueError("G47 fallback scope changed")

    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g46_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G47 unchanged/cross-key reuse policy changed")
    if not reuse.get("same_key_required") or not reuse.get("same_english_required"):
        raise ValueError("G47 exact semantic reuse requirements changed")
    if not reuse.get("project_owned_added_or_changed_keys_use_exact_target_english"):
        raise ValueError("G47 project-owned added/changed-key policy changed")
    if not reuse.get("removed_keys_must_not_be_emitted"):
        raise ValueError("G47 removed-key policy changed")

    publication = scope.get("publication_context", {})
    if publication.get("historical_first_port_maven_only_note") is not True:
        raise ValueError("G47 historical Maven-only context was lost")
    if publication.get("maintained_branch_public_distribution_configured") is not True:
        raise ValueError("G47 maintained-branch publication context was lost")
    if publication.get("curse_project_id") != "238222" or publication.get("modrinth_id") != "u6dRKJwZ":
        raise ValueError("G47 maintained publication identifiers changed")

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
    if endpoint.get("historical_mainline_1_21_11_endpoint") != "1d37cb1a1cf7139170d214adef128f405b865312":
        raise ValueError("G47 historical mainline endpoint changed")
    if endpoint.get("maintained_1_21_11_branch_endpoint") != g47.G47_COMMIT:
        raise ValueError("G47 maintained endpoint changed")
    if endpoint.get("mainline_next_port_commit") != "d395fda29b10f09b860d5a6221b459050f5071d3":
        raise ValueError("G47 mainline next-port boundary changed")
    metadata = audit.get("build_metadata", {})
    if metadata.get("neoforge") != "21.11.45" or metadata.get("neoforge_version_range") != "[21.11.44,)":
        raise ValueError("G47 NeoForge metadata changed")
    if metadata.get("java_toolchain") != "21" or metadata.get("specification_version") != "27.38.0":
        raise ValueError("G47 Java/specification metadata changed")

    print("PASS: maintained Minecraft 1.21.11 frozen delta/scope/ownership validation")
    print("English: 334 total / 328 normal / 6 debug")
    print("G46 -> G47: 291 unchanged + 37 added + 11 removed + 6 changed")
    print("Ownership: 63 full + 26 supplements + 1 complete upstream = 90")
    print("Only exact same-key/same-English G46 semantics may be reused")
    print("Historical first port was Maven-only; maintained branch has CurseForge + Modrinth publishing configured")
    print(f"Frozen upstream literal-safety override keys: {scope.get('upstream_literal_safety_override_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

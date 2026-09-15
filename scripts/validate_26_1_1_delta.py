#!/usr/bin/env python3
"""Validate frozen Minecraft 26.1.1 / JEI 29.4.0 source, scope, ownership, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_26_1_1 as g49

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-26.1.1-language-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g49.parse_json(g49.BASE_SOURCE)
    target = g49.parse_json(g49.TARGET_SOURCE)
    scope = load(g49.SCOPE_PATH)
    diff = load(g49.DIFF_PATH)
    policy = load(g49.POLICY_PATH)
    audit = load(AUDIT_PATH)
    normal = {k for k in target if not k.startswith(g49.DEBUG_PREFIX)}

    if (len(base), len(target), len(normal), len(target)-len(normal)) != (309, 309, 303, 6):
        raise ValueError("G49 frozen English counts changed")
    if base != target:
        raise ValueError("G49 English semantics are no longer identical to G48")
    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (309, 0, 0, 0):
        raise ValueError("G49 frozen diff counts changed")
    if set(diff.get("unchanged_keys", [])) != set(target):
        raise ValueError("G49 unchanged-key set changed")

    full = set(scope["addon_full_locales"])
    supp = set(scope["selected_upstream_incomplete_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supp), len(complete)) != (64, 25, 1) or complete != {"en_us"}:
        raise ValueError("G49 ownership counts changed")
    if len(full | supp | complete) != 90 or full & supp or full & complete or supp & complete:
        raise ValueError("G49 selected ownership partition changed")
    if scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G49 unexpectedly contains malformed selected upstream locales")
    if "uk_ua" not in supp:
        raise ValueError("G49 uk_ua must remain a supplement locale")

    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= full:
        raise ValueError("G49 fallback scope changed")

    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g48_semantics"):
        raise ValueError("G49 G48 reuse policy changed")
    if reuse.get("all_target_keys_are_unchanged_from_g48") is not True:
        raise ValueError("G49 identical-semantics policy changed")
    if reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G49 cross-key reuse must remain forbidden")
    if reuse.get("placeholder_and_technical_literal_safety_required") is not True:
        raise ValueError("G49 literal-safety requirement changed")

    overrides = scope.get("upstream_literal_safety_overrides", {})
    override_count = sum(len(v) for v in overrides.values())
    if override_count != scope.get("upstream_literal_safety_override_count"):
        raise ValueError("G49 safety-override count mismatch")
    if set(overrides) - supp:
        raise ValueError("G49 safety overrides exist outside supplement locales")

    if audit.get("jei_upstream_commit") != g49.G49_COMMIT:
        raise ValueError("G49 audit endpoint changed")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("first_26_1_1_commit") != "b1ebe15147adb0bded6f3e5ccf86b35124fa5929":
        raise ValueError("G49 first endpoint changed")
    if endpoint.get("final_26_1_1_endpoint") != g49.G49_COMMIT:
        raise ValueError("G49 final endpoint changed")
    if endpoint.get("next_patch_commit") != "481a64808dab4ea205772a7289cc766804f5f5d7":
        raise ValueError("G49 next-patch boundary changed")
    if endpoint.get("next_minecraft_version") != "26.1.2":
        raise ValueError("G49 next Minecraft boundary changed")

    metadata = audit.get("build_metadata", {})
    if metadata.get("neoforge") != "26.1.1.1-beta" or metadata.get("neoforge_version_range") != "[26.1.0.8-beta,)":
        raise ValueError("G49 NeoForge metadata changed")
    if metadata.get("java_toolchain") != "25" or metadata.get("specification_version") != "29.4.0":
        raise ValueError("G49 Java/specification metadata changed")
    completeness = audit.get("selected_upstream_completeness", {})
    if completeness.get("uk_ua", {}).get("missing_normal_key_count") != 4:
        raise ValueError("G49 uk_ua missing-key count changed")

    print("PASS: Minecraft 26.1.1 frozen delta/scope/ownership validation")
    print("English: 309 total / 303 normal / 6 debug")
    print("G48 -> G49: 309 unchanged + 0 added + 0 removed + 0 changed")
    print("Ownership: 64 full + 25 supplements + 1 complete upstream = 90")
    print("Only exact same-key/same-English G48 semantics may be reused")
    print("Build: JEI 29.4.0 / NeoForge 26.1.1.1-beta / Java 25")
    print(f"Frozen upstream literal-safety override keys: {override_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

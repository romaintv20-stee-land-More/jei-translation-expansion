#!/usr/bin/env python3
"""Validate frozen Minecraft 26.1.2 / JEI 29.37.0 source, scope, ownership, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_26_1_2 as g50

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-26.1.2-language-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g50.parse_json(g50.BASE_SOURCE)
    target = g50.parse_json(g50.TARGET_SOURCE)
    scope = load(g50.SCOPE_PATH)
    diff = load(g50.DIFF_PATH)
    policy = load(g50.POLICY_PATH)
    audit = load(AUDIT_PATH)
    normal = {k for k in target if not k.startswith(g50.DEBUG_PREFIX)}

    unchanged = {k for k in set(base) & set(target) if base[k] == target[k]}
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {k for k in set(base) & set(target) if base[k] != target[k]}
    if (len(base), len(target), len(normal), len(target)-len(normal)) != (309, 334, 328, 6):
        raise ValueError("G50 frozen English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (294, 34, 9, 6):
        raise ValueError("G50 semantic delta changed")
    if set(diff.get("unchanged_keys", [])) != unchanged:
        raise ValueError("G50 unchanged-key set changed")
    if set(diff.get("added_keys", [])) != added or set(diff.get("removed_keys", [])) != removed:
        raise ValueError("G50 added/removed key sets changed")
    if set(diff.get("changed_english_values", {})) != changed:
        raise ValueError("G50 changed-English key set changed")

    full = set(scope["addon_full_locales"])
    supp = set(scope["selected_upstream_incomplete_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supp), len(complete)) != (63, 26, 1) or complete != {"en_us"}:
        raise ValueError("G50 ownership counts changed")
    if len(full | supp | complete) != 90 or full & supp or full & complete or supp & complete:
        raise ValueError("G50 selected ownership partition changed")
    if "fil_ph" not in supp:
        raise ValueError("G50 fil_ph ownership transition changed")
    if scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G50 unexpectedly contains malformed selected upstream locales")

    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= full:
        raise ValueError("G50 fallback scope changed")

    reuse = policy.get("translation_reuse", {})
    if reuse.get("reuse_only_exact_same_key_same_english") is not True:
        raise ValueError("G50 exact-semantic reuse policy changed")
    if reuse.get("eligible_unchanged_semantics") != 294 or reuse.get("novel_or_changed_semantics") != 40:
        raise ValueError("G50 semantic policy counts changed")
    if reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G50 cross-key reuse must remain forbidden")
    if reuse.get("placeholder_and_technical_literal_safety_required") is not True:
        raise ValueError("G50 literal-safety requirement changed")

    overrides = scope.get("upstream_literal_safety_overrides", {})
    override_count = sum(len(v) for v in overrides.values())
    if override_count != scope.get("upstream_literal_safety_override_count"):
        raise ValueError("G50 safety-override count mismatch")
    if set(overrides) - supp:
        raise ValueError("G50 safety overrides exist outside supplement locales")

    if audit.get("jei_upstream_commit") != g50.G50_COMMIT:
        raise ValueError("G50 audit snapshot changed")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("first_26_1_2_commit") != "481a64808dab4ea205772a7289cc766804f5f5d7":
        raise ValueError("G50 first 26.1.2 commit changed")
    if endpoint.get("base_26_1_1_endpoint") != "5a2ecc40c438e9137a8b64b2d9b48c095fc24c23":
        raise ValueError("G50 base endpoint changed")
    if endpoint.get("maintained_branch") != "26.1" or endpoint.get("pinned_26_1_2_snapshot") != g50.G50_COMMIT:
        raise ValueError("G50 maintained-branch snapshot metadata changed")

    metadata = audit.get("build_metadata", {})
    if metadata.get("neoforge") != "26.1.2.99" or metadata.get("neoforge_version_range") != "[26.1.2.99,)":
        raise ValueError("G50 NeoForge metadata changed")
    if metadata.get("java_toolchain") != "25" or metadata.get("specification_version") != "29.37.0":
        raise ValueError("G50 Java/specification metadata changed")

    print("PASS: Minecraft 26.1.2 frozen delta/scope/ownership validation")
    print("English: 334 total / 328 normal / 6 debug")
    print("G49 -> G50: 294 unchanged + 34 added + 9 removed + 6 changed")
    print("Ownership: 63 full + 26 supplements + 1 complete upstream = 90")
    print("Only exact same-key/same-English G49 semantics may be reused")
    print("Build: JEI 29.37.0 / NeoForge 26.1.2.99 / Java 25")
    print(f"Frozen upstream literal-safety override keys: {override_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

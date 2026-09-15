#!/usr/bin/env python3
"""Validate frozen G45 / Minecraft 1.21.9 source, scope, ownership, reuse, and literal-safety policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21_9 as g45

ROOT = Path(__file__).resolve().parents[1]
RENAMES = {
    "jei.key.category.overlays": "key.category.jei.overlays",
    "jei.key.category.recipe.gui": "key.category.jei.recipe.gui",
    "jei.key.category.cheat.mode": "key.category.jei.cheat.mode",
    "jei.key.category.hover.config.button": "key.category.jei.hover.config.button",
    "jei.key.category.edit.mode": "key.category.jei.edit.mode",
    "jei.key.category.mouse.hover": "key.category.jei.mouse.hover",
    "jei.key.category.search": "key.category.jei.search",
    "jei.key.category.dev.tools": "key.category.jei.dev.tools",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g45.parse_json(g45.BASE_SOURCE)
    target = g45.parse_json(g45.TARGET_SOURCE)
    diff = load(g45.DIFF_PATH)
    scope = load(g45.SCOPE_PATH)
    policy = load(g45.POLICY_PATH)

    unchanged, added, removed, changed = g45.semantic_sets(base, target)
    if (len(base), len(target)) != (305, 305):
        raise ValueError(f"G45 source counts changed: {len(base)}/{len(target)}")
    normal = {k for k in target if not k.startswith(g45.DEBUG_PREFIX)}
    debug = set(target) - normal
    if (len(normal), len(debug)) != (299, 6):
        raise ValueError(f"G45 normal/debug counts changed: {len(normal)}/{len(debug)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (297, 8, 8, 0):
        raise ValueError("G45 semantic delta changed")
    if added != set(RENAMES.values()) or removed != set(RENAMES):
        raise ValueError("G45 category-key rename set changed")
    if changed:
        raise ValueError(f"G45 unexpectedly changes English values: {sorted(changed)}")

    for old, new in RENAMES.items():
        if base[old] != target[new]:
            raise ValueError(f"G45 renamed key meaning changed: {old} -> {new}")
        if old in target or new in base:
            raise ValueError(f"G45 rename is not a clean old/new migration: {old} -> {new}")

    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (297, 8, 8, 0):
        raise ValueError("G45 frozen diff counts changed")
    if set(diff.get("added_keys", [])) != added or set(diff.get("removed_keys", [])) != removed:
        raise ValueError("G45 frozen diff key sets changed")

    if scope.get("minecraft_version") != "1.21.9" or scope.get("jei_version") != "25.0.1":
        raise ValueError("G45 scope target changed")
    if scope.get("upstream_commit") != g45.G45_COMMIT:
        raise ValueError("G45 scope upstream pin changed")
    if scope.get("selected_scope_count") != 90 or scope.get("selected_scope_changed_from_1.21.8") is not False:
        raise ValueError("G45 selected Minecraft language scope changed")
    if scope.get("addon_full_locale_count") != 65:
        raise ValueError("G45 full/override count changed")
    if scope.get("selected_upstream_incomplete_locale_count") != 24:
        raise ValueError("G45 supplement count changed")
    if scope.get("selected_upstream_complete_locale_count") != 1 or scope.get("selected_upstream_complete_locales") != ["en_us"]:
        raise ValueError("G45 complete-upstream ownership changed")
    if scope.get("malformed_upstream_full_override_locales") != ["uk_ua"]:
        raise ValueError("G45 malformed override ownership changed")
    if scope.get("documented_full_english_fallback_count") != 30:
        raise ValueError("G45 documented fallback count changed")
    expected_safety_overrides = {}
    for locale in scope["selected_upstream_incomplete_locales"]:
        upstream = g45.fetch_g45_upstream(locale)
        unsafe = [
            key for key in sorted(normal & set(upstream))
            if not g45.preserves_runtime_literals(target[key], upstream[key])
        ]
        if unsafe:
            expected_safety_overrides[locale] = unsafe
    if sum(len(keys) for keys in expected_safety_overrides.values()) != 89:
        raise ValueError("G45 upstream literal safety override count changed")
    if scope.get("upstream_literal_safety_overrides") != expected_safety_overrides:
        raise ValueError("G45 upstream literal safety override set changed")
    supplement_policy = scope.get("upstream_supplement_policy", {})
    if supplement_policy.get("supplement_missing_keys_plus_explicit_safety_overrides") is not True:
        raise ValueError("G45 explicit supplement safety-override policy missing")
    if supplement_policy.get("explicit_upstream_owned_override_keys") != expected_safety_overrides:
        raise ValueError("G45 explicit upstream-owned override key set changed")
    if supplement_policy.get("never_emit_other_upstream_owned_keys") is not True:
        raise ValueError("G45 supplement policy no longer protects other upstream-owned keys")
    if len(set(scope["addon_full_locales"]) | set(scope["selected_upstream_incomplete_locales"]) | set(scope["selected_upstream_complete_locales"])) != 90:
        raise ValueError("G45 ownership does not cover exactly 90 selected locales")

    reuse = policy.get("translation_reuse", {})
    if reuse.get("reuse_exact_unchanged_g44_semantics") is not True:
        raise ValueError("G45 exact unchanged-key inheritance disabled")
    if reuse.get("category_renames_must_not_reuse_old_key_values") is not True:
        raise ValueError("G45 old-key rename protection disabled")
    if reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G45 cross-key reuse must remain forbidden")
    if reuse.get("future_donor_commit") != g45.DONOR_COMMIT:
        raise ValueError("G45 donor pin changed")
    if reuse.get("future_donor_allowed_only_for_exact_same_key_same_english") is not True:
        raise ValueError("G45 donor semantic guard changed")
    if policy.get("upstream_literal_safety_overrides") != expected_safety_overrides:
        raise ValueError("G45 policy upstream literal safety override set changed")

    donor_en = g45.donor_english()
    for key in added:
        if donor_en.get(key) != target[key]:
            raise ValueError(f"G45 donor English mismatch for {key}")

    print("PASS: Minecraft 1.21.9 frozen delta/source/scope validation")
    print("305 keys = 299 normal + 6 debug")
    print("G44 -> G45: 297 unchanged + 8 added + 8 removed + 0 changed")
    print("Eight category localization IDs are renames; cross-key translation reuse remains forbidden")
    print("Ownership: 65 full/override + 24 supplements + 1 complete upstream = 90")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

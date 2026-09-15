#!/usr/bin/env python3
"""Freeze deterministic G48 / Minecraft 26.1 source, ownership, diff, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import audit_26_1 as audit
import reconstruct_1_21_11 as g47

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.11" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.11-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "26.1" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.11-to-26.1.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-26.1-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-26.1-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g48-mc26.1" / "policy.json"
DEBUG_PREFIX = audit.DEBUG_PREFIX

EXPECTED_ADDED = {
    "jei.config.client.bookmarkList.buttonNavigationVisibility",
    "jei.config.client.bookmarkList.buttonNavigationVisibility.description",
    "jei.config.client.ingredientList.buttonNavigationVisibility",
    "jei.config.client.ingredientList.buttonNavigationVisibility.description",
    "jei.config.debug.debug.crashingTestItemsEnabled",
    "jei.config.debug.debug.crashingTestItemsEnabled.description",
    "jei.config.debug.debug.debugMode",
    "jei.config.debug.debug.debugMode.description",
    "jei.tooltip.bookmarks.recipe",
}
EXPECTED_REMOVED = {
    "gui.jei.search",
    "jei.config.client.advanced.recipeSyncWarningEnabled",
    "jei.config.client.advanced.recipeSyncWarningEnabled.description",
    "jei.config.client.appearance.toastReflowEnabled",
    "jei.config.client.appearance.toastReflowEnabled.description",
    "jei.config.client.bookmarkList.layoutMode",
    "jei.config.client.bookmarkList.layoutMode.description",
    "jei.config.client.bookmarkList.navigationMode",
    "jei.config.client.bookmarkList.navigationMode.description",
    "jei.config.client.bookmarkList.navigationVisibility",
    "jei.config.client.bookmarkList.navigationVisibility.description",
    "jei.config.client.bookmarks.bookmarkOutputAsRecipe",
    "jei.config.client.bookmarks.bookmarkOutputAsRecipe.description",
    "jei.config.client.ingredientList.layoutMode",
    "jei.config.client.ingredientList.layoutMode.description",
    "jei.config.client.ingredientList.navigationMode",
    "jei.config.client.ingredientList.navigationMode.description",
    "jei.config.client.ingredientList.navigationVisibility",
    "jei.config.client.ingredientList.navigationVisibility.description",
    "jei.config.client.input.recipeSlotCyclingEnabled",
    "jei.config.client.input.recipeSlotCyclingEnabled.description",
    "jei.config.debug.debug.debugIngredientsEnabled",
    "jei.config.debug.debug.debugIngredientsEnabled.description",
    "jei.message.server.recipe.sync.error",
    "jei.message.server.recipe.sync.jei.missing",
    "jei.message.server.recipe.sync.unavailable",
    "jei.message.server.recipe.sync.vanilla",
    "jei.tooltip.bookmarks.preview.pin.usage",
    "jei.tooltip.recipe.any",
    "jei.tooltip.recipe.any_fuel",
    "jei.tooltip.recipe.slot.options",
    "key.jei.pauseRecipeCycling",
    "key.jei.recipeForward",
    "key.jei.shareToChat",
}
EXPECTED_CHANGED = {
    "jei.config.client.tooltips.holdShiftToShowBookmarkTooltipFeatures",
    "jei.config.client.tooltips.holdShiftToShowBookmarkTooltipFeatures.description",
    "jei.tooltip.bookmarks.tooltips.usage",
    "jei.tooltip.recipe.tag",
    "jei.tooltip.show.all.recipes.hotkey",
    "jei.tooltip.show.recipes",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    base = audit.clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    previous_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        raise ValueError(f"G47 selected scope changed: {len(selected)}")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal), len(target) - len(normal)) != (334, 309, 303, 6):
        raise ValueError(f"unexpected G48 source counts: {len(base)}/{len(target)}/{len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (294, 9, 34, 6):
        raise ValueError("unexpected G47 -> G48 semantic partition")
    if set(added) != EXPECTED_ADDED or set(removed) != EXPECTED_REMOVED or set(changed) != EXPECTED_CHANGED:
        raise ValueError(f"G48 semantic key sets changed: added={added} removed={removed} changed={changed}")

    first_release = audit.fetch_json(audit.COMMIT_API.format(commit=audit.FIRST_RELEASE_COMMIT))
    if "Minecraft 26.1" not in first_release.get("commit", {}).get("message", ""):
        raise ValueError("G48 first-release marker changed")
    next_patch = audit.fetch_json(audit.COMMIT_API.format(commit=audit.NEXT_PATCH_COMMIT))
    audit.assert_single_parent(next_patch, audit.FINAL_ENDPOINT, "26.1.1 support commit")
    if "26.1.1" not in next_patch.get("commit", {}).get("message", ""):
        raise ValueError("G48 next-patch boundary changed")

    props = audit.fetch_text(f"{audit.RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=25",
        "minecraftVersion=26.1",
        "minecraftVersionRange=[26.1, 26.1]",
        "neoforgeVersion=26.1.0.8-beta",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[26.1.0.8-beta,)",
        "curseProjectId=238222",
        "modrinthId=u6dRKJwZ",
        "specificationVersion=29.2.0",
    ):
        if token not in props:
            raise ValueError(f"G48 metadata missing {token}")

    contents = audit.fetch_json(audit.LANG_API)
    upstream_locales = sorted(
        Path(x["name"]).stem.lower()
        for x in contents
        if x.get("type") == "file" and str(x.get("name", "")).endswith(".json")
    )
    upstream_set = set(upstream_locales)
    completeness: dict[str, dict] = {}
    parsed: dict[str, dict[str, str]] = {}
    malformed: dict[str, str] = {}
    for locale in sorted(selected & upstream_set):
        values, error = audit.parse_locale(locale)
        if error is not None or values is None:
            malformed[locale] = error or "unknown JSON error"
            continue
        parsed[locale] = values
        missing = sorted(normal - set(values))
        completeness[locale] = {
            "present_normal_key_count": len(normal & set(values)),
            "target_normal_key_count": len(normal),
            "missing_normal_key_count": len(missing),
            "missing_normal_keys": missing,
            "extra_key_count": len(set(values) - set(target)),
            "extra_keys": sorted(set(values) - set(target)),
            "malformed_upstream_json": False,
        }
    if malformed:
        raise ValueError(f"G48 selected upstream JSON must all be valid: {malformed}")
    usable = selected & upstream_set
    complete = sorted(x for x in usable if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable)
    if (len(addon_full), len(incomplete), len(complete)) != (64, 25, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected G48 ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")
    if "uk_ua" not in incomplete or completeness["uk_ua"]["missing_normal_key_count"] != 4:
        raise ValueError("G48 expects uk_ua to be valid upstream with 4 missing normal keys")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.11")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "26.1")
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(
            f"G48 Minecraft language membership changed: added={live_added} removed={live_removed} "
            f"absent={sorted(selected-target_codes)}"
        )

    fallback_locales = list(previous_scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 30 or not set(fallback_locales) <= set(addon_full):
        raise ValueError("G48 documented fallback ownership changed")

    upstream_literal_safety_overrides: dict[str, list[str]] = {}
    for locale in incomplete:
        values = parsed[locale]
        unsafe = [
            key for key in sorted(normal & set(values))
            if not g47.preserves_runtime_literals(target[key], values[key])
        ]
        if unsafe:
            upstream_literal_safety_overrides[locale] = unsafe
    override_count = sum(len(keys) for keys in upstream_literal_safety_overrides.values())

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "base_minecraft": "1.21.11",
        "base_jei": "27.38.0",
        "target_minecraft": "26.1",
        "target_jei": "29.2.0",
        "base_key_count": len(base),
        "target_key_count": len(target),
        "target_normal_key_count": len(normal),
        "target_debug_only_key_count": len(target) - len(normal),
        "unchanged_key_and_value_count": len(unchanged),
        "added_key_count": len(added),
        "removed_key_count": len(removed),
        "changed_english_value_count": len(changed),
        "unchanged_keys": unchanged,
        "added_keys": added,
        "removed_keys": removed,
        "changed_english_values": {k: {"old": base[k], "new": target[k]} for k in changed},
        "note": "Only identical same-key English semantics may inherit G47 translations; added and changed meanings use target-owned values or exact target English.",
    })

    publication = {
        "curse_project_id": "238222",
        "modrinth_id": "u6dRKJwZ",
        "public_distribution_configured": True,
    }
    scope = {
        "minecraft_version": "26.1",
        "jei_version": "29.2.0",
        "upstream_commit": audit.PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.11-language-scope.json",
        "raw_language_count": len(target_codes),
        "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.11": False,
        "runtime_locale_filename_case": "lowercase",
        "resource_format": "json",
        "selected_upstream_complete_locales": complete,
        "selected_upstream_complete_locale_count": len(complete),
        "selected_upstream_incomplete_locales": incomplete,
        "selected_upstream_incomplete_locale_count": len(incomplete),
        "malformed_upstream_full_override_locales": [],
        "malformed_upstream_full_override_locale_count": 0,
        "jei_upstream_unselected_or_nonmatching_locales": sorted(upstream_set - selected),
        "addon_full_locale_count": len(addon_full),
        "addon_full_locales": addon_full,
        "new_selected_primary_languages": [],
        "removed_selected_languages": [],
        "downloaded": {
            "base_asset_index_id": str(base_meta["assetIndex"].get("id")),
            "base_asset_index_sha1": base_meta["assetIndex"].get("sha1"),
            "asset_index_id": str(target_meta["assetIndex"].get("id")),
            "asset_index_sha1": target_meta["assetIndex"].get("sha1"),
            "language_asset_file_count": len(target_codes),
            "live_language_asset_additions_from_1.21.11": live_added,
            "live_language_asset_removals_from_1.21.11": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales,
        "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_full_locale_count": len(addon_full) - len(fallback_locales),
        "translation_delta": {
            "base_generation": "g47-mc1.21.11",
            "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": len(changed),
            "reuse_exact_g47_for_unchanged_meanings": True,
            "added_or_changed_project_owned_values_use_exact_target_english": True,
        },
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": override_count,
        "upstream_supplement_policy": {
            "preserve_existing_safe_upstream_keys": True,
            "supplement_missing_keys_plus_explicit_safety_overrides": True,
            "explicit_upstream_owned_override_keys": upstream_literal_safety_overrides,
            "reuse_exact_g47_combined_value_only_for_unchanged_key_and_english": True,
            "cross_key_reuse_allowed": False,
            "never_emit_other_upstream_owned_keys": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "publication_context": publication,
        "source_audit": "upstream/minecraft-26.1-language-audit.json",
        "english_diff": "upstream/diffs/1.21.11-to-26.1.json",
    }
    write_json(SCOPE_PATH, scope)

    write_json(AUDIT_PATH, {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "verified-source-scope-and-upstream-ownership",
        "minecraft": "26.1",
        "jei": "29.2.0",
        "jei_upstream_commit": audit.PINNED_COMMIT,
        "endpoint_resolution": {
            "first_26_1_release_commit": audit.FIRST_RELEASE_COMMIT,
            "final_26_1_endpoint": audit.FINAL_ENDPOINT,
            "next_patch_commit": audit.NEXT_PATCH_COMMIT,
            "next_minecraft_version": "26.1.1",
            "note": "The 26.1.1 support commit directly follows the final exact-26.1 endpoint.",
        },
        "build_metadata": {
            "neoforge": "26.1.0.8-beta",
            "neoforge_loader_version_range": "[4,)",
            "neoforge_version_range": "[26.1.0.8-beta,)",
            "java_toolchain": "25",
            "specification_version": "29.2.0",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_1.21.11": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
        },
        "minecraft_asset_indexes": scope["downloaded"],
        "english_source": {
            "base_key_count": len(base),
            "target_key_count": len(target),
            "target_normal_key_count": len(normal),
            "target_debug_only_key_count": len(target) - len(normal),
            "unchanged_key_and_value_count": len(unchanged),
            "added_keys": added,
            "removed_keys": removed,
            "changed_english_values": {k: {"old": base[k], "new": target[k]} for k in changed},
        },
        "upstream_locale_file_count": len(upstream_locales),
        "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness,
        "selected_upstream_complete_locales": complete,
        "selected_upstream_incomplete_locales": incomplete,
        "addon_full_locales": addon_full,
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "publication_context": publication,
    })

    write_json(POLICY_PATH, {
        "schema_version": 1,
        "generation": "g48-mc26.1",
        "minecraft": "26.1",
        "jei": "29.2.0",
        "upstream_commit": audit.PINNED_COMMIT,
        "selected_scope_count": 90,
        "ownership": {
            "addon_full": len(addon_full),
            "upstream_missing_key_supplements": len(incomplete),
            "upstream_complete": len(complete),
        },
        "translation_reuse": {
            "base_generation": "g47-mc1.21.11",
            "reuse_exact_unchanged_g47_semantics": True,
            "same_key_required": True,
            "same_english_required": True,
            "cross_key_reuse_allowed": False,
            "project_owned_added_or_changed_keys_use_exact_target_english": True,
            "removed_keys_must_not_be_emitted": True,
        },
        "upstream_policy": scope["upstream_supplement_policy"],
        "documented_full_english_fallback_locales": fallback_locales,
        "publication_context": publication,
        "runtime_promotion_requires_resource_stack_validation": True,
    })

    print("PASS: froze deterministic G48 Minecraft 26.1 manifests")
    print("English: 309 total / 303 normal / 6 debug")
    print("G47 -> G48: 294 unchanged + 9 added + 34 removed + 6 changed")
    print("Ownership: 64 full + 25 supplements + 1 complete upstream = 90")
    print(f"Frozen upstream literal-safety override keys: {override_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

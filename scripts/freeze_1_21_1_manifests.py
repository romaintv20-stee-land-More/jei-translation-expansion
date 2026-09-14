#!/usr/bin/env python3
"""Freeze deterministic G39 Minecraft 1.21.1 source/scope/policy manifests from pinned sources."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21-to-1.21.1.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g39-mc1.21.1" / "policy.json"
DEBUG_PREFIX = "description.jei."
G39_COMMIT = "28eb51f58d2798512a2ef75cf8b29189228573ad"
UPSTREAM_COMPLETE = ["en_us", "ja_jp"]
UPSTREAM_INCOMPLETE = [
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "kk_kz", "ko_kr", "lt_lt", "no_no", "pl_pl", "pt_br",
    "ru_ru", "sv_se", "tr_tr", "uk_ua", "vi_vn", "zh_cn",
]
UPSTREAM_UNSELECTED = ["pt_pt", "zh_tw"]
NEWLY_UPSTREAM = ["kk_kz", "no_no", "vi_vn"]


def parse(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> int:
    base = parse(BASE_SOURCE)
    target = parse(TARGET_SOURCE)
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    base_selected = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    normal_added = [k for k in added if not k.startswith(DEBUG_PREFIX)]
    normal_changed = [k for k in changed if not k.startswith(DEBUG_PREFIX)]
    debug_changed = [k for k in changed if k.startswith(DEBUG_PREFIX)]
    normal_target = {k for k in target if not k.startswith(DEBUG_PREFIX)}

    if (len(base), len(target), len(normal_target)) != (176, 286, 280):
        raise RuntimeError("G39 source counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (76, 167, 57, 43):
        raise RuntimeError("G39 semantic delta counts changed")
    if (len(normal_added), len(normal_changed), len(debug_changed)) != (167, 41, 2):
        raise RuntimeError("G39 normal/debug changed partition changed")

    complete = set(UPSTREAM_COMPLETE)
    incomplete = set(UPSTREAM_INCOMPLETE)
    addon_full = base_selected - complete - incomplete
    if len(base_selected) != 90 or len(addon_full) != 64 or len(incomplete) != 24 or len(complete) != 2:
        raise RuntimeError("G39 ownership partition changed")
    if set(NEWLY_UPSTREAM) != set(base_scope["addon_full_locales"]) & (complete | incomplete):
        raise RuntimeError("G39 newly-upstream migration set changed")

    base_fallback = set(base_scope["documented_full_english_fallback_locales"])
    fallback = sorted(base_fallback & addon_full)
    if len(fallback) != 30:
        raise RuntimeError("G39 fallback full-locale count changed")
    translated_full = sorted(addon_full - set(fallback))
    if len(translated_full) != 34:
        raise RuntimeError("G39 translated full-locale count changed")

    diff = {
        "schema_version": 1,
        "base_minecraft": "1.21",
        "base_jei": "19.8.2",
        "target_minecraft": "1.21.1",
        "target_jei": "19.21.1",
        "base_key_count": len(base),
        "target_key_count": len(target),
        "target_normal_key_count": len(normal_target),
        "target_debug_only_key_count": len(target) - len(normal_target),
        "unchanged_key_and_value_count": len(unchanged),
        "added_key_count": len(added),
        "removed_key_count": len(removed),
        "changed_english_value_count": len(changed),
        "changed_debug_only_key_count": len(debug_changed),
        "review_required_normal_added_or_changed_key_count": len(normal_added) + len(normal_changed),
        "unchanged_keys": unchanged,
        "added_keys": added,
        "removed_keys": removed,
        "changed_english_values": {k: {"before": base[k], "after": target[k]} for k in changed},
        "normal_added_keys": normal_added,
        "normal_changed_keys": normal_changed,
        "debug_changed_keys": debug_changed,
        "reuse_rule": "Automatic reuse is allowed only for the 76 exact same key+English-value pairs. All 208 normal added/changed meanings require explicit G39 treatment; removed keys are dropped.",
    }
    write(DIFF_PATH, diff)

    scope = {
        "minecraft_version": "1.21.1",
        "jei_version": "19.21.1",
        "upstream_commit": G39_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21-language-scope.json",
        "raw_language_count": 143,
        "raw_language_count_note": "Minecraft 1.21.1 has the same 143 live language asset files as 1.21. The selected historical primary-language scope remains frozen at 90 languages.",
        "selected_scope_count": 90,
        "selected_scope_changed_from_1.21": False,
        "runtime_locale_filename_case": "lowercase",
        "resource_format": "json",
        "selected_upstream_locale_count": len(complete | incomplete),
        "selected_upstream_complete_locales": sorted(complete),
        "selected_upstream_complete_locale_count": len(complete),
        "selected_upstream_incomplete_locales": sorted(incomplete),
        "selected_upstream_incomplete_locale_count": len(incomplete),
        "jei_upstream_unselected_or_nonmatching_locales": UPSTREAM_UNSELECTED,
        "addon_full_locale_count": len(addon_full),
        "addon_full_locales": sorted(addon_full),
        "removed_selected_languages": [],
        "new_selected_primary_languages": [],
        "downloaded": {
            "base_asset_index_id": "17",
            "base_asset_index_sha1": "5f5b25053629ea06987a0b1eb1c34a70f0b67dd8",
            "asset_index_id": "17",
            "asset_index_sha1": "5f5b25053629ea06987a0b1eb1c34a70f0b67dd8",
            "language_asset_file_count": 143,
            "live_language_asset_additions_from_1.21": [],
            "live_language_asset_removals_from_1.21": [],
        },
        "documented_full_english_fallback_locales": fallback,
        "documented_full_english_fallback_count": len(fallback),
        "translated_or_ai_assisted_full_locale_count": len(translated_full),
        "translation_delta": {
            "base_generation": "g38-mc1.21",
            "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": len(added),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(debug_changed),
            "removed_key_count": len(removed),
            "normal_added_or_changed_key_count": len(normal_added) + len(normal_changed),
            "reuse_exact_g38_for_unchanged_meanings": True,
        },
        "ownership_changes_from_g38": {
            "newly_complete_upstream": [],
            "complete_to_incomplete": [],
            "newly_upstream_from_addon_full": NEWLY_UPSTREAM,
            "no_longer_upstream": [],
            "new_addon_full_locales": [],
            "removed_addon_full_locales": NEWLY_UPSTREAM,
            "complete_count": len(complete),
            "supplement_count": len(incomplete),
            "addon_full_count": len(addon_full),
        },
        "upstream_supplement_policy": {
            "preserve_existing_upstream_keys": True,
            "supplement_only_exact_missing_normal_keys": True,
            "reuse_exact_g38_combined_value_only_for_unchanged_key_and_english": True,
            "changed_or_added_keys_require_reviewed_g39_treatment": True,
            "cross_key_reuse_allowed": False,
            "never_emit_upstream_owned_key": True,
            "retire_supplement_when_upstream_becomes_complete": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "source_audit": "upstream/minecraft-1.21.1-language-audit.json",
        "english_diff": "upstream/diffs/1.21-to-1.21.1.json",
    }
    write(SCOPE_PATH, scope)

    audit = {
        "schema_version": 1,
        "audit_date": "2026-09-14",
        "status": "verified-source-scope-and-upstream-ownership; translation-delta-in-progress",
        "minecraft": "1.21.1",
        "jei": "19.21.1",
        "jei_upstream_commit": G39_COMMIT,
        "endpoint_resolution": {
            "first_1_21_1_commit": "8eb79e0c8f7063fa2a7cc0eb8d31a0c2882532e8",
            "final_1_21_1_commit": G39_COMMIT,
            "next_minecraft_port_commit": "c0d0367841b16fa3a9567c3d93172cbd1f1b578c",
            "next_minecraft_version": "1.21.4",
            "note": "The parent of the 1.21.4 port is the final 1.21.1 endpoint. No separate mainline JEI 1.21.2 or 1.21.3 generation exists on this boundary.",
        },
        "build_metadata": {
            "neoforge": "21.1.116",
            "neoforge_version_range": "[21.0.118-beta,)",
            "forge_module_present_at_final_endpoint": False,
            "java_toolchain": "21",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_1.21": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
            "decoupled_assets": True,
        },
        "minecraft_asset_indexes": {
            "minecraft_1.21": {"id": "17", "sha1": "5f5b25053629ea06987a0b1eb1c34a70f0b67dd8", "language_file_count": 143},
            "minecraft_1.21.1": {"id": "17", "sha1": "5f5b25053629ea06987a0b1eb1c34a70f0b67dd8", "language_file_count": 143},
            "live_language_file_additions": [],
            "live_language_file_removals": [],
        },
        "jei_english": {
            "resource_format": "json",
            "key_count": len(target),
            "normal_key_count": len(normal_target),
            "debug_only_key_count": len(target) - len(normal_target),
        },
        "english_diff_from_1.21": {
            "unchanged_key_and_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(debug_changed),
            "review_required_normal_added_or_changed_key_count": len(normal_added) + len(normal_changed),
            "manifest": "upstream/diffs/1.21-to-1.21.1.json",
        },
        "jei_upstream_locale_count": 28,
        "selected_scope_count": 90,
        "selected_upstream_complete_locales": sorted(complete),
        "selected_upstream_incomplete_locales": sorted(incomplete),
        "upstream_unselected_or_nonmatching_locales": UPSTREAM_UNSELECTED,
        "addon_full_locale_count": len(addon_full),
        "ownership_changes_from_1.21": {
            "newly_complete_upstream": [],
            "complete_to_incomplete": [],
            "newly_upstream_from_addon_full": NEWLY_UPSTREAM,
            "no_longer_upstream": [],
            "removed_addon_full_locales": NEWLY_UPSTREAM,
            "complete_count": len(complete),
            "supplement_count": len(incomplete),
            "addon_full_count": len(addon_full),
        },
        "validation": {
            "exploratory_audit_run": 34903736813,
            "exploratory_audit_job": 104175478010,
            "result": "success",
            "complete_validation_run": None,
            "complete_validation_job": None,
        },
    }
    write(AUDIT_PATH, audit)

    policy = {
        "generation": "g39-mc1.21.1",
        "minecraft": "1.21.1",
        "jei": "19.21.1",
        "pinned_commit": G39_COMMIT,
        "resource_format": "json",
        "selected_scope_count": 90,
        "addon_full_locale_count": len(addon_full),
        "selected_upstream_complete_locale_count": len(complete),
        "selected_upstream_incomplete_locale_count": len(incomplete),
        "documented_full_english_fallback_count": len(fallback),
        "translated_or_ai_assisted_full_locale_count": len(translated_full),
        "english_diff": {
            "base_generation": "g38-mc1.21",
            "unchanged_key_and_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(debug_changed),
            "review_required_normal_added_or_changed_key_count": len(normal_added) + len(normal_changed),
        },
        "translation_reuse": {
            "rule": "Automatic reuse requires the exact same localization key and exact same English source value. Cross-key reuse is forbidden.",
            "base_generation": "g38-mc1.21",
            "reuse_exact_unchanged_g38_semantics": True,
            "cross_key_reuse_allowed": False,
            "changed_or_added_keys_require_reviewed_g39_treatment": True,
        },
        "ownership_change": {
            "newly_upstream_from_addon_full": NEWLY_UPSTREAM,
            "complete_count": len(complete),
            "supplement_count": len(incomplete),
            "addon_full_count": len(addon_full),
        },
        "fallback_policy": {
            "documented_full_english_fallback_allowed": True,
            "fallback_locales_are_complete": True,
            "low_confidence_new_or_changed_semantics_may_use_exact_target_english": True,
            "fallback_must_be_explicit_and_counted": True,
        },
        "later_upstream_backport_policy": {
            "allowed_only_if_same_key_and_exact_same_english_value": True,
            "donor_snapshot": "5593dfe99114c057f018d959bf4c147a70462fef",
            "never_override_g39_upstream_owned_key": True,
        },
        "translation_status": "in-progress-major-semantic-migration",
    }
    write(POLICY_PATH, policy)

    print("PASS: froze G39 source/scope/policy manifests")
    print("English: 286 keys / 280 normal / 6 debug")
    print("Delta: 76 unchanged + 167 added + 57 removed + 43 changed (2 debug)")
    print("Normal meanings requiring G39 treatment: 208")
    print("Ownership: 64 addon-full + 24 supplements + 2 complete upstream = 90")
    print("New upstream ownership: kk_kz, no_no, vi_vn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

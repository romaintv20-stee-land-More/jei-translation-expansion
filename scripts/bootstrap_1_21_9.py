#!/usr/bin/env python3
"""Freeze deterministic G45 / Minecraft 1.21.9 source, ownership, diff, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import audit_1_21_9 as audit

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.8" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.8-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.9" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.8-to-1.21.9.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.9-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.9-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g45-mc1.21.9" / "policy.json"
PINNED_COMMIT = audit.PINNED_COMMIT
NEXT_PORT_COMMIT = audit.NEXT_PORT_COMMIT
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
DONOR_LANG = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{DONOR_COMMIT}/Common/src/main/resources/assets/jei/lang"
DONOR_LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={DONOR_COMMIT}"
DEBUG_PREFIX = audit.DEBUG_PREFIX
EXPECTED_ADDED = audit.NEW_CATEGORY_KEYS
EXPECTED_REMOVED = audit.OLD_CATEGORY_KEYS
UPSTREAM_LITERAL_SAFETY_OVERRIDES = {"ar_sa": ["jei.config.client.search.description"]}
UPSTREAM_LITERAL_SAFETY_OVERRIDE_REASON = "Pinned ar_sa translation omits the fixed technical literal JEI; emit exact target English for this key."


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_donor_locale(locale: str) -> dict[str, str]:
    text = audit.fetch_text(f"{DONOR_LANG}/{locale}.json")
    try:
        return audit.clean(json.loads(text))
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        return audit.clean(json.loads(audit.repair_uk_ua(text)))


def main() -> int:
    base = audit.clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    previous_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(previous_scope["addon_full_locales"]) | set(previous_scope["selected_upstream_complete_locales"]) | set(previous_scope["selected_upstream_incomplete_locales"])
    if len(selected) != 90:
        raise ValueError(f"G44 selected scope changed: {len(selected)}")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal)) != (305, 305, 299):
        raise ValueError(f"unexpected G45 source counts: {len(base)}/{len(target)}/{len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (297, 8, 8, 0):
        raise ValueError("unexpected G44 -> G45 semantic partition")
    if set(added) != EXPECTED_ADDED or set(removed) != EXPECTED_REMOVED:
        raise ValueError(f"G45 key-category migration changed: added={added} removed={removed}")

    next_commit = audit.fetch_json(audit.NEXT_COMMIT_API)
    if [p["sha"] for p in next_commit.get("parents", [])] != [PINNED_COMMIT]:
        raise ValueError("G45 endpoint is no longer the direct parent of the 1.21.10 port")

    props = audit.fetch_text(f"{audit.RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.9",
        "minecraftVersionRange=[1.21.9, 1.21.10)",
        "neoforgeVersion=21.9.2-beta",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.9.2-beta,)",
        "specificationVersion=25.0.1",
    ):
        if token not in props:
            raise ValueError(f"pinned G45 metadata missing {token}")

    contents = audit.fetch_json(audit.LANG_API)
    upstream_locales = sorted(Path(x["name"]).stem.lower() for x in contents if x.get("type") == "file" and str(x.get("name", "")).endswith(".json"))
    upstream_set = set(upstream_locales)
    completeness: dict[str, dict] = {}
    malformed: set[str] = set()
    for locale in sorted(selected & upstream_set):
        values, repaired = audit.parse_locale(locale)
        if repaired:
            malformed.add(locale)
        missing = sorted(normal - set(values))
        completeness[locale] = {
            "present_normal_key_count": len(normal & set(values)),
            "target_normal_key_count": len(normal),
            "missing_normal_key_count": len(missing),
            "missing_normal_keys": missing,
            "extra_key_count": len(set(values) - set(target)),
            "extra_keys": sorted(set(values) - set(target)),
            "malformed_upstream_json": repaired,
        }
    if malformed != {"uk_ua"}:
        raise ValueError(f"unexpected malformed G45 selected upstream locales: {sorted(malformed)}")
    usable = (selected & upstream_set) - malformed
    complete = sorted(x for x in usable if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable)
    if (len(addon_full), len(incomplete), len(complete)) != (65, 24, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected G45 ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.8")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.9")
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(f"G45 Minecraft language membership changed: added={live_added} removed={live_removed} absent={sorted(selected-target_codes)}")

    donor_en = audit.clean(json.loads(audit.fetch_text(f"{DONOR_LANG}/en_us.json")))
    donor_exact_added = sorted(key for key in added if donor_en.get(key) == target[key])
    if set(donor_exact_added) != EXPECTED_ADDED:
        raise ValueError(f"donor snapshot does not preserve all G45 added English semantics exactly: {donor_exact_added}")
    donor_contents = audit.fetch_json(DONOR_LANG_API)
    donor_locales = {Path(x["name"]).stem.lower() for x in donor_contents if x.get("type") == "file" and str(x.get("name", "")).endswith(".json")}
    donor_coverage: dict[str, list[str]] = {}
    for locale in sorted(selected & donor_locales):
        try:
            values = parse_donor_locale(locale)
        except Exception:
            continue
        keys = sorted(key for key in donor_exact_added if key in values)
        if keys:
            donor_coverage[locale] = keys

    fallback_locales = list(previous_scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 30 or "uk_ua" in fallback_locales:
        raise ValueError("G45 documented fallback ownership changed")

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "base_minecraft": "1.21.8", "base_jei": "24.2.0",
        "target_minecraft": "1.21.9", "target_jei": "25.0.1",
        "base_key_count": len(base), "target_key_count": len(target),
        "target_normal_key_count": len(normal), "target_debug_only_key_count": len(target)-len(normal),
        "unchanged_key_and_value_count": len(unchanged), "added_key_count": len(added),
        "removed_key_count": len(removed), "changed_english_value_count": len(changed),
        "unchanged_keys": unchanged, "added_keys": added, "removed_keys": removed,
        "changed_english_values": {k: {"before": base[k], "after": target[k]} for k in changed},
        "note": "Eight Minecraft key-category localization IDs were renamed. Identical English values across different keys do not permit cross-key translation reuse.",
    })

    scope = {
        "minecraft_version": "1.21.9", "jei_version": "25.0.1", "upstream_commit": PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.8-language-scope.json",
        "raw_language_count": len(target_codes), "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.8": False, "runtime_locale_filename_case": "lowercase", "resource_format": "json",
        "selected_upstream_complete_locales": complete, "selected_upstream_complete_locale_count": len(complete),
        "selected_upstream_incomplete_locales": incomplete, "selected_upstream_incomplete_locale_count": len(incomplete),
        "malformed_upstream_full_override_locales": sorted(malformed), "malformed_upstream_full_override_locale_count": len(malformed),
        "jei_upstream_unselected_or_nonmatching_locales": sorted(upstream_set-selected),
        "addon_full_locale_count": len(addon_full), "addon_full_locales": addon_full,
        "new_selected_primary_languages": [], "removed_selected_languages": [],
        "downloaded": {
            "base_asset_index_id": str(base_meta["assetIndex"].get("id")), "base_asset_index_sha1": base_meta["assetIndex"].get("sha1"),
            "asset_index_id": str(target_meta["assetIndex"].get("id")), "asset_index_sha1": target_meta["assetIndex"].get("sha1"),
            "language_asset_file_count": len(target_codes), "live_language_asset_additions_from_1.21.8": live_added, "live_language_asset_removals_from_1.21.8": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales, "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_or_repaired_full_locale_count": len(addon_full)-len(fallback_locales),
        "translation_delta": {
            "base_generation": "g44-mc1.21.8", "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": 8, "removed_key_count": 8, "changed_english_value_count": 0,
            "reuse_exact_g44_for_unchanged_meanings": True,
            "category_key_rename_is_cross_key_reuse": True,
        },
        "exact_future_donor": {"commit": DONOR_COMMIT, "exact_same_key_same_english_added_keys": donor_exact_added, "locale_coverage": donor_coverage},
        "upstream_literal_safety_overrides": UPSTREAM_LITERAL_SAFETY_OVERRIDES,
        "upstream_literal_safety_override_reason": UPSTREAM_LITERAL_SAFETY_OVERRIDE_REASON,
        "upstream_supplement_policy": {
            "preserve_existing_upstream_keys": True,
            "supplement_only_exact_missing_normal_keys": False,
            "supplement_missing_keys_plus_explicit_safety_overrides": True,
            "explicit_upstream_owned_override_keys": UPSTREAM_LITERAL_SAFETY_OVERRIDES,
            "reuse_exact_g44_combined_value_only_for_unchanged_key_and_english": True,
            "future_donor_same_key_same_english_reuse_allowed": True,
            "cross_key_reuse_allowed": False,
            "never_emit_other_upstream_owned_keys": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "malformed_upstream_override_policy": {
            "locale": "uk_ua", "reason": "Pinned upstream uk_ua.json remains syntactically invalid; emit a valid full repair override.",
            "repair_is_frozen_and_minimal": True, "preserve_repaired_upstream_target_normal_values": True,
            "fill_missing_unchanged_keys_from_exact_safe_g44_combined_values": True,
            "fill_missing_added_keys_from_exact_same_key_donor_when_available": True,
            "emit_only_g45_target_keys": True,
        },
        "source_audit": "upstream/minecraft-1.21.9-language-audit.json", "english_diff": "upstream/diffs/1.21.8-to-1.21.9.json",
    }
    write_json(SCOPE_PATH, scope)

    audit_manifest = {
        "schema_version": 1, "audit_date": "2026-09-15", "status": "verified-source-scope-upstream-ownership-and-key-migration-policy",
        "minecraft": "1.21.9", "jei": "25.0.1", "jei_upstream_commit": PINNED_COMMIT,
        "endpoint_resolution": {"final_1_21_9_commit": PINNED_COMMIT, "next_minecraft_port_commit": NEXT_PORT_COMMIT, "next_minecraft_version": "1.21.10", "note": "The 1.21.10 port is directly parented by this endpoint."},
        "build_metadata": {"neoforge": "21.9.2-beta", "neoforge_loader_version_range": "[4,)", "neoforge_version_range": "[21.9.2-beta,)", "java_toolchain": "21", "language_format": "json", "locale_filename_case": "lowercase", "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json"},
        "language_scope": {"selected_scope_count": 90, "changed_from_1.21.8": False, "new_selected_primary_languages": [], "removed_selected_languages": [], "decoupled_assets": True},
        "minecraft_asset_indexes": {"minecraft_1.21.8": {"id": str(base_meta["assetIndex"].get("id")), "sha1": base_meta["assetIndex"].get("sha1"), "language_file_count": len(base_codes)}, "minecraft_1.21.9": {"id": str(target_meta["assetIndex"].get("id")), "sha1": target_meta["assetIndex"].get("sha1"), "language_file_count": len(target_codes)}, "live_language_file_additions": live_added, "live_language_file_removals": live_removed},
        "english_source": {"base_key_count": len(base), "target_key_count": len(target), "target_normal_key_count": len(normal), "target_debug_only_key_count": len(target)-len(normal), "unchanged_key_and_value_count": len(unchanged), "added_keys": added, "removed_keys": removed, "changed_english_values": {}},
        "upstream_locale_file_count": len(upstream_locales), "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness, "malformed_selected_upstream_locales": sorted(malformed),
        "selected_upstream_complete_locales": complete, "selected_upstream_incomplete_locales": incomplete, "addon_full_locales": addon_full,
        "future_donor_commit": DONOR_COMMIT, "future_donor_exact_added_keys": donor_exact_added, "future_donor_locale_coverage": donor_coverage,
        "upstream_literal_safety_overrides": UPSTREAM_LITERAL_SAFETY_OVERRIDES,
        "upstream_literal_safety_override_reason": UPSTREAM_LITERAL_SAFETY_OVERRIDE_REASON,
    }
    write_json(AUDIT_PATH, audit_manifest)

    policy = {
        "generation": "g45-mc1.21.9", "minecraft": "1.21.9", "jei": "25.0.1", "selected_scope_count": 90,
        "source_key_count": len(target), "normal_key_count": len(normal), "debug_only_key_count": len(target)-len(normal),
        "ownership": {"addon_full_or_repair": len(addon_full), "upstream_missing_key_supplements": len(incomplete), "upstream_complete": len(complete)},
        "english_diff": {"unchanged": 297, "added": 8, "removed": 8, "changed": 0, "added_keys": added, "removed_keys": removed},
        "translation_reuse": {
            "reuse_exact_unchanged_g44_semantics": True,
            "category_renames_must_not_reuse_old_key_values": True,
            "future_donor_commit": DONOR_COMMIT,
            "future_donor_allowed_only_for_exact_same_key_same_english": True,
            "cross_key_reuse_allowed": False,
            "uncertain_translation_fallback": "exact-target-English",
        },
        "malformed_upstream_full_override_locales": sorted(malformed),
        "upstream_literal_safety_overrides": UPSTREAM_LITERAL_SAFETY_OVERRIDES,
        "upstream_literal_safety_override_reason": UPSTREAM_LITERAL_SAFETY_OVERRIDE_REASON,
        "runtime_gate": "static translation/reconstruction validation does not promote candidate to release-jars",
    }
    write_json(POLICY_PATH, policy)

    print("PASS: froze G45 Minecraft 1.21.9 manifests")
    print(f"English: {len(target)} total / {len(normal)} normal / {len(target)-len(normal)} debug")
    print(f"Ownership: {len(addon_full)} full/override + {len(incomplete)} supplements + {len(complete)} complete = 90")
    print(f"Exact future donor coverage locales: {len(donor_coverage)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

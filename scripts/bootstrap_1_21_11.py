#!/usr/bin/env python3
"""Freeze deterministic G47 / Minecraft 1.21.11 source, ownership, diff, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import audit_1_21_11 as audit
import reconstruct_1_21_10 as g46

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.10" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.10-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.11" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.10-to-1.21.11.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.11-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.11-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g47-mc1.21.11" / "policy.json"
DEBUG_PREFIX = audit.DEBUG_PREFIX
EXPECTED_ADDED = {
    "jei.config.client.search.identifierSearchMode",
    "jei.config.client.search.identifierSearchMode.description",
}
EXPECTED_REMOVED = {
    "jei.config.client.search.resourceLocationSearchMode",
    "jei.config.client.search.resourceLocationSearchMode.description",
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
        raise ValueError(f"G46 selected scope changed: {len(selected)}")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal)) != (308, 308, 302):
        raise ValueError(f"unexpected G47 source counts: {len(base)}/{len(target)}/{len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (306, 2, 2, 0):
        raise ValueError("unexpected G46 -> G47 semantic partition")
    if set(added) != EXPECTED_ADDED or set(removed) != EXPECTED_REMOVED:
        raise ValueError(f"G47 renamed key sets changed: added={added} removed={removed}")

    first_port = audit.fetch_json(audit.COMMIT_API.format(commit=audit.FIRST_PORT_COMMIT))
    audit.assert_single_parent(first_port, audit.BASE_ENDPOINT, "1.21.11 port")
    first_message = first_port.get("commit", {}).get("message", "")
    if "not be published except on Maven" not in first_message:
        raise ValueError("G47 upstream Maven-only note changed")
    next_port = audit.fetch_json(audit.COMMIT_API.format(commit=audit.NEXT_PORT_COMMIT))
    audit.assert_single_parent(next_port, audit.PINNED_COMMIT, "26.1-snapshot-1 port")

    props = audit.fetch_text(f"{audit.RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.11",
        "minecraftVersionRange=[1.21.11]",
        "neoforgeVersion=21.11.13-beta",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.11.13-beta,)",
        "specificationVersion=27.3.0",
    ):
        if token not in props:
            raise ValueError(f"pinned G47 metadata missing {token}")

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
        raise ValueError(f"G47 selected upstream JSON must all be valid: {malformed}")
    usable = selected & upstream_set
    complete = sorted(x for x in usable if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable)
    if (len(addon_full), len(incomplete), len(complete)) != (64, 25, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected G47 ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")
    if "uk_ua" not in incomplete:
        raise ValueError("G47 expected uk_ua to remain a valid incomplete upstream locale")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.10")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.11")
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(
            f"G47 Minecraft language membership changed: added={live_added} removed={live_removed} absent={sorted(selected-target_codes)}"
        )

    fallback_locales = list(previous_scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 30 or not set(fallback_locales) <= set(addon_full):
        raise ValueError("G47 documented fallback ownership changed")

    upstream_literal_safety_overrides: dict[str, list[str]] = {}
    for locale in incomplete:
        values = parsed[locale]
        unsafe = [
            key for key in sorted(normal & set(values))
            if not g46.preserves_runtime_literals(target[key], values[key])
        ]
        if unsafe:
            upstream_literal_safety_overrides[locale] = unsafe
    override_count = sum(len(keys) for keys in upstream_literal_safety_overrides.values())

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "base_minecraft": "1.21.10",
        "base_jei": "26.2.0",
        "target_minecraft": "1.21.11",
        "target_jei": "27.3.0",
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
        "changed_english_values": {},
        "note": "G47 renames the two resource-location search localization IDs to identifier search IDs. Cross-key translation reuse is forbidden even though the UI role is related.",
    })

    scope = {
        "minecraft_version": "1.21.11",
        "jei_version": "27.3.0",
        "upstream_commit": audit.PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.10-language-scope.json",
        "raw_language_count": len(target_codes),
        "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.10": False,
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
            "live_language_asset_additions_from_1.21.10": live_added,
            "live_language_asset_removals_from_1.21.10": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales,
        "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_full_locale_count": len(addon_full) - len(fallback_locales),
        "translation_delta": {
            "base_generation": "g46-mc1.21.10",
            "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": 0,
            "reuse_exact_g46_for_unchanged_meanings": True,
            "renamed_resource_location_keys_are_not_cross_key_reused": True,
        },
        "new_key_policy": {
            "keys": sorted(EXPECTED_ADDED),
            "project_owned_missing_values_use_exact_target_english": True,
            "reason": "Identifier is a technical Minecraft/API term and the previous Resource Location keys are different localization IDs; exact English is preferred over unsafe cross-key or uncertain translation reuse.",
        },
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": override_count,
        "upstream_supplement_policy": {
            "preserve_existing_safe_upstream_keys": True,
            "supplement_missing_keys_plus_explicit_safety_overrides": True,
            "explicit_upstream_owned_override_keys": upstream_literal_safety_overrides,
            "reuse_exact_g46_combined_value_only_for_unchanged_key_and_english": True,
            "cross_key_reuse_allowed": False,
            "never_emit_other_upstream_owned_keys": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "publication_context": {
            "upstream_jei_target_is_maven_only": True,
            "source_commit": audit.FIRST_PORT_COMMIT,
            "note": "Translation auditing remains valid, but public release packaging must not imply an upstream CurseForge/Modrinth JEI release exists for 1.21.11.",
        },
        "source_audit": "upstream/minecraft-1.21.11-language-audit.json",
        "english_diff": "upstream/diffs/1.21.10-to-1.21.11.json",
    }
    write_json(SCOPE_PATH, scope)

    write_json(AUDIT_PATH, {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "verified-source-scope-upstream-ownership-and-maven-only-context",
        "minecraft": "1.21.11",
        "jei": "27.3.0",
        "jei_upstream_commit": audit.PINNED_COMMIT,
        "endpoint_resolution": {
            "first_1_21_11_port_commit": audit.FIRST_PORT_COMMIT,
            "final_1_21_11_commit": audit.PINNED_COMMIT,
            "next_minecraft_port_commit": audit.NEXT_PORT_COMMIT,
            "next_minecraft_version": "26.1-snapshot-1",
            "first_port_parent": audit.BASE_ENDPOINT,
            "next_port_parent": audit.PINNED_COMMIT,
            "upstream_publication_note": "1.21.11 will not be published except on Maven, for mod developers to build against.",
        },
        "build_metadata": {
            "neoforge": "21.11.13-beta",
            "neoforge_loader_version_range": "[4,)",
            "neoforge_version_range": "[21.11.13-beta,)",
            "java_toolchain": "21",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
            "specification_version": "27.3.0",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_1.21.10": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
            "decoupled_assets": True,
        },
        "minecraft_asset_indexes": {
            "minecraft_1.21.10": {"id": str(base_meta["assetIndex"].get("id")), "sha1": base_meta["assetIndex"].get("sha1"), "language_file_count": len(base_codes)},
            "minecraft_1.21.11": {"id": str(target_meta["assetIndex"].get("id")), "sha1": target_meta["assetIndex"].get("sha1"), "language_file_count": len(target_codes)},
            "live_language_file_additions": live_added,
            "live_language_file_removals": live_removed,
        },
        "english_source": {
            "base_key_count": len(base),
            "target_key_count": len(target),
            "target_normal_key_count": len(normal),
            "target_debug_only_key_count": len(target) - len(normal),
            "unchanged_key_and_value_count": len(unchanged),
            "added_keys": added,
            "removed_keys": removed,
            "changed_english_values": {},
        },
        "upstream_locale_file_count": len(upstream_locales),
        "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness,
        "ownership": {
            "addon_full_locale_count": len(addon_full),
            "selected_upstream_incomplete_locale_count": len(incomplete),
            "selected_upstream_complete_locale_count": len(complete),
            "complete_upstream_locales": complete,
            "malformed_selected_upstream_locales": [],
        },
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": override_count,
        "validation": {
            "exploratory_audit_run": 34965561097,
            "exploratory_result": "success",
            "complete_validation_run": None,
            "complete_result": "pending",
        },
    })

    write_json(POLICY_PATH, {
        "schema_version": 1,
        "generation": "g47-mc1.21.11",
        "minecraft": "1.21.11",
        "jei": "27.3.0",
        "selected_scope_count": 90,
        "translation_reuse": {
            "reuse_exact_unchanged_g46_semantics": True,
            "cross_key_reuse_allowed": False,
            "renamed_resource_location_to_identifier_keys_are_new_semantics_for_translation_ownership": True,
            "project_owned_added_keys_use_exact_target_english": True,
        },
        "upstream_policy": {
            "preserve_safe_upstream_owned_values": True,
            "supplement_missing_normal_keys_only_except_frozen_literal_safety_overrides": True,
            "literal_safety_override_count": override_count,
        },
        "publication_context": {
            "upstream_jei_1_21_11_is_maven_only": True,
            "do_not_claim_public_curseforge_or_modrinth_jei_dependency": True,
        },
        "runtime_promotion_separate": True,
    })

    print("PASS: froze G47 Minecraft 1.21.11 manifests")
    print(f"English: {len(target)} total / {len(normal)} normal / {len(target)-len(normal)} debug")
    print(f"Delta: {len(unchanged)} unchanged + {len(added)} added + {len(removed)} removed + {len(changed)} changed")
    print(f"Ownership: {len(addon_full)} full + {len(incomplete)} supplements + {len(complete)} complete upstream")
    print(f"Literal-safety overrides: {override_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

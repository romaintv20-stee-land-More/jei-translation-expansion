#!/usr/bin/env python3
"""Freeze deterministic G49 / Minecraft 26.1.1 source, ownership, diff, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import audit_26_1_1 as audit
import reconstruct_26_1 as g48

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.1" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-26.1-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "26.1.1" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "26.1-to-26.1.1.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-26.1.1-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-26.1.1-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g49-mc26.1.1" / "policy.json"
DEBUG_PREFIX = audit.DEBUG_PREFIX


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
        raise ValueError(f"G48 selected scope changed: {len(selected)}")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal), len(target) - len(normal)) != (309, 309, 303, 6):
        raise ValueError("unexpected G49 English counts")
    if (len(unchanged), len(added), len(removed), len(changed)) != (309, 0, 0, 0):
        raise ValueError("G48 -> G49 must be semantically identical")

    first_patch = audit.fetch_json(audit.COMMIT_API.format(commit=audit.FIRST_PATCH_COMMIT))
    audit.assert_single_parent(first_patch, audit.BASE_ENDPOINT, "26.1.1 support commit")
    next_patch = audit.fetch_json(audit.COMMIT_API.format(commit=audit.NEXT_PATCH_COMMIT))
    audit.assert_single_parent(next_patch, audit.FINAL_ENDPOINT, "26.1.2 support commit")

    props = audit.fetch_text(f"{audit.RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=25",
        "minecraftVersion=26.1.1",
        "minecraftVersionRange=[26.1, 26.1.1]",
        "neoforgeVersion=26.1.1.1-beta",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[26.1.0.8-beta,)",
        "curseProjectId=238222",
        "modrinthId=u6dRKJwZ",
        "specificationVersion=29.4.0",
    ):
        if token not in props:
            raise ValueError(f"G49 metadata missing {token}")

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

    usable = (selected & upstream_set) - set(malformed)
    complete = sorted(x for x in usable if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable)
    if malformed:
        raise ValueError(f"G49 selected upstream JSON unexpectedly malformed: {malformed}")
    if (len(addon_full), len(incomplete), len(complete)) != (64, 25, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected G49 ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")
    if "uk_ua" not in incomplete or completeness["uk_ua"]["missing_normal_key_count"] != 4:
        raise ValueError("G49 expects uk_ua to remain valid upstream with 4 missing normal keys")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "26.1")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "26.1.1")
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(
            f"G49 Minecraft language membership changed: added={live_added} removed={live_removed} "
            f"absent={sorted(selected-target_codes)}"
        )

    fallback_locales = [
        locale for locale in previous_scope["documented_full_english_fallback_locales"]
        if locale in set(addon_full)
    ]
    if len(fallback_locales) != 30:
        raise ValueError(f"G49 documented fallback ownership changed: {len(fallback_locales)}")

    upstream_literal_safety_overrides: dict[str, list[str]] = {}
    for locale in incomplete:
        values = parsed[locale]
        unsafe = [
            key for key in sorted(normal & set(values))
            if not g48.preserves_runtime_literals(target[key], values[key])
        ]
        if unsafe:
            upstream_literal_safety_overrides[locale] = unsafe
    override_count = sum(len(keys) for keys in upstream_literal_safety_overrides.values())

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "base_minecraft": "26.1",
        "base_jei": "29.2.0",
        "target_minecraft": "26.1.1",
        "target_jei": "29.4.0",
        "base_key_count": len(base),
        "target_key_count": len(target),
        "target_normal_key_count": len(normal),
        "target_debug_only_key_count": len(target) - len(normal),
        "unchanged_key_and_value_count": len(unchanged),
        "added_key_count": 0,
        "removed_key_count": 0,
        "changed_english_value_count": 0,
        "unchanged_keys": unchanged,
        "added_keys": [],
        "removed_keys": [],
        "changed_english_values": {},
        "note": "All G49 English semantics are identical to G48; exact same-key G48 combined values are eligible for deterministic reuse.",
    })

    publication = {
        "curse_project_id": "238222",
        "modrinth_id": "u6dRKJwZ",
        "public_distribution_configured": True,
    }
    scope = {
        "minecraft_version": "26.1.1",
        "jei_version": "29.4.0",
        "upstream_commit": audit.PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-26.1-language-scope.json",
        "raw_language_count": len(target_codes),
        "selected_scope_count": 90,
        "selected_scope_changed_from_26.1": False,
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
            "live_language_asset_additions_from_26.1": live_added,
            "live_language_asset_removals_from_26.1": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales,
        "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_full_locale_count": len(addon_full) - len(fallback_locales),
        "translation_delta": {
            "base_generation": "g48-mc26.1",
            "unchanged_key_and_english_value_count": 309,
            "added_key_count": 0,
            "removed_key_count": 0,
            "changed_english_value_count": 0,
            "reuse_exact_g48_for_all_identical_meanings": True,
        },
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": override_count,
        "upstream_supplement_policy": {
            "preserve_existing_safe_upstream_keys": True,
            "supplement_missing_keys_plus_explicit_safety_overrides": True,
            "explicit_upstream_owned_override_keys": upstream_literal_safety_overrides,
            "reuse_exact_g48_combined_value_only_for_same_key_same_english": True,
            "cross_key_reuse_allowed": False,
            "never_emit_other_upstream_owned_keys": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "publication_context": publication,
        "source_audit": "upstream/minecraft-26.1.1-language-audit.json",
        "english_diff": "upstream/diffs/26.1-to-26.1.1.json",
    }
    write_json(SCOPE_PATH, scope)

    audit_payload = {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "verified-source-scope-and-upstream-ownership",
        "minecraft": "26.1.1",
        "jei": "29.4.0",
        "jei_upstream_commit": audit.PINNED_COMMIT,
        "endpoint_resolution": {
            "first_26_1_1_commit": audit.FIRST_PATCH_COMMIT,
            "final_26_1_1_endpoint": audit.FINAL_ENDPOINT,
            "next_patch_commit": audit.NEXT_PATCH_COMMIT,
            "next_minecraft_version": "26.1.2",
            "note": "The Minecraft 26.1.2 port is directly parented by the final 26.1.1 endpoint.",
        },
        "build_metadata": {
            "neoforge": "26.1.1.1-beta",
            "neoforge_loader_version_range": "[4,)",
            "neoforge_version_range": "[26.1.0.8-beta,)",
            "java_toolchain": "25",
            "specification_version": "29.4.0",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_26.1": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
        },
        "minecraft_asset_indexes": scope["downloaded"],
        "english_source": {
            "base_key_count": len(base),
            "target_key_count": len(target),
            "target_normal_key_count": len(normal),
            "target_debug_only_key_count": len(target) - len(normal),
            "unchanged_key_and_value_count": 309,
            "added_keys": [],
            "removed_keys": [],
            "changed_english_values": {},
        },
        "upstream_locale_file_count": len(upstream_locales),
        "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness,
        "selected_upstream_complete_locales": complete,
        "selected_upstream_incomplete_locales": incomplete,
        "addon_full_locales": addon_full,
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": override_count,
        "publication_context": publication,
    }
    write_json(AUDIT_PATH, audit_payload)

    write_json(POLICY_PATH, {
        "schema_version": 1,
        "generation": "g49-mc26.1.1",
        "minecraft": "26.1.1",
        "jei": "29.4.0",
        "source_commit": audit.PINNED_COMMIT,
        "selected_scope_count": 90,
        "ownership": {
            "addon_full": len(addon_full),
            "upstream_supplements": len(incomplete),
            "complete_upstream": len(complete),
        },
        "translation_reuse": {
            "base_generation": "g48-mc26.1",
            "reuse_exact_unchanged_g48_semantics": True,
            "all_target_keys_are_unchanged_from_g48": True,
            "cross_key_reuse_allowed": False,
            "placeholder_and_technical_literal_safety_required": True,
            "prefer_target_english_if_reused_value_is_unsafe": True,
        },
        "upstream_policy": scope["upstream_supplement_policy"],
        "documented_full_english_fallback_locales": fallback_locales,
        "publication_context": publication,
        "runtime_promotion_separate": True,
    })

    print("PASS: froze G49 Minecraft 26.1.1 manifests")
    print("English: 309 total / 303 normal / 6 debug; all semantics unchanged from G48")
    print(f"Ownership: {len(addon_full)} full + {len(incomplete)} supplements + {len(complete)} complete upstream")
    print(f"Frozen upstream literal-safety override keys: {override_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

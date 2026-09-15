#!/usr/bin/env python3
"""Freeze provisional Minecraft 26.3 RC2 translation manifests without completing G52."""
from __future__ import annotations

import json
from pathlib import Path

import audit_26_3_rc_2 as audit
import reconstruct_26_2 as g51

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.2" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-26.2-language-scope.json"
PROVISIONAL_ROOT = ROOT / "upstream" / "provisional"
TARGET_SOURCE = PROVISIONAL_ROOT / "sources" / "26.3-rc-2" / "en_us.json"
DIFF_PATH = PROVISIONAL_ROOT / "diffs" / "26.2-to-26.3-rc-2.json"
SCOPE_PATH = PROVISIONAL_ROOT / "minecraft-26.3-rc-2-language-scope.json"
AUDIT_PATH = PROVISIONAL_ROOT / "minecraft-26.3-rc-2-language-audit.json"
POLICY_PATH = ROOT / "translations" / "pre-g52-mc26.3-rc2" / "policy.json"
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
        raise ValueError(f"G51 selected scope changed: {len(selected)}")

    branch = audit.fetch_json(audit.BRANCH_API)
    if branch.get("commit", {}).get("sha") != audit.PINNED_COMMIT:
        raise ValueError("26.3 RC branch moved; re-audit instead of freezing this provisional snapshot")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal), len(target) - len(normal)) != (334, 334, 328, 6):
        raise ValueError("unexpected provisional 26.3 RC2 English counts")
    if (len(unchanged), len(added), len(removed), len(changed)) != (334, 0, 0, 0):
        raise ValueError("G51 -> provisional 26.3 RC2 English semantics are no longer identical")

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
        raise ValueError(f"provisional selected upstream JSON unexpectedly malformed: {malformed}")
    if (len(addon_full), len(incomplete), len(complete)) != (63, 26, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected provisional ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "26.2")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == audit.TARGET_MC)
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(
            f"provisional 26.3 Minecraft language membership changed: added={live_added} removed={live_removed} "
            f"absent={sorted(selected-target_codes)}"
        )

    fallback_locales = [
        locale for locale in previous_scope["documented_full_english_fallback_locales"]
        if locale in set(addon_full)
    ]
    if len(fallback_locales) != 30:
        raise ValueError(f"provisional documented fallback ownership changed: {len(fallback_locales)}")

    upstream_literal_safety_overrides: dict[str, list[str]] = {}
    for locale in incomplete:
        values = parsed[locale]
        unsafe = [
            key for key in sorted(normal & set(values))
            if not g51.preserves_runtime_literals(target[key], values[key])
        ]
        if unsafe:
            upstream_literal_safety_overrides[locale] = unsafe
    override_count = sum(len(keys) for keys in upstream_literal_safety_overrides.values())

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "status": "provisional-rc-only",
        "base_minecraft": "26.2",
        "base_jei": "30.32.0",
        "target_minecraft": audit.TARGET_MC,
        "target_jei": "30.32.0",
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
        "note": "Provisional only. All 334 English semantics are identical to G51 at the pinned 26.3-rc-2 Fabric snapshot.",
    })

    downloaded = {
        "base_asset_index_id": str(base_meta["assetIndex"].get("id")),
        "base_asset_index_sha1": base_meta["assetIndex"].get("sha1"),
        "asset_index_id": str(target_meta["assetIndex"].get("id")),
        "asset_index_sha1": target_meta["assetIndex"].get("sha1"),
        "language_asset_file_count": len(target_codes),
        "live_language_asset_additions_from_26.2": live_added,
        "live_language_asset_removals_from_26.2": live_removed,
    }
    scope = {
        "minecraft_version": audit.TARGET_MC,
        "jei_version": "30.32.0",
        "upstream_commit": audit.PINNED_COMMIT,
        "upstream_branch": audit.MAINTAINED_BRANCH,
        "status": "provisional-rc-audit-only",
        "not_a_completed_generation": True,
        "publishable_candidate": False,
        "loader_available_upstream": "fabric",
        "base_scope_manifest": "upstream/minecraft-26.2-language-scope.json",
        "raw_language_count": len(target_codes),
        "selected_scope_count": 90,
        "selected_scope_changed_from_26.2": False,
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
        "downloaded": downloaded,
        "documented_full_english_fallback_locales": fallback_locales,
        "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_full_locale_count": len(addon_full) - len(fallback_locales),
        "translation_delta": {
            "base_generation": "g51-mc26.2",
            "unchanged_key_and_english_value_count": 334,
            "added_key_count": 0,
            "removed_key_count": 0,
            "changed_english_value_count": 0,
            "reuse_exact_g51_for_identical_meanings_only": True,
        },
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": override_count,
        "upstream_supplement_policy": {
            "preserve_existing_safe_upstream_keys": True,
            "supplement_missing_keys_plus_explicit_safety_overrides": True,
            "explicit_upstream_owned_override_keys": upstream_literal_safety_overrides,
            "reuse_exact_g51_combined_value_only_for_same_key_same_english": True,
            "cross_key_reuse_allowed": False,
            "never_emit_other_upstream_owned_keys": True,
        },
        "english_diff": "upstream/provisional/diffs/26.2-to-26.3-rc-2.json",
    }
    write_json(SCOPE_PATH, scope)

    write_json(AUDIT_PATH, {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "provisional-rc-audit-only",
        "not_a_completed_generation": True,
        "minecraft": audit.TARGET_MC,
        "jei": "30.32.0",
        "jei_upstream_commit": audit.PINNED_COMMIT,
        "upstream_branch": audit.MAINTAINED_BRANCH,
        "build_metadata": {
            "loader": "fabric",
            "fabric_loader": "0.19.5",
            "fabric_api": "0.160.4+26.3",
            "fabric_loader_version_range": ">=0.19.0",
            "java_toolchain": "25",
            "specification_version": "30.32.0",
            "language_format": "json",
        },
        "release_gate": {
            "publishable": False,
            "reason": "Minecraft target is 26.3-rc-2 and JEI upstream currently exposes this line on a Fabric-only RC/snapshot branch.",
            "required_before_g52_completion": "Re-audit a publishable 26.3 target and loader state; do not append packaging/completed-versions.json from this provisional snapshot.",
        },
        "minecraft_asset_indexes": downloaded,
        "english_source": {
            "base_key_count": len(base),
            "target_key_count": len(target),
            "target_normal_key_count": len(normal),
            "target_debug_only_key_count": len(target) - len(normal),
            "unchanged_key_and_value_count": len(unchanged),
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
    })

    write_json(POLICY_PATH, {
        "schema_version": 1,
        "generation": "pre-g52-mc26.3-rc2",
        "status": "provisional-only",
        "minecraft": audit.TARGET_MC,
        "jei": "30.32.0",
        "source_commit": audit.PINNED_COMMIT,
        "selected_scope_count": 90,
        "ownership": {
            "addon_full": len(addon_full),
            "upstream_supplements": len(incomplete),
            "complete_upstream": len(complete),
        },
        "translation_reuse": {
            "base_generation": "g51-mc26.2",
            "reuse_only_exact_same_key_same_english": True,
            "eligible_unchanged_key_count": 334,
            "cross_key_reuse_allowed": False,
        },
        "upstream_literal_safety_override_count": override_count,
        "packaging_registration_allowed": False,
        "runtime_promotion_allowed": False,
    })

    print("PASS: froze provisional Minecraft 26.3 RC2 translation manifests")
    print(f"English semantics: {len(unchanged)} unchanged, 0 added, 0 removed, 0 changed")
    print(f"Ownership: full={len(addon_full)} supplements={len(incomplete)} complete={len(complete)}")
    print(f"Provisional upstream literal-safety overrides: {override_count}")
    print("G52 completion/packaging: intentionally blocked until publishable Minecraft 26.3 target is selected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Freeze deterministic G40 / Minecraft 1.21.4 source, diff, scope, audit, and policy manifests."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.4" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.1-to-1.21.4.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.4-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.4-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g40-mc1.21.4" / "policy.json"

PINNED_COMMIT = "26845e0d2a248b0084481b4a433ef7b32152d4c6"
FIRST_PORT_COMMIT = "c0d0367841b16fa3a9567c3d93172cbd1f1b578c"
NEXT_PORT_COMMIT = "2cc5d1e8b7fb4f79c917804d7582bb7c48374499"
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_CONTENTS_API = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
EXPECTED_ADDED = {
    "gui.jei.category.blasting_fuel",
    "gui.jei.category.smelting_fuel",
    "gui.jei.category.smoking_fuel",
}
EXPECTED_REMOVED = {"gui.jei.category.fuel"}


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G40-bootstrap"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch_bytes(url).decode("utf-8"))


def parse_json_bytes(data: bytes) -> dict[str, str]:
    raw = json.loads(data.decode("utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_json(path: Path) -> dict[str, str]:
    return parse_json_bytes(path.read_bytes())


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def language_codes(asset_index: dict) -> set[str]:
    codes: set[str] = set()
    for name in asset_index.get("objects", {}):
        if not name.startswith("minecraft/lang/"):
            continue
        path = Path(name)
        if path.name == "languages.json":
            continue
        if path.suffix in {".lang", ".json"}:
            codes.add(path.stem.lower())
    codes.add("en_us")
    return codes


def main() -> int:
    base = parse_json(BASE_SOURCE)
    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))

    target_raw = fetch_bytes(f"{RAW_LANG}/en_us.json")
    target = parse_json_bytes(target_raw)
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    changed_debug = [key for key in changed if key.startswith(DEBUG_PREFIX)]
    review_normal = sorted(
        key for key in set(added) | set(changed)
        if not key.startswith(DEBUG_PREFIX)
    )

    if (len(base), len(target), len(target_normal)) != (286, 288, 282):
        raise ValueError(f"unexpected G40 source counts: base={len(base)} target={len(target)} normal={len(target_normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (285, 3, 1, 0):
        raise ValueError("unexpected G39 -> G40 semantic partition")
    if set(added) != EXPECTED_ADDED or set(removed) != EXPECTED_REMOVED:
        raise ValueError("unexpected G40 added/removed key set")

    contents = fetch_json(LANG_CONTENTS_API)
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in contents
        if item.get("type") == "file" and str(item.get("name", "")).endswith(".json")
    )
    if len(upstream_locales) != 28:
        raise ValueError(f"expected 28 pinned JEI upstream locale files, got {len(upstream_locales)}")

    completeness: dict[str, dict] = {}
    for locale in upstream_locales:
        values = parse_json_bytes(fetch_bytes(f"{RAW_LANG}/{locale}.json"))
        missing = sorted(target_normal - set(values))
        completeness[locale] = {
            "present_normal_key_count": len(target_normal & set(values)),
            "target_normal_key_count": len(target_normal),
            "missing_normal_key_count": len(missing),
            "missing_normal_keys": missing,
            "extra_key_count": len(set(values) - set(target)),
            "extra_keys": sorted(set(values) - set(target)),
        }

    inherited = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    upstream_set = set(upstream_locales)
    selected_upstream = sorted(inherited & upstream_set)
    selected_complete = sorted(locale for locale in selected_upstream if not completeness[locale]["missing_normal_keys"])
    selected_incomplete = sorted(locale for locale in selected_upstream if completeness[locale]["missing_normal_keys"])
    addon_full = sorted(inherited - upstream_set)
    unselected_upstream = sorted(upstream_set - inherited)

    if len(inherited) != 90:
        raise ValueError(f"G39 selected scope changed: {len(inherited)}")
    if selected_complete != ["en_us"]:
        raise ValueError(f"unexpected G40 complete upstream locales: {selected_complete}")
    if len(selected_incomplete) != 25 or "ja_jp" not in selected_incomplete:
        raise ValueError("G40 must have 25 incomplete upstream locales including ja_jp")
    if len(addon_full) != 64:
        raise ValueError(f"G40 addon-full count must remain 64, got {len(addon_full)}")
    if unselected_upstream != ["pt_pt", "zh_tw"]:
        raise ValueError(f"unexpected unselected upstream locales: {unselected_upstream}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next(item for item in manifest["versions"] if item.get("id") == "1.21.1")
    target_entry = next(item for item in manifest["versions"] if item.get("id") == "1.21.4")
    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_asset = fetch_json(base_meta["assetIndex"]["url"])
    target_asset = fetch_json(target_meta["assetIndex"]["url"])
    base_codes = language_codes(base_asset)
    target_codes = language_codes(target_asset)
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if len(base_codes) != 143 or len(target_codes) != 143 or live_added or live_removed:
        raise ValueError("Minecraft 1.21.1 -> 1.21.4 live language-code scope unexpectedly changed")
    if inherited - target_codes:
        raise ValueError(f"selected locale absent from Minecraft 1.21.4: {sorted(inherited-target_codes)}")

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)

    diff = {
        "schema_version": 1,
        "base_minecraft": "1.21.1",
        "base_jei": "19.21.1",
        "target_minecraft": "1.21.4",
        "target_jei": "20.0.0",
        "base_key_count": len(base),
        "target_key_count": len(target),
        "target_normal_key_count": len(target_normal),
        "target_debug_only_key_count": len(target) - len(target_normal),
        "unchanged_key_and_value_count": len(unchanged),
        "added_key_count": len(added),
        "removed_key_count": len(removed),
        "changed_english_value_count": len(changed),
        "changed_debug_only_key_count": len(changed_debug),
        "review_required_normal_added_or_changed_key_count": len(review_normal),
        "unchanged_keys": unchanged,
        "added_keys": added,
        "removed_keys": removed,
        "changed_english_values": {
            key: {"before": base[key], "after": target[key]}
            for key in changed
        },
    }
    write_json(DIFF_PATH, diff)

    documented_fallback = list(base_scope["documented_full_english_fallback_locales"])
    scope = {
        "minecraft_version": "1.21.4",
        "jei_version": "20.0.0",
        "upstream_commit": PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.1-language-scope.json",
        "raw_language_count": len(target_codes),
        "raw_language_count_note": "Minecraft 1.21.4 keeps the same 143 live language asset-file codes as 1.21.1; the selected historical primary-language scope remains frozen at 90 languages.",
        "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.1": False,
        "runtime_locale_filename_case": "lowercase",
        "resource_format": "json",
        "selected_upstream_locale_count": len(selected_upstream),
        "selected_upstream_complete_locales": selected_complete,
        "selected_upstream_complete_locale_count": len(selected_complete),
        "selected_upstream_incomplete_locales": selected_incomplete,
        "selected_upstream_incomplete_locale_count": len(selected_incomplete),
        "jei_upstream_unselected_or_nonmatching_locales": unselected_upstream,
        "addon_full_locale_count": len(addon_full),
        "addon_full_locales": addon_full,
        "removed_selected_languages": [],
        "new_selected_primary_languages": [],
        "downloaded": {
            "base_asset_index_id": str(base_meta["assetIndex"].get("id")),
            "base_asset_index_sha1": base_meta["assetIndex"].get("sha1"),
            "asset_index_id": str(target_meta["assetIndex"].get("id")),
            "asset_index_sha1": target_meta["assetIndex"].get("sha1"),
            "language_asset_file_count": len(target_codes),
            "live_language_asset_additions_from_1.21.1": live_added,
            "live_language_asset_removals_from_1.21.1": live_removed,
        },
        "documented_full_english_fallback_locales": documented_fallback,
        "documented_full_english_fallback_count": len(documented_fallback),
        "translated_or_ai_assisted_full_locale_count": len(addon_full) - len(documented_fallback),
        "translation_delta": {
            "base_generation": "g39-mc1.21.1",
            "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": len(added),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(changed_debug),
            "removed_key_count": len(removed),
            "normal_added_or_changed_key_count": len(review_normal),
            "reuse_exact_g39_for_unchanged_meanings": True,
        },
        "ownership_changes_from_g39": {
            "newly_complete_upstream": [],
            "complete_to_incomplete": ["ja_jp"],
            "newly_upstream_from_addon_full": [],
            "no_longer_upstream": [],
            "complete_count": len(selected_complete),
            "supplement_count": len(selected_incomplete),
            "addon_full_count": len(addon_full),
        },
        "upstream_supplement_policy": {
            "preserve_existing_upstream_keys": True,
            "supplement_only_exact_missing_normal_keys": True,
            "reuse_exact_g39_combined_value_only_for_unchanged_key_and_english": True,
            "changed_or_added_keys_require_reviewed_g40_treatment": True,
            "cross_key_reuse_allowed": False,
            "never_emit_upstream_owned_key": True,
            "retire_supplement_when_upstream_becomes_complete": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "source_audit": "upstream/minecraft-1.21.4-language-audit.json",
        "english_diff": "upstream/diffs/1.21.1-to-1.21.4.json",
    }
    write_json(SCOPE_PATH, scope)

    audit = {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "verified-source-scope-and-upstream-ownership; translation-delta-in-progress",
        "minecraft": "1.21.4",
        "jei": "20.0.0",
        "jei_upstream_commit": PINNED_COMMIT,
        "endpoint_resolution": {
            "first_1_21_4_commit": FIRST_PORT_COMMIT,
            "final_1_21_4_commit": PINNED_COMMIT,
            "next_minecraft_port_commit": NEXT_PORT_COMMIT,
            "next_minecraft_version": "1.21.5",
            "note": "The pinned endpoint is the parent of the JEI Minecraft 1.21.5 port commit.",
        },
        "build_metadata": {
            "neoforge": "21.4.136",
            "neoforge_loader_version_range": "[4,)",
            "neoforge_version_range": "[21.4.121,)",
            "java_toolchain": "21",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_1.21.1": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
            "decoupled_assets": True,
        },
        "minecraft_asset_indexes": {
            "minecraft_1.21.1": {
                "id": str(base_meta["assetIndex"].get("id")),
                "sha1": base_meta["assetIndex"].get("sha1"),
                "language_file_count": len(base_codes),
            },
            "minecraft_1.21.4": {
                "id": str(target_meta["assetIndex"].get("id")),
                "sha1": target_meta["assetIndex"].get("sha1"),
                "language_file_count": len(target_codes),
            },
            "live_language_file_additions": live_added,
            "live_language_file_removals": live_removed,
        },
        "jei_english": {
            "resource_format": "json",
            "key_count": len(target),
            "normal_key_count": len(target_normal),
            "debug_only_key_count": len(target) - len(target_normal),
        },
        "english_diff_from_1.21.1": {
            "unchanged_key_and_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(changed_debug),
            "review_required_normal_added_or_changed_key_count": len(review_normal),
            "manifest": "upstream/diffs/1.21.1-to-1.21.4.json",
        },
        "jei_upstream_locale_count": len(upstream_locales),
        "selected_scope_count": 90,
        "selected_upstream_complete_locales": selected_complete,
        "selected_upstream_incomplete_locales": selected_incomplete,
        "selected_addon_full_locales": addon_full,
        "jei_upstream_unselected_or_nonmatching_locales": unselected_upstream,
        "upstream_completeness": completeness,
    }
    write_json(AUDIT_PATH, audit)

    policy = {
        "generation": "g40-mc1.21.4",
        "minecraft": "1.21.4",
        "jei": "20.0.0",
        "pinned_commit": PINNED_COMMIT,
        "resource_format": "json",
        "selected_scope_count": 90,
        "addon_full_locale_count": len(addon_full),
        "selected_upstream_complete_locale_count": len(selected_complete),
        "selected_upstream_incomplete_locale_count": len(selected_incomplete),
        "documented_full_english_fallback_count": len(documented_fallback),
        "translated_or_ai_assisted_full_locale_count": len(addon_full) - len(documented_fallback),
        "english_diff": {
            "base_generation": "g39-mc1.21.1",
            "unchanged_key_and_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(changed_debug),
            "review_required_normal_added_or_changed_key_count": len(review_normal),
        },
        "translation_reuse": {
            "rule": "Automatic reuse requires the exact same localization key and exact same English source value. Cross-key reuse is forbidden, and runtime placeholders/technical literals must remain intact.",
            "base_generation": "g39-mc1.21.1",
            "reuse_exact_unchanged_g39_semantics": True,
            "cross_key_reuse_allowed": False,
            "changed_or_added_keys_require_reviewed_g40_treatment": True,
            "runtime_literals_must_be_preserved": True,
        },
        "ownership_change": {
            "newly_upstream_from_addon_full": [],
            "complete_to_incomplete": ["ja_jp"],
            "complete_count": len(selected_complete),
            "supplement_count": len(selected_incomplete),
            "addon_full_count": len(addon_full),
        },
        "fallback_policy": {
            "documented_full_english_fallback_allowed": True,
            "fallback_locales_are_complete": True,
            "low_confidence_new_or_changed_semantics_may_use_exact_target_english": True,
            "fallback_must_be_explicit_and_counted": True,
            "debug_only_keys_remain_exact_target_english": True,
            "unsafe_reuse_or_donor_uses_exact_target_english": True,
        },
        "runtime_literal_policy": {
            "placeholder_multiset_must_match": True,
            "technical_tokens": ["JEI", "Minecraft", "/give", "modId[:name[:meta]]", "mB"],
            "standalone_alphanumeric_tokens_use_boundaries": True,
            "substring_matches_do_not_count": True,
        },
        "later_upstream_backport_policy": {
            "allowed_only_if_same_key_and_exact_same_english_value": True,
            "donor_snapshot": DONOR_COMMIT,
            "never_override_g40_upstream_owned_key": True,
            "runtime_literals_must_be_preserved": True,
        },
        "translation_status": "in-progress-small-semantic-delta",
    }
    write_json(POLICY_PATH, policy)

    print("PASS: frozen Minecraft 1.21.4 / JEI 20.0.0 bootstrap")
    print(f"English: {len(target)} total / {len(target_normal)} normal")
    print(f"Delta: unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}")
    print(f"Ownership: full={len(addon_full)} supplements={len(selected_incomplete)} complete={len(selected_complete)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

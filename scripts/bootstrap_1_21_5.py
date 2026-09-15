#!/usr/bin/env python3
"""Freeze deterministic G41 / Minecraft 1.21.5 source, diff, scope, audit, and policy manifests."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.4" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.4-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.5" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.4-to-1.21.5.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.5-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.5-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g41-mc1.21.5" / "policy.json"

PINNED_COMMIT = "0772287a157beb93f438ee10f88afe402e262856"
FIRST_PORT_COMMIT = "2cc5d1e8b7fb4f79c917804d7582bb7c48374499"
MAINLINE_PRE_NEXT_PORT_COMMIT = "e34c5c1221ca81fbf1ca4ca4433f3332208f49d9"
NEXT_PORT_COMMIT = "2a57409c2af0ce9716749a0329166a41cbcf453f"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_CONTENTS_API = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
NEW_G41_KEYS = {
    "gui.jei.category.grindstone.experience",
    "jei.message.missing.recipes.from.server",
}
MALFORMED_UPSTREAM_FULL_OVERRIDES = {"uk_ua"}


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G41-bootstrap"}
    token = os.getenv("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_json_bytes(data: bytes) -> dict[str, str]:
    return clean_mapping(json.loads(data.decode("utf-8")))


def parse_json(path: Path) -> dict[str, str]:
    return parse_json_bytes(path.read_bytes())


def repair_uk_ua_text(text: str) -> str:
    repaired, count = re.subn(
        r'("jei\.alias\.villager\.spawn\.egg"\s*:\s*"HMMM")\s*(\n\s*"modmenu\.descriptionTranslation\.jei")',
        r"\1,\2",
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("uk_ua: expected missing-comma repair point not found")
    repaired, count = re.subn(r",\s*}\s*$", "\n}\n", repaired, count=1)
    if count != 1:
        raise ValueError("uk_ua: expected trailing-comma repair point not found")
    return repaired


def parse_pinned_locale(locale: str, data: bytes) -> tuple[dict[str, str], bool]:
    text = data.decode("utf-8")
    try:
        return clean_mapping(json.loads(text)), False
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        return clean_mapping(json.loads(repair_uk_ua_text(text))), True


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
    previous_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected_previous = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )

    target_raw = fetch_bytes(f"{RAW_LANG}/en_us.json")
    target = parse_json_bytes(target_raw)
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    changed_debug = [key for key in changed if key.startswith(DEBUG_PREFIX)]
    review_normal = sorted(key for key in set(added) | set(changed) if not key.startswith(DEBUG_PREFIX))

    if (len(base), len(target), len(target_normal)) != (288, 290, 284):
        raise ValueError(f"unexpected G41 source counts: base={len(base)} target={len(target)} normal={len(target_normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (288, 2, 0, 0):
        raise ValueError("unexpected G40 -> G41 semantic partition")
    if set(added) != NEW_G41_KEYS:
        raise ValueError(f"unexpected G41 added keys: {added}")
    if len(selected_previous) != 90:
        raise ValueError(f"G40 selected scope changed: {len(selected_previous)}")

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.5",
        "minecraftVersionRange=[1.21.5, 1.21.6)",
        "neoforgeVersion=21.5.75",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.5.74,)",
        "specificationVersion=21.4.0",
    ):
        if token not in props:
            raise ValueError(f"pinned G41 gradle.properties missing {token}")

    contents = fetch_json(LANG_CONTENTS_API)
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in contents
        if item.get("type") == "file" and str(item.get("name", "")).endswith(".json")
    )
    if len(upstream_locales) != 29:
        raise ValueError(f"expected 29 pinned JEI upstream locale files, got {len(upstream_locales)}")

    upstream_set = set(upstream_locales)
    selected_upstream_candidates = sorted(selected_previous & upstream_set)
    completeness: dict[str, dict] = {}
    malformed_selected: set[str] = set()
    for locale in selected_upstream_candidates:
        values, repaired = parse_pinned_locale(locale, fetch_bytes(f"{RAW_LANG}/{locale}.json"))
        if repaired:
            malformed_selected.add(locale)
        missing = sorted(target_normal - set(values))
        completeness[locale] = {
            "present_normal_key_count": len(target_normal & set(values)),
            "target_normal_key_count": len(target_normal),
            "missing_normal_key_count": len(missing),
            "missing_normal_keys": missing,
            "extra_key_count": len(set(values) - set(target)),
            "extra_keys": sorted(set(values) - set(target)),
            "malformed_upstream_json": repaired,
        }
    if malformed_selected != MALFORMED_UPSTREAM_FULL_OVERRIDES:
        raise ValueError(f"unexpected malformed selected upstream locales: {sorted(malformed_selected)}")

    usable_upstream = (selected_previous & upstream_set) - MALFORMED_UPSTREAM_FULL_OVERRIDES
    selected_complete = sorted(locale for locale in usable_upstream if not completeness[locale]["missing_normal_keys"])
    selected_incomplete = sorted(locale for locale in usable_upstream if completeness[locale]["missing_normal_keys"])
    addon_full = sorted(selected_previous - usable_upstream)
    unselected_upstream = sorted(upstream_set - selected_previous)
    fallback_locales = list(previous_scope["documented_full_english_fallback_locales"])

    if selected_complete != ["en_us"]:
        raise ValueError(f"unexpected G41 complete upstream locales: {selected_complete}")
    if len(selected_incomplete) != 24:
        raise ValueError(f"expected 24 G41 supplements, got {len(selected_incomplete)}")
    if len(addon_full) != 65 or "uk_ua" not in addon_full:
        raise ValueError(f"G41 full ownership must be 65 locales including uk_ua, got {len(addon_full)}")
    if unselected_upstream != ["es_ar", "pt_pt", "zh_tw"]:
        raise ValueError(f"unexpected unselected upstream locales: {unselected_upstream}")
    if len(fallback_locales) != 30 or "uk_ua" in fallback_locales:
        raise ValueError("G41 fallback ownership must keep the 30 G40 fallback locales and exclude uk_ua")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next(item for item in manifest["versions"] if item.get("id") == "1.21.4")
    target_entry = next(item for item in manifest["versions"] if item.get("id") == "1.21.5")
    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_asset = fetch_json(base_meta["assetIndex"]["url"])
    target_asset = fetch_json(target_meta["assetIndex"]["url"])
    base_codes = language_codes(base_asset)
    target_codes = language_codes(target_asset)
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if len(base_codes) != 143 or len(target_codes) != 143 or live_added or live_removed:
        raise ValueError("Minecraft 1.21.4 -> 1.21.5 live language-code scope unexpectedly changed")
    if selected_previous - target_codes:
        raise ValueError(f"selected locale absent from Minecraft 1.21.5: {sorted(selected_previous-target_codes)}")

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)

    diff = {
        "schema_version": 1,
        "base_minecraft": "1.21.4",
        "base_jei": "20.0.0",
        "target_minecraft": "1.21.5",
        "target_jei": "21.4.0",
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
        "changed_english_values": {key: {"before": base[key], "after": target[key]} for key in changed},
    }
    write_json(DIFF_PATH, diff)

    scope = {
        "minecraft_version": "1.21.5",
        "jei_version": "21.4.0",
        "upstream_commit": PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.4-language-scope.json",
        "raw_language_count": len(target_codes),
        "raw_language_count_note": "Minecraft 1.21.5 keeps the same 143 live language asset-file codes as 1.21.4; the selected historical primary-language scope remains frozen at 90 languages.",
        "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.4": False,
        "runtime_locale_filename_case": "lowercase",
        "resource_format": "json",
        "selected_upstream_locale_count": len(selected_complete) + len(selected_incomplete),
        "selected_upstream_complete_locales": selected_complete,
        "selected_upstream_complete_locale_count": len(selected_complete),
        "selected_upstream_incomplete_locales": selected_incomplete,
        "selected_upstream_incomplete_locale_count": len(selected_incomplete),
        "malformed_upstream_full_override_locales": sorted(MALFORMED_UPSTREAM_FULL_OVERRIDES),
        "malformed_upstream_full_override_locale_count": len(MALFORMED_UPSTREAM_FULL_OVERRIDES),
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
            "live_language_asset_additions_from_1.21.4": live_added,
            "live_language_asset_removals_from_1.21.4": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales,
        "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_or_repaired_full_locale_count": len(addon_full) - len(fallback_locales),
        "translation_delta": {
            "base_generation": "g40-mc1.21.4",
            "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": len(added),
            "changed_english_value_count": len(changed),
            "changed_debug_only_key_count": len(changed_debug),
            "removed_key_count": len(removed),
            "normal_added_or_changed_key_count": len(review_normal),
            "reuse_exact_g40_for_unchanged_meanings": True,
        },
        "ownership_changes_from_g40": {
            "newly_complete_upstream": [],
            "complete_to_incomplete": [],
            "newly_upstream_from_addon_full": [],
            "upstream_to_forced_full_override": ["uk_ua"],
            "complete_count": len(selected_complete),
            "supplement_count": len(selected_incomplete),
            "addon_full_count": len(addon_full),
        },
        "upstream_supplement_policy": {
            "preserve_existing_upstream_keys": True,
            "supplement_only_exact_missing_normal_keys": True,
            "reuse_exact_g40_combined_value_only_for_unchanged_key_and_english": True,
            "added_keys_use_exact_target_english_fallback_unless_exact_same_key_donor_is_reviewed": True,
            "cross_key_reuse_allowed": False,
            "never_emit_upstream_owned_key": True,
            "retire_supplement_when_upstream_becomes_complete": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "malformed_upstream_override_policy": {
            "locale": "uk_ua",
            "reason": "Pinned upstream uk_ua.json is syntactically invalid (missing comma plus trailing comma). A valid full override is required so the broken upstream resource cannot prevent localization loading.",
            "repair_is_frozen_and_minimal": True,
            "preserve_repaired_upstream_target_normal_values": True,
            "fill_missing_unchanged_keys_from_exact_safe_g40_combined_values": True,
            "fill_new_keys_with_exact_g41_english_fallback": True,
            "emit_only_g41_target_keys": True,
        },
        "source_audit": "upstream/minecraft-1.21.5-language-audit.json",
        "english_diff": "upstream/diffs/1.21.4-to-1.21.5.json",
    }
    write_json(SCOPE_PATH, scope)

    audit = {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "verified-source-scope-upstream-ownership-and-malformed-locale-override",
        "minecraft": "1.21.5",
        "jei": "21.4.0",
        "jei_upstream_commit": PINNED_COMMIT,
        "endpoint_resolution": {
            "first_1_21_5_commit": FIRST_PORT_COMMIT,
            "final_1_21_5_commit": PINNED_COMMIT,
            "mainline_pre_1_21_6_commit": MAINLINE_PRE_NEXT_PORT_COMMIT,
            "next_minecraft_port_commit": NEXT_PORT_COMMIT,
            "next_minecraft_version": "1.21.6",
            "note": "The dedicated JEI 1.21.5 branch continued receiving fixes after mainline moved to 1.21.6, so its later branch head is the final maintained 1.21.5 localization endpoint.",
        },
        "build_metadata": {
            "neoforge": "21.5.75",
            "neoforge_loader_version_range": "[4,)",
            "neoforge_version_range": "[21.5.74,)",
            "java_toolchain": "21",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_1.21.4": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
            "decoupled_assets": True,
        },
        "minecraft_asset_indexes": {
            "minecraft_1.21.4": {
                "id": str(base_meta["assetIndex"].get("id")),
                "sha1": base_meta["assetIndex"].get("sha1"),
                "language_file_count": len(base_codes),
            },
            "minecraft_1.21.5": {
                "id": str(target_meta["assetIndex"].get("id")),
                "sha1": target_meta["assetIndex"].get("sha1"),
                "language_file_count": len(target_codes),
            },
            "live_language_file_additions": live_added,
            "live_language_file_removals": live_removed,
        },
        "english_source": {
            "base_key_count": len(base),
            "target_key_count": len(target),
            "target_normal_key_count": len(target_normal),
            "target_debug_only_key_count": len(target) - len(target_normal),
            "unchanged_key_and_value_count": len(unchanged),
            "added_keys": added,
            "removed_keys": removed,
            "changed_english_values": {key: {"before": base[key], "after": target[key]} for key in changed},
        },
        "upstream_locale_file_count": len(upstream_locales),
        "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness,
        "malformed_selected_upstream_locales": sorted(malformed_selected),
        "malformed_locale_evidence": {
            "uk_ua": {
                "problem": "JSON syntax invalid at pinned endpoint: missing comma after jei.alias.villager.spawn.egg and trailing comma before closing object.",
                "treatment": "Exclude from upstream supplement ownership and emit a valid full repaired override.",
            }
        },
        "ownership": {
            "complete_upstream": selected_complete,
            "incomplete_upstream": selected_incomplete,
            "addon_full_or_override": addon_full,
            "unselected_upstream": unselected_upstream,
        },
    }
    write_json(AUDIT_PATH, audit)

    policy = {
        "schema_version": 1,
        "generation": "g41-mc1.21.5",
        "minecraft": "1.21.5",
        "jei": "21.4.0",
        "pinned_commit": PINNED_COMMIT,
        "base_generation": "g40-mc1.21.4",
        "selected_scope_count": 90,
        "english_target_key_count": 290,
        "normal_target_key_count": 284,
        "debug_only_key_count": 6,
        "translation_reuse": {
            "reuse_exact_unchanged_g40_semantics": True,
            "same_key_required": True,
            "same_english_value_required": True,
            "cross_key_reuse_allowed": False,
            "runtime_literals_must_be_preserved": True,
            "uncertain_new_semantics_use_exact_english_fallback": True,
        },
        "added_semantics": {
            "count": 2,
            "keys": added,
            "default_treatment": "exact G41 English fallback unless a reviewed exact same-key donor with identical English semantics is available",
        },
        "upstream_ownership": {
            "complete_locales": selected_complete,
            "supplement_locales": selected_incomplete,
            "supplements_are_missing_normal_keys_only": True,
            "supplements_must_not_override_upstream_keys": True,
        },
        "malformed_upstream_override": {
            "locales": ["uk_ua"],
            "full_override_required": True,
            "preserve_repaired_upstream_target_normal_values": True,
            "repair_exact_known_syntax_only": True,
            "emit_only_target_keys": True,
        },
        "full_locale_policy": {
            "addon_full_or_override_count": len(addon_full),
            "documented_full_english_fallback_locales": fallback_locales,
            "documented_full_english_fallback_count": len(fallback_locales),
            "translated_or_ai_assisted_or_repaired_count": len(addon_full) - len(fallback_locales),
        },
        "runtime_gate": {
            "static_validation_is_not_runtime_promotion": True,
            "missing_key_json_supplements_require_resource_stack_merge_test": True,
            "release_jars_reserved_for_runtime_tested_artifacts": True,
        },
    }
    write_json(POLICY_PATH, policy)

    print("PASS: froze G41 Minecraft 1.21.5 / JEI 21.4.0 manifests")
    print("English: 290 total / 284 normal / 6 debug; 288 unchanged + 2 added")
    print("Ownership: 65 full/override + 24 supplements + 1 complete upstream = 90 selected")
    print("uk_ua is explicitly moved to a full repaired override because the pinned upstream JSON is malformed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

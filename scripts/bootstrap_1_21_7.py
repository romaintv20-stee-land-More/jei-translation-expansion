#!/usr/bin/env python3
"""Freeze deterministic G43 / Minecraft 1.21.7 source, diff, scope, audit, and policy manifests."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.6" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.6-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.7" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.6-to-1.21.7.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.7-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.7-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g43-mc1.21.7" / "policy.json"
PINNED_COMMIT = "ee33b5d69f6cf9167c32c2e84fdc69fa1b008440"
NEXT_PORT_COMMIT = "f61efdf5f6604d0d3a55a67cc5d28ec340f189aa"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_CONTENTS_API = "https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref=" + PINNED_COMMIT
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
ADDED_G43_KEYS = {
    "gui.jei.category.grindstone",
    "gui.jei.category.grindstone.experience",
}
MALFORMED_UPSTREAM_FULL_OVERRIDES = {"uk_ua"}


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G43-bootstrap"}
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


def repair_uk_ua_text(text: str) -> str:
    repaired, count = re.subn(
        r'("jei\.alias\.villager\.spawn\.egg"\s*:\s*"HMMM")\s*(\n\s*"modmenu\.descriptionTranslation\.jei")',
        r"\1,\2",
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("uk_ua missing-comma repair point not found")
    repaired, count = re.subn(r",\s*}\s*$", "\n}\n", repaired, count=1)
    if count != 1:
        raise ValueError("uk_ua trailing-comma repair point not found")
    return repaired


def parse_upstream_locale(locale: str, data: bytes) -> tuple[dict[str, str], bool]:
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
        if name.startswith("minecraft/lang/"):
            path = Path(name)
            if path.name != "languages.json" and path.suffix in {".lang", ".json"}:
                codes.add(path.stem.lower())
    codes.add("en_us")
    return codes


def main() -> int:
    base = parse_json_bytes(BASE_SOURCE.read_bytes())
    previous_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        raise ValueError(f"G42 selected scope changed: {len(selected)}")

    target_raw = fetch_bytes(f"{RAW_LANG}/en_us.json")
    target = parse_json_bytes(target_raw)
    target_normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(target_normal)) != (289, 291, 285):
        raise ValueError(f"unexpected G43 source counts: {len(base)}/{len(target)}/{len(target_normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (289, 2, 0, 0):
        raise ValueError("unexpected G42 -> G43 semantic partition")
    if set(added) != ADDED_G43_KEYS:
        raise ValueError(f"unexpected G43 added keys: {added}")

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.7",
        "minecraftVersionRange=[1.21.7, 1.21.8)",
        "neoforgeVersion=21.7.15-beta",
        "neoforgeVersionRange=[21.7.15-beta,)",
        "specificationVersion=23.1.0",
    ):
        if token not in props:
            raise ValueError(f"pinned G43 gradle.properties missing {token}")

    contents = fetch_json(LANG_CONTENTS_API)
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in contents
        if item.get("type") == "file" and str(item.get("name", "")).endswith(".json")
    )
    upstream_set = set(upstream_locales)
    completeness: dict[str, dict] = {}
    malformed: set[str] = set()
    for locale in sorted(selected & upstream_set):
        values, repaired = parse_upstream_locale(locale, fetch_bytes(f"{RAW_LANG}/{locale}.json"))
        if repaired:
            malformed.add(locale)
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
    if malformed != MALFORMED_UPSTREAM_FULL_OVERRIDES:
        raise ValueError(f"unexpected malformed selected upstream locales: {sorted(malformed)}")

    usable_upstream = (selected & upstream_set) - malformed
    complete = sorted(x for x in usable_upstream if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable_upstream if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable_upstream)
    unselected_upstream = sorted(upstream_set - selected)
    fallback_locales = list(previous_scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 30 or "uk_ua" in fallback_locales:
        raise ValueError("G43 fallback ownership unexpectedly changed")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.6")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.7")
    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_asset = fetch_json(base_meta["assetIndex"]["url"])
    target_asset = fetch_json(target_meta["assetIndex"]["url"])
    base_codes = language_codes(base_asset)
    target_codes = language_codes(target_asset)
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed:
        raise ValueError(f"Minecraft live language scope changed and requires manual review: added={live_added} removed={live_removed}")
    if selected - target_codes:
        raise ValueError(f"selected locale absent from Minecraft 1.21.7: {sorted(selected-target_codes)}")

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "base_minecraft": "1.21.6",
        "base_jei": "22.0.0",
        "target_minecraft": "1.21.7",
        "target_jei": "23.1.0",
        "base_key_count": len(base),
        "target_key_count": len(target),
        "target_normal_key_count": len(target_normal),
        "target_debug_only_key_count": len(target)-len(target_normal),
        "unchanged_key_and_value_count": len(unchanged),
        "added_key_count": len(added),
        "removed_key_count": len(removed),
        "changed_english_value_count": len(changed),
        "unchanged_keys": unchanged,
        "added_keys": added,
        "removed_keys": removed,
        "changed_english_values": {k:{"before":base[k],"after":target[k]} for k in changed},
    })

    scope = {
        "minecraft_version": "1.21.7",
        "jei_version": "23.1.0",
        "upstream_commit": PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.6-language-scope.json",
        "raw_language_count": len(target_codes),
        "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.6": False,
        "runtime_locale_filename_case": "lowercase",
        "resource_format": "json",
        "selected_upstream_complete_locales": complete,
        "selected_upstream_complete_locale_count": len(complete),
        "selected_upstream_incomplete_locales": incomplete,
        "selected_upstream_incomplete_locale_count": len(incomplete),
        "malformed_upstream_full_override_locales": sorted(malformed),
        "malformed_upstream_full_override_locale_count": len(malformed),
        "jei_upstream_unselected_or_nonmatching_locales": unselected_upstream,
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
            "live_language_asset_additions_from_1.21.6": live_added,
            "live_language_asset_removals_from_1.21.6": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales,
        "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_or_repaired_full_locale_count": len(addon_full)-len(fallback_locales),
        "translation_delta": {
            "base_generation": "g42-mc1.21.6",
            "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": 0,
            "changed_english_value_count": 0,
            "reuse_exact_g42_for_unchanged_meanings": True,
            "reintroduced_exact_historical_key": "gui.jei.category.grindstone.experience",
            "historical_source_generation": "g41-mc1.21.5",
        },
        "upstream_supplement_policy": {
            "preserve_existing_upstream_keys": True,
            "supplement_only_exact_missing_normal_keys": True,
            "reuse_exact_g42_combined_value_only_for_unchanged_key_and_english": True,
            "historical_same_key_same_english_reuse_allowed": True,
            "cross_key_reuse_allowed": False,
            "never_emit_upstream_owned_key": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "malformed_upstream_override_policy": {
            "locale": "uk_ua",
            "reason": "Pinned upstream uk_ua.json remains syntactically invalid; emit a valid full repair override.",
            "repair_is_frozen_and_minimal": True,
            "preserve_repaired_upstream_target_normal_values": True,
            "fill_missing_unchanged_keys_from_exact_safe_g42_combined_values": True,
            "emit_only_g43_target_keys": True,
        },
        "source_audit": "upstream/minecraft-1.21.7-language-audit.json",
        "english_diff": "upstream/diffs/1.21.6-to-1.21.7.json",
    }
    write_json(SCOPE_PATH, scope)

    audit = {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "verified-source-scope-upstream-ownership-and-malformed-locale-override",
        "minecraft": "1.21.7",
        "jei": "23.1.0",
        "jei_upstream_commit": PINNED_COMMIT,
        "endpoint_resolution": {
            "final_1_21_7_commit": PINNED_COMMIT,
            "next_minecraft_port_commit": NEXT_PORT_COMMIT,
            "next_minecraft_version": "1.21.8",
            "note": "The 1.21.8 port directly follows this endpoint, making it the final 1.21.7 mainline endpoint.",
        },
        "build_metadata": {
            "neoforge": "21.7.15-beta",
            "neoforge_loader_version_range": "[4,)",
            "neoforge_version_range": "[21.7.15-beta,)",
            "java_toolchain": "21",
            "language_format": "json",
            "locale_filename_case": "lowercase",
            "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json",
        },
        "language_scope": {
            "selected_scope_count": 90,
            "changed_from_1.21.6": False,
            "new_selected_primary_languages": [],
            "removed_selected_languages": [],
            "decoupled_assets": True,
        },
        "minecraft_asset_indexes": {
            "minecraft_1.21.6": {"id":str(base_meta["assetIndex"].get("id")),"sha1":base_meta["assetIndex"].get("sha1"),"language_file_count":len(base_codes)},
            "minecraft_1.21.7": {"id":str(target_meta["assetIndex"].get("id")),"sha1":target_meta["assetIndex"].get("sha1"),"language_file_count":len(target_codes)},
            "live_language_file_additions": live_added,
            "live_language_file_removals": live_removed,
        },
        "english_source": {
            "base_key_count": len(base),
            "target_key_count": len(target),
            "target_normal_key_count": len(target_normal),
            "target_debug_only_key_count": len(target)-len(target_normal),
            "unchanged_key_and_value_count": len(unchanged),
            "added_keys": added,
            "removed_keys": removed,
            "changed_english_values": {},
        },
        "upstream_locale_file_count": len(upstream_locales),
        "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness,
        "malformed_selected_upstream_locales": sorted(malformed),
        "ownership": {
            "complete_upstream": complete,
            "incomplete_upstream": incomplete,
            "addon_full_or_override": addon_full,
            "unselected_upstream": unselected_upstream,
        },
    }
    write_json(AUDIT_PATH, audit)

    policy = {
        "schema_version": 1,
        "generation": "g43-mc1.21.7",
        "minecraft": "1.21.7",
        "jei": "23.1.0",
        "pinned_commit": PINNED_COMMIT,
        "base_generation": "g42-mc1.21.6",
        "selected_scope_count": 90,
        "english_target_key_count": 291,
        "normal_target_key_count": 285,
        "debug_only_key_count": 6,
        "translation_reuse": {
            "reuse_exact_unchanged_g42_semantics": True,
            "same_key_required": True,
            "same_english_value_required": True,
            "cross_key_reuse_allowed": False,
            "historical_same_key_same_english_reuse_allowed": True,
            "runtime_literals_must_be_preserved": True,
            "uncertain_values_use_exact_english_fallback": True,
        },
        "added_semantics": {
            "count": 2,
            "keys": added,
            "fresh_translation_required_or_english_fallback": ["gui.jei.category.grindstone"],
            "exact_historical_same_key_reuse_permitted": ["gui.jei.category.grindstone.experience"],
            "historical_source_generation": "g41-mc1.21.5",
        },
        "upstream_ownership": {
            "complete_locales": complete,
            "supplement_locales": incomplete,
            "supplements_are_missing_normal_keys_only": True,
            "supplements_must_not_override_upstream_keys": True,
        },
        "malformed_upstream_override": {
            "locales": sorted(malformed),
            "full_override_required": True,
            "repair_is_minimal_and_deterministic": True,
        },
        "release_gate": {
            "static_reconstruction_is_not_runtime_promotion": True,
            "runtime_resource_stack_merge_test_required": True,
        },
    }
    write_json(POLICY_PATH, policy)

    print("PASS: froze G43 Minecraft 1.21.7 / JEI 23.1.0 manifests")
    print(f"English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug; {len(unchanged)} unchanged + {len(added)} added")
    print(f"Ownership: {len(addon_full)} full/override + {len(incomplete)} supplements + {len(complete)} complete upstream = 90 selected")
    print(f"Upstream files: {len(upstream_locales)}; malformed full overrides: {sorted(malformed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

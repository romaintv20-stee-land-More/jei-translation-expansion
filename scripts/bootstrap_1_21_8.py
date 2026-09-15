#!/usr/bin/env python3
"""Freeze deterministic G44 / Minecraft 1.21.8 source, ownership, diff, and reuse policy."""
from __future__ import annotations

import json
import re
from pathlib import Path

import audit_1_21_8 as audit

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.7" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.7-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.8" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.7-to-1.21.8.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.8-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.8-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g44-mc1.21.8" / "policy.json"
PINNED_COMMIT = audit.PINNED_COMMIT
NEXT_PORT_COMMIT = audit.NEXT_PORT_COMMIT
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
DONOR_LANG = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{DONOR_COMMIT}/Common/src/main/resources/assets/jei/lang"
DONOR_LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={DONOR_COMMIT}"
DEBUG_PREFIX = audit.DEBUG_PREFIX
EXPECTED_ADDED = {
    "jei.config.client.lookupHistory",
    "jei.config.client.lookupHistory.description",
    "jei.config.client.lookupHistory.displaySide",
    "jei.config.client.lookupHistory.displaySide.description",
    "jei.config.client.lookupHistory.enabled",
    "jei.config.client.lookupHistory.enabled.description",
    "jei.config.client.lookupHistory.maxIngredients",
    "jei.config.client.lookupHistory.maxIngredients.description",
    "jei.config.client.lookupHistory.maxRows",
    "jei.config.client.lookupHistory.maxRows.description",
    "jei.tooltip.bookmarks.disable",
    "jei.tooltip.bookmarks.enable",
    "jei.tooltip.lookupHistory.disable",
    "jei.tooltip.lookupHistory.enable",
    "jei.tooltip.lookupHistory.usage",
}
EXPECTED_REMOVED = {"jei.tooltip.bookmarks"}


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
        repaired, count = re.subn(
            r'("jei\.alias\.villager\.spawn\.egg"\s*:\s*"HMMM")\s*(\n\s*"modmenu\.descriptionTranslation\.jei")',
            r"\1,\2", text, count=1,
        )
        if count != 1:
            raise ValueError("donor uk_ua missing-comma repair point changed")
        repaired, count = re.subn(r",\s*}\s*$", "\n}\n", repaired, count=1)
        if count != 1:
            raise ValueError("donor uk_ua trailing-comma repair point changed")
        return audit.clean(json.loads(repaired))


def main() -> int:
    base = audit.clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    previous_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(previous_scope["addon_full_locales"]) | set(previous_scope["selected_upstream_complete_locales"]) | set(previous_scope["selected_upstream_incomplete_locales"])
    if len(selected) != 90:
        raise ValueError(f"G43 selected scope changed: {len(selected)}")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal)) != (291, 305, 299):
        raise ValueError(f"unexpected G44 source counts: {len(base)}/{len(target)}/{len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (290, 15, 1, 0):
        raise ValueError("unexpected G43 -> G44 semantic partition")
    if set(added) != EXPECTED_ADDED or set(removed) != EXPECTED_REMOVED:
        raise ValueError(f"G44 added/removed sets changed: added={added} removed={removed}")

    next_commit = audit.fetch_json(audit.NEXT_COMMIT_API)
    if [p["sha"] for p in next_commit.get("parents", [])] != [PINNED_COMMIT]:
        raise ValueError("G44 endpoint is no longer the direct parent of the 1.21.9 port")

    props = audit.fetch_text(f"{audit.RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.8",
        "minecraftVersionRange=[1.21.8, 1.21.9)",
        "neoforgeVersion=21.8.47",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.8.9,)",
        "specificationVersion=24.2.0",
    ):
        if token not in props:
            raise ValueError(f"pinned G44 metadata missing {token}")

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
        raise ValueError(f"unexpected malformed G44 selected upstream locales: {sorted(malformed)}")
    usable = (selected & upstream_set) - malformed
    complete = sorted(x for x in usable if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable)
    if (len(addon_full), len(incomplete), len(complete)) != (65, 24, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected G44 ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.7")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.8")
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(f"G44 Minecraft language membership changed: added={live_added} removed={live_removed} absent={sorted(selected-target_codes)}")

    donor_en = audit.clean(json.loads(audit.fetch_text(f"{DONOR_LANG}/en_us.json")))
    donor_exact_added = sorted(key for key in added if donor_en.get(key) == target[key])
    if set(donor_exact_added) != EXPECTED_ADDED:
        raise ValueError(f"donor snapshot does not preserve all G44 added English semantics exactly: {donor_exact_added}")
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
        raise ValueError("G44 documented fallback ownership changed")

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version":1,
        "base_minecraft":"1.21.7","base_jei":"23.1.0",
        "target_minecraft":"1.21.8","target_jei":"24.2.0",
        "base_key_count":len(base),"target_key_count":len(target),
        "target_normal_key_count":len(normal),"target_debug_only_key_count":len(target)-len(normal),
        "unchanged_key_and_value_count":len(unchanged),"added_key_count":len(added),
        "removed_key_count":len(removed),"changed_english_value_count":len(changed),
        "unchanged_keys":unchanged,"added_keys":added,"removed_keys":removed,
        "changed_english_values":{k:{"before":base[k],"after":target[k]} for k in changed},
    })

    scope = {
        "minecraft_version":"1.21.8","jei_version":"24.2.0","upstream_commit":PINNED_COMMIT,
        "base_scope_manifest":"upstream/minecraft-1.21.7-language-scope.json",
        "raw_language_count":len(target_codes),"selected_scope_count":90,
        "selected_scope_changed_from_1.21.7":False,"runtime_locale_filename_case":"lowercase","resource_format":"json",
        "selected_upstream_complete_locales":complete,"selected_upstream_complete_locale_count":len(complete),
        "selected_upstream_incomplete_locales":incomplete,"selected_upstream_incomplete_locale_count":len(incomplete),
        "malformed_upstream_full_override_locales":sorted(malformed),"malformed_upstream_full_override_locale_count":len(malformed),
        "jei_upstream_unselected_or_nonmatching_locales":sorted(upstream_set-selected),
        "addon_full_locale_count":len(addon_full),"addon_full_locales":addon_full,
        "new_selected_primary_languages":[],"removed_selected_languages":[],
        "downloaded":{"base_asset_index_id":str(base_meta["assetIndex"].get("id")),"base_asset_index_sha1":base_meta["assetIndex"].get("sha1"),"asset_index_id":str(target_meta["assetIndex"].get("id")),"asset_index_sha1":target_meta["assetIndex"].get("sha1"),"language_asset_file_count":len(target_codes),"live_language_asset_additions_from_1.21.7":live_added,"live_language_asset_removals_from_1.21.7":live_removed},
        "documented_full_english_fallback_locales":fallback_locales,"documented_full_english_fallback_count":len(fallback_locales),
        "translated_or_ai_assisted_or_repaired_full_locale_count":len(addon_full)-len(fallback_locales),
        "translation_delta":{"base_generation":"g43-mc1.21.7","unchanged_key_and_english_value_count":len(unchanged),"added_key_count":15,"removed_key_count":1,"changed_english_value_count":0,"reuse_exact_g43_for_unchanged_meanings":True},
        "exact_future_donor":{"commit":DONOR_COMMIT,"exact_same_key_same_english_added_keys":donor_exact_added,"locale_coverage":donor_coverage},
        "upstream_supplement_policy":{"preserve_existing_upstream_keys":True,"supplement_only_exact_missing_normal_keys":True,"reuse_exact_g43_combined_value_only_for_unchanged_key_and_english":True,"future_donor_same_key_same_english_reuse_allowed":True,"cross_key_reuse_allowed":False,"never_emit_upstream_owned_key":True,"runtime_merge_requires_validation_before_jar_promotion":True},
        "malformed_upstream_override_policy":{"locale":"uk_ua","reason":"Pinned upstream uk_ua.json remains syntactically invalid; emit a valid full repair override.","repair_is_frozen_and_minimal":True,"preserve_repaired_upstream_target_normal_values":True,"fill_missing_unchanged_keys_from_exact_safe_g43_combined_values":True,"fill_missing_added_keys_from_exact_same-key donor when available":True,"emit_only_g44_target_keys":True},
        "source_audit":"upstream/minecraft-1.21.8-language-audit.json","english_diff":"upstream/diffs/1.21.7-to-1.21.8.json",
    }
    write_json(SCOPE_PATH, scope)

    audit_manifest = {
        "schema_version":1,"audit_date":"2026-09-15","status":"verified-source-scope-upstream-ownership-and-donor-semantics",
        "minecraft":"1.21.8","jei":"24.2.0","jei_upstream_commit":PINNED_COMMIT,
        "endpoint_resolution":{"final_1_21_8_commit":PINNED_COMMIT,"next_minecraft_port_commit":NEXT_PORT_COMMIT,"next_minecraft_version":"1.21.9","note":"The 1.21.9 port is directly parented by this endpoint."},
        "build_metadata":{"neoforge":"21.8.47","neoforge_loader_version_range":"[4,)","neoforge_version_range":"[21.8.9,)","java_toolchain":"21","language_format":"json","locale_filename_case":"lowercase","english_source_path":"Common/src/main/resources/assets/jei/lang/en_us.json"},
        "language_scope":{"selected_scope_count":90,"changed_from_1.21.7":False,"new_selected_primary_languages":[],"removed_selected_languages":[],"decoupled_assets":True},
        "minecraft_asset_indexes":{"minecraft_1.21.7":{"id":str(base_meta["assetIndex"].get("id")),"sha1":base_meta["assetIndex"].get("sha1"),"language_file_count":len(base_codes)},"minecraft_1.21.8":{"id":str(target_meta["assetIndex"].get("id")),"sha1":target_meta["assetIndex"].get("sha1"),"language_file_count":len(target_codes)},"live_language_file_additions":live_added,"live_language_file_removals":live_removed},
        "english_source":{"base_key_count":len(base),"target_key_count":len(target),"target_normal_key_count":len(normal),"target_debug_only_key_count":len(target)-len(normal),"unchanged_key_and_value_count":len(unchanged),"added_keys":added,"removed_keys":removed,"changed_english_values":{}},
        "upstream_locale_file_count":len(upstream_locales),"upstream_locales":upstream_locales,"selected_upstream_completeness":completeness,"malformed_selected_upstream_locales":sorted(malformed),
        "ownership":{"complete_upstream":complete,"incomplete_upstream":incomplete,"addon_full_or_override":addon_full,"unselected_upstream":sorted(upstream_set-selected)},
        "exact_future_donor":{"commit":DONOR_COMMIT,"all_added_english_semantics_exact":True,"locale_coverage":donor_coverage},
    }
    write_json(AUDIT_PATH, audit_manifest)

    policy = {
        "schema_version":1,"generation":"g44-mc1.21.8","minecraft":"1.21.8","jei":"24.2.0","pinned_commit":PINNED_COMMIT,"base_generation":"g43-mc1.21.7","selected_scope_count":90,
        "english_target_key_count":305,"normal_target_key_count":299,"debug_only_key_count":6,
        "translation_reuse":{"reuse_exact_unchanged_g43_semantics":True,"same_key_required":True,"same_english_value_required":True,"future_donor_commit":DONOR_COMMIT,"future_donor_allowed_only_for_exact_same_key_same_english":True,"cross_key_reuse_allowed":False,"runtime_literals_must_be_preserved":True,"uncertain_values_use_exact_english_fallback":True},
        "added_semantics":{"count":15,"keys":added},"removed_semantics":{"count":1,"keys":removed,"must_not_be_emitted":True},
        "upstream_ownership":{"complete_locales":complete,"supplement_locales":incomplete,"supplements_are_missing_normal_keys_only":True,"supplements_must_not_override_upstream_keys":True},
        "malformed_upstream_override":{"locales":["uk_ua"],"full_override_required":True,"repair_is_frozen_and_minimal":True},
        "runtime_promotion":{"static_validation_is_not_runtime_validation":True,"runtime_merge_test_required":True},
    }
    write_json(POLICY_PATH, policy)

    print("PASS: froze G44 Minecraft 1.21.8 / JEI 24.2.0 manifests")
    print(f"English: 305 total / 299 normal / 6 debug; delta 290 unchanged + 15 added + 1 removed + 0 changed")
    print(f"Ownership: {len(addon_full)} full/override + {len(incomplete)} supplements + {len(complete)} complete upstream = 90")
    print(f"Exact future donor {DONOR_COMMIT[:7]} covers all 15 added English semantics; donor locale files with at least one added translation: {len(donor_coverage)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

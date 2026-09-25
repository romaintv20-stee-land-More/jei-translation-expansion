#!/usr/bin/env python3
"""Freeze final G52 English, scope, reuse policy and ownership manifests."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

import audit_26_3 as audit
import reconstruct_26_2 as g51

ROOT = audit.ROOT
SOURCE = ROOT / "upstream/sources/26.3/en_us.json"
DIFF = ROOT / "upstream/diffs/26.2-to-26.3.json"
SCOPE = ROOT / "upstream/minecraft-26.3-language-scope.json"
AUDIT = ROOT / "upstream/minecraft-26.3-language-audit.json"
POLICY = ROOT / "translations/g52-mc26.3/policy.json"

def write_json(path: Path, data: dict, verify: bool) -> None:
    new = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if verify:
        if not path.is_file() or path.read_text(encoding="utf-8") != new:
            raise ValueError(f"Frozen G52 manifest is missing or stale: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8")

def freeze(verify: bool = False) -> dict:
    a = audit.audit()
    p = a["previous"]
    target = a["target"]
    normal = a["normal"]
    overrides = {}
    for locale in a["incomplete"]:
        upstream = a["upstream"][locale]
        unsafe = sorted(k for k in normal & upstream.keys()
                        if not g51.preserves_runtime_literals(target[k], upstream[k]))
        if unsafe:
            overrides[locale] = unsafe
    override_count = sum(len(v) for v in overrides.values())
    fallback = sorted(set(p["documented_full_english_fallback_locales"]) & set(a["full"]))
    if len(fallback) != 30:
        raise ValueError(f"Documented G51 English fallbacks changed: {len(fallback)}")
    diff = {
        "schema_version": 1, "base_minecraft": "26.2", "base_jei": "30.32.0",
        "target_minecraft": "26.3", "target_jei": audit.JEI_VERSION,
        "base_key_count": len(a["base"]), "target_key_count": len(target),
        "target_normal_key_count": len(normal), "target_debug_only_key_count": 6,
        "unchanged_key_and_value_count": len(a["unchanged"]),
        "added_key_count": len(a["added"]), "removed_key_count": len(a["removed"]),
        "changed_english_value_count": len(a["changed"]),
        "unchanged_keys": a["unchanged"], "added_keys": a["added"],
        "added_english_values": {k:target[k] for k in a["added"]},
        "removed_keys": a["removed"],
        "changed_english_values": {k:{"from":a["base"][k],"to":target[k]} for k in a["changed"]},
        "note": "Only the 193 identical key-and-English-meaning pairs can reuse G51 translations. Added, renamed, removed and English-changed keys must not inherit other-key translations."
    }
    ready = a["readiness"]["minecraft"]
    scope = copy.deepcopy(p)
    scope.update({
        "minecraft_version":"26.3", "jei_version":audit.JEI_VERSION,
        "upstream_commit":audit.PIN, "upstream_branch":audit.BRANCH,
        "snapshot_status":"final-minecraft-pinned-jei-26.3-branch",
        "base_scope_manifest":"upstream/minecraft-26.2-language-scope.json",
        "raw_language_count":ready["language_asset_file_count"],
        "selected_scope_count":90, "selected_scope_changed_from_26.2":False,
        "selected_upstream_complete_locales":a["complete"],
        "selected_upstream_complete_locale_count":len(a["complete"]),
        "selected_upstream_incomplete_locales":a["incomplete"],
        "selected_upstream_incomplete_locale_count":len(a["incomplete"]),
        "malformed_upstream_full_override_locales":[],
        "malformed_upstream_full_override_locale_count":0,
        "jei_upstream_unselected_or_nonmatching_locales":sorted(a["upstream_names"]-a["selected"]),
        "addon_full_locale_count":len(a["full"]), "addon_full_locales":a["full"],
        "new_selected_primary_languages":[], "removed_selected_languages":[],
        "documented_full_english_fallback_locales":fallback,
        "documented_full_english_fallback_count":len(fallback),
        "translated_or_ai_assisted_full_locale_count":len(a["full"])-len(fallback),
        "translation_delta":{
            "base_generation":"g51-mc26.2", "unchanged_key_and_english_value_count":len(a["unchanged"]),
            "added_key_count":len(a["added"]), "removed_key_count":len(a["removed"]),
            "changed_english_value_count":len(a["changed"]),
            "reuse_exact_g51_for_identical_meanings_only":True,
            "untranslated_new_or_changed_entries_use_english_fallback":True},
        "upstream_literal_safety_overrides":overrides,
        "upstream_literal_safety_override_count":override_count,
        "source_audit":"upstream/minecraft-26.3-language-audit.json",
        "english_diff":"upstream/diffs/26.2-to-26.3.json",
    })
    scope.pop("selected_scope_changed_from_26.1.2", None)
    scope["downloaded"] = {
        "base_asset_index_id":a["readiness"]["base_g51"]["asset_index_id"],
        "base_asset_index_sha1":a["readiness"]["base_g51"]["asset_index_sha1"],
        "asset_index_id":ready["asset_index_id"],
        "asset_index_sha1":ready["asset_index_sha1"],
        "language_asset_file_count":ready["language_asset_file_count"],
        "live_language_asset_additions_from_26.2":ready["language_additions_from_26_2"],
        "live_language_asset_removals_from_26.2":ready["language_removals_from_26_2"]}
    scope["upstream_supplement_policy"] = {
        "preserve_existing_safe_upstream_keys":True,
        "supplement_missing_keys_plus_explicit_safety_overrides":True,
        "explicit_upstream_owned_override_keys":overrides,
        "reuse_exact_g51_combined_value_only_for_same_key_same_english":True,
        "cross_key_reuse_allowed":False, "never_emit_other_upstream_owned_keys":True,
        "runtime_merge_requires_validation_before_jar_promotion":True}
    policy = {
        "schema_version":1, "generation":"g52-mc26.3",
        "minecraft":"26.3", "jei":audit.JEI_VERSION, "source_commit":audit.PIN,
        "selected_scope_count":90,
        "ownership":{"addon_full":63,"upstream_supplements":26,"complete_upstream":1},
        "translation_reuse":{"base_generation":"g51-mc26.2",
            "reuse_only_exact_same_key_same_english":True,
            "eligible_unchanged_key_count":193, "cross_key_reuse_allowed":False},
        "added_key_count":304, "changed_english_value_count":87,
        "new_or_changed_key_fallback":"English unless specifically provided by safe upstream JEI",
        "upstream_literal_safety_override_count":override_count,
        "static_candidate_build_allowed":True, "runtime_promotion_allowed":False,
        "runtime_promotion_separate":True}
    report = {
        "schema_version":1, "audit_date":"2026-09-25",
        "status":"verified-exact-pinned-jei-26.3-branch-source-and-locale-ownership",
        "minecraft":"26.3", "jei":audit.JEI_VERSION,
        "upstream_commit":audit.PIN, "upstream_branch":audit.BRANCH,
        "build":{"neoforge":audit.NEOFORGE_VERSION,"minimum_neoforge":audit.NEOFORGE_MIN,
                 "java":25,"neoforge_loader_version_range":"[4,)"},
        "english_keys":{"base":334,"target":584,"normal":578,"debug":6,
                       "unchanged":193,"added":304,"removed":54,"changed":87},
        "languages":{"selected":90,"addon_full":63,"supplements":26,
                     "upstream_complete":1,"upstream_safety_overrides":override_count},
        "source_version_is_branch_specification":True,
        "translation_quality_note":"New or English-changed source keys require translation review; English fallbacks do not imply native-language completion.",
        "runtime_merge_test_passed":False,
        "minecraft_asset_index_sha1":ready["asset_index_sha1"],
        "minecraft_language_asset_file_count":ready["language_asset_file_count"],
    }
    for path,data in ((SOURCE,target),(DIFF,diff),(SCOPE,scope),(AUDIT,report),(POLICY,policy)):
        write_json(path,data,verify)
    print(f"PASS: {'verified' if verify else 'frozen'} G52 English source, delta, ownership and policy")
    print(f"90 languages; 63 complete addon files; 26 upstream supplements; 1 upstream complete")
    print(f"584 keys (578 normal + 6 debug), 304 new; upstream safety overrides: {override_count}")
    return report

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    freeze(verify=args.verify)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

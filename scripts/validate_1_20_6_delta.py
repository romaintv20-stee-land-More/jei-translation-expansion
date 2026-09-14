#!/usr/bin/env python3
"""Validate G37 Minecraft 1.20.6 / JEI 18.0.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_20_6 as g37

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.20.6-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.6-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g37-mc1.20.6" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20.4-to-1.20.6.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.4-language-scope.json"
EXPECTED_COMPLETE = {"en_us"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru",
    "sv_se", "tr_tr", "uk_ua", "zh_cn",
}
FALLBACK = {
    "ba_ru", "bar", "br_fr", "bs_ba", "fo_fo", "fur_it", "fy_nl", "gd_gb", "haw_us", "ig_ng",
    "kk_kz", "kn_in", "ksh", "kw_gb", "li_li", "lmo", "lo_la", "mn_mn", "nah", "ovd", "ry_ua",
    "sah_sah", "se_no", "so_so", "szl", "ta_in", "tl_ph", "tt_ru", "vec_it", "yi_de", "yo_ng",
}


def main() -> int:
    errors: list[str] = []
    base = g37.parse_json(g37.BASE_SOURCE)
    target = g37.parse_json(g37.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g37.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g37.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (157, 157, 151):
        errors.append("G37 English counts must remain 157 total / 151 normal")
    if (len(unchanged), len(added), len(removed), len(changed)) != (157, 0, 0, 0):
        errors.append("G37 semantic delta must remain 157 unchanged + 0 added + 0 removed + 0 changed")
    if diff["added_keys"] or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G37 frozen diff must contain no semantic changes")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (67, 1, 22, 90):
        errors.append("G37 ownership partition must be 67 full + 1 complete + 22 supplements = 90")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G37 ownership partitions overlap")
    if complete != EXPECTED_COMPLETE or incomplete != EXPECTED_INCOMPLETE:
        errors.append("G37 upstream ownership differs from frozen exploratory audit")

    base_full = set(base_scope["addon_full_locales"])
    base_complete = set(base_scope["selected_upstream_complete_locales"])
    base_incomplete = set(base_scope["selected_upstream_incomplete_locales"])
    if full != base_full or complete != base_complete or incomplete != base_incomplete:
        errors.append("G37 ownership must match G36 exactly")
    if scope["new_selected_primary_languages"] or scope["removed_selected_languages"]:
        errors.append("G37 must not add or remove selected Minecraft languages")
    if set(scope["documented_full_english_fallback_locales"]) != FALLBACK:
        errors.append("G37 documented full-English fallback set changed")
    if scope["translated_or_ai_assisted_full_locale_count"] != 36:
        errors.append("G37 translated/AI-assisted full locale count must remain 36")

    try:
        remote_english = g37.fetch_upstream_json(g37.G37_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G37 English source differs from pinned JEI 18.0.0")
        for locale in sorted(complete | incomplete):
            upstream = g37.fetch_upstream_json(g37.G37_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: expected complete upstream")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: expected incomplete upstream")
    except Exception as exc:
        errors.append(f"failed pinned-upstream verification: {exc}")

    endpoint = audit["endpoint_resolution"]
    if endpoint["next_minecraft_port_commit"] != "4f54914d4364b102d940a4aac4bd94969a33a429" or endpoint["next_minecraft_version"] != "1.21":
        errors.append("G37 endpoint boundary changed")
    build = audit["build_metadata"]
    if build["forge"] != "50.1.3" or build["mappings_version"] != "1.20.6-2024.06.02-1.20.6" or build["java_toolchain"] != "21":
        errors.append("G37 frozen build metadata changed")
    assets = audit["minecraft_asset_indexes"]
    if assets["minecraft_1.20.6"]["id"] != "16" or assets["minecraft_1.20.6"]["sha1"] != "ccf52649de5f7af097d939c9a94640ac695883ea":
        errors.append("G37 frozen Minecraft 1.20.6 asset metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g36_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G37 policy must enforce exact G36 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20.6 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.20.6 / JEI 18.0.0 G37 source, scope and ownership QA")
    print("English: 157 keys / 151 normal / 6 debug; all 157 semantics unchanged")
    print("Selected language scope: 90, unchanged from G36")
    print("Ownership: 67 addon-full + 22 supplements + 1 complete upstream")
    print("Java target advances to 21; translation ownership remains unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

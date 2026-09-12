#!/usr/bin/env python3
"""Validate G17 Minecraft 1.15.1 / JEI 6.0.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_15_1 as g17

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.15.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.15.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g17-mc1.15.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.14.4-to-1.15.1.json"


def main() -> int:
    errors: list[str] = []
    base = g17.parse_json(g17.BASE_SOURCE)
    target = g17.parse_json(g17.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g17.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if target != base:
        errors.append("G17 stored English source differs semantically from G16")
    if (len(target), len(normal)) != (109, 106):
        errors.append(f"G17 English counts changed: total={len(target)} normal={len(normal)}")
    if any((diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"])):
        errors.append("G17 frozen diff must have no added/removed/changed English meanings")
    if diff["unchanged_key_and_value_count"] != 109:
        errors.append("G17 frozen diff must contain 109 unchanged key/value pairs")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (66, 5, 16, 87):
        errors.append("G17 ownership partition must be 66 full + 5 complete + 16 supplements = 87")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G17 ownership partitions overlap")
    if scope["raw_language_count"] != 122 or scope["selected_scope_count"] != 87:
        errors.append("G17 Minecraft raw/selected counts must be 122/87")

    expected_complete = {"de_de", "en_us", "pl_pl", "pt_br", "ru_ru"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
        "it_it", "ja_jp", "ko_kr", "lt_lt", "sv_se", "tr_tr", "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G17 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G17 incomplete upstream set changed: {sorted(incomplete)}")

    removed_selected = {"kab_kab", "moh_ca", "nuk", "oj_ca", "scn"}
    if set(scope["removed_previously_selected_codes"]) != removed_selected:
        errors.append("G17 removed-selected set changed")
    if removed_selected & selected:
        errors.append("G17 must not retain Minecraft locale codes removed in 1.15.1")
    if set(scope["new_selected_primary_languages"]) != {"lmo"} or "lmo" not in full:
        errors.append("G17 must select Lombard (lmo) as the one new primary language")
    if set(scope["deferred_new_codes"]) != {"lzh", "rpr", "zh_hk"}:
        errors.append("G17 deferred new-code classification changed")

    try:
        remote_english = g17.fetch_upstream_json(g17.G17_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G17 English source differs from pinned JEI 6.0.0")
        for locale in sorted(complete):
            upstream = g17.fetch_upstream_json(g17.G17_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G17 keys")
        for locale in sorted(incomplete):
            upstream = g17.fetch_upstream_json(g17.G17_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G17 pinned-upstream ownership verification: {exc}")

    sv_upstream = g17.fetch_upstream_json(g17.G17_COMMIT, "sv_se")
    expected_sv_missing = {
        "gui.jei.category.blasting", "gui.jei.category.campfire",
        "gui.jei.category.smoking", "key.jei.toggleEditMode",
    }
    if normal - set(sv_upstream) != expected_sv_missing:
        errors.append(f"sv_se G17 missing set changed: {sorted(normal - set(sv_upstream))}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "58c12b1e2878e0a78719778acb803746450b3f1c":
        errors.append("G17 Minecraft 1.15 asset-index SHA changed")
    if set(asset["added_codes_since_1.14.4"]) != {"lmo", "lzh", "rpr", "zh_hk"}:
        errors.append("G17 Minecraft added-code set changed")
    if set(asset["removed_codes_since_1.14.4"]) != {"got_de", "kab_kab", "moh_ca", "nuk", "oj_ca", "scn", "swg", "tzl_tzl"}:
        errors.append("G17 Minecraft removed-code set changed")
    if not policy["translation_reuse"]["all_semantics_reuse_g16"]:
        errors.append("G17 policy must enforce exact G16 semantic inheritance")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.15.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.15.1 / JEI 6.0.0 G17 source, scope and ownership QA")
    print("English: 109 semantic keys / 106 normal / 3 debug; all 109 unchanged from G16")
    print("Minecraft raw/selected: 122 / 87")
    print("Selected upstream: 21 (5 complete + 16 supplements)")
    print("Addon-owned full locales: 66 (65 inherited + new lmo fallback)")
    print("Removed selected Minecraft codes: kab_kab, moh_ca, nuk, oj_ca, scn")
    print("sv_se upstream regression: three category translations are now supplement-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

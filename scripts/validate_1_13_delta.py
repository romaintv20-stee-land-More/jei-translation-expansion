#!/usr/bin/env python3
"""Validate G12 Minecraft 1.13 / JEI 4.14.4 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_13 as g12

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.13-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.13-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g12-mc1.13" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.12.2-to-1.13.json"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + g12.G12_COMMIT


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G12-QA"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    errors: list[str] = []
    base = g12.parse_lang(g12.BASE_SOURCE)
    target = g12.parse_json(g12.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g12.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    changed_debug = {key for key in changed if key.startswith(g12.DEBUG_PREFIX)}
    reviewed_normal = added | (changed - changed_debug)

    if (len(target), len(normal)) != (105, 102):
        errors.append(f"G12 English counts changed: total={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed), len(changed_debug), len(reviewed_normal)) != (59, 4, 14, 42, 3, 43):
        errors.append(
            "G12 English diff changed: "
            f"unchanged={len(unchanged)} added={len(added)} removed={len(removed)} "
            f"changed={len(changed)} changed_debug={len(changed_debug)} reviewed_normal={len(reviewed_normal)}"
        )
    if set(diff["added_keys"]) != added or set(diff["removed_keys"]) != removed or set(diff["changed_english_values"]) != changed:
        errors.append("G12 diff manifest key sets differ from computed source diff")
    for key, pair in diff["changed_english_values"].items():
        if pair != [base[key], target[key]]:
            errors.append(f"G12 diff manifest old/new value mismatch for {key}")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (62, 9, 12, 83):
        errors.append("G12 ownership partition must be 62 full + 9 complete + 12 supplements = 83")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G12 ownership partitions overlap")
    if scope["raw_language_count"] != 113 or scope["selected_scope_count"] != 83:
        errors.append("G12 Minecraft raw/selected scope counts must remain 113/83")

    expected_complete = {"de_de", "en_us", "fr_fr", "ja_jp", "pl_pl", "pt_br", "ru_ru", "sv_se", "zh_cn"}
    expected_incomplete = {"ar_sa", "bg_bg", "cs_cz", "el_gr", "es_es", "fi_fi", "he_il", "it_it", "ko_kr", "lt_lt", "tr_tr", "uk_ua"}
    if complete != expected_complete:
        errors.append(f"G12 complete selected upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G12 incomplete selected upstream set changed: {sorted(incomplete)}")
    if set(scope["jei_upstream_unselected_or_nonmatching_locales"]) != {"en_au", "nb_no", "zh_tw"}:
        errors.append("G12 unselected JEI locale set changed")

    if scope.get("selected_locale_code_renames") != {"ksh_de": "ksh"}:
        errors.append("G12 ksh_de -> ksh locale-code migration changed")
    if set(scope["new_selected_primary_languages"]) != {"nuk", "ovd", "szl"}:
        errors.append("G12 new selected primary-language set changed")
    if not {"ksh", "nuk", "ovd", "szl"} <= full:
        errors.append("G12 renamed/new selected languages are not all addon-full locales")
    if "ksh_de" in selected:
        errors.append("G12 selected runtime scope must use ksh, not removed ksh_de")

    try:
        remote_english = g12.fetch_upstream_json(g12.G12_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G12 English source differs from pinned JEI 4.14.4")
        listing = fetch_json(CONTENTS_URL)
        live_locales = {
            Path(item["name"]).stem.lower()
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".json")
        }
        if len(live_locales) != 24:
            errors.append(f"expected 24 JEI 4.14.4 JSON locale files, got {len(live_locales)}")
        if full & live_locales:
            errors.append("G12 addon-full ownership overlaps live JEI upstream JSON locale files")
        if not (complete | incomplete) <= live_locales:
            errors.append("G12 selected upstream ownership contains locale absent from live pinned JEI")
        for locale in sorted(complete):
            upstream = g12.fetch_upstream_json(g12.G12_COMMIT, locale)
            missing = normal - set(upstream)
            if missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing {len(missing)} normal keys")
        for locale in sorted(incomplete):
            upstream = g12.fetch_upstream_json(g12.G12_COMMIT, locale)
            missing = normal - set(upstream)
            if not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G12 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "2175b85e150c64f7ed285e7624b87c18cd992497":
        errors.append("G12 frozen Minecraft asset-index SHA changed")
    if set(asset["added_codes_since_1_12_2"]) != {"brb", "enp", "enws", "ksh", "nuk", "ovd", "swg", "sxu", "szl"}:
        errors.append("G12 frozen added Minecraft locale-code set changed")
    if set(asset["removed_codes_since_1_12_2"]) != {"de_alg", "en_ws", "ksh_de"}:
        errors.append("G12 frozen removed Minecraft locale-code set changed")
    if policy["english_diff"]["reviewed_normal_added_or_changed_key_count"] != 43:
        errors.append("G12 policy reviewed-normal-key count changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.13 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.13 / JEI 4.14.4 G12 source, scope and ownership QA")
    print("English: 105 semantic keys / 102 normal / 3 debug; resource format JSON")
    print("G11 -> G12: 59 unchanged, 4 added, 14 removed, 42 changed")
    print("Reviewed normal added/changed meanings: 43")
    print("Minecraft raw/selected: 113 / 83")
    print("Locale migration: ksh_de -> ksh; new selected: nuk, ovd, szl")
    print("Selected upstream: 21 (9 complete + 12 supplements)")
    print("Addon-owned full locales: 62")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

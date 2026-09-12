#!/usr/bin/env python3
"""Validate G14 Minecraft 1.14.2 / JEI 6.0.0 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_14_2 as g14

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.14.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.14.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g14-mc1.14.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.13.2-to-1.14.2.json"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + g14.G14_COMMIT


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G14-QA"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    errors: list[str] = []
    base = g14.parse_json(g14.BASE_SOURCE)
    target = g14.parse_json(g14.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g14.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    reviewed_normal = {key for key in added | changed if not key.startswith(g14.DEBUG_PREFIX)}

    if (len(target), len(normal)) != (109, 106):
        errors.append(f"G14 English counts changed: total={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed), len(reviewed_normal)) != (106, 3, 0, 0, 3):
        errors.append(
            "G14 English diff changed: "
            f"unchanged={len(unchanged)} added={len(added)} removed={len(removed)} "
            f"changed={len(changed)} reviewed_normal={len(reviewed_normal)}"
        )
    if added != g14.NEW_G14_KEYS:
        errors.append(f"G14 added-key set changed: {sorted(added)}")
    if set(diff["added_keys"]) != added or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G14 diff manifest differs from computed source diff")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (70, 2, 19, 91):
        errors.append("G14 ownership partition must be 70 full + 2 complete + 19 supplements = 91")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G14 ownership partitions overlap")
    if scope["raw_language_count"] != 126 or scope["selected_scope_count"] != 91:
        errors.append("G14 Minecraft raw/selected counts must remain 126/91")

    expected_complete = {"en_us", "pl_pl"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "it_it", "ja_jp", "ko_kr", "lt_lt", "pt_br", "ru_ru", "sv_se",
        "tr_tr", "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G14 complete selected upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G14 incomplete selected upstream set changed: {sorted(incomplete)}")
    if set(scope["jei_upstream_unselected_or_nonmatching_locales"]) != {"en_au", "nb_no", "zh_tw"}:
        errors.append("G14 unselected JEI locale set changed")

    new_languages = {"ba_ru", "scn", "tl_ph", "yi_de"}
    if set(scope["new_selected_primary_languages"]) != new_languages or not new_languages <= full:
        errors.append("G14 new selected primary-language ownership changed")
    expected_deferred = {
        "regional_or_dialect_variants": ["es_ec", "esan"],
        "constructed_languages": ["isv"],
        "historical_or_nonprimary_languages": ["got_de"],
    }
    if scope["new_deferred_minecraft_codes"] != expected_deferred:
        errors.append("G14 new-language deferral policy changed")

    try:
        remote_english = g14.fetch_upstream_json(g14.G14_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G14 English source differs from pinned JEI 6.0.0")
        listing = fetch_json(CONTENTS_URL)
        live_locales = {
            Path(item["name"]).stem.lower()
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".json")
        }
        if len(live_locales) != 24:
            errors.append(f"expected 24 JEI 6.0.0 JSON locale files, got {len(live_locales)}")
        if full & live_locales:
            errors.append("G14 addon-full ownership overlaps live JEI upstream JSON locales")
        if not (complete | incomplete) <= live_locales:
            errors.append("G14 selected upstream ownership contains locale absent from pinned JEI")
        for locale in sorted(complete):
            upstream = g14.fetch_upstream_json(g14.G14_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G14 keys")
        for locale in sorted(incomplete):
            upstream = g14.fetch_upstream_json(g14.G14_COMMIT, locale)
            missing = normal - set(upstream)
            if not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
            if not g14.NEW_G14_KEYS <= missing:
                errors.append(f"{locale}: expected all three new G14 category keys to be missing upstream")
    except Exception as exc:
        errors.append(f"failed live G14 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "43b2f3021fe9f7d768378de95538e22da3ee8301":
        errors.append("G14 frozen Minecraft asset-index SHA changed")
    if set(asset["added_codes_since_1.13.2"]) != {"ba_ru", "es_ec", "esan", "got_de", "isv", "scn", "tl_ph", "yi_de"}:
        errors.append("G14 frozen added Minecraft language-code set changed")
    if asset["removed_codes_since_1.13.2"]:
        errors.append("G14 must not remove any Minecraft 1.13.2 language code")
    if policy["english_diff"]["reviewed_normal_added_or_changed_key_count"] != 3:
        errors.append("G14 policy reviewed-normal-key count changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.14.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.14.2 / JEI 6.0.0 G14 source, scope and ownership QA")
    print("English: 109 semantic keys / 106 normal / 3 debug; JSON")
    print("G13 -> G14: 106 unchanged, 3 added, 0 removed, 0 changed")
    print("Minecraft raw/selected: 126 / 91")
    print("New selected: ba_ru, scn, tl_ph, yi_de")
    print("Deferred: es_ec, esan, isv, got_de")
    print("Selected upstream: 21 (2 complete + 19 supplements)")
    print("Addon-owned full locales: 70")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

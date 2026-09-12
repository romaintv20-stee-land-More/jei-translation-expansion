#!/usr/bin/env python3
"""Validate G13 Minecraft 1.13.2 / JEI 5.0.0 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_13_2 as g13

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.13.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.13.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g13-mc1.13.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.13-to-1.13.2.json"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + g13.G13_COMMIT


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G13-QA"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    errors: list[str] = []
    base = g13.parse_json(g13.BASE_SOURCE)
    target = g13.parse_json(g13.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g13.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    changed_debug = {key for key in changed if key.startswith(g13.DEBUG_PREFIX)}
    reviewed_normal = added | (changed - changed_debug)

    if (len(target), len(normal)) != (106, 103):
        errors.append(f"G13 English counts changed: total={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed), len(changed_debug), len(reviewed_normal)) != (101, 1, 0, 4, 1, 4):
        errors.append(
            "G13 English diff changed: "
            f"unchanged={len(unchanged)} added={len(added)} removed={len(removed)} "
            f"changed={len(changed)} changed_debug={len(changed_debug)} reviewed_normal={len(reviewed_normal)}"
        )
    if set(diff["added_keys"]) != added or set(diff["removed_keys"]) != removed or set(diff["changed_english_values"]) != changed:
        errors.append("G13 diff manifest key sets differ from computed source diff")
    for key, pair in diff["changed_english_values"].items():
        if pair != [base[key], target[key]]:
            errors.append(f"G13 diff manifest old/new mismatch for {key}")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (66, 2, 19, 87):
        errors.append("G13 ownership partition must be 66 full + 2 complete + 19 supplements = 87")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G13 ownership partitions overlap")
    if scope["raw_language_count"] != 118 or scope["selected_scope_count"] != 87:
        errors.append("G13 Minecraft raw/selected counts must remain 118/87")

    expected_complete = {"en_us", "pl_pl"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "it_it", "ja_jp", "ko_kr", "lt_lt", "pt_br", "ru_ru", "sv_se",
        "tr_tr", "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G13 complete selected upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G13 incomplete selected upstream set changed: {sorted(incomplete)}")
    if set(scope["jei_upstream_unselected_or_nonmatching_locales"]) != {"en_au", "nb_no", "zh_tw"}:
        errors.append("G13 unselected JEI locale set changed")

    new_languages = {"bar", "kk_kz", "moh_ca", "tt_ru"}
    if set(scope["new_selected_primary_languages"]) != new_languages:
        errors.append("G13 new selected primary-language set changed")
    if not new_languages <= full:
        errors.append("G13 new selected languages are not all addon-full locales")
    if scope["new_deferred_minecraft_codes"] != {"regional_or_dialect_variants": ["fra_de"]}:
        errors.append("G13 fra_de deferral policy changed")

    try:
        remote_english = g13.fetch_upstream_json(g13.G13_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G13 English source differs from pinned JEI 5.0.0")
        listing = fetch_json(CONTENTS_URL)
        live_locales = {
            Path(item["name"]).stem.lower()
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".json")
        }
        if len(live_locales) != 24:
            errors.append(f"expected 24 JEI 5.0.0 JSON locale files, got {len(live_locales)}")
        if full & live_locales:
            errors.append("G13 addon-full ownership overlaps live JEI upstream JSON locales")
        if not (complete | incomplete) <= live_locales:
            errors.append("G13 selected upstream ownership contains locale absent from pinned JEI")
        for locale in sorted(complete):
            upstream = g13.fetch_upstream_json(g13.G13_COMMIT, locale)
            missing = normal - set(upstream)
            if missing:
                errors.append(f"{locale}: frozen complete upstream locale missing {len(missing)} normal keys")
        for locale in sorted(incomplete):
            upstream = g13.fetch_upstream_json(g13.G13_COMMIT, locale)
            missing = normal - set(upstream)
            if not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G13 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "a8ef90d58d4a170f85e3439470c99c25aa8e988b":
        errors.append("G13 frozen Minecraft asset-index SHA changed")
    if set(asset["added_codes_since_1_13"]) != {"bar", "fra_de", "kk_kz", "moh_ca", "tt_ru"}:
        errors.append("G13 frozen added Minecraft language-code set changed")
    if asset["removed_codes_since_1_13"]:
        errors.append("G13 must not remove any Minecraft 1.13 language code")
    if policy["english_diff"]["reviewed_normal_added_or_changed_key_count"] != 4:
        errors.append("G13 policy reviewed-normal-key count changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.13.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.13.2 / JEI 5.0.0 G13 source, scope and ownership QA")
    print("English: 106 semantic keys / 103 normal / 3 debug; JSON")
    print("G12 -> G13: 101 unchanged, 1 added, 0 removed, 4 changed")
    print("Reviewed normal added/changed meanings: 4")
    print("Minecraft raw/selected: 118 / 87")
    print("New selected: bar, kk_kz, moh_ca, tt_ru; fra_de deferred")
    print("Selected upstream: 21 (2 complete + 19 supplements)")
    print("Addon-owned full locales: 66")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

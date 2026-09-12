#!/usr/bin/env python3
"""Validate G16 Minecraft 1.14.4 / JEI 6.0.1 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_14_4 as g16

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.14.4-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.14.4-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g16-mc1.14.4" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.14.3-to-1.14.4.json"


def main() -> int:
    errors: list[str] = []
    base = g16.parse_json(g16.BASE_SOURCE)
    target = g16.parse_json(g16.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g16.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if target != base:
        errors.append("G16 stored English source differs from G15")
    if (len(target), len(normal)) != (109, 106):
        errors.append(f"G16 English counts changed: total={len(target)} normal={len(normal)}")
    if any((diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"])):
        errors.append("G16 frozen diff must have no added/removed/changed English meanings")
    if diff["unchanged_key_and_value_count"] != 109:
        errors.append("G16 frozen diff must contain 109 unchanged key/value pairs")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (70, 5, 16, 91):
        errors.append("G16 ownership partition must be 70 full + 5 complete + 16 supplements = 91")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G16 ownership partitions overlap")
    if scope["raw_language_count"] != 126 or scope["selected_scope_count"] != 91:
        errors.append("G16 Minecraft raw/selected counts must remain 126/91")

    expected_complete = {"de_de", "en_us", "pl_pl", "pt_br", "ru_ru"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
        "it_it", "ja_jp", "ko_kr", "lt_lt", "sv_se", "tr_tr", "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G16 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G16 incomplete upstream set changed: {sorted(incomplete)}")
    if {"de_de", "ru_ru"} & incomplete:
        errors.append("G16 must retire de_de and ru_ru supplement ownership")

    try:
        remote_english = g16.fetch_upstream_json(g16.G16_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G16 English source differs from pinned JEI 6.0.1")
        for locale in sorted(complete):
            upstream = g16.fetch_upstream_json(g16.G16_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G16 keys")
        for locale in sorted(incomplete):
            upstream = g16.fetch_upstream_json(g16.G16_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G16 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "43b2f3021fe9f7d768378de95538e22da3ee8301" or not asset["asset_index_identical_to_1.14.3"]:
        errors.append("G16 Minecraft asset index must be identical to G15")
    if asset["added_codes_since_1.14.3"] or asset["removed_codes_since_1.14.3"]:
        errors.append("G16 must not add or remove Minecraft language codes")
    if not policy["translation_reuse"]["all_semantics_reuse_g15"]:
        errors.append("G16 policy must enforce exact G15 semantic inheritance")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.14.4 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.14.4 / JEI 6.0.1 G16 source, scope and ownership QA")
    print("English: 109 semantic keys / 106 normal / 3 debug; all 109 unchanged from G15")
    print("Minecraft raw/selected: 126 / 91; exact 1.14 asset index reused")
    print("Selected upstream: 21 (5 complete + 16 supplements)")
    print("Ownership migration: de_de and ru_ru supplements retired; both now complete upstream")
    print("Addon-owned full locales: 70")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

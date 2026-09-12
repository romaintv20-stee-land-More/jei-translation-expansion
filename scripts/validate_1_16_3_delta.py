#!/usr/bin/env python3
"""Validate G21 Minecraft 1.16.3 / JEI 7.6.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_16_3 as g21

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.16.3-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.3-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g21-mc1.16.3" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.2-to-1.16.3.json"


def main() -> int:
    errors: list[str] = []
    base = g21.parse_json(g21.BASE_SOURCE)
    target = g21.parse_json(g21.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g21.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if (len(base), len(target), len(normal)) != (114, 114, 111):
        errors.append(f"G21 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if base != target:
        errors.append("G21 English source must exactly match G20")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (114, 0, 0, 0):
        errors.append("G21 frozen source diff counts changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (67, 3, 18, 88):
        errors.append("G21 ownership partition must be 67 full + 3 complete + 18 supplements = 88")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G21 ownership partitions overlap")
    if scope["raw_language_count"] != 125 or scope["selected_scope_count"] != 88:
        errors.append("G21 Minecraft raw/selected counts must remain 125/88")

    expected_complete = {"en_us", "pt_br", "sv_se"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "ru_ru", "tr_tr",
        "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G21 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G21 incomplete upstream set changed: {sorted(incomplete)}")

    try:
        remote_english = g21.fetch_upstream_json(g21.G21_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G21 English source differs from pinned JEI 7.6.0")
        for locale in sorted(complete):
            upstream = g21.fetch_upstream_json(g21.G21_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G21 keys")
        for locale in sorted(incomplete):
            upstream = g21.fetch_upstream_json(g21.G21_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G21 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2":
        errors.append("G21 Minecraft asset index SHA changed")
    if asset["added_codes_since_1.16.2"] or asset["removed_codes_since_1.16.2"]:
        errors.append("G21 Minecraft language inventory must be identical to G20")
    if scope["selected_scope_changed_from_1.16.2"]:
        errors.append("G21 selected scope must remain unchanged from G20")
    if not policy["translation_reuse"]["reuse_unchanged_g20_semantics"]:
        errors.append("G21 policy must enforce exact G20 reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.3 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.16.3 / JEI 7.6.0 G21 source, scope and ownership QA")
    print("English: 114 keys / 111 normal / 3 debug; all 114 unchanged from G20")
    print("Minecraft raw/selected: 125 / 88, unchanged from G20")
    print("Selected upstream: 21 (3 complete + 18 supplements)")
    print("Addon-owned full locales: 67")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

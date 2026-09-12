#!/usr/bin/env python3
"""Validate G19 Minecraft 1.16.1 / JEI 7.0.1 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_16_1 as g19

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.16.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g19-mc1.16.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.15.2-to-1.16.1.json"


def main() -> int:
    errors: list[str] = []
    base = g19.parse_json(g19.BASE_SOURCE)
    target = g19.parse_json(g19.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g19.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if (len(base), len(target), len(normal)) != (110, 110, 107):
        errors.append(f"G19 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if set(base) != set(target):
        errors.append("G19 must preserve the exact G18 key set")
    changed = {key for key in base if base[key] != target.get(key)}
    if changed != g19.CHANGED_KEYS:
        errors.append(f"G19 changed-key set differs from frozen policy: {sorted(changed)}")
    if target.get("jei.tooltip.liquid.amount") != "%s mB" or target.get("jei.tooltip.liquid.amount.with.capacity") != "%s / %s mB":
        errors.append("G19 liquid placeholder target values changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (108, 0, 0, 2):
        errors.append("G19 frozen source diff counts changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (67, 3, 18, 88):
        errors.append("G19 ownership partition must be 67 full + 3 complete + 18 supplements = 88")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G19 ownership partitions overlap")
    if scope["raw_language_count"] != 125 or scope["selected_scope_count"] != 88:
        errors.append("G19 Minecraft raw/selected counts must be 125/88")
    if g19.NEW_LOCALE not in full:
        errors.append("fur_it must be selected as a new G19 addon-full locale")
    if {"swg", "tok"} & selected:
        errors.append("swg and tok must remain outside selected G19 scope")

    expected_complete = {"en_us", "ja_jp", "pl_pl"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "it_it", "ko_kr", "lt_lt", "pt_br", "ru_ru", "sv_se", "tr_tr",
        "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G19 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G19 incomplete upstream set changed: {sorted(incomplete)}")

    try:
        remote_english = g19.fetch_upstream_json(g19.G19_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G19 English source differs from pinned JEI 7.0.1")
        for locale in sorted(complete):
            upstream = g19.fetch_upstream_json(g19.G19_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G19 keys")
        for locale in sorted(incomplete):
            upstream = g19.fetch_upstream_json(g19.G19_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G19 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2":
        errors.append("G19 Minecraft asset index SHA changed")
    if asset["added_codes_since_1.15.2"] != ["fur_it", "swg", "tok"] or asset["removed_codes_since_1.15.2"]:
        errors.append("G19 Minecraft language-code delta changed")
    if scope["new_selected_primary_languages"] != ["fur_it"]:
        errors.append("G19 must select only fur_it from newly added Minecraft codes")
    if not policy["translation_reuse"]["reuse_unchanged_g18_semantics"]:
        errors.append("G19 policy must enforce exact G18 reuse for unchanged meanings")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.16.1 / JEI 7.0.1 G19 source, scope and ownership QA")
    print("English: 110 keys / 107 normal / 3 debug; 108 unchanged + 2 changed liquid placeholders")
    print("Minecraft raw/selected: 125 / 88; new codes fur_it, swg, tok; only fur_it selected")
    print("Selected upstream: 21 (3 complete + 18 supplements)")
    print("Addon-owned full locales: 67")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

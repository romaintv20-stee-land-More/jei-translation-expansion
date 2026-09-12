#!/usr/bin/env python3
"""Validate G18 Minecraft 1.15.2 / JEI 6.0.2 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_15_2 as g18

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.15.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.15.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g18-mc1.15.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.15.1-to-1.15.2.json"


def main() -> int:
    errors: list[str] = []
    base = g18.parse_json(g18.BASE_SOURCE)
    target = g18.parse_json(g18.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g18.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if (len(base), len(target), len(normal)) != (109, 110, 107):
        errors.append(f"G18 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if set(target) - set(base) != {g18.NEW_KEY} or target[g18.NEW_KEY] != "Stonecutting":
        errors.append("G18 must add exactly gui.jei.category.stoneCutter=Stonecutting")
    if set(base) - set(target):
        errors.append(f"G18 unexpectedly removed keys: {sorted(set(base)-set(target))}")
    changed = [key for key in base if target.get(key) != base[key]]
    if changed:
        errors.append(f"G18 changed inherited English values: {changed}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (109, 1, 0, 0):
        errors.append("G18 frozen source diff counts changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (66, 3, 18, 87):
        errors.append("G18 ownership partition must be 66 full + 3 complete + 18 supplements = 87")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G18 ownership partitions overlap")
    if scope["raw_language_count"] != 122 or scope["selected_scope_count"] != 87:
        errors.append("G18 Minecraft raw/selected counts must remain 122/87")

    expected_complete = {"en_us", "ja_jp", "pl_pl"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "it_it", "ko_kr", "lt_lt", "pt_br", "ru_ru", "sv_se", "tr_tr",
        "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G18 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G18 incomplete upstream set changed: {sorted(incomplete)}")

    try:
        remote_english = g18.fetch_upstream_json(g18.G18_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G18 English source differs from pinned JEI 6.0.2")
        for locale in sorted(complete):
            upstream = g18.fetch_upstream_json(g18.G18_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G18 keys")
        for locale in sorted(incomplete):
            upstream = g18.fetch_upstream_json(g18.G18_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G18 pinned-upstream ownership verification: {exc}")

    for locale in ("de_de", "pt_br", "ru_ru"):
        upstream = g18.fetch_upstream_json(g18.G18_COMMIT, locale)
        if normal - set(upstream) != {g18.NEW_KEY}:
            errors.append(f"{locale}: expected only Stonecutting to be missing, got {sorted(normal-set(upstream))}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "58c12b1e2878e0a78719778acb803746450b3f1c" or not asset["asset_index_identical_to_1.15.1"]:
        errors.append("G18 Minecraft asset index must be identical to G17")
    if asset["added_codes_since_1.15.1"] or asset["removed_codes_since_1.15.1"]:
        errors.append("G18 must not add or remove Minecraft language codes")
    if not policy["translation_reuse"]["reuse_unchanged_g17_semantics"]:
        errors.append("G18 policy must enforce exact G17 reuse for unchanged meanings")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.15.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.15.2 / JEI 6.0.2 G18 source, scope and ownership QA")
    print("English: 110 keys / 107 normal / 3 debug; 109 unchanged + Stonecutting")
    print("Minecraft raw/selected: 122 / 87; exact 1.15 asset index reused")
    print("Selected upstream: 21 (3 complete + 18 supplements)")
    print("Ownership: ja_jp complete; de_de, pt_br and ru_ru each miss only Stonecutting")
    print("Addon-owned full locales: 66")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

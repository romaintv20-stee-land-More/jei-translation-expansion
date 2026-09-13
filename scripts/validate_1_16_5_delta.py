#!/usr/bin/env python3
"""Validate G23 Minecraft 1.16.5 / JEI 7.7.1 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_16_5 as g23

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.16.5-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.5-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g23-mc1.16.5" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.4-to-1.16.5.json"


def main() -> int:
    errors: list[str] = []
    base = g23.parse_json(g23.BASE_SOURCE)
    target = g23.parse_json(g23.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g23.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if (len(base), len(target), len(normal)) != (114, 119, 113):
        errors.append(f"G23 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    expected_added = {
        "description.jei.debug.formatting.1",
        "description.jei.debug.formatting.2",
        "description.jei.debug.formatting.3",
        "jei.message.ftblibrary",
        "key.jei.nextCategory",
        "key.jei.previousCategory",
    }
    if set(diff["added_keys"]) != expected_added:
        errors.append(f"G23 added-key set changed: {sorted(diff['added_keys'])}")
    if diff["removed_keys"] != ["jei.message.ftbguilib"]:
        errors.append(f"G23 removed-key set changed: {diff['removed_keys']}")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (113, 6, 1, 0):
        errors.append("G23 frozen source diff counts changed")
    if "jei.message.ftbguilib" in target or "jei.message.ftblibrary" not in target:
        errors.append("G23 FTB library key replacement is not frozen correctly")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (66, 7, 15, 88):
        errors.append("G23 ownership partition must be 66 full + 7 complete + 15 supplements = 88")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G23 ownership partitions overlap")
    if scope["raw_language_count"] != 125 or scope["selected_scope_count"] != 88:
        errors.append("G23 Minecraft raw/selected counts must remain 125/88")

    expected_complete = {"en_us", "it_it", "ko_kr", "ru_ru", "sv_se", "tr_tr", "zh_cn"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "id_id", "ja_jp", "lt_lt", "pl_pl", "pt_br", "uk_ua",
    }
    if complete != expected_complete:
        errors.append(f"G23 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G23 incomplete upstream set changed: {sorted(incomplete)}")
    if "id_id" in full or "id_id" not in incomplete:
        errors.append("G23 id_id must move from addon-full to upstream-incomplete")

    try:
        remote_english = g23.fetch_upstream_json(g23.G23_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G23 English source differs from pinned JEI 7.7.1")
        for locale in sorted(complete):
            upstream = g23.fetch_upstream_json(g23.G23_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G23 keys")
        for locale in sorted(incomplete):
            upstream = g23.fetch_upstream_json(g23.G23_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is actually complete upstream")
    except Exception as exc:
        errors.append(f"failed live G23 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2":
        errors.append("G23 Minecraft asset index SHA changed")
    if asset["added_codes_since_1.16.4"] or asset["removed_codes_since_1.16.4"]:
        errors.append("G23 Minecraft language inventory must be identical to G22")
    if scope["selected_scope_changed_from_1.16.4"]:
        errors.append("G23 selected scope must remain unchanged from G22")
    if audit["jei_upstream_locale_count"] != 25:
        errors.append("G23 pinned JEI upstream locale count must be 25")
    if not policy["translation_reuse"]["reuse_unchanged_g22_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G23 translation reuse policy changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.5 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.16.5 / JEI 7.7.1 G23 source, scope and ownership QA")
    print("English: 119 keys / 113 normal / 6 debug; 113 unchanged, 6 added, 1 removed")
    print("Minecraft raw/selected: 125 / 88, unchanged from G22")
    print("JEI upstream locales: 25; selected upstream: 22 (7 complete + 15 supplements)")
    print("Addon-owned full locales: 66")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

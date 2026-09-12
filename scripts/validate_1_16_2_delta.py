#!/usr/bin/env python3
"""Validate G20 Minecraft 1.16.2 / JEI 7.3.2 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_16_2 as g20

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.16.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g20-mc1.16.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.1-to-1.16.2.json"


def main() -> int:
    errors: list[str] = []
    base = g20.parse_json(g20.BASE_SOURCE)
    target = g20.parse_json(g20.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g20.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    if (len(base), len(target), len(normal)) != (110, 114, 111):
        errors.append(f"G20 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {k for k in set(base) & set(target) if base[k] != target[k]}
    if added != g20.ADDED_KEYS or removed or changed:
        errors.append(f"G20 English delta differs from frozen policy: added={sorted(added)} removed={sorted(removed)} changed={sorted(changed)}")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (110, 4, 0, 0):
        errors.append("G20 frozen source diff counts changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (67, 2, 19, 88):
        errors.append("G20 ownership partition must be 67 full + 2 complete + 19 supplements = 88")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G20 ownership partitions overlap")
    if scope["raw_language_count"] != 125 or scope["selected_scope_count"] != 88:
        errors.append("G20 Minecraft raw/selected counts must remain 125/88")

    expected_complete = {"en_us", "pt_br"}
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "ru_ru", "sv_se",
        "tr_tr", "uk_ua", "zh_cn",
    }
    if complete != expected_complete:
        errors.append(f"G20 complete upstream set changed: {sorted(complete)}")
    if incomplete != expected_incomplete:
        errors.append(f"G20 incomplete upstream set changed: {sorted(incomplete)}")

    try:
        remote_english = g20.fetch_upstream_json(g20.G20_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G20 English source differs from pinned JEI 7.3.2")
        for locale in sorted(complete):
            upstream = g20.fetch_upstream_json(g20.G20_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G20 keys")
        for locale in sorted(incomplete):
            upstream = g20.fetch_upstream_json(g20.G20_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G20 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2":
        errors.append("G20 Minecraft asset index SHA changed")
    if asset["added_codes_since_1.16.1"] or asset["removed_codes_since_1.16.1"]:
        errors.append("G20 Minecraft language code inventory must be identical to G19")
    if scope["selected_scope_changed_from_1.16.1"]:
        errors.append("G20 selected scope must remain unchanged from G19")
    if not policy["translation_reuse"]["reuse_unchanged_g19_semantics"]:
        errors.append("G20 policy must enforce exact G19 reuse for unchanged meanings")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.16.2 / JEI 7.3.2 G20 source, scope and ownership QA")
    print("English: 114 keys / 111 normal / 3 debug; 110 unchanged + 4 added")
    print("Minecraft raw/selected: 125 / 88, unchanged from G19")
    print("Selected upstream: 21 (2 complete + 19 supplements)")
    print("Addon-owned full locales: 67")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

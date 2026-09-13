#!/usr/bin/env python3
"""Validate G25 Minecraft 1.18 / JEI 9.0.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_18 as g25

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.18-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.18-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g25-mc1.18" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.17.1-to-1.18.json"


def main() -> int:
    errors: list[str] = []
    base = g25.parse_json(g25.BASE_SOURCE)
    target = g25.parse_json(g25.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g25.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])

    if (len(base), len(target), len(normal)) != (141, 141, 135):
        errors.append(f"G25 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if base != target or (len(unchanged), len(added), len(removed), len(changed)) != (141, 0, 0, 0):
        errors.append("G25 English source must remain exactly identical to G24")
    if added != diff["added_keys"] or removed != diff["removed_keys"] or changed != sorted(diff["changed_english_values"]):
        errors.append("G25 frozen key delta differs from stored pinned sources")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 1, 21, 86):
        errors.append("G25 ownership partition must be 64 full + 1 complete + 21 supplements = 86")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G25 ownership partitions overlap")
    if complete != {"en_us"}:
        errors.append(f"G25 complete upstream set changed: {sorted(complete)}")
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br",
        "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn",
    }
    if incomplete != expected_incomplete:
        errors.append(f"G25 incomplete upstream set changed: {sorted(incomplete)}")
    if scope["raw_language_count"] != 124 or scope["selected_scope_count"] != 86:
        errors.append("G25 Minecraft raw/selected counts must be 124/86")
    if scope["removed_selected_languages"]:
        errors.append("G25 must not remove any selected G24 locale")
    if set(scope["deferred_new_languages"]) != {"ry_ua"}:
        errors.append("G25 must defer exactly new asset-only ry_ua")

    try:
        remote_english = g25.fetch_upstream_json(g25.G25_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G25 English source differs from pinned JEI 9.0.0")
        for locale in sorted(complete | incomplete):
            upstream = g25.fetch_upstream_json(g25.G25_COMMIT, locale)
            g24_upstream = g25.g24.fetch_upstream_json(g25.g24.G24_COMMIT, locale)
            if upstream != g24_upstream:
                errors.append(f"{locale}: G25 upstream locale differs from G24")
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G25 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G25 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "d31a2e85ae149dd1b1a7070b22cb8887892fda6c":
        errors.append("G25 Minecraft asset index SHA changed")
    if set(asset["added_codes_since_1.17.1"]) != {"ry_ua"} or asset["removed_codes_since_1.17.1"]:
        errors.append("G25 Minecraft asset-code delta must be +ry_ua and no removals")
    registry = audit["client_language_registry_investigation"]
    if registry["ry_ua_explicitly_registered_in_client_jar"]:
        errors.append("G25 frozen scope assumes ry_ua is not explicitly registered in the 1.18 client JAR")
    if not policy["translation_reuse"]["reuse_unchanged_g24_semantics"]:
        errors.append("G25 policy must enforce exact G24 reuse for all meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G25 policy must forbid cross-key translation reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.18 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.18 / JEI 9.0.0 G25 source, scope and ownership QA")
    print("English: 141 keys / 135 normal / 6 debug; all 141 unchanged from G24")
    print("Minecraft raw/selected: 124 / 86; ry_ua deferred as asset-only at this point")
    print("Selected upstream: 22 (1 complete + 21 supplements)")
    print("Addon-owned full locales: 64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

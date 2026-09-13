#!/usr/bin/env python3
"""Validate G26 Minecraft 1.18.1 / JEI 9.4.1 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_18_1 as g26

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.18.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.18.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g26-mc1.18.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.18-to-1.18.1.json"


def main() -> int:
    errors: list[str] = []
    base = g26.parse_json(g26.BASE_SOURCE)
    target = g26.parse_json(g26.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g26.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g26.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (141, 149, 143):
        errors.append(f"G26 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (124, 11, 3, 14):
        errors.append("G26 English semantic delta must remain 124 unchanged + 11 added + 3 removed + 14 changed")
    if sorted(added) != diff["added_keys"] or sorted(removed) != diff["removed_keys"] or sorted(changed) != sorted(diff["changed_english_values"]):
        errors.append("G26 frozen key delta differs from stored pinned sources")
    for key in changed:
        entry = diff["changed_english_values"].get(key, {})
        if entry.get("from") != base[key] or entry.get("to") != target[key]:
            errors.append(f"{key}: frozen changed-English values do not match pinned sources")
    if diff["reviewed_normal_added_or_changed_key_count"] != 25 or diff["changed_debug_only_key_count"] != 0:
        errors.append("G26 reviewed semantic counts must remain 25 normal and 0 debug-only changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 1, 21, 86):
        errors.append("G26 ownership partition must be 64 full + 1 complete + 21 supplements = 86")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G26 ownership partitions overlap")
    if complete != {"en_us"}:
        errors.append(f"G26 complete upstream set changed: {sorted(complete)}")
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br",
        "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn",
    }
    if incomplete != expected_incomplete:
        errors.append(f"G26 incomplete upstream set changed: {sorted(incomplete)}")
    if scope["raw_language_count"] != 124 or scope["selected_scope_count"] != 86:
        errors.append("G26 Minecraft raw/selected counts must be 124/86")
    if scope["removed_selected_languages"] or scope["new_minecraft_codes"]:
        errors.append("G26 Minecraft 1.18.1 must inherit the 1.18 language asset inventory unchanged")
    if set(scope["deferred_new_languages"]) != {"ry_ua"}:
        errors.append("G26 must keep deferred asset-only ry_ua")

    try:
        remote_english = g26.fetch_upstream_json(g26.G26_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G26 English source differs from pinned JEI 9.4.1")
        for locale in sorted(complete | incomplete):
            upstream = g26.fetch_upstream_json(g26.G26_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G26 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G26 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "d31a2e85ae149dd1b1a7070b22cb8887892fda6c" or asset["id"] != "1.18":
        errors.append("G26 Minecraft asset index must remain the exact 1.18 index")
    if asset["added_codes_since_1.18"] or asset["removed_codes_since_1.18"]:
        errors.append("G26 Minecraft asset-code delta from 1.18 must remain empty")
    registry = audit["client_language_registry_investigation"]
    if registry["ry_ua_explicitly_registered_in_client_jar"]:
        errors.append("G26 frozen scope assumes ry_ua is not explicitly registered in the 1.18.1 client JAR")
    if not policy["translation_reuse"]["reuse_unchanged_g25_semantics"]:
        errors.append("G26 policy must enforce exact G25 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G26 policy must forbid cross-key translation reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.18.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.18.1 / JEI 9.4.1 G26 source, scope and ownership QA")
    print("English: 149 keys / 143 normal / 6 debug")
    print("Delta: 124 unchanged + 11 added + 3 removed + 14 changed")
    print("Minecraft raw/selected: 124 / 86; ry_ua remains deferred")
    print("Selected upstream: 22 (1 complete + 21 supplements)")
    print("Addon-owned full locales: 64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

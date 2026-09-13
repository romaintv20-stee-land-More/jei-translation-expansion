#!/usr/bin/env python3
"""Validate G27 Minecraft 1.18.2 / JEI 10.1.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_18_2 as g27

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.18.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.18.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g27-mc1.18.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.18.1-to-1.18.2.json"


def main() -> int:
    errors: list[str] = []
    base = g27.parse_json(g27.BASE_SOURCE)
    target = g27.parse_json(g27.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g27.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g27.semantic_sets(base, target)
    expected_added = {
        "jei.key.combo.alt", "jei.key.combo.command", "jei.key.combo.control",
        "jei.key.combo.shift", "key.jei.closeRecipeGui",
    }
    if (len(base), len(target), len(normal)) != (149, 154, 148):
        errors.append(f"G27 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (149, 5, 0, 0):
        errors.append("G27 English semantic delta must remain 149 unchanged + 5 added + 0 removed + 0 changed")
    if added != expected_added:
        errors.append(f"G27 added-key set changed: {sorted(added)}")
    if sorted(added) != diff["added_keys"] or sorted(removed) != diff["removed_keys"] or sorted(changed) != sorted(diff["changed_english_values"]):
        errors.append("G27 frozen key delta differs from stored pinned sources")
    if diff["reviewed_normal_added_or_changed_key_count"] != 5 or diff["changed_debug_only_key_count"] != 0:
        errors.append("G27 reviewed semantic counts must remain 5 normal and 0 debug-only changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 1, 21, 86):
        errors.append("G27 ownership partition must be 64 full + 1 complete + 21 supplements = 86")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G27 ownership partitions overlap")
    if complete != {"en_us"}:
        errors.append(f"G27 complete upstream set changed: {sorted(complete)}")
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br",
        "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn",
    }
    if incomplete != expected_incomplete:
        errors.append(f"G27 incomplete upstream set changed: {sorted(incomplete)}")
    if scope["raw_language_count"] != 124 or scope["selected_scope_count"] != 86:
        errors.append("G27 Minecraft raw/selected counts must be 124/86")
    if scope["removed_selected_languages"] or scope["new_minecraft_codes"]:
        errors.append("G27 Minecraft 1.18.2 must inherit the 1.18.1 language asset inventory unchanged")
    if set(scope["deferred_new_languages"]) != {"ry_ua"}:
        errors.append("G27 must keep deferred asset-only ry_ua")

    try:
        remote_english = g27.fetch_upstream_json(g27.G27_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G27 English source differs from pinned JEI 10.1.0")
        for locale in sorted(complete | incomplete):
            upstream = g27.fetch_upstream_json(g27.G27_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G27 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G27 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "d31a2e85ae149dd1b1a7070b22cb8887892fda6c" or asset["id"] != "1.18":
        errors.append("G27 Minecraft asset index must remain the exact 1.18 index")
    if asset["added_codes_since_1.18.1"] or asset["removed_codes_since_1.18.1"]:
        errors.append("G27 Minecraft asset-code delta from 1.18.1 must remain empty")
    registry = audit["client_language_registry_investigation"]
    if registry["ry_ua_explicitly_registered_in_client_jar"]:
        errors.append("G27 frozen scope assumes ry_ua is not explicitly registered in the 1.18.2 client JAR")
    if audit["build_metadata"]["mappings_channel"] != "parchment" or audit["build_metadata"]["mappings_version"] != "2022.03.13-1.18.2":
        errors.append("G27 frozen build metadata must use Parchment 2022.03.13-1.18.2")
    if not policy["translation_reuse"]["reuse_unchanged_g26_semantics"]:
        errors.append("G27 policy must enforce exact G26 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G27 policy must forbid cross-key translation reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.18.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.18.2 / JEI 10.1.0 G27 source, scope and ownership QA")
    print("English: 154 keys / 148 normal / 6 debug")
    print("Delta: 149 unchanged + 5 added + 0 removed + 0 changed")
    print("Minecraft raw/selected: 124 / 86; ry_ua remains deferred")
    print("Selected upstream: 22 (1 complete + 21 supplements)")
    print("Addon-owned full locales: 64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

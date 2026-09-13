#!/usr/bin/env python3
"""Validate G28 Minecraft 1.19 / JEI 11.1.1 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_19 as g28

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.19-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g28-mc1.19" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.18.2-to-1.19.json"


def main() -> int:
    errors: list[str] = []
    base = g28.parse_json(g28.BASE_SOURCE)
    target = g28.parse_json(g28.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g28.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g28.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (154, 154, 148):
        errors.append(f"G28 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (154, 0, 0, 0):
        errors.append("G28 English semantic delta must remain 154 unchanged + 0 added + 0 removed + 0 changed")
    if diff["unchanged_key_and_value_count"] != 154 or diff["added_keys"] or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G28 frozen English diff differs from pinned sources")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 3, 19, 86):
        errors.append("G28 ownership partition must be 64 full + 3 complete + 19 supplements = 86")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G28 ownership partitions overlap")
    if complete != {"bg_bg", "en_us", "pl_pl"}:
        errors.append(f"G28 complete upstream set changed: {sorted(complete)}")
    expected_incomplete = {
        "ar_sa", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
        "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pt_br", "ru_ru", "sv_se",
        "tr_tr", "uk_ua", "zh_cn",
    }
    if incomplete != expected_incomplete:
        errors.append(f"G28 incomplete upstream set changed: {sorted(incomplete)}")
    if scope["raw_language_count"] != 124 or scope["selected_scope_count"] != 86:
        errors.append("G28 Minecraft raw/selected counts must be 124/86")
    if scope["removed_selected_languages"] or scope["new_minecraft_codes"]:
        errors.append("G28 Minecraft 1.19 must keep the same language-code inventory as G27")
    if set(scope["deferred_new_languages"]) != {"ry_ua"}:
        errors.append("G28 must keep deferred asset-only ry_ua")

    try:
        remote_english = g28.fetch_upstream_json(g28.G28_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G28 English source differs from pinned JEI 11.1.1")
        for locale in sorted(complete | incomplete):
            upstream = g28.fetch_upstream_json(g28.G28_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G28 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G28 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "a9c8b05a8082a65678beda6dfa2b8f21fa627bce" or asset["id"] != "1.19":
        errors.append("G28 Minecraft asset index no longer matches frozen 1.19 metadata")
    if asset["added_codes_since_1.18.2"] or asset["removed_codes_since_1.18.2"]:
        errors.append("G28 Minecraft asset-code delta from 1.18.2 must remain empty")
    if audit["client_language_registry_investigation"]["ry_ua_explicitly_registered_in_client_jar"]:
        errors.append("G28 frozen scope assumes ry_ua is not explicitly registered in the client JAR")
    if audit["build_metadata"]["mappings_channel"] != "parchment" or audit["build_metadata"]["mappings_version"] != "1.18.2-2022.07.10-1.19":
        errors.append("G28 frozen build metadata must use Parchment 1.18.2-2022.07.10-1.19")
    if not policy["translation_reuse"]["reuse_unchanged_g27_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G28 policy must enforce exact G27 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.19 / JEI 11.1.1 G28 source, scope and ownership QA")
    print("English: 154 keys / 148 normal / 6 debug; all 154 unchanged from G27")
    print("Minecraft raw/selected: 124 / 86; ry_ua remains deferred")
    print("Selected upstream: 22 (3 complete + 19 supplements)")
    print("Addon-owned full locales: 64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate G29 Minecraft 1.19.1 / JEI 11.2.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_19_1 as g29

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.19.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g29-mc1.19.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.19-to-1.19.1.json"


def main() -> int:
    errors: list[str] = []
    base = g29.parse_json(g29.BASE_SOURCE)
    target = g29.parse_json(g29.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g29.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g29.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (154, 153, 147):
        errors.append(f"G29 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 0, 1, 0):
        errors.append("G29 English semantic delta must remain 153 unchanged + 0 added + 1 removed + 0 changed")
    if removed != {g29.REMOVED_KEY}:
        errors.append(f"G29 removed-key set changed: {sorted(removed)}")
    if diff["removed_keys"] != [g29.REMOVED_KEY]:
        errors.append("G29 frozen diff no longer records the single removed key")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 3, 19, 86):
        errors.append("G29 ownership partition must be 64 full + 3 complete + 19 supplements = 86")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G29 ownership partitions overlap")
    if complete != {"bg_bg", "en_us", "pl_pl"}:
        errors.append(f"G29 complete upstream set changed: {sorted(complete)}")
    expected_incomplete = {
        "ar_sa", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
        "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pt_br", "ru_ru", "sv_se",
        "tr_tr", "uk_ua", "zh_cn",
    }
    if incomplete != expected_incomplete:
        errors.append(f"G29 incomplete upstream set changed: {sorted(incomplete)}")
    if scope["raw_language_count"] != 124 or scope["selected_scope_count"] != 86:
        errors.append("G29 Minecraft raw/selected counts must be 124/86")
    if scope["removed_selected_languages"] or scope["new_minecraft_codes"]:
        errors.append("G29 Minecraft 1.19.1 must keep the same language-code inventory as G28")
    if set(scope["deferred_new_languages"]) != {"ry_ua"}:
        errors.append("G29 must keep deferred asset-only ry_ua")

    try:
        remote_english = g29.fetch_upstream_json(g29.G29_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G29 English source differs from pinned JEI 11.2.0")
        for locale in sorted(complete | incomplete):
            upstream = g29.fetch_upstream_json(g29.G29_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G29 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G29 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "a9c8b05a8082a65678beda6dfa2b8f21fa627bce" or asset["id"] != "1.19":
        errors.append("G29 Minecraft asset index no longer matches frozen metadata")
    if asset["added_codes_since_1.19"] or asset["removed_codes_since_1.19"]:
        errors.append("G29 Minecraft asset-code delta from 1.19 must remain empty")
    if audit["client_language_registry_investigation"]["ry_ua_explicitly_registered_in_client_jar"]:
        errors.append("G29 frozen scope assumes ry_ua is not explicitly registered in the client JAR")
    build = audit["build_metadata"]
    if build["forge"] != "42.0.0" or build["mappings_version"] != "1.18.2-2022.07.10-1.19.1" or build["java_toolchain"] != "17":
        errors.append("G29 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g28_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G29 policy must enforce exact G28 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.19.1 / JEI 11.2.0 G29 source, scope and ownership QA")
    print("English: 153 keys / 147 normal / 6 debug; 153 unchanged + 1 removed from G28")
    print("Minecraft raw/selected: 124 / 86; ry_ua remains deferred")
    print("Selected upstream: 22 (3 complete + 19 supplements)")
    print("Addon-owned full locales: 64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

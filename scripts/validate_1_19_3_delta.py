#!/usr/bin/env python3
"""Validate G31 Minecraft 1.19.3 / JEI 12.3.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_19_3 as g31

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.19.3-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.3-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g31-mc1.19.3" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.19.2-to-1.19.3.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.2-language-scope.json"
EXPECTED_ADDED = {
    "config.jei.advanced.addBookmarksToFront",
    "config.jei.advanced.addBookmarksToFront.comment",
    "jei.message.config.folder",
}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru", "sv_se",
    "tr_tr", "uk_ua", "zh_cn",
}


def main() -> int:
    errors: list[str] = []
    base = g31.parse_json(g31.BASE_SOURCE)
    target = g31.parse_json(g31.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g31.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g31.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (153, 156, 150):
        errors.append(f"G31 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 3, 0, 0):
        errors.append("G31 English semantic delta must remain 153 unchanged + 3 added + 0 removed + 0 changed")
    if added != EXPECTED_ADDED:
        errors.append(f"G31 added-key set changed: {sorted(added)}")
    if set(diff["added_keys"]) != EXPECTED_ADDED or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G31 frozen diff no longer matches the reviewed three-key addition")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (66, 1, 21, 88):
        errors.append("G31 ownership partition must be 66 full + 1 complete + 21 supplements = 88")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G31 ownership partitions overlap")
    if complete != {"en_us"}:
        errors.append(f"G31 complete upstream set changed: {sorted(complete)}")
    if incomplete != EXPECTED_INCOMPLETE:
        errors.append(f"G31 incomplete upstream set changed: {sorted(incomplete)}")
    if set(scope["new_selected_primary_languages"]) != {"nah", "ry_ua"}:
        errors.append("G31 must add exactly Nahuatl and Rusyn to the selected primary-language scope")
    if not {"nah", "ry_ua"} <= full:
        errors.append("G31 Nahuatl and Rusyn must be addon-owned full locales")

    base_full = set(base_scope["addon_full_locales"])
    if full - {"nah", "ry_ua"} != base_full:
        errors.append("G31 inherited addon-full set differs from G30")
    if set(scope["ownership_changes_from_g30"]["complete_to_incomplete"]) != {"bg_bg", "pl_pl"}:
        errors.append("G31 must move bg_bg and pl_pl from complete upstream to supplements")
    if scope["selected_scope_count"] != 88 or scope["raw_language_count"] != 143:
        errors.append("G31 frozen scope counts must be live-raw 143 / selected 88")
    if len(scope["documented_full_english_fallback_locales"]) != 29:
        errors.append("G31 must document 29 complete-English fallback locales")
    if scope["translated_or_ai_assisted_full_locale_count"] != 37:
        errors.append("G31 translated/AI-assisted full locale count must remain 37")

    try:
        remote_english = g31.fetch_upstream_json(g31.G31_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G31 English source differs from pinned JEI 12.3.0")
        for locale in sorted(complete | incomplete):
            upstream = g31.fetch_upstream_json(g31.G31_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G31 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G31 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "909daaf41d8477693cd3c871c823f68455e064ab" or asset["id"] != "2":
        errors.append("G31 frozen Minecraft asset metadata changed")
    if set(audit["historical_language_scope"]["new_selected_primary_languages"]) != {"nah", "ry_ua"}:
        errors.append("G31 frozen historical language additions changed")
    if len(audit["historical_language_scope"]["later_live_asset_codes_not_attributed_to_g31"]) != 18:
        errors.append("G31 decoupled post-release asset exclusion count must remain 18")
    build = audit["build_metadata"]
    if build["forge"] != "44.1.5" or build["mappings_version"] != "1.18.2-2022.07.10-1.19.3" or build["java_toolchain"] != "17":
        errors.append("G31 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g30_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G31 policy must enforce exact G30 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.3 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.19.3 / JEI 12.3.0 G31 source, scope and ownership QA")
    print("English: 156 keys / 150 normal / 6 debug; 153 unchanged + 3 added")
    print("Historical selected scope: 88; new languages: nah, ry_ua")
    print("Selected upstream: 22 (1 complete + 21 supplements)")
    print("Addon-owned full locales: 66")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

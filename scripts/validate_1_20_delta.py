#!/usr/bin/env python3
"""Validate G33 Minecraft 1.20 / JEI 14.0.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_20 as g33

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.20-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g33-mc1.20" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.19.4-to-1.20.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.4-language-scope.json"
EXPECTED_COMPLETE = {"en_us", "uk_ua"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru", "sv_se",
    "tr_tr", "zh_cn",
}
EXPECTED_NEW = {"lo_la", "sah_sah"}


def main() -> int:
    errors: list[str] = []
    base = g33.parse_json(g33.BASE_SOURCE)
    target = g33.parse_json(g33.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g33.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g33.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (156, 156, 150):
        errors.append(f"G33 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("G33 English semantic delta must remain 156 unchanged + 0 added + 0 removed + 0 changed")
    if diff["added_keys"] or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G33 frozen diff must contain no semantic changes")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (68, 2, 20, 90):
        errors.append("G33 ownership partition must be 68 full + 2 complete + 20 supplements = 90")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G33 ownership partitions overlap")
    if complete != EXPECTED_COMPLETE:
        errors.append(f"G33 complete upstream set changed: {sorted(complete)}")
    if incomplete != EXPECTED_INCOMPLETE:
        errors.append(f"G33 incomplete upstream set changed: {sorted(incomplete)}")

    base_full = set(base_scope["addon_full_locales"])
    base_selected = (
        base_full
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if full - EXPECTED_NEW != base_full:
        errors.append("G33 inherited addon-full ownership must be exactly G32 plus Lao/Yakut")
    if selected != base_selected | EXPECTED_NEW:
        errors.append("G33 selected language membership must be G32 plus Lao/Yakut")
    if set(scope["new_selected_primary_languages"]) != EXPECTED_NEW or scope["removed_selected_languages"]:
        errors.append("G33 must add exactly lo_la and sah_sah and remove no selected language")
    if set(scope["ownership_changes_from_g32"]["new_addon_full_locales"]) != EXPECTED_NEW:
        errors.append("G33 must record Lao/Yakut as new addon-full locales")
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 31 or not EXPECTED_NEW <= fallback:
        errors.append("G33 must have 31 documented complete-English fallbacks including Lao/Yakut")
    if scope["translated_or_ai_assisted_full_locale_count"] != 37:
        errors.append("G33 translated/AI-assisted full locale count must remain 37")

    try:
        remote_english = g33.fetch_upstream_json(g33.G33_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G33 English source differs from pinned JEI 14.0.0")
        for locale in sorted(complete | incomplete):
            upstream = g33.fetch_upstream_json(g33.G33_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G33 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G33 pinned-upstream ownership verification: {exc}")

    build = audit["build_metadata"]
    if build["forge"] != "46.0.1" or build["mappings_version"] != "1.19.3-2023.03.12-1.19.4" or build["java_toolchain"] != "17":
        errors.append("G33 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g32_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G33 policy must enforce exact G32 reuse and forbid cross-key reuse")
    if set(policy["fallback_policy"]["new_fallback_locales"]) != EXPECTED_NEW:
        errors.append("G33 fallback policy must explicitly name Lao/Yakut")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.20 / JEI 14.0.0 G33 source, scope and ownership QA")
    print("English: 156 keys / 150 normal / 6 debug; all 156 semantics unchanged")
    print("Selected language scope: 90 (G32 + Lao + Yakut)")
    print("Selected upstream: 22 (2 complete + 20 supplements)")
    print("Addon-owned full locales: 68")
    print("lo_la and sah_sah use documented complete-English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

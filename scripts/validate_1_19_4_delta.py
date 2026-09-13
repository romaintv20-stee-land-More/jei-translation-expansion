#!/usr/bin/env python3
"""Validate G32 Minecraft 1.19.4 / JEI 13.1.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_19_4 as g32

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.19.4-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.4-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g32-mc1.19.4" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.19.3-to-1.19.4.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.3-language-scope.json"
EXPECTED_COMPLETE = {"en_us", "uk_ua"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru", "sv_se",
    "tr_tr", "zh_cn",
}


def main() -> int:
    errors: list[str] = []
    base = g32.parse_json(g32.BASE_SOURCE)
    target = g32.parse_json(g32.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g32.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g32.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (156, 156, 150):
        errors.append(f"G32 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("G32 English semantic delta must remain 156 unchanged + 0 added + 0 removed + 0 changed")
    if diff["added_keys"] or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G32 frozen diff must contain no semantic changes")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (66, 2, 20, 88):
        errors.append("G32 ownership partition must be 66 full + 2 complete + 20 supplements = 88")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G32 ownership partitions overlap")
    if complete != EXPECTED_COMPLETE:
        errors.append(f"G32 complete upstream set changed: {sorted(complete)}")
    if incomplete != EXPECTED_INCOMPLETE:
        errors.append(f"G32 incomplete upstream set changed: {sorted(incomplete)}")

    base_full = set(base_scope["addon_full_locales"])
    base_selected = (
        base_full
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if full != base_full:
        errors.append("G32 addon-full ownership must be identical to G31")
    if selected != base_selected:
        errors.append("G32 selected language membership must be identical to G31")
    if scope["new_selected_primary_languages"] or scope["removed_selected_languages"]:
        errors.append("G32 must not add or remove selected primary languages")
    if set(scope["ownership_changes_from_g31"]["newly_complete_upstream"]) != {"uk_ua"}:
        errors.append("G32 must record uk_ua as newly complete upstream")
    if len(scope["documented_full_english_fallback_locales"]) != 29:
        errors.append("G32 must retain 29 documented complete-English fallback locales")
    if scope["translated_or_ai_assisted_full_locale_count"] != 37:
        errors.append("G32 translated/AI-assisted full locale count must remain 37")

    try:
        remote_english = g32.fetch_upstream_json(g32.G32_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G32 English source differs from pinned JEI 13.1.0")
        for locale in sorted(complete | incomplete):
            upstream = g32.fetch_upstream_json(g32.G32_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G32 keys")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G32 pinned-upstream ownership verification: {exc}")

    build = audit["build_metadata"]
    if build["forge"] != "45.0.40" or build["mappings_version"] != "1.19.3-2023.03.12-1.19.4" or build["java_toolchain"] != "17":
        errors.append("G32 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g31_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G32 policy must enforce exact G31 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.4 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.19.4 / JEI 13.1.0 G32 source, scope and ownership QA")
    print("English: 156 keys / 150 normal / 6 debug; all 156 semantics unchanged")
    print("Selected language scope: 88, unchanged from G31")
    print("Selected upstream: 22 (2 complete + 20 supplements)")
    print("Addon-owned full locales: 66")
    print("uk_ua promoted from supplement to complete upstream ownership")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

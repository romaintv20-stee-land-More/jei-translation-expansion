#!/usr/bin/env python3
"""Validate G34 Minecraft 1.20.1 / JEI 15.2.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_20_1 as g34

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.20.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g34-mc1.20.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20-to-1.20.1.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20-language-scope.json"
EXPECTED_COMPLETE = {"en_us", "uk_ua"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru", "sv_se",
    "tr_tr", "zh_cn",
}


def main() -> int:
    errors: list[str] = []
    base = g34.parse_json(g34.BASE_SOURCE)
    target = g34.parse_json(g34.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g34.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g34.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (156, 156, 150):
        errors.append("G34 English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("G34 English semantic delta must remain 156 unchanged + 0 added + 0 removed + 0 changed")
    if diff["added_keys"] or diff["removed_keys"] or diff["changed_english_values"]:
        errors.append("G34 frozen diff must contain no semantic changes")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (68, 2, 20, 90):
        errors.append("G34 ownership partition must be 68 full + 2 complete + 20 supplements = 90")
    if complete != EXPECTED_COMPLETE or incomplete != EXPECTED_INCOMPLETE:
        errors.append("G34 upstream ownership differs from frozen audit")

    base_selected = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if selected != base_selected:
        errors.append("G34 selected language scope must match G33 exactly")
    if full != set(base_scope["addon_full_locales"]):
        errors.append("G34 addon-full ownership must match G33 exactly")
    if scope["new_selected_primary_languages"] or scope["removed_selected_languages"]:
        errors.append("G34 must not add or remove selected languages")
    if len(scope["documented_full_english_fallback_locales"]) != 31:
        errors.append("G34 documented complete-English fallback count must remain 31")

    try:
        remote_english = g34.fetch_upstream_json(g34.G34_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G34 English source differs from pinned JEI 15.2.0")
        for locale in sorted(complete | incomplete):
            upstream = g34.fetch_upstream_json(g34.G34_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: expected complete upstream")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: expected incomplete upstream")
    except Exception as exc:
        errors.append(f"failed pinned-upstream verification: {exc}")

    build = audit["build_metadata"]
    if build["forge"] != "47.0.1" or build["mappings_version"] != "1.19.3-2023.03.12-1.20.1" or build["java_toolchain"] != "17":
        errors.append("G34 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g33_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G34 policy must enforce exact G33 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.20.1 / JEI 15.2.0 G34 source, scope and ownership QA")
    print("English: 156 keys / 150 normal / 6 debug; all 156 semantics unchanged")
    print("Selected language scope: 90, unchanged from G33")
    print("Ownership: 68 addon-full + 20 supplements + 2 complete upstream")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

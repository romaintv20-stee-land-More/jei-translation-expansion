#!/usr/bin/env python3
"""Validate G38 Minecraft 1.21 / JEI 19.8.2 source, scope, ownership and reviewed semantic delta."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21 as g38
import validate_1_14_2_complete as baseqa

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g38-mc1.21" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20.6-to-1.21.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.6-language-scope.json"
EXPECTED_COMPLETE = {"en_us", "ja_jp"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru", "sv_se",
    "tr_tr", "uk_ua", "zh_cn",
}


def main() -> int:
    errors: list[str] = []
    base = g38.parse_json(g38.BASE_SOURCE)
    target = g38.parse_json(g38.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g38.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g38.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (157, 176, 170):
        errors.append("G38 English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 19, 0, 1):
        errors.append("G38 semantic partition must remain 156 unchanged + 19 added + 0 removed + 1 changed")
    if set(diff["added_keys"]) != added or set(diff["changed_english_values"]) != changed or diff["removed_keys"]:
        errors.append("G38 frozen English diff does not match pinned source")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (67, 2, 21, 90):
        errors.append("G38 ownership partition must be 67 full + 2 complete + 21 supplements = 90")
    if complete != EXPECTED_COMPLETE or incomplete != EXPECTED_INCOMPLETE:
        errors.append("G38 upstream ownership differs from frozen exploratory audit")

    base_selected = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if selected != base_selected:
        errors.append("G38 selected language scope must match G37 exactly")
    if full != set(base_scope["addon_full_locales"]):
        errors.append("G38 addon-full ownership must match G37 exactly")
    if scope["new_selected_primary_languages"] or scope["removed_selected_languages"]:
        errors.append("G38 must not add or remove selected languages")
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 31 or not fallback <= full:
        errors.append("G38 documented complete-English fallback set must remain 31 addon-full locales")

    try:
        remote_english = g38.fetch_upstream_json(g38.G38_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G38 English source differs from pinned JEI 19.8.2")
        for locale in sorted(complete | incomplete):
            upstream = g38.fetch_upstream_json(g38.G38_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: expected complete upstream")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: expected incomplete upstream")
    except Exception as exc:
        errors.append(f"failed pinned-upstream verification: {exc}")

    delta = g38.reviewed_delta()
    translated_full = full - fallback
    if set(delta) != translated_full or len(delta) != 36:
        errors.append("G38 semantic delta must cover exactly the 36 translated/AI-assisted full locales")
    for locale, values in delta.items():
        if set(values) != added | changed:
            errors.append(f"{locale}: reviewed semantic delta key set differs from 20 G38 changed/new meanings")
            continue
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)

    endpoint = audit["endpoint_resolution"]
    if endpoint["next_minecraft_port_commit"] != "8eb79e0c8f7063fa2a7cc0eb8d31a0c2882532e8" or endpoint["next_minecraft_version"] != "1.21.1":
        errors.append("G38 endpoint boundary changed")
    build = audit["build_metadata"]
    if build["forge"] != "51.0.31" or build["mappings_channel"] != "official" or build["java_toolchain"] != "21":
        errors.append("G38 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g37_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G38 policy must enforce exact G37 reuse and forbid cross-key reuse")
    if scope["ownership_changes_from_g37"]["newly_complete_upstream"] != ["ja_jp"]:
        errors.append("G38 must record ja_jp becoming complete upstream")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.21 source/scope/delta validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.21 / JEI 19.8.2 G38 source, scope, ownership and semantic-delta QA")
    print("English: 176 keys / 170 normal / 6 debug; 156 unchanged + 19 added + 1 changed")
    print("Selected language scope: 90, unchanged from G37")
    print("Ownership: 67 addon-full + 21 supplements + 2 complete upstream")
    print("Reviewed semantic delta: 36 translated/AI-assisted full locales x 20 changed/new meanings")
    print("ja_jp is now complete upstream and no longer receives a supplement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

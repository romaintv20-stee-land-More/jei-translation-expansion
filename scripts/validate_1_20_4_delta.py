#!/usr/bin/env python3
"""Validate G36 Minecraft 1.20.4 / JEI 17.3.0 source, scope, ownership and reviewed delta."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_20_4 as g36

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.20.4-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.4-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g36-mc1.20.4" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20.2-to-1.20.4.json"
DELTA_PATH = ROOT / "translations" / "g36-mc1.20.4" / "semantic-delta.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.2-language-scope.json"
EXPECTED_COMPLETE = {"en_us"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br", "ru_ru",
    "sv_se", "tr_tr", "uk_ua", "zh_cn",
}
FALLBACK = {
    "ba_ru", "bar", "br_fr", "bs_ba", "fo_fo", "fur_it", "fy_nl", "gd_gb", "haw_us", "ig_ng",
    "kk_kz", "kn_in", "ksh", "kw_gb", "li_li", "lmo", "lo_la", "mn_mn", "nah", "ovd", "ry_ua",
    "sah_sah", "se_no", "so_so", "szl", "ta_in", "tl_ph", "tt_ru", "vec_it", "yi_de", "yo_ng",
}


def main() -> int:
    errors: list[str] = []
    base = g36.parse_json(g36.BASE_SOURCE)
    target = g36.parse_json(g36.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g36.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    delta = json.loads(DELTA_PATH.read_text(encoding="utf-8"))["locales"]

    unchanged, added, removed, changed = g36.semantic_sets(base, target)
    if (len(base), len(target), len(normal)) != (156, 157, 151):
        errors.append("G36 English counts must be 156 -> 157 with 151 normal target keys")
    if (len(unchanged), len(added), len(removed), len(changed)) != (155, 1, 0, 1):
        errors.append("G36 semantic delta must remain 155 unchanged + 1 added + 0 removed + 1 changed")
    if added != {g36.ADDED_KEY} or changed != {g36.CHANGED_KEY}:
        errors.append("G36 added/changed key identities differ from frozen audit")
    if diff["added_keys"] != [g36.ADDED_KEY] or set(diff["changed_english_values"]) != {g36.CHANGED_KEY}:
        errors.append("G36 frozen diff key identities changed")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (67, 1, 22, 90):
        errors.append("G36 ownership partition must be 67 full + 1 complete + 22 supplements = 90")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G36 ownership partitions overlap")
    if complete != EXPECTED_COMPLETE or incomplete != EXPECTED_INCOMPLETE:
        errors.append("G36 upstream ownership differs from frozen exploratory audit")

    base_full = set(base_scope["addon_full_locales"])
    base_selected = base_full | set(base_scope["selected_upstream_complete_locales"]) | set(base_scope["selected_upstream_incomplete_locales"])
    if selected != base_selected:
        errors.append("G36 selected language scope must match G35 exactly")
    if base_full - full != {"hu_hu"} or full - base_full:
        errors.append("G36 addon-full ownership must equal G35 minus hu_hu")
    if scope["new_selected_primary_languages"] or scope["removed_selected_languages"]:
        errors.append("G36 must not add or remove selected Minecraft languages")
    if set(scope["documented_full_english_fallback_locales"]) != FALLBACK:
        errors.append("G36 documented full-English fallback set changed")
    if scope["translated_or_ai_assisted_full_locale_count"] != 36:
        errors.append("G36 translated/AI-assisted full locale count must be 36")

    translated_full = full - FALLBACK
    expected_delta_locales = translated_full | incomplete
    if set(delta) != expected_delta_locales:
        errors.append(f"G36 reviewed delta locale set differs: expected {len(expected_delta_locales)}, got {len(delta)}")
    for locale in sorted(translated_full):
        if set(delta.get(locale, {})) != {g36.CHANGED_KEY, g36.ADDED_KEY}:
            errors.append(f"{locale}: full translated G36 delta must contain exactly both reviewed semantic keys")
    for locale in sorted(incomplete):
        keys = set(delta.get(locale, {}))
        if locale in translated_full:
            continue
        if keys != {g36.ADDED_KEY}:
            errors.append(f"{locale}: G36 supplement delta must contain exactly the new render-crash key")
    for locale, values in delta.items():
        for key, value in values.items():
            if key not in {g36.CHANGED_KEY, g36.ADDED_KEY}:
                errors.append(f"{locale}: delta contains unexpected key {key}")
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{locale}: empty reviewed translation for {key}")

    try:
        remote_english = g36.fetch_upstream_json(g36.G36_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G36 English source differs from pinned JEI 17.3.0")
        for locale in sorted(complete | incomplete):
            upstream = g36.fetch_upstream_json(g36.G36_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: expected complete upstream")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: expected incomplete upstream")
            if locale in incomplete and g36.ADDED_KEY not in missing:
                errors.append(f"{locale}: expected new render-crash key to be missing upstream")
            if locale in incomplete and g36.CHANGED_KEY in missing:
                errors.append(f"{locale}: changed tooltip-crash key must remain upstream-owned")
    except Exception as exc:
        errors.append(f"failed pinned-upstream verification: {exc}")

    endpoint = audit["endpoint_resolution"]
    if endpoint["next_minecraft_port_commit"] != "268a4fbad505dad57f557fa2f4d11471e36a69b9" or endpoint["next_minecraft_version"] != "1.20.6":
        errors.append("G36 endpoint boundary changed")
    build = audit["build_metadata"]
    if build["forge"] != "49.0.19" or build["mappings_version"] != "1.20.3-2023.12.31-1.20.3" or build["java_toolchain"] != "17":
        errors.append("G36 frozen build metadata changed")
    if not policy["translation_reuse"]["reuse_unchanged_g35_semantics"] or policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G36 policy must enforce exact G35 reuse and forbid cross-key reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20.4 source/scope/delta validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.20.4 / JEI 17.3.0 G36 source, scope, ownership and semantic-delta QA")
    print("English: 157 keys / 151 normal / 6 debug; 155 unchanged + 1 added + 1 changed")
    print("Selected language scope: 90, unchanged from G35")
    print("Ownership: 67 addon-full + 22 supplements + 1 complete upstream")
    print("hu_hu moves to upstream supplement ownership; uk_ua moves from complete to supplement ownership")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

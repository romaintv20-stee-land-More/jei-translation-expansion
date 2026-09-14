#!/usr/bin/env python3
"""Validate G39 Minecraft 1.21.1 / JEI 19.21.1 source, scope and resolution policy."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_21_1 as g39

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g39-mc1.21.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21-to-1.21.1.json"
BASE_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21-language-scope.json"
EXPECTED_COMPLETE = {"en_us", "ja_jp"}
EXPECTED_NEW_UPSTREAM = {"kk_kz", "no_no", "vi_vn"}
EXPECTED_INCOMPLETE = {
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "kk_kz", "ko_kr", "lt_lt", "no_no", "pl_pl", "pt_br",
    "ru_ru", "sv_se", "tr_tr", "uk_ua", "vi_vn", "zh_cn",
}


def main() -> int:
    errors: list[str] = []
    base = g39.parse_json(g39.BASE_SOURCE)
    target = g39.parse_json(g39.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g39.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    base_scope = json.loads(BASE_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g39.semantic_partition()
    normal_added = {k for k in added if not k.startswith(g39.DEBUG_PREFIX)}
    normal_changed = {k for k in changed if not k.startswith(g39.DEBUG_PREFIX)}
    debug_changed = {k for k in changed if k.startswith(g39.DEBUG_PREFIX)}
    if (len(base), len(target), len(normal)) != (176, 286, 280):
        errors.append("G39 English counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (76, 167, 57, 43):
        errors.append("G39 semantic partition must remain 76 unchanged + 167 added + 57 removed + 43 changed")
    if (len(normal_added), len(normal_changed), len(debug_changed)) != (167, 41, 2):
        errors.append("G39 normal/debug semantic partition changed")
    if set(diff["added_keys"]) != added or set(diff["removed_keys"]) != removed or set(diff["changed_english_values"]) != changed:
        errors.append("G39 frozen English diff does not match pinned sources")
    if diff["review_required_normal_added_or_changed_key_count"] != 208:
        errors.append("G39 must retain 208 normal meanings requiring explicit treatment")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 2, 24, 90):
        errors.append("G39 ownership partition must be 64 full + 2 complete + 24 supplements = 90")
    if complete != EXPECTED_COMPLETE or incomplete != EXPECTED_INCOMPLETE:
        errors.append("G39 upstream ownership differs from frozen audit")

    base_selected = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if selected != base_selected:
        errors.append("G39 selected language scope must match G38 exactly")
    if set(base_scope["addon_full_locales"]) - full != EXPECTED_NEW_UPSTREAM:
        errors.append("G39 addon-full migration must move exactly kk_kz, no_no and vi_vn upstream")
    migration = scope["ownership_changes_from_g38"]
    if set(migration["newly_upstream_from_addon_full"]) != EXPECTED_NEW_UPSTREAM:
        errors.append("G39 ownership migration manifest changed")
    if scope["new_selected_primary_languages"] or scope["removed_selected_languages"]:
        errors.append("G39 must not add or remove selected languages")
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(fallback) != 30 or not fallback <= full:
        errors.append("G39 documented full-English fallback set must contain 30 addon-full locales")
    if len(full - fallback) != 34:
        errors.append("G39 translated/AI-assisted addon-full locale count must remain 34")

    try:
        remote_english = g39.fetch_upstream_json(g39.G39_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G39 English source differs from pinned JEI 19.21.1")
        for locale in sorted(complete | incomplete):
            upstream = g39.fetch_upstream_json(g39.G39_COMMIT, locale)
            missing = normal - set(upstream)
            if locale in complete and missing:
                errors.append(f"{locale}: expected complete upstream")
            if locale in incomplete and not missing:
                errors.append(f"{locale}: expected incomplete upstream")
    except Exception as exc:
        errors.append(f"failed pinned-upstream verification: {exc}")

    donor_en = g39.donor_english()
    stable_donor = {k for k in normal if donor_en.get(k) == target[k]}
    if len(stable_donor) != 253:
        errors.append(f"G39 pinned donor exact-semantic coverage changed: {len(stable_donor)} != 253")
    for locale in sorted(selected):
        donor = g39.donor_locale(locale)
        if donor is None:
            continue
        for key in set(donor) & normal:
            if key not in stable_donor:
                # It is legal for donor files to contain later semantics, but those values must never be selected.
                if g39.exact_donor_value(locale, key, target[key]) is not None:
                    errors.append(f"{locale}: donor resolver accepted non-identical English semantics for {key}")

    endpoint = audit["endpoint_resolution"]
    if endpoint["next_minecraft_port_commit"] != "c0d0367841b16fa3a9567c3d93172cbd1f1b578c" or endpoint["next_minecraft_version"] != "1.21.4":
        errors.append("G39 endpoint boundary changed")
    build = audit["build_metadata"]
    if build["neoforge"] != "21.1.116" or build["java_toolchain"] != "21" or build["forge_module_present_at_final_endpoint"]:
        errors.append("G39 frozen build metadata changed")
    reuse = policy["translation_reuse"]
    if not reuse["reuse_exact_unchanged_g38_semantics"] or reuse["cross_key_reuse_allowed"]:
        errors.append("G39 policy must enforce exact G38 reuse and forbid cross-key reuse")
    donor_policy = policy["later_upstream_backport_policy"]
    if not donor_policy["allowed_only_if_same_key_and_exact_same_english_value"]:
        errors.append("G39 donor policy must enforce exact same-key + same-English semantics")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.21.1 source/scope/provenance validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.21.1 / JEI 19.21.1 G39 source, scope, ownership and provenance QA")
    print("English: 286 keys / 280 normal / 6 debug")
    print("Semantic delta: 76 unchanged + 167 added + 57 removed + 43 changed (2 debug)")
    print("Normal new/changed meanings requiring explicit treatment: 208")
    print("Selected scope: 90 = 64 addon-full + 24 supplements + 2 complete upstream")
    print("Pinned later-JEI donor provides 253/280 exact key+English semantics; only exact matches are eligible")
    print("G39 final endpoint is NeoForge-based; Forge-only packaging must not be used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

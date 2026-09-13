#!/usr/bin/env python3
"""Validate G24 Minecraft 1.17.1 / JEI 8.3.0 source, scope and ownership."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_17_1 as g24

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.17.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.17.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g24-mc1.17.1" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.5-to-1.17.1.json"


def main() -> int:
    errors: list[str] = []
    base = g24.parse_json(g24.BASE_SOURCE)
    target = g24.parse_json(g24.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g24.DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    normal_changed = sorted(k for k in set(added) | set(changed) if not k.startswith(g24.DEBUG_PREFIX))

    if (len(base), len(target), len(normal)) != (119, 141, 135):
        errors.append(f"G24 English counts changed: base={len(base)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed), len(normal_changed)) != (87, 24, 2, 30, 53):
        errors.append("G24 computed source delta counts no longer match frozen 87/24/2/30/53")
    if added != sorted(diff["added_keys"]) or removed != sorted(diff["removed_keys"]) or changed != sorted(diff["changed_english_values"]):
        errors.append("G24 frozen key delta differs from stored pinned sources")
    for key in changed:
        frozen = diff["changed_english_values"][key]
        if frozen != {"from": base[key], "to": target[key]}:
            errors.append(f"{key}: frozen changed English values differ from stored sources")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if (len(full), len(complete), len(incomplete), len(selected)) != (64, 1, 21, 86):
        errors.append("G24 ownership partition must be 64 full + 1 complete + 21 supplements = 86")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G24 ownership partitions overlap")
    if complete != {"en_us"}:
        errors.append(f"G24 complete upstream set changed: {sorted(complete)}")
    expected_incomplete = {
        "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr",
        "he_il", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt", "pl_pl", "pt_br",
        "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn",
    }
    if incomplete != expected_incomplete:
        errors.append(f"G24 incomplete upstream set changed: {sorted(incomplete)}")
    if scope["raw_language_count"] != 123 or scope["selected_scope_count"] != 86:
        errors.append("G24 Minecraft raw/selected counts must be 123/86")
    if set(scope["removed_selected_languages"]) != {"gv_im", "mi_nz"}:
        errors.append("G24 removed selected languages must be exactly gv_im and mi_nz")
    if set(scope["deferred_new_languages"]) != {"zlm_arab"}:
        errors.append("G24 must defer only new zlm_arab from the new-code set")

    try:
        remote_english = g24.fetch_upstream_json(g24.G24_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G24 English source differs from pinned JEI 8.3.0")
        for locale in sorted(complete):
            upstream = g24.fetch_upstream_json(g24.G24_COMMIT, locale)
            if normal - set(upstream):
                errors.append(f"{locale}: frozen complete upstream locale is missing normal G24 keys")
        for locale in sorted(incomplete):
            upstream = g24.fetch_upstream_json(g24.G24_COMMIT, locale)
            if not (normal - set(upstream)):
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G24 pinned-upstream ownership verification: {exc}")

    asset = audit["minecraft_asset_index"]
    if asset["sha1"] != "f425401a00adf0112fde624ee80c66333530f8a1":
        errors.append("G24 Minecraft asset index SHA changed")
    if set(asset["added_codes_since_1.16.5"]) != {"zlm_arab"}:
        errors.append("G24 Minecraft added-code set changed")
    if set(asset["removed_codes_since_1.16.5"]) != {"gv_im", "mi_nz", "swg"}:
        errors.append("G24 Minecraft removed-code set changed")
    if not policy["translation_reuse"]["reuse_unchanged_g23_semantics"]:
        errors.append("G24 policy must enforce exact G23 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        errors.append("G24 policy must forbid cross-key translation reuse")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.17.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.17.1 / JEI 8.3.0 G24 source, scope and ownership QA")
    print("English: 141 keys / 135 normal / 6 debug; 87 unchanged, 24 added, 2 removed, 30 changed")
    print("Minecraft raw/selected: 123 / 86")
    print("Selected upstream: 22 (1 complete + 21 supplements)")
    print("Addon-owned full locales: 64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

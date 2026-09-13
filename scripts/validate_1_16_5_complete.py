#!/usr/bin/env python3
"""Validate complete G23 Minecraft 1.16.5 / JEI 7.7.1 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_16_5 as g23
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g23.parse_json(g23.BASE_SOURCE)
    target = g23.parse_json(g23.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g23.DEBUG_PREFIX)}
    scope = json.loads(g23.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g23.reconstruct_full(target, scope)
    supplements = g23.reconstruct_supplements(target, scope)
    g22_full = g23.reconstruct_g22_full()
    g22_supplements = g23.reconstruct_g22_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (66, 15, 119, 113):
        errors.append(f"G23 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if set(full) != set(g22_full) - {"id_id"}:
        errors.append("G23 addon-full locale set must equal G22 full set minus id_id")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 28:
        errors.append("G23 must retain 28 documented complete-English fallback locales")

    for locale, values in full.items():
        previous = g22_full[locale]
        expected = {key: g23.inherit_or_target(key, base, target, previous) for key in target}
        if values != expected:
            errors.append(f"{locale}: full G23 values differ from deterministic G22 inheritance + G23 new-key fallback")
        if set(values) != set(target):
            errors.append(f"{locale}: full G23 key set differs from target")
            continue
        if "jei.message.ftbguilib" in values:
            errors.append(f"{locale}: removed G22 ftbguilib key leaked into G23")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G23 target English")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g23.fetch_upstream_json(g23.G23_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g23.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        previous = g23.g22_combined_locale(locale, g22_full, g22_supplements)
        for key, value in values.items():
            expected = g23.inherit_or_target(key, base, target, previous)
            if value != expected:
                errors.append(f"{locale}: G23 supplement value is not deterministic for {key}")
            if key not in base and value != target[key]:
                errors.append(f"{locale}: new G23 meaning must use exact target English for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 113 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    expected_complete = {"en_us", "it_it", "ko_kr", "ru_ru", "sv_se", "tr_tr", "zh_cn"}
    if complete_set != expected_complete:
        errors.append(f"G23 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g23.fetch_upstream_json(g23.G23_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G23")

    for retired in ("it_it", "ko_kr", "tr_tr", "zh_cn"):
        if retired in supplements:
            errors.append(f"G23 must retire {retired} supplement because upstream is complete")
    for restored in ("pl_pl", "pt_br"):
        if set(supplements.get(restored, {})) != {"key.jei.nextCategory", "key.jei.previousCategory"}:
            errors.append(f"G23 {restored} supplement must contain exactly the two new category navigation keys")
    if set(supplements.get("id_id", {})) != {"jei.message.ftblibrary"}:
        errors.append("G23 id_id supplement must contain exactly jei.message.ftblibrary")
    if set(supplements.get("ja_jp", {})) != {"gui.jei.category.smelting.time.seconds", "key.jei.nextCategory", "key.jei.previousCategory"}:
        errors.append("G23 ja_jp supplement missing-key set changed")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G23 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G23 ownership partitions do not cover exactly 88 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.16.5-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g23.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 66 or len(full_files) != 66 or {p.stem for p in full_files} != full_set:
            errors.append("G23 full output file set differs from frozen ownership")
        if supplement_count != 15 or len(supplement_files) != 15 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G23 supplement output file set differs from frozen ownership")
        if key_count != 119:
            errors.append("G23 output key count must be 119")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.5 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 7.7.1 / Minecraft 1.16.5 complete JSON translation QA")
    print("Complete addon locales: 66")
    print("Inherited translated/AI-assisted full locales: 38")
    print("Documented complete English fallbacks: 28")
    print("Selected complete upstream locales: 7")
    print("Missing-key-only upstream supplements: 15")
    print("Keys per complete addon locale: 119")
    print("113 unchanged G22 semantics are inherited exactly; six new keys use target-English fallback when project-owned")
    print("id_id is upstream-owned with one supplement key; pl_pl and pt_br each require two category-navigation keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

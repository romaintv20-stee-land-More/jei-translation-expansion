#!/usr/bin/env python3
"""Validate complete G24 Minecraft 1.17.1 / JEI 8.3.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_17_1 as g24
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g24.parse_json(g24.BASE_SOURCE)
    target = g24.parse_json(g24.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g24.DEBUG_PREFIX)}
    scope = json.loads(g24.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g24.reconstruct_full(target, scope)
    supplements = g24.reconstruct_supplements(target, scope)
    g23_full = g24.reconstruct_g23_full()
    g23_supplements = g24.reconstruct_g23_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 21, 141, 135):
        errors.append(f"G24 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if set(full) != set(g23_full) - {"gv_im", "mi_nz"}:
        errors.append("G24 addon-full locale set must equal G23 full set minus gv_im and mi_nz")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G24 must retain 27 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G24 key set differs from target")
            continue
        previous = g23_full[locale]
        for key, value in values.items():
            if key in base and base[key] == target[key]:
                if value != previous[key]:
                    errors.append(f"{locale}: unchanged G23 value not inherited for {key}")
            elif value != target[key]:
                errors.append(f"{locale}: new/changed G24 meaning must use exact target English for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G24 target English")

    for locale, values in supplements.items():
        upstream = g24.fetch_upstream_json(g24.G24_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g24.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        previous = g24.g23_combined_locale(locale, g23_full, g23_supplements)
        for key, value in values.items():
            if key in base and base[key] == target[key]:
                if value != previous[key]:
                    errors.append(f"{locale}: unchanged G23 supplement value not inherited for {key}")
            elif value != target[key]:
                errors.append(f"{locale}: new/changed supplement meaning must use exact G24 target English for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 135 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us"}:
        errors.append(f"G24 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g24.fetch_upstream_json(g24.G24_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G24")

    for became_incomplete in ("it_it", "ko_kr", "ru_ru", "sv_se", "tr_tr", "zh_cn"):
        if became_incomplete not in supplements:
            errors.append(f"G24 must restore a supplement for {became_incomplete}")
    if "gv_im" in full or "mi_nz" in full or "gv_im" in supplements or "mi_nz" in supplements:
        errors.append("G24 must not emit removed Minecraft locales gv_im or mi_nz")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G24 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 86:
        errors.append("G24 ownership partitions do not cover exactly 86 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.17.1-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g24.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G24 full output file set differs from frozen ownership")
        if supplement_count != 21 or len(supplement_files) != 21 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G24 supplement output file set differs from frozen ownership")
        if key_count != 141:
            errors.append("G24 output key count must be 141")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.17.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 8.3.0 / Minecraft 1.17.1 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Inherited translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 21")
    print("Keys per complete addon locale: 141")
    print("87 unchanged G23 semantics are inherited exactly; all added/changed project-owned meanings use target English")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate complete G16 Minecraft 1.14.4 / JEI 6.0.1 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_14_4 as g16
import validate_1_14_2_complete as g14qa


def main() -> int:
    errors: list[str] = []
    target = g16.parse_json(g16.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g16.DEBUG_PREFIX)}
    scope = json.loads(g16.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g16.reconstruct_full(target, scope)
    supplements = g16.reconstruct_supplements(target, scope)
    g15_full = g16.reconstruct_g15_full()
    g15_supplements = g16.reconstruct_g15_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (70, 16, 109, 106):
        errors.append(
            f"G16 counts changed: full={len(full)} supplements={len(supplements)} "
            f"target={len(target)} normal={len(normal)}"
        )
    if full != g15_full:
        errors.append("G16 addon-full resources must be exact G15 reconstruction inheritance")
    if {"de_de", "ru_ru"} & set(supplements):
        errors.append("G16 must not emit de_de or ru_ru supplements")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31:
        errors.append("G16 must retain 31 documented complete-English fallback locales")
    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G16 key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact target English")
        for key, value in values.items():
            g14qa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g16.fetch_upstream_json(g16.G16_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g16.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g15 = g16.g15_combined_locale(locale, g15_full, g15_supplements)
        for key, value in values.items():
            if value != combined_g15[key]:
                errors.append(f"{locale}: G16 supplement does not exactly inherit G15 value for {key}")
            g14qa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 106 normal target keys")

    for locale in ("de_de", "en_us", "pl_pl", "pt_br", "ru_ru"):
        upstream = g16.fetch_upstream_json(g16.G16_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G16")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G16 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 91:
        errors.append("G16 ownership partitions do not cover exactly 91 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.14.4-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g16.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 70 or len(full_files) != 70 or {p.stem for p in full_files} != full_set:
            errors.append("G16 full output file set differs from frozen ownership")
        if supplement_count != 16 or len(supplement_files) != 16 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G16 supplement output file set differs from frozen ownership")
        if key_count != 109:
            errors.append("G16 output key count must be 109")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.14.4 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 6.0.1 / Minecraft 1.14.4 complete JSON translation QA")
    print("Complete addon locales: 70")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 5")
    print("Missing-key-only upstream supplements: 16")
    print("Keys per complete addon locale: 109")
    print("All 109 G15 semantic values are inherited exactly")
    print("de_de and ru_ru ownership migrations to complete upstream are validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

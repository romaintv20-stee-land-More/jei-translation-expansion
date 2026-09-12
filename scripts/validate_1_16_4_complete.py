#!/usr/bin/env python3
"""Validate complete G22 Minecraft 1.16.4 / JEI 7.6.1 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_16_4 as g22
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    target = g22.parse_json(g22.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g22.DEBUG_PREFIX)}
    scope = json.loads(g22.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g22.reconstruct_full(target, scope)
    supplements = g22.reconstruct_supplements(target, scope)
    g21_full = g22.reconstruct_g21_full()
    g21_supplements = g22.reconstruct_g21_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 16, 114, 111):
        errors.append(f"G22 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if set(full) != set(g21_full):
        errors.append("G22 addon-full locale set must exactly match G21")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 28:
        errors.append("G22 must retain 28 documented complete-English fallback locales")

    for locale, values in full.items():
        if values != g21_full[locale]:
            errors.append(f"{locale}: full G22 values differ from exact G21 inheritance")
        if set(values) != set(target):
            errors.append(f"{locale}: full G22 key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G22 target English")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g22.fetch_upstream_json(g22.G22_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g22.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g21 = g22.g21_combined_locale(locale, g21_full, g21_supplements)
        for key, value in values.items():
            if value != combined_g21[key]:
                errors.append(f"{locale}: G22 supplement changed inherited G21 value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 111 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    expected_complete = {"en_us", "pl_pl", "pt_br", "ru_ru", "sv_se"}
    if complete_set != expected_complete:
        errors.append(f"G22 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g22.fetch_upstream_json(g22.G22_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G22")
    for retired in ("pl_pl", "ru_ru"):
        if retired in supplements:
            errors.append(f"G22 must retire {retired} supplement and use complete upstream locale")
    if "ja_jp" not in supplements:
        errors.append("G22 must retain ja_jp supplement for its one missing normal key")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G22 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G22 ownership partitions do not cover exactly 88 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.16.4-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g22.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G22 full output file set differs from frozen ownership")
        if supplement_count != 16 or len(supplement_files) != 16 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G22 supplement output file set differs from frozen ownership")
        if key_count != 114:
            errors.append("G22 output key count must be 114")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.4 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 7.6.1 / Minecraft 1.16.4 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 28")
    print("Selected complete upstream locales: 5")
    print("Missing-key-only upstream supplements: 16")
    print("Keys per complete addon locale: 114")
    print("All 114 G21 semantics are inherited exactly")
    print("pl_pl and ru_ru are fully upstream-owned in G22")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate complete G21 Minecraft 1.16.3 / JEI 7.6.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_16_3 as g21
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    target = g21.parse_json(g21.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g21.DEBUG_PREFIX)}
    scope = json.loads(g21.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g21.reconstruct_full(target, scope)
    supplements = g21.reconstruct_supplements(target, scope)
    g20_full = g21.reconstruct_g20_full()
    g20_supplements = g21.reconstruct_g20_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 18, 114, 111):
        errors.append(f"G21 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if set(full) != set(g20_full):
        errors.append("G21 addon-full locale set must exactly match G20")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 28:
        errors.append("G21 must retain 28 documented complete-English fallback locales")

    for locale, values in full.items():
        if values != g20_full[locale]:
            errors.append(f"{locale}: full G21 values differ from exact G20 inheritance")
        if set(values) != set(target):
            errors.append(f"{locale}: full G21 key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G21 target English")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g21.fetch_upstream_json(g21.G21_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g21.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g20 = g21.g20_combined_locale(locale, g20_full, g20_supplements)
        for key, value in values.items():
            if value != combined_g20[key]:
                errors.append(f"{locale}: G21 supplement changed inherited G20 value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 111 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    for locale in complete_set:
        upstream = g21.fetch_upstream_json(g21.G21_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G21")
    if "sv_se" not in complete_set or "sv_se" in supplements:
        errors.append("G21 must retire sv_se supplement and use complete upstream Swedish")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G21 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G21 ownership partitions do not cover exactly 88 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.16.3-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g21.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G21 full output file set differs from frozen ownership")
        if supplement_count != 18 or len(supplement_files) != 18 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G21 supplement output file set differs from frozen ownership")
        if key_count != 114:
            errors.append("G21 output key count must be 114")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.3 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 7.6.0 / Minecraft 1.16.3 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 28")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 18")
    print("Keys per complete addon locale: 114")
    print("All 114 G20 semantics are inherited exactly")
    print("sv_se is fully upstream-owned in G21")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

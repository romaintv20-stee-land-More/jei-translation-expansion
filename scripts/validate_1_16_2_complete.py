#!/usr/bin/env python3
"""Validate complete G20 Minecraft 1.16.2 / JEI 7.3.2 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_16_2 as g20
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    target = g20.parse_json(g20.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g20.DEBUG_PREFIX)}
    scope = json.loads(g20.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g20.reconstruct_full(target, scope)
    supplements = g20.reconstruct_supplements(target, scope)
    g19_full = g20.reconstruct_g19_full()
    g19_supplements = g20.reconstruct_g19_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 19, 114, 111):
        errors.append(f"G20 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if set(full) != set(g19_full):
        errors.append("G20 addon-full locale set must exactly match G19")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 28:
        errors.append("G20 must retain 28 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G20 key set differs from target")
            continue
        old = g19_full[locale]
        for key, old_value in old.items():
            if values.get(key) != old_value:
                errors.append(f"{locale}: G20 changed inherited G19 value for {key}")
        for key in g20.ADDED_KEYS:
            if values.get(key) != target[key]:
                errors.append(f"{locale}: new G20 key {key} is not exact target English")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G20 target English")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g20.fetch_upstream_json(g20.G20_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g20.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g19 = g20.g19_combined_locale(locale, g19_full, g19_supplements)
        for key, value in values.items():
            if key in g20.ADDED_KEYS:
                if value != target[key]:
                    errors.append(f"{locale}: new G20 key {key} must use exact target English when project-owned")
            elif value != combined_g19[key]:
                errors.append(f"{locale}: G20 supplement changed inherited G19 value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 111 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    for locale in complete_set:
        upstream = g20.fetch_upstream_json(g20.G20_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G20")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G20 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G20 ownership partitions do not cover exactly 88 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.16.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g20.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G20 full output file set differs from frozen ownership")
        if supplement_count != 19 or len(supplement_files) != 19 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G20 supplement output file set differs from frozen ownership")
        if key_count != 114:
            errors.append("G20 output key count must be 114")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 7.3.2 / Minecraft 1.16.2 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 28")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 114")
    print("All 110 G19 semantics are inherited exactly")
    print("All four new project-owned G20 meanings are exact target English")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

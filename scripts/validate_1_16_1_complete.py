#!/usr/bin/env python3
"""Validate complete G19 Minecraft 1.16.1 / JEI 7.0.1 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_16_1 as g19
import validate_1_14_2_complete as g14qa


def main() -> int:
    errors: list[str] = []
    target = g19.parse_json(g19.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g19.DEBUG_PREFIX)}
    scope = json.loads(g19.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g19.reconstruct_full(target, scope)
    supplements = g19.reconstruct_supplements(target, scope)
    g18_full = g19.reconstruct_g18_full()
    g18_supplements = g19.reconstruct_g18_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 18, 110, 107):
        errors.append(
            f"G19 counts changed: full={len(full)} supplements={len(supplements)} "
            f"target={len(target)} normal={len(normal)}"
        )
    if set(full) - {g19.NEW_LOCALE} != set(g18_full):
        errors.append("G19 inherited addon-full locale set must exactly match G18")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 28:
        errors.append("G19 must have 28 documented complete-English fallback locales")
    if g19.NEW_LOCALE not in fallback_locales:
        errors.append("fur_it must be a documented complete-English fallback locale")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G19 key set differs from target")
            continue
        if locale == g19.NEW_LOCALE:
            if values != target:
                errors.append("fur_it: new fallback locale must equal exact G19 target English")
        else:
            old = g18_full[locale]
            for key, old_value in old.items():
                if key in g19.CHANGED_KEYS:
                    if values.get(key) != target[key]:
                        errors.append(f"{locale}: changed G19 key {key} is not exact target English")
                elif values.get(key) != old_value:
                    errors.append(f"{locale}: G19 changed inherited G18 value for {key}")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact target English")
        for key, value in values.items():
            g14qa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g19.fetch_upstream_json(g19.G19_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g19.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g18 = g19.g18_combined_locale(locale, g18_full, g18_supplements)
        for key, value in values.items():
            if key in g19.CHANGED_KEYS:
                if value != target[key]:
                    errors.append(f"{locale}: changed placeholder key {key} must use exact target English")
            elif value != combined_g18[key]:
                errors.append(f"{locale}: G19 supplement changed inherited G18 value for {key}")
            g14qa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 107 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    for locale in complete_set:
        upstream = g19.fetch_upstream_json(g19.G19_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G19")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G19 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G19 ownership partitions do not cover exactly 88 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.16.1-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g19.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G19 full output file set differs from frozen ownership")
        if supplement_count != 18 or len(supplement_files) != 18 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G19 supplement output file set differs from frozen ownership")
        if key_count != 110:
            errors.append("G19 output key count must be 110")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.16.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 7.0.1 / Minecraft 1.16.1 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 28")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 18")
    print("Keys per complete addon locale: 110")
    print("All 108 unchanged G18 semantic values are inherited exactly")
    print("Changed liquid placeholders are exact target English wherever project-owned")
    print("fur_it is an exact target-English documented fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

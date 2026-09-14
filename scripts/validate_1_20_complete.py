#!/usr/bin/env python3
"""Validate complete G33 Minecraft 1.20 / JEI 14.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_20 as g33
import validate_1_14_2_complete as baseqa

NEW_FULL = {"lo_la", "sah_sah"}


def main() -> int:
    errors: list[str] = []
    base = g33.parse_json(g33.BASE_SOURCE)
    target = g33.parse_json(g33.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g33.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g33.semantic_sets(base, target)
    scope = json.loads(g33.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g33.reconstruct_full(target, scope)
    supplements = g33.reconstruct_supplements(target, scope)
    g32_full = g33.reconstruct_g32_full()

    if (len(full), len(supplements), len(target), len(normal)) != (68, 20, 156, 150):
        errors.append(f"G33 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("G33 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31 or not NEW_FULL <= fallback_locales:
        errors.append("G33 must retain 29 inherited fallbacks plus Lao/Yakut = 31")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G33 key set differs from target")
            continue
        if locale in NEW_FULL:
            if values != target:
                errors.append(f"{locale}: new documented complete-English fallback is not exact G33 English")
        else:
            old = g32_full.get(locale)
            if old is None:
                errors.append(f"{locale}: inherited G33 full locale is absent from G32")
                continue
            for key, value in values.items():
                if value != old.get(key):
                    errors.append(f"{locale}: unchanged G33 full value differs from exact G32 value for {key}")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G33 target English")

    for locale, values in supplements.items():
        upstream = g33.fetch_upstream_json(g33.G33_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g33.g32_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g33.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if key not in unchanged:
                errors.append(f"{locale}: supplement contains non-unchanged G33 key: {key}")
            if value != previous_combined.get(key):
                errors.append(f"{locale}: G33 supplement differs from exact G32 combined value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 150 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us", "uk_ua"}:
        errors.append(f"G33 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g33.fetch_upstream_json(g33.G33_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G33")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G33 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 90:
        errors.append("G33 ownership partitions do not cover exactly 90 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.20-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g33.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 68 or len(full_files) != 68 or {p.stem for p in full_files} != full_set:
            errors.append("G33 full output file set differs from frozen ownership")
        if supplement_count != 20 or len(supplement_files) != 20 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G33 supplement output file set differs from frozen ownership")
        if key_count != 156:
            errors.append("G33 output key count must be 156")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 14.0.0 / Minecraft 1.20 complete JSON translation QA")
    print("Complete addon locales: 68")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 20")
    print("Keys per complete addon locale: 156")
    print("All 156 G32 meanings inherit exactly; Lao/Yakut are documented complete-English fallbacks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

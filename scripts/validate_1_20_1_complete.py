#!/usr/bin/env python3
"""Validate complete G34 Minecraft 1.20.1 / JEI 15.2.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_20_1 as g34
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g34.parse_json(g34.BASE_SOURCE)
    target = g34.parse_json(g34.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g34.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g34.semantic_sets(base, target)
    scope = json.loads(g34.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g34.reconstruct_full(target, scope)
    supplements = g34.reconstruct_supplements(target, scope)
    g33_full = g34.reconstruct_g33_full()

    if (len(full), len(supplements), len(target), len(normal)) != (68, 20, 156, 150):
        errors.append(f"G34 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("G34 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31:
        errors.append("G34 documented complete-English fallback count must remain 31")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G34 key set differs from target")
            continue
        old = g33_full.get(locale)
        if old is None:
            errors.append(f"{locale}: inherited G34 full locale is absent from G33")
            continue
        for key, value in values.items():
            if value != old.get(key):
                errors.append(f"{locale}: unchanged G34 full value differs from exact G33 value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G34 target English")

    for locale, values in supplements.items():
        upstream = g34.fetch_upstream_json(g34.G34_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g34.g33_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g34.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if key not in unchanged:
                errors.append(f"{locale}: supplement contains non-unchanged G34 key: {key}")
            if value != previous_combined.get(key):
                errors.append(f"{locale}: G34 supplement differs from exact G33 combined value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 150 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us", "uk_ua"}:
        errors.append(f"G34 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g34.fetch_upstream_json(g34.G34_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G34")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G34 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 90:
        errors.append("G34 ownership partitions do not cover exactly 90 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.20.1-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g34.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 68 or len(full_files) != 68 or {p.stem for p in full_files} != full_set:
            errors.append("G34 full output file set differs from frozen ownership")
        if supplement_count != 20 or len(supplement_files) != 20 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G34 supplement output file set differs from frozen ownership")
        if key_count != 156:
            errors.append("G34 output key count must be 156")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 15.2.0 / Minecraft 1.20.1 complete JSON translation QA")
    print("Complete addon locales: 68")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 20")
    print("Keys per complete addon locale: 156")
    print("All 156 G33 meanings inherit exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

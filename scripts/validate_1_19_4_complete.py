#!/usr/bin/env python3
"""Validate complete G32 Minecraft 1.19.4 / JEI 13.1.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_19_4 as g32
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g32.parse_json(g32.BASE_SOURCE)
    target = g32.parse_json(g32.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g32.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g32.semantic_sets(base, target)
    scope = json.loads(g32.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g32.reconstruct_full(target, scope)
    supplements = g32.reconstruct_supplements(target, scope)
    g31_full = g32.reconstruct_g31_full()

    if (len(full), len(supplements), len(target), len(normal)) != (66, 20, 156, 150):
        errors.append(f"G32 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("G32 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 29:
        errors.append("G32 must retain 29 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G32 key set differs from target")
            continue
        old = g31_full.get(locale)
        if old is None:
            errors.append(f"{locale}: G32 full locale is absent from G31")
            continue
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
            if value != old.get(key):
                errors.append(f"{locale}: unchanged G32 full value differs from exact G31 value for {key}")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G32 target English")

    for locale, values in supplements.items():
        upstream = g32.fetch_upstream_json(g32.G32_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g32.g31_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g32.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if key not in unchanged:
                errors.append(f"{locale}: supplement contains non-unchanged G32 key: {key}")
            if value != previous_combined.get(key):
                errors.append(f"{locale}: G32 supplement differs from exact G31 combined value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 150 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us", "uk_ua"}:
        errors.append(f"G32 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g32.fetch_upstream_json(g32.G32_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G32")
    if "uk_ua" in supplements:
        errors.append("uk_ua supplement must be retired in G32")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G32 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G32 ownership partitions do not cover exactly 88 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.19.4-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g32.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 66 or len(full_files) != 66 or {p.stem for p in full_files} != full_set:
            errors.append("G32 full output file set differs from frozen ownership")
        if supplement_count != 20 or len(supplement_files) != 20 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G32 supplement output file set differs from frozen ownership")
        if key_count != 156:
            errors.append("G32 output key count must be 156")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.4 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 13.1.0 / Minecraft 1.19.4 complete JSON translation QA")
    print("Complete addon locales: 66")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 29")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 20")
    print("Keys per complete addon locale: 156")
    print("All 156 G31 meanings inherit exactly; uk_ua is now fully upstream")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

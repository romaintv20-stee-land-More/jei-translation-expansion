#!/usr/bin/env python3
"""Validate complete G28 Minecraft 1.19 / JEI 11.1.1 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_19 as g28
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g28.parse_json(g28.BASE_SOURCE)
    target = g28.parse_json(g28.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g28.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g28.semantic_sets(base, target)
    scope = json.loads(g28.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g28.reconstruct_full(target, scope)
    supplements = g28.reconstruct_supplements(target, scope)
    g27_full = g28.reconstruct_g27_full()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 19, 154, 148):
        errors.append(f"G28 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (154, 0, 0, 0):
        errors.append("G28 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G28 must retain 27 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G28 key set differs from target")
            continue
        if values != g27_full[locale]:
            errors.append(f"{locale}: full G28 locale is not exact G27 inheritance")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G28 target English")

    for locale, values in supplements.items():
        upstream = g28.fetch_upstream_json(g28.G28_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g28.g27_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g28.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if value != previous_combined.get(key):
                errors.append(f"{locale}: unchanged G28 supplement differs from exact G27 combined value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 148 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"bg_bg", "en_us", "pl_pl"}:
        errors.append(f"G28 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g28.fetch_upstream_json(g28.G28_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G28")

    if "bg_bg" in supplements or "pl_pl" in supplements:
        errors.append("G28 must retire bg_bg and pl_pl supplements")
    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G28 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 86:
        errors.append("G28 ownership partitions do not cover exactly 86 selected languages")
    if "ry_ua" in full_set or "ry_ua" in supplement_set or "ry_ua" in complete_set:
        errors.append("G28 must not emit deferred asset-only ry_ua")

    with tempfile.TemporaryDirectory(prefix="jei-1.19-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g28.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G28 full output file set differs from frozen ownership")
        if supplement_count != 19 or len(supplement_files) != 19 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G28 supplement output file set differs from frozen ownership")
        if key_count != 154:
            errors.append("G28 output key count must be 154")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 11.1.1 / Minecraft 1.19 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 154")
    print("All 154 values inherit G27 exactly; bg_bg and pl_pl supplements are retired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

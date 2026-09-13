#!/usr/bin/env python3
"""Validate complete G29 Minecraft 1.19.1 / JEI 11.2.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_19_1 as g29
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g29.parse_json(g29.BASE_SOURCE)
    target = g29.parse_json(g29.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g29.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g29.semantic_sets(base, target)
    scope = json.loads(g29.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g29.reconstruct_full(target, scope)
    supplements = g29.reconstruct_supplements(target, scope)
    g28_full = g29.reconstruct_g28_full()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 19, 153, 147):
        errors.append(f"G29 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 0, 1, 0):
        errors.append("G29 semantic partition changed")
    if removed != {g29.REMOVED_KEY}:
        errors.append(f"G29 removed-key set changed: {sorted(removed)}")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G29 must retain 27 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G29 key set differs from target")
            continue
        expected = {key: g28_full[locale][key] for key in target}
        if values != expected:
            errors.append(f"{locale}: full G29 locale is not exact G28 inheritance minus removed key")
        if g29.REMOVED_KEY in values:
            errors.append(f"{locale}: removed G28 key is still emitted")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G29 target English")

    for locale, values in supplements.items():
        upstream = g29.fetch_upstream_json(g29.G29_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g29.g28_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g29.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        if g29.REMOVED_KEY in values:
            errors.append(f"{locale}: supplement emits removed key")
        for key, value in values.items():
            if value != previous_combined.get(key):
                errors.append(f"{locale}: unchanged G29 supplement differs from exact G28 combined value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 147 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"bg_bg", "en_us", "pl_pl"}:
        errors.append(f"G29 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g29.fetch_upstream_json(g29.G29_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G29")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G29 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 86:
        errors.append("G29 ownership partitions do not cover exactly 86 selected languages")
    if "ry_ua" in full_set or "ry_ua" in supplement_set or "ry_ua" in complete_set:
        errors.append("G29 must not emit deferred asset-only ry_ua")

    with tempfile.TemporaryDirectory(prefix="jei-1.19.1-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g29.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G29 full output file set differs from frozen ownership")
        if supplement_count != 19 or len(supplement_files) != 19 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G29 supplement output file set differs from frozen ownership")
        if key_count != 153:
            errors.append("G29 output key count must be 153")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 11.2.0 / Minecraft 1.19.1 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 153")
    print("All remaining values inherit G28 exactly; the removed G28 key is not emitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

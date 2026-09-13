#!/usr/bin/env python3
"""Validate complete G27 Minecraft 1.18.2 / JEI 10.1.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_18_2 as g27
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g27.parse_json(g27.BASE_SOURCE)
    target = g27.parse_json(g27.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g27.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g27.semantic_sets(base, target)
    changed_or_added = added | changed
    scope = json.loads(g27.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g27.reconstruct_full(target, scope)
    supplements = g27.reconstruct_supplements(target, scope)
    g26_full = g27.reconstruct_g26_full()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 21, 154, 148):
        errors.append(f"G27 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (149, 5, 0, 0):
        errors.append("G27 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G27 must retain 27 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G27 key set differs from target")
            continue
        for key, value in values.items():
            if key in unchanged:
                expected = g26_full[locale].get(key)
                if value != expected:
                    errors.append(f"{locale}: unchanged G27 value differs from exact G26 inheritance for {key}")
            elif key in changed_or_added and value != target[key]:
                errors.append(f"{locale}: added/changed G27 value must be exact target English for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if set(values) & removed:
            errors.append(f"{locale}: full G27 locale emits removed G26 keys")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G27 target English")

    for locale, values in supplements.items():
        upstream = g27.fetch_upstream_json(g27.G27_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g27.g26_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g27.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        if set(values) & removed:
            errors.append(f"{locale}: supplement emits removed G26 key")
        for key, value in values.items():
            if key in unchanged:
                if value != previous_combined.get(key):
                    errors.append(f"{locale}: unchanged supplement value differs from exact G26 combined value for {key}")
            elif key in changed_or_added and value != target[key]:
                errors.append(f"{locale}: added/changed supplement value must be exact G27 target English for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 148 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us"}:
        errors.append(f"G27 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g27.fetch_upstream_json(g27.G27_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G27")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G27 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 86:
        errors.append("G27 ownership partitions do not cover exactly 86 selected languages")
    if "ry_ua" in full_set or "ry_ua" in supplement_set or "ry_ua" in complete_set:
        errors.append("G27 must not emit deferred asset-only ry_ua")

    with tempfile.TemporaryDirectory(prefix="jei-1.18.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g27.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G27 full output file set differs from frozen ownership")
        if supplement_count != 21 or len(supplement_files) != 21 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G27 supplement output file set differs from frozen ownership")
        if key_count != 154:
            errors.append("G27 output key count must be 154")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.18.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 10.1.0 / Minecraft 1.18.2 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 21")
    print("Keys per complete addon locale: 154")
    print("149 unchanged values inherit G26 exactly; 5 new meanings use exact G27 English")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

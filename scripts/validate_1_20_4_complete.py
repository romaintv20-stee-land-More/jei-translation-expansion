#!/usr/bin/env python3
"""Validate complete G36 Minecraft 1.20.4 / JEI 17.3.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_20_4 as g36
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g36.parse_json(g36.BASE_SOURCE)
    target = g36.parse_json(g36.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g36.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g36.semantic_sets(base, target)
    scope = json.loads(g36.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g36.reconstruct_full(target, scope)
    supplements = g36.reconstruct_supplements(target, scope)
    g35_full = g36.reconstruct_g35_full()
    delta = g36.reviewed_delta()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 22, 157, 151):
        errors.append(f"G36 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (155, 1, 0, 1):
        errors.append("G36 semantic partition changed")
    if added != {g36.ADDED_KEY} or changed != {g36.CHANGED_KEY}:
        errors.append("G36 added/changed key identity changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31:
        errors.append("G36 documented complete-English fallback count must remain 31")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G36 key set differs from target")
            continue
        old = g35_full.get(locale)
        if old is None:
            errors.append(f"{locale}: inherited G36 full locale is absent from G35")
            continue
        for key, value in values.items():
            if key in unchanged and value != old.get(key):
                errors.append(f"{locale}: unchanged G36 full value differs from exact G35 value for {key}")
            elif key in {g36.CHANGED_KEY, g36.ADDED_KEY}:
                expected = target[key] if locale in fallback_locales else delta.get(locale, {}).get(key)
                if value != expected:
                    errors.append(f"{locale}: reviewed G36 semantic value differs for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G36 target English")

    for locale, values in supplements.items():
        upstream = g36.fetch_upstream_json(g36.G36_COMMIT, locale)
        missing = normal - set(upstream)
        previous_complete = g36.g35_complete_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g36.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if key in unchanged:
                if value != previous_complete.get(key):
                    errors.append(f"{locale}: unchanged G36 supplement differs from exact complete G35 value for {key}")
            elif key == g36.ADDED_KEY:
                if value != delta.get(locale, {}).get(key):
                    errors.append(f"{locale}: new G36 supplement value differs from reviewed semantic delta for {key}")
            else:
                errors.append(f"{locale}: supplement contains unexpected non-inherited key {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 151 normal target keys")
        if g36.CHANGED_KEY not in upstream:
            errors.append(f"{locale}: changed tooltip-crash key is unexpectedly not upstream-owned")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us"}:
        errors.append(f"G36 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g36.fetch_upstream_json(g36.G36_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G36")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G36 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 90:
        errors.append("G36 ownership partitions do not cover exactly 90 selected languages")
    if "hu_hu" in full_set or "hu_hu" not in supplement_set:
        errors.append("G36 hu_hu ownership migration was not applied")
    if "uk_ua" in complete_set or "uk_ua" not in supplement_set:
        errors.append("G36 uk_ua complete-to-supplement ownership migration was not applied")

    with tempfile.TemporaryDirectory(prefix="jei-1.20.4-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g36.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G36 full output file set differs from frozen ownership")
        if supplement_count != 22 or len(supplement_files) != 22 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G36 supplement output file set differs from frozen ownership")
        if key_count != 157:
            errors.append("G36 output key count must be 157")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20.4 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 17.3.0 / Minecraft 1.20.4 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Translated/AI-assisted full locales: 36")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 22")
    print("Keys per complete addon locale: 157")
    print("155 G35 meanings inherit exactly; 2 new/changed meanings use reviewed G36 translations or explicit English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

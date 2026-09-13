#!/usr/bin/env python3
"""Validate complete G31 Minecraft 1.19.3 / JEI 12.3.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_19_3 as g31
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g31.parse_json(g31.BASE_SOURCE)
    target = g31.parse_json(g31.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g31.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g31.semantic_sets(base, target)
    scope = json.loads(g31.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g31.reconstruct_full(target, scope)
    supplements = g31.reconstruct_supplements(target, scope)
    g30_full = g31.reconstruct_g30_full()

    if (len(full), len(supplements), len(target), len(normal)) != (66, 21, 156, 150):
        errors.append(f"G31 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 3, 0, 0):
        errors.append("G31 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 29 or not g31.NEW_FULL_LOCALES <= fallback_locales:
        errors.append("G31 must retain 29 documented complete-English fallback locales including nah and ry_ua")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G31 key set differs from target")
            continue
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G31 target English")
        if locale in g31.NEW_FULL_LOCALES:
            if values != target:
                errors.append(f"{locale}: new G31 fallback locale must equal target English exactly")
            continue
        old = g30_full.get(locale)
        if old is None:
            errors.append(f"{locale}: inherited G31 full locale is absent from G30")
            continue
        for key in unchanged:
            if values.get(key) != old.get(key):
                errors.append(f"{locale}: unchanged G31 full value differs from exact G30 value for {key}")
        for key in added:
            if values.get(key) != target[key]:
                errors.append(f"{locale}: new G31 full value is not exact target English for {key}")

    for locale, values in supplements.items():
        upstream = g31.fetch_upstream_json(g31.G31_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g31.g30_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g31.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if key in unchanged:
                if value != previous_combined.get(key):
                    errors.append(f"{locale}: unchanged G31 supplement differs from exact G30 combined value for {key}")
            elif key in added:
                if value != target[key]:
                    errors.append(f"{locale}: new G31 supplement value is not exact target English for {key}")
            else:
                errors.append(f"{locale}: supplement contains key outside frozen semantic partition: {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 150 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us"}:
        errors.append(f"G31 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g31.fetch_upstream_json(g31.G31_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G31")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G31 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 88:
        errors.append("G31 ownership partitions do not cover exactly 88 selected languages")
    if not {"nah", "ry_ua"} <= full_set:
        errors.append("G31 must emit full Nahuatl and Rusyn locale files")

    with tempfile.TemporaryDirectory(prefix="jei-1.19.3-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g31.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 66 or len(full_files) != 66 or {p.stem for p in full_files} != full_set:
            errors.append("G31 full output file set differs from frozen ownership")
        if supplement_count != 21 or len(supplement_files) != 21 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G31 supplement output file set differs from frozen ownership")
        if key_count != 156:
            errors.append("G31 output key count must be 156")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.3 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 12.3.0 / Minecraft 1.19.3 complete JSON translation QA")
    print("Complete addon locales: 66")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 29")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 21")
    print("Keys per complete addon locale: 156")
    print("153 unchanged meanings inherit G30 exactly; 3 new meanings use exact G31 English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

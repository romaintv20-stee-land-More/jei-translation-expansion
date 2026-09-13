#!/usr/bin/env python3
"""Validate complete G30 Minecraft 1.19.2 / JEI 11.5.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_19_2 as g30
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g30.parse_json(g30.BASE_SOURCE)
    target = g30.parse_json(g30.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g30.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g30.semantic_sets(base, target)
    scope = json.loads(g30.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g30.reconstruct_full(target, scope)
    supplements = g30.reconstruct_supplements(target, scope)
    g29_full = g30.reconstruct_g29_full()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 19, 153, 147):
        errors.append(f"G30 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 0, 0, 0):
        errors.append("G30 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G30 must retain 27 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G30 key set differs from target")
            continue
        if values != g29_full[locale]:
            errors.append(f"{locale}: full G30 locale is not exact G29 inheritance")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G30 target English")

    for locale, values in supplements.items():
        upstream = g30.fetch_upstream_json(g30.G30_COMMIT, locale)
        missing = normal - set(upstream)
        previous_combined = g30.g29_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g30.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if value != previous_combined.get(key):
                errors.append(f"{locale}: unchanged G30 supplement differs from exact G29 combined value for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 147 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"bg_bg", "en_us", "pl_pl"}:
        errors.append(f"G30 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g30.fetch_upstream_json(g30.G30_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G30")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G30 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 86:
        errors.append("G30 ownership partitions do not cover exactly 86 selected languages")
    if "ry_ua" in full_set or "ry_ua" in supplement_set or "ry_ua" in complete_set:
        errors.append("G30 must not emit deferred asset-only ry_ua")

    with tempfile.TemporaryDirectory(prefix="jei-1.19.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g30.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G30 full output file set differs from frozen ownership")
        if supplement_count != 19 or len(supplement_files) != 19 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G30 supplement output file set differs from frozen ownership")
        if key_count != 153:
            errors.append("G30 output key count must be 153")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.19.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 11.5.0 / Minecraft 1.19.2 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 153")
    print("All values inherit G29 exactly because all G30 English semantics are unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

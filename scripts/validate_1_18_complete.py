#!/usr/bin/env python3
"""Validate complete G25 Minecraft 1.18 / JEI 9.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_18 as g25
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    target = g25.parse_json(g25.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g25.DEBUG_PREFIX)}
    scope = json.loads(g25.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g25.reconstruct_full(target, scope)
    supplements = g25.reconstruct_supplements(target, scope)
    g24_full = g25.reconstruct_g24_full()
    g24_supplements = g25.reconstruct_g24_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 21, 141, 135):
        errors.append(f"G25 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if full != g24_full:
        errors.append("G25 full reconstructed locale data must be exactly identical to G24")
    if supplements != g24_supplements:
        errors.append("G25 supplements must be exactly identical to G24")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G25 must retain 27 documented complete-English fallback locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G25 key set differs from target")
            continue
        for key, value in values.items():
            if value != g24_full[locale][key]:
                errors.append(f"{locale}: G25 value differs from exact G24 inheritance for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G25 target English")

    for locale, values in supplements.items():
        upstream = g25.fetch_upstream_json(g25.G25_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g25.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if value != g24_supplements[locale][key]:
                errors.append(f"{locale}: G25 supplement value differs from exact G24 inheritance for {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 135 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us"}:
        errors.append(f"G25 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g25.fetch_upstream_json(g25.G25_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G25")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G25 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 86:
        errors.append("G25 ownership partitions do not cover exactly 86 selected languages")
    if "ry_ua" in full_set or "ry_ua" in supplement_set or "ry_ua" in complete_set:
        errors.append("G25 must not emit deferred asset-only ry_ua")

    with tempfile.TemporaryDirectory(prefix="jei-1.18-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g25.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G25 full output file set differs from frozen ownership")
        if supplement_count != 21 or len(supplement_files) != 21 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G25 supplement output file set differs from frozen ownership")
        if key_count != 141:
            errors.append("G25 output key count must be 141")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.18 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 9.0.0 / Minecraft 1.18 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Inherited translated/AI-assisted full locales: 37")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 21")
    print("Keys per complete addon locale: 141")
    print("All G25 project-owned values are exact G24 inheritance because all English semantics are unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

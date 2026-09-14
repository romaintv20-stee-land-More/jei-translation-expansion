#!/usr/bin/env python3
"""Validate complete G37 Minecraft 1.20.6 / JEI 18.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_20_6 as g37
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g37.parse_json(g37.BASE_SOURCE)
    target = g37.parse_json(g37.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g37.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g37.semantic_sets(base, target)
    scope = json.loads(g37.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g37.reconstruct_full(target, scope)
    supplements = g37.reconstruct_supplements(target, scope)
    g36_full = g37.reconstruct_g36_full()
    g36_supplements = g37.reconstruct_g36_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 22, 157, 151):
        errors.append(f"G37 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (157, 0, 0, 0):
        errors.append("G37 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31:
        errors.append("G37 documented complete-English fallback count must remain 31")

    for locale, values in full.items():
        old = g36_full.get(locale)
        if old is None:
            errors.append(f"{locale}: inherited G37 full locale is absent from G36")
            continue
        if values != old:
            errors.append(f"{locale}: G37 full resource differs from exact G36 resource despite unchanged English semantics")
        if set(values) != set(target):
            errors.append(f"{locale}: full G37 key set differs from target")
            continue
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G37 target English")

    for locale, values in supplements.items():
        upstream = g37.fetch_upstream_json(g37.G37_COMMIT, locale)
        missing = normal - set(upstream)
        old = g36_supplements.get(locale)
        if old is None:
            errors.append(f"{locale}: inherited G37 supplement is absent from G36")
            continue
        if values != old:
            errors.append(f"{locale}: G37 supplement differs from exact G36 supplement despite unchanged English/upstream semantics")
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g37.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 151 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us"}:
        errors.append(f"G37 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g37.fetch_upstream_json(g37.G37_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G37")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G37 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 90:
        errors.append("G37 ownership partitions do not cover exactly 90 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.20.6-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g37.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G37 full output file set differs from frozen ownership")
        if supplement_count != 22 or len(supplement_files) != 22 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G37 supplement output file set differs from frozen ownership")
        if key_count != 157:
            errors.append("G37 output key count must be 157")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.20.6 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 18.0.0 / Minecraft 1.20.6 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Translated/AI-assisted full locales: 36")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 22")
    print("Keys per complete addon locale: 157")
    print("All G36 full and supplement translation values are inherited exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

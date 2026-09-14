#!/usr/bin/env python3
"""Validate complete G38 Minecraft 1.21 / JEI 19.8.2 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21 as g38
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g38.parse_json(g38.BASE_SOURCE)
    target = g38.parse_json(g38.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g38.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g38.semantic_sets(base, target)
    changed_or_added = added | changed
    scope = json.loads(g38.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g38.reconstruct_full(target, scope)
    supplements = g38.reconstruct_supplements(target, scope)
    g37_full = g38.reconstruct_g37_full()
    delta = g38.reviewed_delta()

    if (len(full), len(supplements), len(target), len(normal)) != (67, 21, 176, 170):
        errors.append(f"G38 counts changed: full={len(full)} supplements={len(supplements)} target={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 19, 0, 1):
        errors.append("G38 semantic partition changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31:
        errors.append("G38 documented complete-English fallback count must remain 31")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G38 key set differs from target")
            continue
        old = g37_full.get(locale)
        if old is None:
            errors.append(f"{locale}: inherited G38 full locale is absent from G37")
            continue
        for key, value in values.items():
            if key in unchanged:
                if value != old.get(key):
                    errors.append(f"{locale}: unchanged G38 full value differs from exact G37 value for {key}")
            elif key in changed_or_added:
                expected = target[key] if locale in fallback_locales else delta.get(locale, {}).get(key, target[key])
                if value != expected:
                    errors.append(f"{locale}: reviewed G38 semantic value differs for {key}")
            else:
                errors.append(f"{locale}: unexpected G38 semantic key {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact G38 target English")

    for locale, values in supplements.items():
        upstream = g38.fetch_upstream_json(g38.G38_COMMIT, locale)
        missing = normal - set(upstream)
        previous_complete = g38.g37_combined_locale(locale)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g38.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        for key, value in values.items():
            if key in unchanged:
                if value != previous_complete.get(key):
                    errors.append(f"{locale}: unchanged G38 supplement differs from exact G37 combined value for {key}")
            elif key in changed_or_added:
                expected = delta.get(locale, {}).get(key, target[key])
                if value != expected:
                    errors.append(f"{locale}: new/changed G38 supplement value differs from reviewed/fallback policy for {key}")
            else:
                errors.append(f"{locale}: supplement contains unexpected non-inherited key {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 170 normal target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us", "ja_jp"}:
        errors.append(f"G38 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g38.fetch_upstream_json(g38.G38_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G38")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G38 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 90:
        errors.append("G38 ownership partitions do not cover exactly 90 selected languages")
    if "ja_jp" in supplement_set or "ja_jp" not in complete_set:
        errors.append("G38 ja_jp supplement retirement was not applied")

    with tempfile.TemporaryDirectory(prefix="jei-1.21-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g38.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 67 or len(full_files) != 67 or {p.stem for p in full_files} != full_set:
            errors.append("G38 full output file set differs from frozen ownership")
        if supplement_count != 21 or len(supplement_files) != 21 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G38 supplement output file set differs from frozen ownership")
        if key_count != 176:
            errors.append("G38 output key count must be 176")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.21 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 19.8.2 / Minecraft 1.21 complete JSON translation QA")
    print("Complete addon locales: 67")
    print("Translated/AI-assisted full locales: 36")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 21")
    print("Keys per complete addon locale: 176")
    print("156 G37 meanings inherit exactly; 20 G38 new/changed meanings use reviewed translations or explicit English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

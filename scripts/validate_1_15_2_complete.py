#!/usr/bin/env python3
"""Validate complete G18 Minecraft 1.15.2 / JEI 6.0.2 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_15_2 as g18
import validate_1_14_2_complete as g14qa


def main() -> int:
    errors: list[str] = []
    base = g18.parse_json(g18.BASE_SOURCE)
    target = g18.parse_json(g18.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g18.DEBUG_PREFIX)}
    scope = json.loads(g18.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g18.reconstruct_full(target, scope)
    supplements = g18.reconstruct_supplements(target, scope)
    g17_full = g18.reconstruct_g17_full()
    g17_supplements = g18.reconstruct_g17_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (66, 18, 110, 107):
        errors.append(
            f"G18 counts changed: full={len(full)} supplements={len(supplements)} "
            f"target={len(target)} normal={len(normal)}"
        )
    if set(full) != set(g17_full):
        errors.append("G18 addon-full locale set must exactly match G17")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G18 must retain 27 documented complete-English fallback locales")
    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G18 key set differs from target")
            continue
        for key, old_value in g17_full[locale].items():
            if values.get(key) != old_value:
                errors.append(f"{locale}: G18 changed inherited G17 value for {key}")
        if values.get(g18.NEW_KEY) != target[g18.NEW_KEY]:
            errors.append(f"{locale}: new Stonecutting key is not exact target English")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact target English")
        for key, value in values.items():
            g14qa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g18.fetch_upstream_json(g18.G18_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g18.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g17 = g18.g17_combined_locale(locale, g17_full, g17_supplements)
        for key, value in values.items():
            if key in base:
                if value != combined_g17[key]:
                    errors.append(f"{locale}: G18 supplement changed inherited G17 value for {key}")
            elif key == g18.NEW_KEY:
                if value != target[g18.NEW_KEY]:
                    errors.append(f"{locale}: project-owned Stonecutting key must use exact target English")
            else:
                errors.append(f"{locale}: unexpected G18-only supplement key {key}")
            g14qa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 107 normal target keys")

    for locale in ("de_de", "pt_br", "ru_ru"):
        if supplements.get(locale) != {g18.NEW_KEY: target[g18.NEW_KEY]}:
            errors.append(f"{locale}: expected a one-key Stonecutting supplement")
    if "ja_jp" in supplements:
        errors.append("ja_jp must not emit a G18 supplement because pinned upstream is complete")

    complete_set = set(scope["selected_upstream_complete_locales"])
    for locale in complete_set:
        upstream = g18.fetch_upstream_json(g18.G18_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G18")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G18 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 87:
        errors.append("G18 ownership partitions do not cover exactly 87 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.15.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g18.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 66 or len(full_files) != 66 or {p.stem for p in full_files} != full_set:
            errors.append("G18 full output file set differs from frozen ownership")
        if supplement_count != 18 or len(supplement_files) != 18 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G18 supplement output file set differs from frozen ownership")
        if key_count != 110:
            errors.append("G18 output key count must be 110")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.15.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 6.0.2 / Minecraft 1.15.2 complete JSON translation QA")
    print("Complete addon locales: 66")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 18")
    print("Keys per complete addon locale: 110")
    print("All 109 G17 semantic values are inherited exactly")
    print("Stonecutting is exact target English wherever project-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

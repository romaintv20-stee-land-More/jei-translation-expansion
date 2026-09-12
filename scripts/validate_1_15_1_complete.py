#!/usr/bin/env python3
"""Validate complete G17 Minecraft 1.15.1 / JEI 6.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_15_1 as g17
import validate_1_14_2_complete as g14qa


def main() -> int:
    errors: list[str] = []
    target = g17.parse_json(g17.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g17.DEBUG_PREFIX)}
    scope = json.loads(g17.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g17.reconstruct_full(target, scope)
    supplements = g17.reconstruct_supplements(target, scope)
    g16_full = g17.reconstruct_g16_full()
    g16_supplements = g17.reconstruct_g16_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (66, 16, 109, 106):
        errors.append(
            f"G17 counts changed: full={len(full)} supplements={len(supplements)} "
            f"target={len(target)} normal={len(normal)}"
        )

    inherited_expected = set(g16_full) - g17.REMOVED_G16_FULL
    if set(full) - g17.NEW_G17_FULL != inherited_expected:
        errors.append("G17 inherited full locale set is not G16 minus removed Minecraft codes")
    for locale in inherited_expected:
        if full[locale] != g16_full[locale]:
            errors.append(f"{locale}: G17 full resource is not exact G16 inheritance")
    if full.get("lmo") != target:
        errors.append("lmo must use exact target-English complete fallback")
    if g17.REMOVED_G16_FULL & set(full):
        errors.append("G17 emits a full locale removed from the Minecraft 1.15.1 catalog")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27:
        errors.append("G17 must have 27 documented complete-English fallback locales")
    if "lmo" not in fallback_locales:
        errors.append("G17 Lombard must be documented as a complete-English fallback")
    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G17 key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact target English")
        for key, value in values.items():
            g14qa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g17.fetch_upstream_json(g17.G17_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g17.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g16 = g17.g16_combined_locale(locale, g16_full, g16_supplements)
        for key, value in values.items():
            if value != combined_g16[key]:
                errors.append(f"{locale}: G17 supplement does not exactly inherit G16 combined value for {key}")
            g14qa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 106 normal target keys")

    sv_newly_missing = {
        "gui.jei.category.blasting", "gui.jei.category.campfire", "gui.jei.category.smoking"
    }
    if not sv_newly_missing <= set(supplements.get("sv_se", {})):
        errors.append("sv_se supplement is missing one of the three G17 upstream-regressed category keys")
    g16_sv_upstream = g17.g16.fetch_upstream_json(g17.g16.G16_COMMIT, "sv_se")
    for key in sv_newly_missing:
        if supplements.get("sv_se", {}).get(key) != g16_sv_upstream.get(key):
            errors.append(f"sv_se: failed to preserve pinned G16 upstream translation for {key}")

    for locale in ("de_de", "en_us", "pl_pl", "pt_br", "ru_ru"):
        upstream = g17.fetch_upstream_json(g17.G17_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G17")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G17 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 87:
        errors.append("G17 ownership partitions do not cover exactly 87 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.15.1-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g17.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 66 or len(full_files) != 66 or {p.stem for p in full_files} != full_set:
            errors.append("G17 full output file set differs from frozen ownership")
        if supplement_count != 16 or len(supplement_files) != 16 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G17 supplement output file set differs from frozen ownership")
        if key_count != 109:
            errors.append("G17 output key count must be 109")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.15.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 6.0.0 / Minecraft 1.15.1 complete JSON translation QA")
    print("Complete addon locales: 66")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 5")
    print("Missing-key-only upstream supplements: 16")
    print("Keys per complete addon locale: 109")
    print("All 109 G16 semantic values are inherited exactly")
    print("Lombard fallback and Swedish upstream-regression recovery are validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

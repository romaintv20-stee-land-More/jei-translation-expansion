#!/usr/bin/env python3
"""Validate complete G15 Minecraft 1.14.3 / JEI 6.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_14_3 as g15
import validate_1_14_2_complete as g14qa


def main() -> int:
    errors: list[str] = []
    target = g15.parse_json(g15.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g15.DEBUG_PREFIX)}
    scope = json.loads(g15.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g15.reconstruct_full(target, scope)
    supplements = g15.reconstruct_supplements(target, scope)
    g14_full = g15.reconstruct_g14_full()
    g14_supplements = g15.reconstruct_g14_supplements()

    if (len(full), len(supplements), len(target), len(normal)) != (70, 18, 109, 106):
        errors.append(
            f"G15 counts changed: full={len(full)} supplements={len(supplements)} "
            f"target={len(target)} normal={len(normal)}"
        )
    if full != g14_full:
        errors.append("G15 addon-full resources must be exact G14 reconstruction inheritance")
    if "pt_br" in supplements:
        errors.append("G15 must not emit a pt_br supplement")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31:
        errors.append("G15 must retain 31 documented complete-English fallback locales")
    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G15 key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete-English fallback is not exact target English")
        for key, value in values.items():
            g14qa.validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g15.fetch_upstream_json(g15.G15_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g15.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: supplement contains debug-only key")
        combined_g14 = g15.g14_combined_locale(locale, g14_full, g14_supplements)
        for key, value in values.items():
            if value != combined_g14[key]:
                errors.append(f"{locale}: G15 supplement does not exactly inherit G14 value for {key}")
            g14qa.validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 106 normal target keys")

    pt_br_upstream = g15.fetch_upstream_json(g15.G15_COMMIT, "pt_br")
    if normal - set(pt_br_upstream):
        errors.append("pt_br is expected to be complete upstream in G15")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G15 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 91:
        errors.append("G15 ownership partitions do not cover exactly 91 selected languages")

    with tempfile.TemporaryDirectory(prefix="jei-1.14.3-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g15.reconstruct_all(output)
        full_files = sorted((output / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplement_files = sorted((output / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if full_count != 70 or len(full_files) != 70 or {p.stem for p in full_files} != full_set:
            errors.append("G15 full output file set differs from frozen ownership")
        if supplement_count != 18 or len(supplement_files) != 18 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G15 supplement output file set differs from frozen ownership")
        if key_count != 109:
            errors.append("G15 output key count must be 109")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.14.3 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: JEI 6.0.0 / Minecraft 1.14.3 complete JSON translation QA")
    print("Complete addon locales: 70")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 3")
    print("Missing-key-only upstream supplements: 18")
    print("Keys per complete addon locale: 109")
    print("All 109 G14 semantic values are inherited exactly")
    print("pt_br ownership migration to complete upstream is validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

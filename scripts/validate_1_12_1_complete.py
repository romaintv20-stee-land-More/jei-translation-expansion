#!/usr/bin/env python3
"""Validate complete G10 Minecraft 1.12.1 / JEI 4.7.8 reconstructed resources."""
from __future__ import annotations

import json

import reconstruct_1_12_1 as g10


def main() -> int:
    errors: list[str] = []
    target = g10.parse_lang(g10.TARGET_SOURCE)
    scope = json.loads(g10.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g10.reconstruct_full(target, scope)
    supplements = g10.reconstruct_supplements(target, scope)
    g9_full = g10.reconstruct_g9_full()
    g9_supplements = g10.reconstruct_g9_supplements()

    if (len(full), len(supplements), len(target)) != (60, 18, 93):
        errors.append(f"G10 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")
    if full != g9_full:
        errors.append("G10 full addon resources differ from exact G9 reconstruction")
    if supplements != g9_supplements:
        errors.append("G10 supplements differ from exact G9 reconstruction")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: G10 full file key set differs from target")
    for locale, values in supplements.items():
        if not set(values) <= set(target):
            errors.append(f"{locale}: G10 supplement contains key absent from target")
        if any(key.startswith(g10.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: G10 supplement contains debug-only key")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G10 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 80:
        errors.append("G10 emitted ownership partitions do not cover exactly 80 selected languages")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.12.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 4.7.8 / Minecraft 1.12.1 complete translation QA")
    print("Complete addon locales: 60")
    print("Inherited translated/AI-assisted full locales: 40")
    print("Documented complete English fallbacks: 20")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 18")
    print("Keys per complete addon locale: 93")
    print("New G10 semantic translations authored: 0")
    print("All G10 emitted resources are exact G9 reconstruction inheritance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate complete G9 Minecraft 1.12 / JEI 4.7.5 reconstructed resources."""
from __future__ import annotations

import json

import reconstruct_1_12 as g9


def main() -> int:
    errors: list[str] = []
    target = g9.parse_lang(g9.TARGET_SOURCE)
    scope = json.loads(g9.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g9.reconstruct_full(target, scope)
    supplements = g9.reconstruct_supplements(target, scope)
    g8_full = g9.reconstruct_g8_full()
    g8_supplements = g9.reconstruct_g8_supplements()

    if (len(full), len(supplements), len(target)) != (60, 18, 93):
        errors.append(f"G9 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full file key set differs from target")
        if locale in g9.NEW_SELECTED:
            if values != target:
                errors.append(f"{locale}: new G9 documented fallback must equal exact target English")
        else:
            if locale not in g8_full or values != g8_full[locale]:
                errors.append(f"{locale}: inherited G9 full locale differs from exact G8 reconstruction")

    expected_supplements = set(scope["selected_upstream_incomplete_locales"])
    if set(supplements) != expected_supplements:
        errors.append("G9 supplement locale set differs from frozen scope")
    if "ja_jp" in supplements:
        errors.append("ja_jp must emit no G9 supplement because JEI 4.7.5 is complete")

    recovery = g9.parse_lang(g9.SV_RECOVERY_PATH)
    expected_sv = dict(g8_supplements["sv_se"])
    expected_sv.update(recovery)
    if supplements.get("sv_se") != expected_sv:
        errors.append("sv_se G9 supplement is not exact G8 supplement + four recovered upstream translations")

    for locale, values in supplements.items():
        if locale != "sv_se":
            if locale not in g8_supplements:
                errors.append(f"{locale}: G9 supplement has no G8 inheritance source")
            elif values != g8_supplements[locale]:
                errors.append(f"{locale}: unchanged G9 supplement differs from exact G8 project values")
        if set(values) & {key for key in target if key.startswith(g9.DEBUG_PREFIX)}:
            errors.append(f"{locale}: supplement contains debug-only key")
        if not set(values) <= set(target):
            errors.append(f"{locale}: supplement contains key absent from target")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G9 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 80:
        errors.append("G9 emitted ownership partitions do not cover exactly 80 selected languages")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.12 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 4.7.5 / Minecraft 1.12 complete translation QA")
    print("Complete addon locales: 60")
    print("Inherited translated/AI-assisted full locales: 40")
    print("Documented complete English fallbacks: 20")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 18")
    print("Keys per complete addon locale: 93")
    print("New G9 semantic translations authored: 0")
    print("Swedish dropped upstream translations recovered exactly from pinned G8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

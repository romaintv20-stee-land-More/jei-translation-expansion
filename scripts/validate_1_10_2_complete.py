#!/usr/bin/env python3
"""Validate reconstructed JEI 3.14.8 / Minecraft 1.10.2 addon resources."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import reconstruct_1_10_2 as g6

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "translations" / "g6-mc1.10.2" / "policy.json"
DEBUG_PREFIX = "description.jei."
PLACEHOLDER_RE = re.compile(r"%(?:CTRL|MODNAME|,d|s)")
TECHNICAL_TOKENS = (
    "JEI",
    "Minecraft",
    "/give",
    "modId[:name[:meta]]",
    "ItemStack",
    "ModId",
    "mB",
)


def placeholders(value: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(value))


def validate_value(locale: str, key: str, english: str, translated: str, errors: list[str]) -> None:
    if placeholders(english) != placeholders(translated):
        errors.append(
            f"{locale}: placeholder mismatch in {key}: "
            f"{placeholders(english)} != {placeholders(translated)}"
        )
    for token in TECHNICAL_TOKENS:
        if token in english and token not in translated:
            errors.append(f"{locale}: missing technical token {token!r} in {key}")
    if key.startswith(DEBUG_PREFIX) and translated != english:
        errors.append(f"{locale}: debug-only key must remain English: {key}")


def main() -> int:
    errors: list[str] = []
    english = g6.parse_lang(g6.TARGET_SOURCE)
    base = g6.parse_lang(g6.BASE_SOURCE)
    scope = json.loads(g6.SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g6.AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    _, _, _, unchanged = g6.source_sets(base, english)
    fallback_review = set(policy["conservative_review_fallback_keys"])
    full_fallback_locales = set(policy["documented_full_english_fallback_locales"])
    normal_keys = {key for key in english if not key.startswith(DEBUG_PREFIX)}

    g5_full = g6.reconstruct_g5_full()
    g4_full = g6.reconstruct_g4_full()

    with tempfile.TemporaryDirectory(prefix="jei-1.10.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g6.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"

        full_files = sorted(full_dir.glob("*.lang"))
        full_locales = {path.stem for path in full_files}
        expected_full_locales = set(scope["addon_full_locales"])
        if full_count != 52 or len(full_files) != 52 or full_locales != expected_full_locales:
            errors.append("G6 full output must contain exactly the 52 addon-owned locales")
        if key_count != 87 or len(english) != 87:
            errors.append("G6 complete target must contain exactly 87 keys")

        for path in full_files:
            locale = path.stem
            values = g6.parse_lang(path)
            if set(values) != set(english):
                errors.append(f"{locale}: complete G6 key set mismatch")
                continue
            for key in english:
                validate_value(locale, key, english[key], values[key], errors)

            if locale in full_fallback_locales:
                if values != english:
                    errors.append(f"{locale}: documented full-English fallback is not exactly English")
                continue

            for key in unchanged:
                if values[key] != g5_full[locale][key]:
                    errors.append(f"{locale}: unchanged key not reused exactly from G5: {key}")
            if locale in g4_full:
                if values[g6.CRAFTING_KEY] != g4_full[locale][g6.CRAFTING_KEY]:
                    errors.append(f"{locale}: Crafting semantic reversion not restored from G4")
            else:
                if values[g6.CRAFTING_KEY] != english[g6.CRAFTING_KEY]:
                    errors.append(f"{locale}: Crafting fallback differs from target English")
            for key in fallback_review:
                if values[key] != english[key]:
                    errors.append(f"{locale}: conservative G6 fallback key is not exact target English: {key}")

        supplement_files = sorted(supplement_dir.glob("*.lang"))
        supplement_locales = {path.stem for path in supplement_files}
        expected_supplement_locales = set(scope["selected_upstream_incomplete_locales"])
        if supplement_count != 16 or len(supplement_files) != 16 or supplement_locales != expected_supplement_locales:
            errors.append("G6 supplement output must contain exactly the 16 selected incomplete upstream locales")

        expected_supplements = g6.reconstruct_supplements(english, scope, audit)
        for path in supplement_files:
            locale = path.stem
            values = g6.parse_lang(path)
            expected_missing = set(audit["selected_upstream_locale_completeness"][locale]["missing_normal_keys"])
            if set(values) != expected_missing:
                errors.append(f"{locale}: supplement key set is not exact audited missing set")
            if values != expected_supplements[locale]:
                errors.append(f"{locale}: supplement differs from deterministic G6 reconstruction")
            for key, translated in values.items():
                validate_value(locale, key, english[key], translated, errors)
                if key in fallback_review and translated != english[key]:
                    errors.append(f"{locale}: reviewed missing key should use exact English fallback: {key}")

        # No addon resource may be produced for a complete upstream selected locale.
        for locale in scope["selected_upstream_complete_locales"]:
            if (full_dir / f"{locale}.lang").exists() or (supplement_dir / f"{locale}.lang").exists():
                errors.append(f"{locale}: addon must emit nothing because JEI upstream is complete")

    if len(normal_keys) != 84:
        errors.append("G6 normal key count must be 84")
    if len(full_fallback_locales) != 12:
        errors.append("G6 documented full fallback locale count must be 12")
    if len(fallback_review) != 33:
        errors.append("G6 conservative review fallback key count must be 33")
    if policy["translated_or_ai_assisted_full_locale_count"] != 40:
        errors.append("G6 translated/AI-assisted full locale count must be 40")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.10.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 3.14.8 / Minecraft 1.10.2 complete translation QA")
    print("Complete addon locales: 52")
    print("Selected complete upstream locales: 4")
    print("Missing-key-only upstream supplements: 16")
    print("Keys per complete addon locale: 87")
    print("Documented full-English fallback locales: 12")
    print("Inherited translated/AI-assisted full locales: 40")
    print("Conservative G6 added/changed fallback keys: 33")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

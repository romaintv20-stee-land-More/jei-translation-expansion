#!/usr/bin/env python3
"""Validate reconstructed JEI 4.1.1 / Minecraft 1.11 addon resources."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import reconstruct_1_10_2 as g6
import reconstruct_1_11 as g7

ROOT = Path(__file__).resolve().parents[1]
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
    english = g7.parse_lang(g7.TARGET_SOURCE)
    scope = json.loads(g7.SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g7.AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g7.POLICY_PATH.read_text(encoding="utf-8"))
    normal_keys = {key for key in english if not key.startswith(DEBUG_PREFIX)}

    if g7.parse_lang(g7.BASE_SOURCE) != english:
        errors.append("G7 target English is not exactly identical to G6 base English")

    g6_full = g7.reconstruct_g6_full()
    g6_full_lookup = g7.lower_lookup(set(g6_full))
    g6_supplements = g7.reconstruct_g6_supplements()
    g6_supp_lookup = g7.lower_lookup(set(g6_supplements))
    persistent = set(audit["persistent_incomplete_locales_from_g6"])
    de_expected = set(
        audit["ownership_changes_from_g6"]["became_incomplete"]["de_de"]["missing_normal_keys"]
    )

    with tempfile.TemporaryDirectory(prefix="jei-1.11-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g7.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"

        full_files = sorted(full_dir.glob("*.lang"))
        full_locales = {path.stem for path in full_files}
        expected_full = set(scope["addon_full_locales"])
        if full_count != 52 or len(full_files) != 52 or full_locales != expected_full:
            errors.append("G7 full output must contain exactly the 52 addon-owned locales")
        if key_count != 87 or len(english) != 87 or len(normal_keys) != 84:
            errors.append("G7 target must contain 87 keys / 84 normal keys")

        for path in full_files:
            locale = path.stem
            if path.name != path.name.lower():
                errors.append(f"{path.name}: G7 full output filename must be lowercase")
            values = g7.parse_lang(path)
            if set(values) != set(english):
                errors.append(f"{locale}: complete G7 key set mismatch")
                continue
            if locale not in g6_full_lookup:
                errors.append(f"{locale}: no G6 full locale available for exact inheritance")
            elif values != g6_full[g6_full_lookup[locale]]:
                errors.append(f"{locale}: G7 full values are not exact G6 inheritance")
            for key in english:
                validate_value(locale, key, english[key], values[key], errors)

        supplement_files = sorted(supplement_dir.glob("*.lang"))
        supplement_locales = {path.stem for path in supplement_files}
        expected_supplements = set(scope["selected_upstream_incomplete_locales"])
        if supplement_count != 16 or len(supplement_files) != 16 or supplement_locales != expected_supplements:
            errors.append("G7 supplement output must contain exactly the 16 selected incomplete upstream locales")

        reconstructed = g7.reconstruct_supplements(english, scope, audit)
        for path in supplement_files:
            locale = path.stem
            if path.name != path.name.lower():
                errors.append(f"{path.name}: G7 supplement filename must be lowercase")
            values = g7.parse_lang(path)
            if values != reconstructed[locale]:
                errors.append(f"{locale}: supplement differs from deterministic G7 reconstruction")
            if locale in persistent:
                if locale not in g6_supp_lookup:
                    errors.append(f"{locale}: persistent supplement missing from G6")
                elif values != g6_supplements[g6_supp_lookup[locale]]:
                    errors.append(f"{locale}: persistent supplement is not exact G6 inheritance")
            elif locale == "de_de":
                if set(values) != de_expected:
                    errors.append("de_de: supplement is not the exact 16-key G7 missing set")
                if values != g7.parse_lang(g7.DE_REUSE_PATH):
                    errors.append("de_de: supplement differs from preserved pinned G6 upstream translations")
            else:
                errors.append(f"{locale}: unexpected non-persistent G7 supplement")

            for key, translated in values.items():
                validate_value(locale, key, english[key], translated, errors)
                if key.startswith(DEBUG_PREFIX):
                    errors.append(f"{locale}: supplement must never contain debug-only key {key}")

        # Complete upstream selected locales must receive no addon resource.
        for locale in scope["selected_upstream_complete_locales"]:
            if (full_dir / f"{locale}.lang").exists() or (supplement_dir / f"{locale}.lang").exists():
                errors.append(f"{locale}: addon must emit nothing because JEI upstream is complete")

        if (supplement_dir / "sv_se.lang").exists():
            errors.append("sv_se: retired G6 supplement must not be emitted in G7")
        if not (supplement_dir / "de_de.lang").exists():
            errors.append("de_de: new G7 supplement was not emitted")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 12:
        errors.append("G7 documented full-English fallback locale count must remain 12")
    if policy["new_translation_entries_required"] != 0:
        errors.append("G7 must require zero new semantic translation entries")
    if policy["upstream_complete_selected_locales"] != ["en_us", "ru_ru", "sv_se", "uk_ua"]:
        errors.append("G7 policy complete-upstream locale list changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.11 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 4.1.1 / Minecraft 1.11 complete translation QA")
    print("Complete addon locales: 52")
    print("Selected complete upstream locales: 4")
    print("Missing-key-only upstream supplements: 16")
    print("Keys per complete addon locale: 87")
    print("New semantic translations authored in G7: 0")
    print("Ownership migration: de_de supplement added; sv_se supplement retired")
    print("All emitted locale filenames are lowercase")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

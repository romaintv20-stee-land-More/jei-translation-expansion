#!/usr/bin/env python3
"""Validate complete reconstructed JEI 3.3.3 / Minecraft 1.9 addon resources."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import reconstruct_1_9 as g3

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream" / "sources" / "1.9" / "en_US.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.9-language-scope.json"
NEW_POLICY_PATH = ROOT / "translations" / "g3-mc1.9" / "new-full-policy.json"
DEBUG_PREFIX = "description.jei."
PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|(?:\d+\$)?[,]?[a-zA-Z])")
TECHNICAL_TOKENS = (
    "JEI",
    "Minecraft",
    "modId[:name[:meta]]",
    "ItemStack",
    "ModId",
    "mB",
    "Ctrl",
    "Shift",
    "XP",
)
INHERITED_FALLBACKS = {"gv_IM", "kw_GB", "se_NO"}


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
    english = g3.parse_lang(SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(NEW_POLICY_PATH.read_text(encoding="utf-8"))
    new_fallbacks = set(policy["documented_english_fallback_locales"])
    documented_fallbacks = INHERITED_FALLBACKS | new_fallbacks
    normal_keys = [key for key in english if not key.startswith(DEBUG_PREFIX)]

    with tempfile.TemporaryDirectory(prefix="jei-1.9-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g3.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"

        full_files = sorted(full_dir.glob("*.lang"))
        if full_count != scope["addon_full_locale_count"] or len(full_files) != full_count:
            errors.append("full addon locale count mismatch")
        if key_count != len(english):
            errors.append("reconstructed full key count mismatch")

        for path in full_files:
            locale = path.stem
            translated = g3.parse_lang(path)
            if set(translated) != set(english):
                errors.append(f"{locale}: complete key set mismatch")
                continue
            for key in english:
                validate_value(locale, key, english[key], translated[key], errors)

            english_equal = sum(translated[key] == english[key] for key in normal_keys)
            if locale in documented_fallbacks:
                if english_equal != len(normal_keys):
                    errors.append(f"{locale}: documented English fallback is not fully English")
            elif english_equal == len(normal_keys):
                errors.append(f"{locale}: unexpected full English fallback")

        supplement_files = sorted(supplement_dir.glob("*.lang"))
        if supplement_count != scope["upstream_missing_key_supplement_locale_count"]:
            errors.append("supplement locale count mismatch")
        if len(supplement_files) != supplement_count:
            errors.append("supplement output file count mismatch")

        for path in supplement_files:
            locale = path.stem
            values = g3.parse_lang(path)
            for key, translated in values.items():
                if key not in english:
                    errors.append(f"{locale}: supplement contains unknown key {key}")
                    continue
                if key.startswith(DEBUG_PREFIX):
                    errors.append(f"{locale}: supplement unexpectedly contains debug key {key}")
                validate_value(locale, key, english[key], translated, errors)

    expected_new_files = set(policy["translated_ai_assisted_locales"])
    actual_new_files = {path.stem for path in g3.NEW_FULL_DIR.glob("*.lang")}
    if actual_new_files != expected_new_files:
        errors.append(
            f"new translated source file set mismatch: expected={sorted(expected_new_files)}, "
            f"actual={sorted(actual_new_files)}"
        )

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.9 validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    translated_full_count = scope["addon_full_locale_count"] - len(documented_fallbacks)
    print("PASS: JEI 3.3.3 / Minecraft 1.9 complete translation QA")
    print(f"Complete addon locales: {scope['addon_full_locale_count']}")
    print(f"Translated/AI-assisted complete locales: {translated_full_count}")
    print(f"Documented complete English fallbacks: {len(documented_fallbacks)}")
    print(f"Missing-key-only upstream supplements: {scope['upstream_missing_key_supplement_locale_count']}")
    print(f"Complete keys per full locale: {len(english)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

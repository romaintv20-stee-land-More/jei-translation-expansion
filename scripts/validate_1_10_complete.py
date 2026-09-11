#!/usr/bin/env python3
"""Validate complete reconstructed JEI 3.7.1 / Minecraft 1.10 addon resources."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import reconstruct_1_10 as g5

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "translations" / "g5-mc1.10" / "policy.json"
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
    "XP",
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
    english = g5.parse_lang(g5.TARGET_SOURCE)
    scope = json.loads(g5.G5_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g5.G5_AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    fallback_locales = set(policy["documented_full_english_fallback_locales"])
    normal_keys = [key for key in english if not key.startswith(DEBUG_PREFIX)]

    with tempfile.TemporaryDirectory(prefix="jei-1.10-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g5.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"

        full_files = sorted(full_dir.glob("*.lang"))
        if full_count != scope["addon_full_locale_count"] or len(full_files) != full_count:
            errors.append("full addon locale count mismatch")
        if key_count != len(english):
            errors.append("reconstructed full key count mismatch")

        g3_full = g5.reconstruct_g3_full()
        for path in full_files:
            locale = path.stem
            translated = g5.parse_lang(path)
            if set(translated) != set(english):
                errors.append(f"{locale}: complete key set mismatch")
                continue
            for key in english:
                validate_value(locale, key, english[key], translated[key], errors)

            english_equal = sum(translated[key] == english[key] for key in normal_keys)
            if locale in fallback_locales:
                if english_equal != len(normal_keys):
                    errors.append(f"{locale}: documented English fallback is not fully English")
            elif english_equal == len(normal_keys):
                errors.append(f"{locale}: unexpected full English fallback")

            if translated[g5.CRAFTING_KEY] != g3_full[locale][g5.CRAFTING_KEY]:
                errors.append(f"{locale}: craftingTable value was not restored exactly from G3")
            for removed in g5.REMOVED_KEYS:
                if removed in translated:
                    errors.append(f"{locale}: removed G4 key leaked into G5 output: {removed}")

        expected_supplement_locales = set(scope["upstream_missing_key_supplement_locales"])
        supplement_files = sorted(supplement_dir.glob("*.lang"))
        actual_supplement_locales = {path.stem for path in supplement_files}
        if supplement_count != scope["upstream_missing_key_supplement_locale_count"]:
            errors.append("supplement locale count mismatch")
        if actual_supplement_locales != expected_supplement_locales:
            errors.append(
                f"supplement file set mismatch: expected={sorted(expected_supplement_locales)}, "
                f"actual={sorted(actual_supplement_locales)}"
            )

        expected_supplements = g5.reconstruct_supplements(english, scope, audit)
        for path in supplement_files:
            locale = path.stem
            values = g5.parse_lang(path)
            if values != expected_supplements[locale]:
                errors.append(f"{locale}: supplement output differs from deterministic reconstruction")
            audited_count = audit["jei_upstream_locale_completeness"][locale]["missing_normal"]
            if len(values) != audited_count:
                errors.append(
                    f"{locale}: supplement has {len(values)} keys, audited missing count is {audited_count}"
                )
            for key, translated in values.items():
                if key not in english:
                    errors.append(f"{locale}: supplement contains unknown key {key}")
                    continue
                if key.startswith(DEBUG_PREFIX):
                    errors.append(f"{locale}: supplement unexpectedly contains debug key {key}")
                if key in g5.REMOVED_KEYS:
                    errors.append(f"{locale}: removed G4 key leaked into supplement: {key}")
                validate_value(locale, key, english[key], translated, errors)

        ko = g5.parse_lang(supplement_dir / "ko_KR.lang")
        if ko.get(g5.CRAFTING_KEY) != "제작대":
            errors.append("ko_KR: Crafting Table translation was not restored to G3 제작대")
        ru = g5.parse_lang(supplement_dir / "ru_RU.lang")
        expected_ru = {
            "config.jei.advanced.colorSearchEnabled",
            "config.jei.advanced.colorSearchEnabled.comment",
        }
        if set(ru) != expected_ru:
            errors.append("ru_RU: supplement is not the exact two-key color-search set")
        for locale in ("fr_FR", "zh_CN"):
            values = g5.parse_lang(supplement_dir / f"{locale}.lang")
            if set(values) != {"jei.tooltip.cheat.mode"}:
                errors.append(f"{locale}: supplement must contain only jei.tooltip.cheat.mode")

    if len(english) != 78 or len(normal_keys) != 75:
        errors.append("G5 target key counts changed unexpectedly")
    if len(fallback_locales) != 10:
        errors.append("G5 fallback locale count changed unexpectedly")
    if policy["new_translation_entries_required"] != 0:
        errors.append("G5 policy unexpectedly declares new translation work")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.10 validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 3.7.1 / Minecraft 1.10 complete translation QA")
    print(f"Complete addon locales: {scope['addon_full_locale_count']}")
    print(f"Translated/AI-assisted complete locales: {policy['translated_or_ai_assisted_full_locale_count']}")
    print(f"Documented complete English fallbacks: {policy['full_english_fallback_locale_count']}")
    print(f"Missing-key-only upstream supplements: {scope['upstream_missing_key_supplement_locale_count']}")
    print(f"Complete keys per full locale: {len(english)}")
    print("New translation entries authored in G5: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

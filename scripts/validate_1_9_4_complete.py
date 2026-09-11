#!/usr/bin/env python3
"""Validate complete reconstructed JEI 3.6.8 / Minecraft 1.9.4 addon resources."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import reconstruct_1_9_4 as g4

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "translations" / "g4-mc1.9.4" / "policy.json"
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
    english = g4.parse_lang(g4.TARGET_SOURCE)
    scope = json.loads(g4.G4_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g4.G4_AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    fallback_locales = set(policy["documented_full_english_fallback_locales"])
    normal_keys = [key for key in english if not key.startswith(DEBUG_PREFIX)]

    with tempfile.TemporaryDirectory(prefix="jei-1.9.4-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g4.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"

        full_files = sorted(full_dir.glob("*.lang"))
        if full_count != scope["addon_full_locale_count"] or len(full_files) != full_count:
            errors.append("full addon locale count mismatch")
        if key_count != len(english):
            errors.append("reconstructed full key count mismatch")

        for path in full_files:
            locale = path.stem
            translated = g4.parse_lang(path)
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

        # Recompute exact expected missing-key sets from the versioned inheritance
        # rules, then require supplements to match them exactly. This is the
        # no-upstream-overwrite guard: an upstream-owned key cannot leak into the
        # addon simply because it existed in an older supplement.
        g3_target = g4.parse_lang(g4.BASE_SOURCE)
        g3_scope = json.loads(g4.G3_SCOPE_PATH.read_text(encoding="utf-8"))
        g3_audit = json.loads(g4.G3_AUDIT_PATH.read_text(encoding="utf-8"))
        g3_supplements = g4.g3.reconstruct_supplements(g3_target, g3_scope, g3_audit)
        expected_sets = g4.expected_supplement_key_sets(g3_supplements)

        for path in supplement_files:
            locale = path.stem
            values = g4.parse_lang(path)
            if set(values) != expected_sets[locale]:
                errors.append(
                    f"{locale}: exact supplement key set mismatch: "
                    f"missing={sorted(expected_sets[locale] - set(values))}, "
                    f"extra={sorted(set(values) - expected_sets[locale])}"
                )
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
                validate_value(locale, key, english[key], translated, errors)

        # Regression guards for the two most important G4 ownership transitions.
        ko = g4.parse_lang(supplement_dir / "ko_KR.lang")
        if ko.get("gui.jei.category.craftingTable") != "제작":
            errors.append("ko_KR: Crafting translation was not revised for G4 semantics")
        ru = g4.parse_lang(supplement_dir / "ru_RU.lang")
        if set(ru) != g4.RU_CURRENT_MISSING:
            errors.append("ru_RU: obsolete G3 supplement keys leaked into G4 output")
        zh = g4.parse_lang(supplement_dir / "zh_CN.lang")
        if set(zh) != g4.ZH_CURRENT_MISSING:
            errors.append("zh_CN: obsolete G3 supplement keys leaked into G4 output")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.9.4 validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 3.6.8 / Minecraft 1.9.4 complete translation QA")
    print(f"Complete addon locales: {scope['addon_full_locale_count']}")
    print(f"Translated/AI-assisted complete locales: {policy['translated_or_ai_assisted_full_locale_count']}")
    print(f"Documented complete English fallbacks: {policy['full_english_fallback_locale_count']}")
    print(f"Missing-key-only upstream supplements: {scope['upstream_missing_key_supplement_locale_count']}")
    print(f"Complete keys per full locale: {len(english)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

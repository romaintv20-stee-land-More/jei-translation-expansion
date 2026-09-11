#!/usr/bin/env python3
"""Validate reconstructed JEI 4.5.1 / Minecraft 1.11.2 addon resources."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import reconstruct_1_11 as g7
import reconstruct_1_11_2 as g8

DEBUG_PREFIX = "description.jei."
PLACEHOLDER_RE = re.compile(r"%(?:CTRL|MODNAME|,d|s)")
TECHNICAL_TOKENS = (
    "JEI",
    "Minecraft",
    "/give",
    "modId[:name[:meta]]",
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
    english = g8.parse_lang(g8.TARGET_SOURCE)
    base_english = g8.parse_lang(g8.BASE_SOURCE)
    scope = json.loads(g8.SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g8.AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g8.POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g8.DIFF_PATH.read_text(encoding="utf-8"))
    unchanged = {key for key in set(base_english) & set(english) if base_english[key] == english[key]}
    reviewed = set(diff["reviewed_added_or_changed_keys"])
    removed = set(diff["removed_keys"])
    normal_keys = {key for key in english if not key.startswith(DEBUG_PREFIX)}

    if (len(english), len(normal_keys), len(unchanged), len(reviewed), len(removed)) != (93, 90, 85, 8, 1):
        errors.append("G8 frozen key counts changed before complete QA")

    g7_full = g8.reconstruct_g7_full()
    g7_supplements = g8.reconstruct_g7_supplements()

    with tempfile.TemporaryDirectory(prefix="jei-1.11.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g8.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"

        full_files = sorted(full_dir.glob("*.lang"))
        full_locales = {path.stem for path in full_files}
        expected_full = set(scope["addon_full_locales"])
        if full_count != 52 or len(full_files) != 52 or full_locales != expected_full:
            errors.append("G8 full output must contain exactly the 52 addon-owned locales")
        if key_count != 93:
            errors.append("G8 complete files must contain 93 keys")

        for path in full_files:
            locale = path.stem
            if path.name != path.name.lower():
                errors.append(f"{path.name}: G8 full output filename must be lowercase")
            values = g8.parse_lang(path)
            if set(values) != set(english):
                errors.append(f"{locale}: complete G8 key set mismatch")
                continue
            if locale not in g7_full:
                errors.append(f"{locale}: no G7 full file available for inheritance")
                continue
            old = g7_full[locale]
            for key in english:
                if key.startswith(DEBUG_PREFIX):
                    if values[key] != english[key]:
                        errors.append(f"{locale}: debug key does not equal target English: {key}")
                elif key in unchanged:
                    if values[key] != old[key]:
                        errors.append(f"{locale}: unchanged key was not inherited exactly from G7: {key}")
                elif key in reviewed:
                    if values[key] != english[key]:
                        errors.append(f"{locale}: reviewed G8 key must use target-English fallback: {key}")
                else:
                    errors.append(f"{locale}: target key escaped G8 realization policy: {key}")
                validate_value(locale, key, english[key], values[key], errors)
            for key in removed:
                if key in values:
                    errors.append(f"{locale}: removed G7 key leaked into G8 output: {key}")

        supplement_files = sorted(supplement_dir.glob("*.lang"))
        supplement_locales = {path.stem for path in supplement_files}
        expected_supplements = set(scope["selected_upstream_incomplete_locales"])
        if supplement_count != 19 or len(supplement_files) != 19 or supplement_locales != expected_supplements:
            errors.append("G8 supplement output must contain exactly the 19 incomplete selected upstream locales")

        reconstructed = g8.reconstruct_supplements(english, scope, audit, diff)
        unexpected_old_fallbacks: list[tuple[str, str]] = []
        for path in supplement_files:
            locale = path.stem
            if path.name != path.name.lower():
                errors.append(f"{path.name}: G8 supplement filename must be lowercase")
            values = g8.parse_lang(path)
            expected_missing = set(audit["selected_upstream_locale_completeness"][locale]["missing_normal_keys"])
            if set(values) != expected_missing:
                errors.append(f"{locale}: supplement key set is not exact audited upstream missing set")
            if values != reconstructed[locale]:
                errors.append(f"{locale}: supplement differs from deterministic G8 reconstruction")
            old = g7_supplements.get(locale, {})
            for key, translated in values.items():
                if key in unchanged and key in old:
                    if translated != old[key]:
                        errors.append(f"{locale}: unchanged missing key was not inherited from G7 supplement: {key}")
                elif key in reviewed:
                    if translated != english[key]:
                        errors.append(f"{locale}: missing reviewed G8 key must use target-English fallback: {key}")
                elif key in unchanged:
                    unexpected_old_fallbacks.append((locale, key))
                    if translated != english[key]:
                        errors.append(f"{locale}: ownership-regression fallback must equal target English: {key}")
                else:
                    errors.append(f"{locale}: supplement key escaped G8 realization policy: {key}")
                validate_value(locale, key, english[key], translated, errors)
                if key.startswith(DEBUG_PREFIX):
                    errors.append(f"{locale}: supplement must never contain debug-only key {key}")

        # For this audited endpoint, no unchanged old translation disappears without an existing
        # G7 supplement. This assertion protects against silently losing a translation.
        if unexpected_old_fallbacks:
            errors.append(
                "G8 found unchanged missing keys without reusable G7 supplement values: "
                + ", ".join(f"{locale}:{key}" for locale, key in unexpected_old_fallbacks)
            )

        # en_us is the only selected upstream locale that must receive no addon resource.
        if (full_dir / "en_us.lang").exists() or (supplement_dir / "en_us.lang").exists():
            errors.append("en_us: addon must emit nothing because JEI 4.5.1 is complete upstream")

    if len(scope["documented_full_english_fallback_locales"]) != 12:
        errors.append("G8 documented full-English fallback locale count must remain 12")
    if policy["unchanged_key_and_value_count"] != 85 or len(policy["reviewed_keys"]) != 8:
        errors.append("G8 policy no longer matches exact semantic diff")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.11.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 4.5.1 / Minecraft 1.11.2 complete translation QA")
    print("Complete addon locales: 52")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 93")
    print("G8 reviewed keys using documented project fallback: 8")
    print("All unchanged missing translations are inherited from G7 where project-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate partial supplements for locales already shipped by JEI 1.8.9.

The addon must not overwrite upstream translations unnecessarily. For each official
non-English locale, this validator requires the supplement to contain exactly the
normal target keys missing from JEI's own file. Debug-only keys are excluded.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.8.9" / "en_US.lang"
OFFICIAL_DIR = ROOT / "upstream" / "sources" / "1.8.9" / "official"
SUPPLEMENT_DIR = ROOT / "translations" / "g2-mc1.8.9" / "upstream-supplements"
EXPECTED_LOCALES = {"de_DE", "fi_FI", "ko_KR", "ru_RU", "zh_CN"}
DEBUG_PREFIX = "description.jei."
PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|(?:\d+\$)?[,]?[a-zA-Z])")
TECHNICAL_TOKENS = ("JEI", "Minecraft", "mB", "modId[:name[:meta]]", "ItemStack", "ModId", "Ctrl")
PREFIX_SYMBOLS = ("@", "#", "$", "^")


def parse_lang(path: Path) -> tuple[dict[str, str], list[str]]:
    data: dict[str, str] = {}
    duplicates: list[str] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in raw:
            raise ValueError(f"{path}:{lineno}: non-comment line has no '='")
        key, value = raw.split("=", 1)
        key = key.strip()
        if key in data:
            duplicates.append(key)
        data[key] = value
    return data, duplicates


def placeholders(value: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(value))


def main() -> int:
    errors: list[str] = []
    target, target_dupes = parse_lang(TARGET_SOURCE)
    if target_dupes:
        errors.append(f"target source duplicate keys: {target_dupes}")

    official_files = {p.stem: p for p in OFFICIAL_DIR.glob("*.lang")}
    supplement_files = {p.stem: p for p in SUPPLEMENT_DIR.glob("*.lang")}

    if set(official_files) != EXPECTED_LOCALES:
        errors.append(
            f"official snapshot locale set mismatch: expected={sorted(EXPECTED_LOCALES)} "
            f"found={sorted(official_files)}"
        )
    if set(supplement_files) != EXPECTED_LOCALES:
        errors.append(
            f"supplement locale set mismatch: expected={sorted(EXPECTED_LOCALES)} "
            f"found={sorted(supplement_files)}"
        )

    normal_target_keys = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    coverage: list[tuple[str, int, int, int]] = []

    for locale in sorted(EXPECTED_LOCALES):
        if locale not in official_files or locale not in supplement_files:
            continue
        official, official_dupes = parse_lang(official_files[locale])
        supplement, supplement_dupes = parse_lang(supplement_files[locale])
        if official_dupes:
            errors.append(f"{locale}: duplicate upstream snapshot keys: {official_dupes}")
        if supplement_dupes:
            errors.append(f"{locale}: duplicate supplement keys: {supplement_dupes}")

        official_target_keys = set(official) & set(target)
        expected_missing = normal_target_keys - official_target_keys
        actual = set(supplement)

        overlap = actual & set(official)
        if overlap:
            errors.append(f"{locale}: supplement overrides upstream keys: {', '.join(sorted(overlap))}")

        missing = expected_missing - actual
        extra = actual - expected_missing
        if missing:
            errors.append(f"{locale}: missing supplement keys: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{locale}: unexpected supplement keys: {', '.join(sorted(extra))}")

        for key in sorted(actual & set(target)):
            en = target[key]
            tr = supplement[key]
            if not tr:
                errors.append(f"{locale}: empty supplement translation for {key}")
                continue
            if placeholders(en) != placeholders(tr):
                errors.append(
                    f"{locale}: placeholder mismatch in {key}: "
                    f"{placeholders(en)} != {placeholders(tr)}"
                )
            for token in TECHNICAL_TOKENS:
                if token in en and token not in tr:
                    errors.append(f"{locale}: missing technical token {token!r} in {key}")
            for symbol in PREFIX_SYMBOLS:
                if symbol in en and symbol not in tr:
                    errors.append(f"{locale}: missing prefix symbol {symbol!r} in {key}")
            if key == "config.jei.search.prefixRequiredForCreativeTabSearch" and "%%" not in tr:
                errors.append(f"{locale}: missing literal '%%' marker in {key}")
            if key == "config.jei.search.prefixRequiredForCreativeTabSearch.comment" and "%" not in tr:
                errors.append(f"{locale}: missing literal '%' marker in {key}")

        merged_normal = (official_target_keys & normal_target_keys) | actual
        if merged_normal != normal_target_keys:
            errors.append(f"{locale}: upstream + supplement does not cover all normal target keys")

        coverage.append((locale, len(official_target_keys & normal_target_keys), len(actual), len(normal_target_keys)))

    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 1.8.9 upstream-locale supplement QA")
    for locale, upstream_count, supplement_count, target_count in coverage:
        print(
            f"{locale}: upstream normal keys={upstream_count}, "
            f"supplement keys={supplement_count}, covered={target_count}/{target_count}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

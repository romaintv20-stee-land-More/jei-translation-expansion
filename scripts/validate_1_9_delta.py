#!/usr/bin/env python3
"""Validate the JEI 3.3.3 / Minecraft 1.9 inherited translation deltas."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream" / "sources" / "1.9" / "en_US.lang"
SCOPE = ROOT / "upstream" / "minecraft-1.9-language-scope.json"
INHERITED_DELTA = ROOT / "translations" / "g3-mc1.9" / "inherited-delta.tsv"
SUPPLEMENT_DELTA = ROOT / "translations" / "g3-mc1.9" / "upstream-supplement-delta.tsv"

DELTA_KEYS = [
    "jei.tooltip.shapeless.recipe",
    "key.jei.focusSearch",
    "key.jei.toggleOverlay",
]
SUPPLEMENT_DELTA_KEYS = [
    "jei.tooltip.shapeless.recipe",
    "key.jei.focusSearch",
]
FALLBACK_LOCALES = {"gv_IM", "kw_GB", "se_NO"}


def parse_lang(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in raw:
            raise ValueError(f"{path}:{lineno}: missing '='")
        key, value = raw.split("=", 1)
        key = key.strip()
        if key in result:
            raise ValueError(f"{path}:{lineno}: duplicate key {key}")
        result[key] = value
    return result


def read_tsv(path: Path, expected_keys: list[str]) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["locale", *expected_keys]:
            raise ValueError(f"{path}: unexpected header {reader.fieldnames}")
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            locale = (row.get("locale") or "").strip()
            if not locale or locale in rows:
                raise ValueError(f"{path}: empty or duplicate locale {locale!r}")
            values = {key: row.get(key, "") for key in expected_keys}
            if any(value == "" for value in values.values()):
                raise ValueError(f"{path}: empty translation in {locale}")
            rows[locale] = values
        return rows


def main() -> int:
    english = parse_lang(SOURCE)
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    inherited = read_tsv(INHERITED_DELTA, DELTA_KEYS)
    supplements = read_tsv(SUPPLEMENT_DELTA, SUPPLEMENT_DELTA_KEYS)

    expected_inherited = set(scope["inherited_addon_locales"])
    if set(inherited) != expected_inherited:
        raise ValueError(
            "Inherited locale set mismatch: "
            f"missing={sorted(expected_inherited - set(inherited))}, "
            f"extra={sorted(set(inherited) - expected_inherited)}"
        )

    expected_supplements = set(scope["upstream_missing_key_supplement_locales"])
    if set(supplements) != expected_supplements:
        raise ValueError(
            "Supplement-delta locale set mismatch: "
            f"missing={sorted(expected_supplements - set(supplements))}, "
            f"extra={sorted(set(supplements) - expected_supplements)}"
        )

    for key in DELTA_KEYS:
        if key not in english:
            raise ValueError(f"Target English source is missing audited delta key: {key}")

    for locale in FALLBACK_LOCALES:
        values = inherited[locale]
        for key in DELTA_KEYS:
            if values[key] != english[key]:
                raise ValueError(
                    f"{locale}: documented fallback must keep English for {key}: "
                    f"{values[key]!r} != {english[key]!r}"
                )

    translated = sorted(expected_inherited - FALLBACK_LOCALES)
    for locale in translated:
        if all(inherited[locale][key] == english[key] for key in DELTA_KEYS):
            raise ValueError(f"{locale}: all three inherited delta values are still English")

    print("PASS: JEI 1.9 inherited delta QA")
    print(f"Inherited addon locales: {len(inherited)}")
    print(f"Delta keys per inherited locale: {len(DELTA_KEYS)}")
    print(f"Inherited delta entries: {len(inherited) * len(DELTA_KEYS)}")
    print(f"Translated/AI-assisted inherited locales: {len(translated)}")
    print(f"Documented English fallback locales: {len(FALLBACK_LOCALES)}")
    print(f"Upstream supplement locales with new-key delta: {len(supplements)}")
    print(f"Supplement new-key entries: {len(supplements) * len(SUPPLEMENT_DELTA_KEYS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

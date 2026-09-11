#!/usr/bin/env python3
"""Validate JEI Translation Expansion localization files.

Currently validates the audited Minecraft 1.8 / JEI 2.15.0 generation.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream" / "sources" / "1.8" / "en_US.lang"
TRANSLATIONS = ROOT / "translations" / "g1-mc1.8"

EXPECTED_ADDON_LOCALES = {
    "af_ZA", "ar_SA", "ast_ES", "az_AZ", "bg_BG", "ca_ES", "cs_CZ",
    "cy_GB", "da_DK", "el_GR", "eo_UY", "es_ES", "et_EE", "eu_ES",
    "fa_IR", "fil_PH", "fr_FR", "ga_IE", "gl_ES", "gv_IM", "he_IL",
    "hi_IN", "hr_HR", "hu_HU", "hy_AM", "id_ID", "is_IS", "it_IT",
    "ja_JP", "ka_GE", "kw_GB", "la_LA", "lb_LU", "lt_LT", "lv_LV",
    "mi_NZ", "ms_MY", "mt_MT", "nds_DE", "nl_NL", "no_NO", "oc_FR",
    "pl_PL", "pt_BR", "ro_RO", "se_NO", "sk_SK", "sl_SI", "sr_SP",
    "sv_SE", "th_TH", "tr_TR", "uk_UA", "vi_VN",
}

DOCUMENTED_ENGLISH_FALLBACKS = {"gv_IM", "kw_GB", "se_NO"}
DEBUG_PREFIX = "description.jei."

PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|(?:\d+\$)?[,]?[a-zA-Z])")
TECHNICAL_TOKENS = (
    "/give",
    "@ModName",
    "modId:name[:meta]",
    "NBT",
    "ItemStack",
    "JEI",
    "Minecraft",
    "mB",
    "Ctrl",
)


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
    source, source_dupes = parse_lang(SOURCE)
    if source_dupes:
        errors.append(f"source has duplicate keys: {source_dupes}")

    files = sorted(TRANSLATIONS.glob("*.lang"))
    found_locales = {p.stem for p in files}
    missing_files = sorted(EXPECTED_ADDON_LOCALES - found_locales)
    extra_files = sorted(found_locales - EXPECTED_ADDON_LOCALES)
    if missing_files:
        errors.append(f"missing locale files: {', '.join(missing_files)}")
    if extra_files:
        errors.append(f"unexpected locale files: {', '.join(extra_files)}")

    for path in files:
        locale = path.stem
        try:
            translated, dupes = parse_lang(path)
        except Exception as exc:
            errors.append(str(exc))
            continue

        if dupes:
            errors.append(f"{locale}: duplicate keys: {', '.join(dupes)}")

        missing = sorted(set(source) - set(translated))
        extra = sorted(set(translated) - set(source))
        if missing:
            errors.append(f"{locale}: missing keys: {', '.join(missing)}")
        if extra:
            errors.append(f"{locale}: extra keys: {', '.join(extra)}")

        for key in sorted(set(source) & set(translated)):
            en = source[key]
            tr = translated[key]
            if placeholders(en) != placeholders(tr):
                errors.append(
                    f"{locale}: placeholder mismatch in {key}: "
                    f"{placeholders(en)} != {placeholders(tr)}"
                )
            for token in TECHNICAL_TOKENS:
                if token in en and token not in tr:
                    errors.append(f"{locale}: missing technical token {token!r} in {key}")
            if key.startswith(DEBUG_PREFIX) and tr != en:
                errors.append(f"{locale}: debug-only key must remain English: {key}")

        # English fallback is intentional only for explicitly documented low-confidence locales.
        normal_keys = [k for k in source if not k.startswith(DEBUG_PREFIX)]
        english_equal = sum(translated.get(k) == source[k] for k in normal_keys)
        if locale in DOCUMENTED_ENGLISH_FALLBACKS:
            if english_equal != len(normal_keys):
                errors.append(f"{locale}: documented fallback must remain fully English")
        elif english_equal == len(normal_keys):
            errors.append(f"{locale}: unexpected full English fallback")

    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 1.8 translation QA")
    print(f"Source keys: {len(source)}")
    print(f"Addon locale files: {len(files)}")
    print(f"Translated/AI-assisted locales: {len(files) - len(DOCUMENTED_ENGLISH_FALLBACKS)}")
    print(f"Documented English fallbacks: {len(DOCUMENTED_ENGLISH_FALLBACKS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

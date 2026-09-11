#!/usr/bin/env python3
"""Validate JEI 1.8.9 localization deltas against the audited 1.8 base."""
from __future__ import annotations

from pathlib import Path
import csv
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.8" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.8.9" / "en_US.lang"
DELTAS = ROOT / "translations" / "g2-mc1.8.9"

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
PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|(?:\d+\$)?[,]?[a-zA-Z])")
TECHNICAL_TOKENS = ("modId[:name[:meta]]", "ModId", "JEI")
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
    base, base_dupes = parse_lang(BASE_SOURCE)
    target, target_dupes = parse_lang(TARGET_SOURCE)
    if base_dupes:
        errors.append(f"1.8 source has duplicate keys: {base_dupes}")
    if target_dupes:
        errors.append(f"1.8.9 source has duplicate keys: {target_dupes}")

    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {k for k in set(base) & set(target) if base[k] != target[k]}
    expected_delta = added | changed
    unchanged = (set(base) & set(target)) - changed
    ordered_delta = [k for k in target if k in expected_delta]

    if len(base) != 58:
        errors.append(f"expected 58 source keys for 1.8, got {len(base)}")
    if len(target) != 75:
        errors.append(f"expected 75 source keys for 1.8.9, got {len(target)}")
    if len(added) != 19 or len(removed) != 2 or len(changed) != 10:
        errors.append(
            "unexpected 1.8 -> 1.8.9 diff: "
            f"added={len(added)}, removed={len(removed)}, changed={len(changed)}"
        )
    if len(unchanged) != 46:
        errors.append(f"expected 46 reusable unchanged keys, got {len(unchanged)}")
    if ((set(base) - removed) | expected_delta) != set(target):
        errors.append("base + removals + delta does not reconstruct the target key set")

    locale_rows: dict[str, dict[str, str]] = {}
    batch_files = sorted(DELTAS.glob("delta-*.tsv"))
    if len(batch_files) != 6:
        errors.append(f"expected 6 delta TSV batches, got {len(batch_files)}")

    expected_header = ["locale", *ordered_delta]
    for path in batch_files:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != expected_header:
                errors.append(f"{path.name}: unexpected header/key order")
                continue
            for row in reader:
                locale = (row.get("locale") or "").strip()
                if not locale:
                    errors.append(f"{path.name}: row with empty locale")
                    continue
                if locale in locale_rows:
                    errors.append(f"duplicate locale across delta batches: {locale}")
                    continue
                locale_rows[locale] = {k: row.get(k, "") for k in ordered_delta}

    found = set(locale_rows)
    missing_locales = sorted(EXPECTED_ADDON_LOCALES - found)
    extra_locales = sorted(found - EXPECTED_ADDON_LOCALES)
    if missing_locales:
        errors.append(f"missing 1.8.9 delta locales: {', '.join(missing_locales)}")
    if extra_locales:
        errors.append(f"unexpected 1.8.9 delta locales: {', '.join(extra_locales)}")

    for locale, delta in sorted(locale_rows.items()):
        if set(delta) != expected_delta:
            errors.append(f"{locale}: delta key set mismatch")
            continue
        for key in ordered_delta:
            en = target[key]
            tr = delta[key]
            if not tr:
                errors.append(f"{locale}: empty translation for {key}")
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
                    errors.append(f"{locale}: missing search-prefix symbol {symbol!r} in {key}")
            if key == "config.jei.search.prefixRequiredForCreativeTabSearch" and "%%" not in tr:
                errors.append(f"{locale}: missing literal '%%' marker in {key}")
            if key == "config.jei.search.prefixRequiredForCreativeTabSearch.comment" and "%" not in tr:
                errors.append(f"{locale}: missing literal '%' marker in {key}")

        if locale in DOCUMENTED_ENGLISH_FALLBACKS:
            if any(delta[k] != target[k] for k in ordered_delta):
                errors.append(f"{locale}: documented fallback delta must remain English")
        elif all(delta[k] == target[k] for k in ordered_delta):
            errors.append(f"{locale}: unexpected full English fallback delta")

    if errors:
        print(f"FAIL: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 1.8.9 delta QA")
    print(f"1.8 source keys: {len(base)}")
    print(f"1.8.9 source keys: {len(target)}")
    print(f"Reusable unchanged keys: {len(unchanged)}")
    print(f"Added keys: {len(added)}")
    print(f"Changed English meanings: {len(changed)}")
    print(f"Removed keys: {len(removed)}")
    print(f"Delta keys per addon locale: {len(expected_delta)}")
    print(f"Addon locale deltas: {len(locale_rows)}")
    print(f"Translated/AI-assisted deltas: {len(locale_rows) - len(DOCUMENTED_ENGLISH_FALLBACKS)}")
    print(f"Documented English fallback deltas: {len(DOCUMENTED_ENGLISH_FALLBACKS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Audit semantically exact later-JEI translation backports for G39 supplements."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
G39_COMMIT = "28eb51f58d2798512a2ef75cf8b29189228573ad"
# Current mainline JEI snapshot at audit time; used only as a translation donor.
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
LANG_PATH = "Common/src/main/resources/assets/jei/lang/{locale}.json"
SELECTED_INCOMPLETE = (
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "kk_kz", "ko_kr", "lt_lt", "no_no", "pl_pl", "pt_br",
    "ru_ru", "sv_se", "tr_tr", "uk_ua", "vi_vn", "zh_cn",
)
DEBUG_PREFIX = "description.jei."


def _url(commit: str, locale: str) -> str:
    return f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/" + LANG_PATH.format(locale=locale)


def fetch_strict(commit: str, locale: str) -> dict[str, str]:
    req = urllib.request.Request(_url(commit, locale), headers={"User-Agent": "JEI-Translation-Expansion-G39-backport-audit"})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = json.loads(response.read().decode("utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def fetch_donor(locale: str) -> tuple[dict[str, str] | None, str]:
    req = urllib.request.Request(_url(DONOR_COMMIT, locale), headers={"User-Agent": "JEI-Translation-Expansion-G39-backport-audit"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "absent"
        raise
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"invalid-json:{exc.lineno}:{exc.colno}"
    return ({str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}, "ok")


def parse(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def main() -> int:
    target = parse(TARGET)
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    donor_en, donor_en_status = fetch_donor("en_us")
    if donor_en is None:
        raise RuntimeError(f"donor English locale unavailable: {donor_en_status}")
    semantically_stable = {k for k in normal if donor_en.get(k) == target[k]}
    print(f"Donor commit: {DONOR_COMMIT}")
    print(f"G39 normal target keys: {len(normal)}")
    print(f"Exact same key+English semantics in donor snapshot: {len(semantically_stable)}")
    total = 0
    useful_locales = 0
    unavailable: list[str] = []
    for locale in SELECTED_INCOMPLETE:
        current = fetch_strict(G39_COMMIT, locale)
        missing = normal - set(current)
        donor, status = fetch_donor(locale)
        if donor is None:
            unavailable.append(f"{locale}({status})")
            print(f"{locale}: missing={len(missing)} donor={status} backportable=0 remaining={len(missing)}")
            continue
        backportable = sorted(k for k in missing & semantically_stable if k in donor)
        if backportable:
            useful_locales += 1
            total += len(backportable)
        remaining = len(missing) - len(backportable)
        print(f"{locale}: missing={len(missing)} backportable={len(backportable)} remaining={remaining}")
        if backportable:
            print("  " + ", ".join(backportable))
    print(f"Backportable exact translations total: {total} across {useful_locales} locales")
    print(f"Unavailable donor locales ({len(unavailable)}): {', '.join(unavailable) or '(none)'}")
    print("PASS: donor audit uses only identical localization key + identical English value; malformed/absent donor locales are skipped, never trusted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

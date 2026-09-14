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
# Later mainline JEI snapshot after the 1.21.10 port; used only as a translation donor.
DONOR_COMMIT = "5593dfe99114c057f018d959bf4c147a70462fef"
LANG_PATH = "Common/src/main/resources/assets/jei/lang/{locale}.json"
SELECTED_INCOMPLETE = (
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "es_es", "fi_fi", "fr_fr", "he_il",
    "hu_hu", "id_id", "it_it", "kk_kz", "ko_kr", "lt_lt", "no_no", "pl_pl", "pt_br",
    "ru_ru", "sv_se", "tr_tr", "uk_ua", "vi_vn", "zh_cn",
)
DEBUG_PREFIX = "description.jei."


def fetch(commit: str, locale: str) -> dict[str, str] | None:
    url = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/" + LANG_PATH.format(locale=locale)
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G39-backport-audit"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def main() -> int:
    target = parse(TARGET)
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    donor_en = fetch(DONOR_COMMIT, "en_us")
    if donor_en is None:
        raise RuntimeError("donor English locale missing")
    semantically_stable = {k for k in normal if donor_en.get(k) == target[k]}
    print(f"G39 normal target keys: {len(normal)}")
    print(f"Exact same key+English semantics in donor snapshot: {len(semantically_stable)}")
    total = 0
    useful_locales = 0
    for locale in SELECTED_INCOMPLETE:
        current = fetch(G39_COMMIT, locale)
        if current is None:
            raise RuntimeError(f"G39 upstream locale unexpectedly missing: {locale}")
        missing = normal - set(current)
        donor = fetch(DONOR_COMMIT, locale)
        if donor is None:
            print(f"{locale}: missing={len(missing)} donor=absent backportable=0")
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
    print("PASS: donor audit uses only identical localization key + identical English value")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

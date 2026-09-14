#!/usr/bin/env python3
"""Audit later JEI translations that can safely backport into G39 addon-full locales."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
LANG_PATH = "Common/src/main/resources/assets/jei/lang/{locale}.json"
DEBUG_PREFIX = "description.jei."


def parse(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def fetch(locale: str) -> tuple[dict[str, str] | None, str]:
    url = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{DONOR_COMMIT}/" + LANG_PATH.format(locale=locale)
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G39-addon-donor-audit"})
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


def main() -> int:
    target = parse(TARGET_PATH)
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    full = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    translated = sorted(full - fallback)
    if len(translated) != 34:
        raise RuntimeError(f"expected 34 translated addon-full locales, got {len(translated)}")

    donor_en, status = fetch("en_us")
    if donor_en is None:
        raise RuntimeError(f"donor English unavailable: {status}")
    stable = {k for k in normal if donor_en.get(k) == target[k]}
    print(f"Donor commit: {DONOR_COMMIT}")
    print(f"Exact stable G39 semantics available in donor English: {len(stable)}/{len(normal)}")
    useful = 0
    total = 0
    for locale in translated:
        donor, status = fetch(locale)
        if donor is None:
            print(f"{locale}: donor={status} exact-backportable=0")
            continue
        keys = sorted(stable & set(donor))
        if keys:
            useful += 1
            total += len(keys)
        print(f"{locale}: donor=ok exact-backportable={len(keys)}")
    print(f"Exact donor translations available: {total} values across {useful}/{len(translated)} translated addon-full locales")
    print("PASS: addon donor audit only counts exact key + exact English semantic matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

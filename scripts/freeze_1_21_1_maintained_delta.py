#!/usr/bin/env python3
"""Freeze the maintained JEI 1.21.1 English source and translation-review delta."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEAD = "bf7b64d24f18b957ffdb806227b6077a2088eaff"
TARGET_URL = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{HEAD}/Common/src/main/resources/assets/jei/lang/en_us.json"
OLD = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
OUT_DIR = ROOT / "maintenance" / "1.21.1-jei-19.56.0"
PACKAGING = ROOT / "packaging" / "completed-versions.json"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-freeze-maintained-1.21.1"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8")


def parse(text: str) -> dict[str, str]:
    raw = json.loads(text)
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def main() -> int:
    old = parse(OLD.read_text(encoding="utf-8"))
    raw_target = fetch(TARGET_URL)
    target = parse(raw_target)
    added = sorted(set(target) - set(old))
    changed = sorted(k for k in set(target) & set(old) if target[k] != old[k])
    removed = sorted(set(old) - set(target))

    packaging = json.loads(PACKAGING.read_text(encoding="utf-8"))
    donors: dict[str, dict[str, str]] = {}
    after = False
    for cfg in packaging["versions"]:
        if cfg["generation"] == "G39":
            after = True
            continue
        if not after or cfg.get("format") != "json":
            continue
        path = ROOT / "upstream" / "sources" / cfg["minecraft"] / "en_us.json"
        if not path.is_file():
            continue
        values = parse(path.read_text(encoding="utf-8"))
        for key in added + changed:
            if values.get(key) == target[key] and key not in donors:
                donors[key] = {"generation": cfg["generation"], "minecraft": cfg["minecraft"]}

    needs = [key for key in added + changed if key not in donors]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "en_us.json").write_text(raw_target if raw_target.endswith("\n") else raw_target + "\n", encoding="utf-8")
    review = {
        "minecraft": "1.21.1",
        "jei": "19.56.0",
        "upstream_commit": HEAD,
        "historical_generation": "G39",
        "counts": {
            "target": len(target),
            "added": len(added),
            "changed_english": len(changed),
            "removed": len(removed),
            "exact_later_donor": len(donors),
            "requires_new_translation": len(needs),
        },
        "added_keys": added,
        "changed_english_keys": changed,
        "removed_keys": removed,
        "exact_later_generation_donors": donors,
        "requires_new_translation": {key: target[key] for key in needs},
    }
    (OUT_DIR / "translation-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(review["counts"], indent=2))
    print(f"PASS: froze maintained 1.21.1 source and {len(needs)} new translation meanings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

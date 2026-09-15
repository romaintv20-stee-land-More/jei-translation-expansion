#!/usr/bin/env python3
"""Register maintained G47 / Minecraft 1.21.11 as a static candidate target."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "packaging" / "completed-versions.json"

G47 = {
    "generation": "G47",
    "minecraft": "1.21.11",
    "jei": "27.38.0",
    "era": "modern",
    "loader": "neoforge",
    "neoforge": "21.11.45",
    "loader_version_range": "[4,)",
    "neoforge_version_range": "[21.11.44,)",
    "jei_modid": "jei",
    "java_target": 21,
    "format": "json",
    "full": 63,
    "supplements": 26,
    "keys": 334,
    "reconstruct_script": "scripts/reconstruct_1_21_11.py",
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    versions = data["versions"]
    existing = [item for item in versions if item.get("generation") == "G47" or item.get("minecraft") == "1.21.11"]
    if existing:
        if existing != [G47]:
            raise ValueError(f"existing G47 packaging metadata differs: {existing}")
        print("G47 packaging metadata already current")
        return 0
    if not versions or versions[-1].get("generation") != "G46" or versions[-1].get("minecraft") != "1.21.10":
        raise ValueError("G47 registration requires G46 / Minecraft 1.21.10 as the current final target")
    versions.append(G47)
    data["note"] = "G1-G47 are translation/reconstruction complete. These builds are static-validated release candidates until their required runtime gates are complete."
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: registered G47 / Minecraft 1.21.11 / JEI 27.38.0 for static candidate packaging")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

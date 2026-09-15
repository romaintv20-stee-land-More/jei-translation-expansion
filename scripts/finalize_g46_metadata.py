#!/usr/bin/env python3
"""Register completed G46 / Minecraft 1.21.10 packaging metadata deterministically."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "completed-versions.json"
EXPECTED = {
    "generation": "G46",
    "minecraft": "1.21.10",
    "jei": "26.2.0",
    "era": "modern",
    "loader": "neoforge",
    "neoforge": "21.10.64",
    "loader_version_range": "[4,)",
    "neoforge_version_range": "[21.9.2-beta,)",
    "jei_modid": "jei",
    "java_target": 21,
    "format": "json",
    "full": 64,
    "supplements": 25,
    "keys": 308,
    "reconstruct_script": "scripts/reconstruct_1_21_10.py",
}


def main() -> int:
    data = json.loads(PACKAGING.read_text(encoding="utf-8"))
    versions = data["versions"]
    existing = [item for item in versions if item.get("generation") == "G46" or item.get("minecraft") == "1.21.10"]
    if existing:
        if existing != [EXPECTED]:
            raise ValueError(f"existing G46 packaging entry differs from expected: {existing}")
    else:
        if not versions or versions[-1].get("generation") != "G45" or versions[-1].get("minecraft") != "1.21.9":
            raise ValueError("G46 must be appended directly after completed G45")
        versions.append(EXPECTED)
    data["note"] = "G1-G46 are translation/reconstruction complete. These builds are static-validated release candidates until their required runtime gates are complete."
    PACKAGING.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: registered G46 Minecraft 1.21.10 / JEI 26.2.0 packaging metadata")
    print("Ownership: 64 full + 25 supplements + 1 complete upstream = 90")
    print("Keys: 308; loader: NeoForge 21.10.64; Java 21")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

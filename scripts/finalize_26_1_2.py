#!/usr/bin/env python3
"""Register G50 packaging metadata and synchronize the canonical project status."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "completed-versions.json"
STATUS = ROOT / "PROJECT_STATUS.md"

G50 = {
    "generation": "G50",
    "minecraft": "26.1.2",
    "jei": "29.37.0",
    "era": "modern",
    "loader": "neoforge",
    "neoforge": "26.1.2.99",
    "loader_version_range": "[4,)",
    "neoforge_version_range": "[26.1.2.99,)",
    "jei_modid": "jei",
    "java_target": 25,
    "format": "json",
    "full": 63,
    "supplements": 26,
    "keys": 334,
    "reconstruct_script": "scripts/reconstruct_26_1_2.py",
}


def register() -> None:
    data = json.loads(PACKAGING.read_text(encoding="utf-8"))
    matches = [
        item for item in data["versions"]
        if item.get("generation") == "G50" or item.get("minecraft") == "26.1.2"
    ]
    if matches:
        if matches != [G50]:
            raise ValueError(f"existing G50 packaging metadata differs: {matches}")
    else:
        last = data["versions"][-1]
        if last.get("generation") != "G49" or last.get("minecraft") != "26.1.1":
            raise ValueError(f"expected G49 as latest completed target, got {last}")
        data["versions"].append(G50)
    data["note"] = (
        "G1-G50 are translation/reconstruction complete. These builds are static-validated "
        "release candidates until their required runtime gates are complete."
    )
    PACKAGING.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_upstream_registries.py"), "--date", "2026-09-15"],
        cwd=ROOT,
        check=True,
    )
    print("PASS: registered G50 packaging metadata and synchronized upstream registries")


def update_status(sha256: str) -> None:
    if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
        raise ValueError("invalid G50 SHA-256")
    text = STATUS.read_text(encoding="utf-8")
    row49 = "| G49 | 26.1.1 | 29.4.0 | `5a2ecc4` | 309 | 90 | 64 | 25 | 1 | complete; NeoForge candidate validated |"
    row50 = "| G50 | 26.1.2 | 29.37.0 | `d7c73ed` | 334 | 90 | 63 | 26 | 1 | complete; NeoForge candidate validated |"
    if row50 not in text:
        if row49 not in text:
            raise ValueError("G49 status row not found")
        text = text.replace(row49, row49 + "\n" + row50, 1)

    milestone = f"""### G50 — Minecraft 26.1.2 / JEI 29.37.0

- first 26.1.2 support commit `481a64808dab4ea205772a7289cc766804f5f5d7` directly follows the G49 endpoint
- maintained JEI `26.1` branch snapshot pinned at `d7c73ed63a7a25a9ad416428eafef3a3dcf0f1c8` for reproducibility; this is a maintained snapshot, not claimed as a historical final endpoint
- build: NeoForge `26.1.2.99`, minimum `[26.1.2.99,)`, Java 25
- 334 keys = 328 normal + 6 debug
- G49→G50 semantic delta = 294 unchanged + 34 added + 9 removed + 6 changed-English values
- translation reuse remains limited to exact same-key/same-English meanings; the 40 added/changed meanings fall back to exact target English when not already owned by upstream
- selected scope remains 90; ownership = 63 addon-full locales + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- `fil_ph` moves from add-on full ownership to an incomplete upstream supplement locale
- Minecraft language membership remains 143 codes with no additions/removals
- all selected upstream JSON files are syntactically valid at the pinned snapshot
- 91 upstream-owned values require frozen literal-safety overrides so placeholders and fixed technical literals remain exact
- isolated complete reconstruction validation run `35020580691`, green
- deterministic Java-25 NeoForge candidate SHA-256 `{sha256}`
- runtime promotion remains separately gated

"""
    marker = "## Candidate packaging state\n"
    if "### G50 — Minecraft 26.1.2 / JEI 29.37.0" not in text:
        if marker not in text:
            raise ValueError("candidate packaging heading not found")
        text = text.replace(marker, milestone + marker, 1)

    old_pack = (
        "- The canonical candidate inventory on `main` contains **48 version-specific 1.0.0 candidates through Minecraft 26.1**.\n"
        "- G49 / Minecraft 26.1.1 has passed complete static reconstruction and deterministic Java-25 NeoForge candidate validation; canonical persistence follows its merge to `main`.\n"
        "- Candidate JARs are not runtime-promoted finals."
    )
    new_pack = (
        "- The canonical candidate inventory on `main` contains **49 version-specific 1.0.0 candidates through Minecraft 26.1.1**.\n"
        "- G50 / Minecraft 26.1.2 has passed complete static reconstruction and deterministic Java-25 NeoForge candidate validation; canonical persistence follows its merge to `main`.\n"
        "- Candidate JARs are not runtime-promoted finals."
    )
    if old_pack in text:
        text = text.replace(old_pack, new_pack, 1)

    start = text.find("## Current next target\n")
    end = text.find("\n## Documentation synchronization debt", start)
    if start < 0 or end < 0:
        raise ValueError("current next target section not found")
    next_section = """## Current next target

- Merge G50 and persist `candidate-jars/26.1.2/jei-translation-expansion-1.0.0-mc26.1.2-neoforge.jar` using the validated candidate digest above.
- Because JEI still maintains Minecraft 26.1.2 on branch `26.1`, re-audit that branch before declaring a later 26.1.2 snapshot or moving to a subsequent chronological target.
- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.
"""
    text = text[:start] + next_section + text[end:]
    text = text.replace(
        "`PROJECT_STATUS.md`, `packaging/completed-versions.json`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through validated G49 on the work branch.",
        "`PROJECT_STATUS.md`, `packaging/completed-versions.json`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through validated G50 on the work branch.",
    )
    text = text.replace(
        "NeoForge candidates G39–G49 remain static candidates",
        "NeoForge candidates G39–G50 remain static candidates",
    )
    STATUS.write_text(text, encoding="utf-8")
    print(f"PASS: synchronized PROJECT_STATUS.md through G50 ({sha256})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("register", "status"), required=True)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.phase == "register":
        register()
    else:
        if not args.sha256:
            raise ValueError("--sha256 is required for status phase")
        update_status(args.sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

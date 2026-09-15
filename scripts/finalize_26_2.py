#!/usr/bin/env python3
"""Register G51 packaging metadata and synchronize the canonical project status."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "completed-versions.json"
STATUS = ROOT / "PROJECT_STATUS.md"

G51 = {
    "generation": "G51",
    "minecraft": "26.2",
    "jei": "30.32.0",
    "era": "modern",
    "loader": "neoforge",
    "neoforge": "26.2.0.69",
    "loader_version_range": "[4,)",
    "neoforge_version_range": "[26.2.0.67,)",
    "jei_modid": "jei",
    "java_target": 25,
    "format": "json",
    "full": 63,
    "supplements": 26,
    "keys": 334,
    "reconstruct_script": "scripts/reconstruct_26_2.py",
}


def register() -> None:
    data = json.loads(PACKAGING.read_text(encoding="utf-8"))
    matches = [
        item for item in data["versions"]
        if item.get("generation") == "G51" or item.get("minecraft") == "26.2"
    ]
    if matches:
        if matches != [G51]:
            raise ValueError(f"existing G51 packaging metadata differs: {matches}")
    else:
        last = data["versions"][-1]
        if last.get("generation") != "G50" or last.get("minecraft") != "26.1.2":
            raise ValueError(f"expected G50 as latest completed target, got {last}")
        data["versions"].append(G51)
    data["note"] = (
        "G1-G51 are translation/reconstruction complete. These builds are static-validated "
        "release candidates until their required runtime gates are complete."
    )
    PACKAGING.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_upstream_registries.py"), "--date", "2026-09-15"],
        cwd=ROOT,
        check=True,
    )
    print("PASS: registered G51 packaging metadata and synchronized upstream registries")


def replace_section(text: str, heading: str, next_heading: str, body: str) -> str:
    start = text.find(heading)
    end = text.find(next_heading, start + len(heading))
    if start < 0 or end < 0:
        raise ValueError(f"could not locate section {heading!r}")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


def update_status(sha256: str, run_id: str) -> None:
    if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
        raise ValueError("invalid G51 SHA-256")
    if not run_id.isdigit():
        raise ValueError("invalid G51 workflow run id")

    text = STATUS.read_text(encoding="utf-8")
    row50 = "| G50 | 26.1.2 | 29.37.0 | `d7c73ed` | 334 | 90 | 63 | 26 | 1 | complete; NeoForge candidate validated |"
    row51 = "| G51 | 26.2 | 30.32.0 | `f93563c` | 334 | 90 | 63 | 26 | 1 | complete; NeoForge candidate validated |"
    if row51 not in text:
        if row50 not in text:
            raise ValueError("G50 status row not found")
        text = text.replace(row50, row50 + "\n" + row51, 1)

    milestone = f"""### G51 — Minecraft 26.2 / JEI 30.32.0

- first 26.2 support commit `71d31cea392876a8414426e15f6f31f1b40ca9cc` follows parent `79442458a4bc67ccb7d8925986c2d81e4cd2b7ff`
- maintained JEI `26.2` branch snapshot pinned at `f93563ca4965d511bd07d4f041b3a6ddd1158ef0` for reproducibility; this is an actively maintained snapshot, not claimed as a historical final endpoint
- build: NeoForge `26.2.0.69`, minimum `[26.2.0.67,)`, Java 25
- 334 keys = 328 normal + 6 debug
- G50→G51 semantic delta = 334 unchanged + 0 added + 0 removed + 0 changed-English values
- all translation reuse is exact same-key/same-English reuse from G50; cross-key reuse remains forbidden
- selected scope remains 90; ownership = 63 addon-full locales + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- Minecraft language membership remains 143 codes with no additions/removals
- all selected upstream JSON files are syntactically valid at the pinned snapshot
- frozen literal-safety overrides preserve placeholders and fixed technical literals for unsafe upstream-owned values
- isolated complete reconstruction validation run `35022849550`, green
- deterministic Java-25 NeoForge packaging/finalization run `{run_id}`, green
- validated candidate SHA-256 `{sha256}`
- runtime promotion remains separately gated

"""
    marker = "## Candidate packaging state\n"
    if "### G51 — Minecraft 26.2 / JEI 30.32.0" not in text:
        if marker not in text:
            raise ValueError("candidate packaging heading not found")
        text = text.replace(marker, milestone + marker, 1)

    candidate_body = """## Candidate packaging state

- The canonical candidate inventory on `main` contains **50 version-specific 1.0.0 candidates through Minecraft 26.1.2**.
- G51 / Minecraft 26.2 has passed complete static reconstruction and deterministic Java-25 NeoForge candidate validation; canonical persistence follows its merge to `main`.
- Candidate JARs are not runtime-promoted finals."""
    text = replace_section(text, "## Candidate packaging state\n", "## Current next target\n", candidate_body)

    next_body = """## Current next target

- Merge G51 and persist `candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar` using the validated candidate digest above.
- Because JEI actively maintains Minecraft 26.2 on branch `26.2`, re-audit that branch before declaring a later 26.2 snapshot or selecting the next chronological Minecraft target.
- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied."""
    text = replace_section(text, "## Current next target\n", "## Documentation synchronization debt\n", next_body)

    text = re.sub(
        r"are synchronized through validated G50 on the work branch\.",
        "are synchronized through validated G51 on the work branch.",
        text,
    )
    text = text.replace("NeoForge candidates G39–G50 remain static candidates", "NeoForge candidates G39–G51 remain static candidates")
    STATUS.write_text(text, encoding="utf-8")
    print(f"PASS: synchronized PROJECT_STATUS.md through G51 ({sha256})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("register", "status"), required=True)
    parser.add_argument("--sha256")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.phase == "register":
        register()
    else:
        if not args.sha256 or not args.run_id:
            raise ValueError("--sha256 and --run-id are required for status phase")
        update_status(args.sha256, args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

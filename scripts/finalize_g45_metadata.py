#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "completed-versions.json"
STATUS = ROOT / "PROJECT_STATUS.md"

G45 = {
    "generation": "G45",
    "minecraft": "1.21.9",
    "jei": "25.0.1",
    "era": "modern",
    "loader": "neoforge",
    "neoforge": "21.9.2-beta",
    "loader_version_range": "[4,)",
    "neoforge_version_range": "[21.9.2-beta,)",
    "jei_modid": "jei",
    "java_target": 21,
    "format": "json",
    "full": 65,
    "supplements": 24,
    "keys": 305,
    "reconstruct_script": "scripts/reconstruct_1_21_9.py",
}


def register() -> None:
    data = json.loads(PACKAGING.read_text(encoding="utf-8"))
    versions = data["versions"]
    matches = [x for x in versions if x.get("generation") == "G45" or x.get("minecraft") == "1.21.9"]
    if matches:
        if len(matches) != 1 or matches[0] != G45 or versions[-1] != G45:
            raise ValueError(f"existing G45 packaging metadata differs from frozen target: {matches}")
    else:
        if versions[-1].get("generation") != "G44" or versions[-1].get("minecraft") != "1.21.8":
            raise ValueError(f"expected G44 as previous target, got {versions[-1]}")
        versions.append(dict(G45))
    data["note"] = (
        "G1-G45 are translation/reconstruction complete. These builds are static-validated "
        "release candidates until their required runtime gates are complete."
    )
    PACKAGING.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: registered G45 / Minecraft 1.21.9 packaging target")


def status(sha256: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("invalid SHA-256")
    text = STATUS.read_text(encoding="utf-8")
    table_anchor = "| G44 | 1.21.8 | 24.2.0 | `2f8e4ec` | 305 | 90 | 65 | 24 | 1 | complete; NeoForge packaging validated |\n"
    line = "| G45 | 1.21.9 | 25.0.1 | `bdfdb4c` | 305 | 90 | 65 | 24 | 1 | complete; NeoForge packaging validated |\n"
    if line not in text:
        if table_anchor not in text:
            raise ValueError("G44 table anchor missing")
        text = text.replace(table_anchor, table_anchor + line, 1)

    heading = "### G45 — Minecraft 1.21.9 / JEI 25.0.1"
    milestone = (
        heading + "\n\n"
        "- final 1.21.9 mainline endpoint `bdfdb4c09026c4fb488805ff729c66ae48ede875`\n"
        "- next Minecraft port `0999689eb56a4bb3f7061af263de7aef387f0045` targets 1.21.10 and directly follows the G45 endpoint\n"
        "- build: NeoForge `21.9.2-beta`, minimum `[21.9.2-beta,)`, Java 21\n"
        "- 305 keys = 299 normal + 6 debug\n"
        "- G44→G45 semantic delta = 297 unchanged + 8 added + 8 removed + 0 changed-English values\n"
        "- eight JEI key-category localization IDs move from `jei.key.category.*` to `key.category.jei.*`; matching English meanings do not permit cross-key translation reuse\n"
        "- selected scope remains 90; ownership = 65 addon/full-override + 24 supplement locales + 1 complete upstream (`en_us`)\n"
        "- pinned `uk_ua.json` remains malformed and is handled as a deterministic full repair override\n"
        "- 89 pinned upstream-owned values across incomplete locales fail exact placeholder/technical-literal preservation; only this frozen key set receives explicit safe same-key/English overrides, while all other upstream-owned keys remain preserved\n"
        "- exact future-donor reuse for the eight added IDs is allowed only for same key + same English semantics\n"
        "- complete fixed reconstruction QA run `34959813095`, green\n"
        f"- deterministic NeoForge candidate SHA-256 `{sha256}`\n"
        "- runtime promotion remains separately gated\n\n"
    )
    if heading not in text:
        anchor = "## Candidate packaging state\n"
        if anchor not in text:
            raise ValueError("candidate section anchor missing")
        text = text.replace(anchor, milestone + anchor, 1)

    text = re.sub(
        r"- The canonical candidate inventory on `main` contains \*\*\d+ version-specific 1\.0\.0 candidates through Minecraft [^*]+\*\*\.\n",
        "- The canonical candidate inventory on `main` contains **44 version-specific 1.0.0 candidates through Minecraft 1.21.8**.\n",
        text,
        count=1,
    )
    text = text.replace(
        "- G44 has passed complete translation/reconstruction QA and deterministic NeoForge packaging on the work branch; canonical `candidate-jars/1.21.8/` persistence follows merge to `main`.\n",
        "- G45 has passed complete translation/reconstruction QA and deterministic NeoForge packaging on the work branch; canonical `candidate-jars/1.21.9/` persistence follows merge to `main`.\n",
    )
    start = text.index("## Current next target\n")
    end = text.index("## Documentation synchronization debt\n", start)
    current = (
        "## Current next target\n\n"
        "- Merge the completed G45 / Minecraft 1.21.9 work and let the main packaging workflow persist its NeoForge candidate.\n"
        "- The chronological next audit target is **G46 = Minecraft 1.21.10**.\n"
        "- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.\n\n"
    )
    text = text[:start] + current + text[end:]
    text = text.replace(
        "- `PROJECT_STATUS.md`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through completed G44.",
        "- `PROJECT_STATUS.md`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through completed G45.",
    )
    text = text.replace(
        "- `README.md`, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` should be synchronized through G44 before final public release preparation.",
        "- `README.md`, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` should be synchronized through G45 before final public release preparation.",
    )
    text = text.replace("G39–G44 NeoForge candidates", "G39–G45 NeoForge candidates")
    STATUS.write_text(text, encoding="utf-8")
    print("PASS: PROJECT_STATUS synchronized through validated G45")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["register", "status"])
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.phase == "register":
        register()
    else:
        if not args.sha256:
            parser.error("status phase requires --sha256")
        status(args.sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

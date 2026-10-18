#!/usr/bin/env python3
"""Build an UNRELEASED NeoForge 26.3 translation-only JAR candidate from audited JEI 31.10 staging.

The game provides native language search in Minecraft 26.3: do not package
the untested language-search drafts for older Minecraft editions here.
This script does not upload, publish, or modify already released JAR files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_completed_jar_neoforge as nf
from reconstruct_26_2 import preserves_runtime_literals

STAGED = ROOT / "translations/g53-mc26.3-31.10.0.63"
JEI_VERSION = "31.10.0.63"
CANDIDATE_VERSION = "1.0.1-rc.1"
MINECRAFT = "26.3"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def approved_metadata() -> dict:
    matrix = read_json(ROOT / "packaging/completed-versions.json")
    matching = [v for v in matrix["versions"] if v["minecraft"] == MINECRAFT]
    if len(matching) != 1:
        raise ValueError("Missing or ambiguous NeoForge Minecraft 26.3 configuration")
    cfg = dict(matching[0])
    if cfg["loader"] != "neoforge" or cfg["java_target"] != 25:
        raise ValueError("Unexpected Minecraft 26.3 loader/Java configuration")
    cfg["jei"] = JEI_VERSION
    cfg["jei_version_range"] = "[31.10.0.63,31.11.0)"
    return cfg


def staged_language_resources() -> tuple[list[tuple[str, bytes]], dict]:
    audit = read_json(STAGED / "audit.json")
    if audit.get("jei_version") != JEI_VERSION or audit.get("target") != "Minecraft 26.3":
        raise ValueError("Staged audit does not match Minecraft/JEI target")
    if audit.get("keys_new") != 614 or audit.get("keys_old") != 584:
        raise ValueError("Unexpected upstream JEI key delta")
    english = read_json(STAGED / "upstream/en_us.json")
    if len(english) != 614 or any(not isinstance(v, str) for v in english.values()):
        raise ValueError("Invalid English source key baseline")
    files = audit.get("files", {})
    locales = audit.get("locales", {})
    if len(files) != 89 or set(files) != set(locales):
        raise ValueError("Expected 89 add-on translations plus upstream en_us")

    entries: list[tuple[str, bytes]] = []
    full = supplements = 0
    for locale, relative in sorted(files.items()):
        file_path = ROOT / relative
        if file_path.resolve().is_relative_to(STAGED.resolve()) is False:
            raise ValueError("Staged locale references an external file")
        if file_path.name != locale + ".json" or not file_path.is_file():
            raise ValueError("Missing staged locale: " + locale)
        source = read_json(file_path)
        if not isinstance(source, dict) or not source or set(source) - set(english):
            raise ValueError("Unknown, empty or malformed language keys: " + locale)
        if not all(
            isinstance(value, str) and preserves_runtime_literals(english[key], value)
            for key, value in source.items()
        ):
            raise ValueError("Unsafe language placeholders or literals: " + locale)
        if "/full/" in relative.replace("\\", "/"):
            if set(source) != set(english):
                raise ValueError("Incomplete full addon locale: " + locale)
            full += 1
        elif "/supplements/" in relative.replace("\\", "/"):
            if len(source) >= len(english):
                raise ValueError("An upstream supplement covers all English keys: " + locale)
            supplements += 1
        else:
            raise ValueError("Unknown locale ownership: " + locale)
        entries.append(("assets/jei/lang/" + locale + ".json", file_path.read_bytes()))
    if full + supplements != 89:
        raise ValueError("Unexpected language ownership count")
    if "en_us" in files:
        raise ValueError("Never overwrite upstream JEI English with a bundled copy")
    return entries, {"full": full, "supplements": supplements, "keys": len(english)}


def build(output_dir: Path) -> Path:
    cfg = approved_metadata()
    locales, counts = staged_language_resources()
    with tempfile.TemporaryDirectory(prefix="jei-26.3-next-") as scratch:
        work = Path(scratch)
        entry_class = nf.compile_entrypoint(cfg, CANDIDATE_VERSION, work)
        metadata = nf.neoforge_mods_toml(cfg, CANDIDATE_VERSION)
        data = entry_class.read_bytes()
        if struct.unpack(">H", data[6:8])[0] != 69:
            raise ValueError("Expected a Java 25 NeoForge entrypoint")

        manifest = (
            "Manifest-Version: 1.0\r\n"
            "Implementation-Title: JEI Translation Expansion\r\n"
            "Implementation-Version: " + CANDIDATE_VERSION + "\r\n"
            "Minecraft-Version: " + MINECRAFT + "\r\n"
            "JEI-Version: " + JEI_VERSION + "\r\n"
            "Java-Version: 25\r\n\r\n"
        ).encode("utf-8")
        contents = [
            ("META-INF/MANIFEST.MF", manifest),
            ("META-INF/neoforge.mods.toml", metadata),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (ROOT / "NOTICE").read_bytes()),
            (nf.base.MOD_CLASS_ENTRY, data),
            *locales,
        ]
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / ("jei-translation-expansion-" + CANDIDATE_VERSION
                               + "-mc26.3-neoforge.jar")
        with zipfile.ZipFile(output, "w") as archive:
            for name, data in sorted(contents, key=lambda item: item[0]):
                nf.base.add_bytes(archive, name, data)

    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        names = archive.namelist()
        if bad is not None or len(names) != len(set(names)):
            raise ValueError("Corrupt or duplicate JAR entries")
        if len([n for n in names if n.startswith("assets/jei/lang/") and n.endswith(".json")]) != 89:
            raise ValueError("Missing locale resource files")
        if "META-INF/neoforge.mods.toml" not in names or "META-INF/mods.toml" in names:
            raise ValueError("Incorrect NeoForge metadata")
        if nf.NEOFORGE_STUB_ENTRY in names or nf.base.FORGE_STUB_ENTRY in names:
            raise ValueError("Compile-time annotation stub leaked into the JAR")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"UNRELEASED candidate: {output}")
    print(f"Target JEI: {JEI_VERSION}; Minecraft: {MINECRAFT}; NeoForge; Java 25")
    print(f"Language resources: {counts['full']} full, {counts['supplements']} supplements; source keys: {counts['keys']}")
    print(f"SHA256: {digest}")
    print("This is NOT runtime tested. Do not publish or claim all search/font options work.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "build/next-26.3")
    args = parser.parse_args()
    build(args.output)

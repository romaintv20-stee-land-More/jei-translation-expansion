#!/usr/bin/env python3
"""Build review-only 26.1–26.2 NeoForge update candidates from audited staged JEI source.

NEVER publish these as fully translated or runtime-verified. The default game
language picker provides native search in the 26.x line. No untested legacy
GUI adapters are bundled in these JARs, nor any third-party font file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_completed_jar_neoforge as nf
from reconstruct_26_2 import preserves_runtime_literals

TARGETS = {
    "26.1": ("29.43.0.107", 562),
    "26.1.1": ("29.43.0.107", 562),
    "26.1.2": ("29.43.0.107", 562),
    "26.2": ("30.39.0.233", 613),
}
VERSION = "1.0.1-rc.1"
STAGED_ROOT = ROOT / "translations/staged-published-2026-10-11"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def metadata(mc: str, jei: str) -> dict:
    cfgs = load(ROOT / "packaging/completed-versions.json")["versions"]
    target = [cfg for cfg in cfgs if cfg["minecraft"] == mc]
    if len(target) != 1:
        raise ValueError("Manifest does not identify an exact Minecraft version: " + mc)
    cfg = dict(target[0])
    if cfg.get("loader") != "neoforge" or cfg["java_target"] != 25:
        raise ValueError("This builder supports only NeoForge 26.x with Java 25")
    cfg["jei"] = jei
    # Constrain compatibility to the exact audited JEI build, not an untested major version.
    cfg["jei_version_range"] = "[" + jei + "]"
    return cfg


def staged(mc: str, jei: str, expected_keys: int) -> tuple[list[tuple[str, bytes]], dict]:
    root = STAGED_ROOT / mc
    diff = load(root / "semantic-diff.json")
    if diff.get("minecraft") != mc or diff.get("new_jei") != jei:
        raise ValueError("Semantic audit does not match build target")
    if "source ONLY" not in diff.get("note", "").upper() and "Staged sources ONLY" not in diff.get("note", ""):
        raise ValueError("Audit must retain the staged-only limitation")
    english = load(root / "source/en_us.json")
    if len(english) != expected_keys or not all(isinstance(k, str) and isinstance(v, str)
                                                 and v.strip() for k, v in english.items()):
        raise ValueError("Unexpected upstream English baseline or incomplete values")
    entries = []
    ownership = {"full": 0, "supplement": 0}
    locales: set[str] = set()
    for folder in ("full", "supplements"):
        lang = root / folder / "assets/jei/lang"
        for path in sorted(lang.glob("*.json")):
            code = path.stem
            if not re.fullmatch(r"[a-z0-9_]+", code) or code in locales or code == "en_us":
                raise ValueError("Duplicate/invalid language code: " + code)
            values = load(path)
            if not values or not isinstance(values, dict) or set(values) - set(english):
                raise ValueError("Empty locale or keys outside target JEI version: " + code)
            if not all(isinstance(v, str) and v.strip() and preserves_runtime_literals(english[k], v)
                       for k, v in values.items()):
                raise ValueError("Untrusted interpolation/literal in: " + code)
            if folder == "full" and set(values) != set(english):
                raise ValueError("Incomplete full translation: " + code)
            if folder == "supplements" and len(values) >= len(english):
                raise ValueError("Supplement must not override all upstream keys: " + code)
            expected_owner = diff["locale_counts"][code]["ownership"]
            if folder == "full" and expected_owner != "full":
                raise ValueError("Full ownership does not match audited source: " + code)
            if folder == "supplements" and expected_owner == "full":
                raise ValueError("Supplement ownership mismatch: " + code)
            ownership["full" if folder == "full" else "supplement"] += 1
            entries.append((f"assets/jei/lang/{code}.json", path.read_bytes()))
            locales.add(code)
    if len(locales) != 89 or locales != set(diff["locale_counts"]):
        raise ValueError(f"Expected 89 locales for {mc}; got {len(locales)}")
    report = {
        "minecraft": mc, "jei_version": jei, "version": VERSION,
        "locale_files": len(locales), "source_keys": len(english),
        "ownership": ownership, "translation_fallbacks_to_english": diff["totals"]["english_fallback"],
        "native_search": True, "fonts_runtime_tested": False,
        "status": "REVIEW CANDIDATE; NOT TESTED IN-GAME; DO NOT PUBLISH AS STABLE",
    }
    return entries, report


def build(mc: str, output: Path) -> None:
    jei, expected_keys = TARGETS[mc]
    cfg = metadata(mc, jei)
    languages, report = staged(mc, jei, expected_keys)
    with tempfile.TemporaryDirectory(prefix=f"jei-{mc}-staged-") as tmp:
        work = Path(tmp)
        clazz = nf.compile_entrypoint(cfg, VERSION, work)
        if struct.unpack(">H", clazz.read_bytes()[6:8])[0] != 69:
            raise ValueError("Java-25 major-class mismatch")
        metadata_toml = nf.neoforge_mods_toml(cfg, VERSION)
        manifest = (
            "Manifest-Version: 1.0\r\n"
            "Implementation-Title: JEI Translation Expansion\r\n"
            f"Implementation-Version: {VERSION}\r\n"
            f"Minecraft-Version: {mc}\r\n"
            f"JEI-Version: {jei}\r\n"
            "Java-Version: 25\r\n\r\n"
        ).encode()
        contents = [
            ("META-INF/MANIFEST.MF", manifest),
            ("META-INF/neoforge.mods.toml", metadata_toml),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (ROOT / "NOTICE").read_bytes()),
            (nf.base.MOD_CLASS_ENTRY, clazz.read_bytes()),
            *languages,
        ]
        output.mkdir(parents=True, exist_ok=True)
        filename = f"jei-translation-expansion-{VERSION}-mc{mc}-neoforge.jar"
        target = output / filename
        with zipfile.ZipFile(target, "w") as jar:
            for name, content in sorted(contents):
                nf.base.add_bytes(jar, name, content)
    with zipfile.ZipFile(target) as jar:
        if jar.testzip() is not None or len(set(jar.namelist())) != len(jar.namelist()):
            raise ValueError("Invalid output JAR ZIP")
        if sum(x.startswith("assets/jei/lang/") and x.endswith(".json") for x in jar.namelist()) != 89:
            raise ValueError("Incorrect number of language resources in compiled JAR")
        if nf.NEOFORGE_STUB_ENTRY in jar.namelist() or nf.base.FORGE_STUB_ENTRY in jar.namelist():
            raise ValueError("Compile-only annotation leaked into JAR")
        if "META-INF/mods.toml" in jar.namelist():
            raise ValueError("Forge metadata wrongly included in NeoForge JAR")
    report["jar_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    report["jar_filename"] = filename
    (output / f"report-mc{mc}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                                 encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minecraft", required=True, choices=sorted(TARGETS))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/updated-26x")
    args = parser.parse_args()
    build(args.minecraft, args.output_dir)


if __name__ == "__main__":
    main()

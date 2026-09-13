#!/usr/bin/env python3
"""Build a reproducible JEI Translation Expansion prototype JAR for Minecraft 1.8.

The JAR contains the 54 G1 addon-owned complete locale files, a tiny client-only
Forge @Mod entrypoint, metadata, LICENSE and NOTICE. Existing JEI 2.15.0 locales
are intentionally not packaged so upstream translations remain authoritative.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "1.8"
JAVA_TEMPLATE = PACKAGING / "src" / "JeiTranslationExpansion.java.in"
FORGE_MOD_STUB = PACKAGING / "compile-stubs" / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
MCMOD_TEMPLATE = PACKAGING / "mcmod.info.in"
TRANSLATIONS = ROOT / "translations" / "g1-mc1.8"
ENGLISH_SOURCE = ROOT / "upstream" / "sources" / "1.8" / "en_US.lang"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "releases" / "1.8"

MOD_CLASS_ENTRY = "io/github/romaintv20/jeitranslationexpansion/JeiTranslationExpansion.class"
FORGE_STUB_ENTRY = "net/minecraftforge/fml/common/Mod.class"
EXPECTED_FULL_LOCALES = 54
EXPECTED_KEY_COUNT = 58
UPSTREAM_OWNED = {"de_DE", "en_US", "fi_FI", "ko_KR", "ru_RU", "zh_CN"}
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_lang_keys(path: Path) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for lineno, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in raw:
            raise RuntimeError(f"Malformed .lang line {path}:{lineno}: {raw!r}")
        key = raw.split("=", 1)[0].strip()
        if not key:
            raise RuntimeError(f"Empty key at {path}:{lineno}")
        if key in seen:
            raise RuntimeError(f"Duplicate key {key!r} in {path}")
        seen.add(key)
        keys.append(key)
    return keys


def validate_locales() -> list[Path]:
    english_keys = parse_lang_keys(ENGLISH_SOURCE)
    if len(english_keys) != EXPECTED_KEY_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_KEY_COUNT} English keys, got {len(english_keys)}")
    english_set = set(english_keys)

    files = sorted(TRANSLATIONS.glob("*.lang"))
    if len(files) != EXPECTED_FULL_LOCALES:
        raise RuntimeError(f"Expected {EXPECTED_FULL_LOCALES} G1 locale files, got {len(files)}")

    locale_names = {p.stem for p in files}
    overlap = locale_names & UPSTREAM_OWNED
    if overlap:
        raise RuntimeError(f"G1 addon files unexpectedly overlap upstream JEI locales: {sorted(overlap)}")

    for path in files:
        keys = parse_lang_keys(path)
        key_set = set(keys)
        if len(keys) != EXPECTED_KEY_COUNT or key_set != english_set:
            missing = sorted(english_set - key_set)
            extra = sorted(key_set - english_set)
            raise RuntimeError(
                f"Locale {path.stem} does not exactly cover G1 English keys: "
                f"count={len(keys)} missing={missing} extra={extra}"
            )
    return files


def compile_entrypoint(version: str, work: Path) -> Path:
    src_root = work / "src"
    source = src_root / "io" / "github" / "romaintv20" / "jeitranslationexpansion" / "JeiTranslationExpansion.java"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(JAVA_TEMPLATE.read_text(encoding="utf-8").replace("@PROJECT_VERSION@", version), encoding="utf-8")

    stub_source = src_root / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
    stub_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FORGE_MOD_STUB, stub_source)

    classes = work / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "javac", "-source", "7", "-target", "7", "-Xlint:-options",
        "-d", str(classes), str(stub_source), str(source)
    ], check=True)

    if not (classes / MOD_CLASS_ENTRY).is_file():
        raise RuntimeError("Compiled Forge mod entrypoint is missing")
    if not (classes / FORGE_STUB_ENTRY).is_file():
        raise RuntimeError("Compile-only Forge annotation stub did not compile")
    return classes


def add_bytes(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build_jar(version: str, output_dir: Path) -> tuple[Path, str]:
    if not re.fullmatch(r"[0-9A-Za-z._-]+", version):
        raise ValueError("version may contain only letters, digits, dot, underscore and hyphen")

    locale_files = validate_locales()

    with tempfile.TemporaryDirectory(prefix="jei-translation-expansion-1.8-") as tmp_name:
        work = Path(tmp_name)
        classes = compile_entrypoint(version, work)

        mcmod = MCMOD_TEMPLATE.read_text(encoding="utf-8").replace("@PROJECT_VERSION@", version)
        metadata = json.loads(mcmod)
        if metadata[0]["modid"] != "jei_translation_expansion":
            raise RuntimeError("mcmod.info modid mismatch")
        if metadata[0]["mcversion"] != "1.8":
            raise RuntimeError("mcmod.info Minecraft version mismatch")

        manifest = (
            "Manifest-Version: 1.0\r\n"
            "Implementation-Title: JEI Translation Expansion\r\n"
            f"Implementation-Version: {version}\r\n"
            "Implementation-Vendor: romaintv20-stee-land-More\r\n"
            "\r\n"
        ).encode("utf-8")

        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"jei-translation-expansion-{version}-mc1.8-forge.jar"
        if output.exists():
            output.unlink()

        entries: list[tuple[str, bytes]] = [
            ("META-INF/MANIFEST.MF", manifest),
            ("mcmod.info", mcmod.encode("utf-8")),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (ROOT / "NOTICE").read_bytes()),
            (MOD_CLASS_ENTRY, (classes / MOD_CLASS_ENTRY).read_bytes()),
        ]
        for lang_file in locale_files:
            entries.append((f"assets/jei/lang/{lang_file.name}", lang_file.read_bytes()))

        with zipfile.ZipFile(output, "w") as zf:
            for arcname, data in sorted(entries, key=lambda item: item[0]):
                add_bytes(zf, arcname, data)

        with zipfile.ZipFile(output, "r") as zf:
            names = set(zf.namelist())
            packaged_lang = sorted(n for n in names if n.startswith("assets/jei/lang/") and n.endswith(".lang"))
            if len(packaged_lang) != EXPECTED_FULL_LOCALES:
                raise RuntimeError(f"Built JAR has {len(packaged_lang)} language files, expected {EXPECTED_FULL_LOCALES}")
            if MOD_CLASS_ENTRY not in names:
                raise RuntimeError("Built JAR is missing the Forge @Mod entrypoint")
            if FORGE_STUB_ENTRY in names:
                raise RuntimeError("Compile-only Forge annotation stub leaked into built JAR")
            if "assets/jei/lang/en_US.lang" in names:
                raise RuntimeError("Upstream-owned en_US.lang must not be packaged")
            for locale in UPSTREAM_OWNED:
                if f"assets/jei/lang/{locale}.lang" in names:
                    raise RuntimeError(f"Upstream-owned locale unexpectedly packaged: {locale}")

        return output, sha256_file(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0-ci")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    output, digest = build_jar(args.version, args.output_dir)
    print("PASS: built Minecraft 1.8 Forge prototype JAR")
    print(f"Output: {output}")
    print(f"SHA256: {digest}")
    print(f"Packaged language resources: {EXPECTED_FULL_LOCALES} full addon locales")
    print(f"Keys per locale: {EXPECTED_KEY_COUNT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

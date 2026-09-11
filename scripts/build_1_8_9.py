#!/usr/bin/env python3
"""Build a reproducible JEI Translation Expansion JAR for Minecraft 1.8.9.

The build uses a tiny client-only Forge @Mod class so FML discovers the JAR and
Minecraft adds its assets to the resource manager. It packages:
- 54 complete locales absent from upstream JEI;
- 5 partial locale supplements that contain only keys missing upstream;
- minimal Forge metadata/stub code;
- LICENSE and NOTICE.

The final release archive policy is still separate: only runtime-tested builds
should be copied to release-jars/1.8.9/.
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
import urllib.request
import zipfile

from reconstruct_1_8_9 import reconstruct_all

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "1.8.9"
JAVA_TEMPLATE = PACKAGING / "src" / "JeiTranslationExpansion.java.in"
MCMOD_TEMPLATE = PACKAGING / "mcmod.info.in"
SUPPLEMENTS = ROOT / "translations" / "g2-mc1.8.9" / "upstream-supplements"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "releases" / "1.8.9"
DEFAULT_CACHE_DIR = ROOT / "build" / "cache" / "forge"

FORGE_VERSION = "1.8.9-11.15.1.1855"
FORGE_FILENAME = f"forge-{FORGE_VERSION}-universal.jar"
FORGE_SHA1 = "4eb58f00059a9b3aaf386330491b58ffa5300d35"
FORGE_URLS = (
    f"https://maven.minecraftforge.net/net/minecraftforge/forge/{FORGE_VERSION}/{FORGE_FILENAME}",
    f"https://files.minecraftforge.net/maven/net/minecraftforge/forge/{FORGE_VERSION}/{FORGE_FILENAME}",
)

MOD_CLASS_ENTRY = "io/github/romaintv20/jeitranslationexpansion/JeiTranslationExpansion.class"
EXPECTED_FULL_LOCALES = 54
EXPECTED_SUPPLEMENTS = {"de_DE", "fi_FI", "ko_KR", "ru_RU", "zh_CN"}
EXPECTED_LANG_FILES = EXPECTED_FULL_LOCALES + len(EXPECTED_SUPPLEMENTS)
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_forge_jar(path: Path) -> Path:
    if path.is_file() and sha1_file(path) == FORGE_SHA1:
        return path
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    for url in FORGE_URLS:
        try:
            print(f"Downloading Forge compile dependency: {url}")
            with urllib.request.urlopen(url, timeout=60) as response, path.open("wb") as out:
                shutil.copyfileobj(response, out)
            actual = sha1_file(path)
            if actual != FORGE_SHA1:
                errors.append(f"{url}: SHA1 {actual} != expected {FORGE_SHA1}")
                path.unlink(missing_ok=True)
                continue
            return path
        except Exception as exc:  # pragma: no cover - network-dependent
            errors.append(f"{url}: {exc}")
            path.unlink(missing_ok=True)

    raise RuntimeError("Unable to download verified Forge JAR:\n- " + "\n- ".join(errors))


def compile_stub(version: str, forge_jar: Path, work: Path) -> Path:
    src_root = work / "src"
    source = src_root / "io" / "github" / "romaintv20" / "jeitranslationexpansion" / "JeiTranslationExpansion.java"
    source.parent.mkdir(parents=True, exist_ok=True)
    text = JAVA_TEMPLATE.read_text(encoding="utf-8").replace("@PROJECT_VERSION@", version)
    source.write_text(text, encoding="utf-8")

    classes = work / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    cmd = [
        "javac",
        "-source", "7",
        "-target", "7",
        "-Xlint:-options",
        "-classpath", str(forge_jar),
        "-d", str(classes),
        str(source),
    ]
    subprocess.run(cmd, check=True)
    class_file = classes / MOD_CLASS_ENTRY
    if not class_file.is_file():
        raise RuntimeError(f"Compiled mod class missing: {class_file}")
    return classes


def add_bytes(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build_jar(version: str, forge_jar: Path, output_dir: Path) -> tuple[Path, str]:
    if not re.fullmatch(r"[0-9A-Za-z._-]+", version):
        raise ValueError("version may contain only letters, digits, dot, underscore and hyphen")

    with tempfile.TemporaryDirectory(prefix="jei-translation-expansion-1.8.9-") as tmp_name:
        work = Path(tmp_name)
        lang_dir = work / "resources" / "assets" / "jei" / "lang"
        full_count, key_count = reconstruct_all(lang_dir)
        if full_count != EXPECTED_FULL_LOCALES or key_count != 75:
            raise RuntimeError(
                f"Unexpected reconstructed locale result: locales={full_count}, keys={key_count}"
            )

        supplement_files = sorted(SUPPLEMENTS.glob("*.lang"))
        supplement_locales = {p.stem for p in supplement_files}
        if supplement_locales != EXPECTED_SUPPLEMENTS:
            raise RuntimeError(
                f"Unexpected supplement set: {sorted(supplement_locales)}"
            )
        for source in supplement_files:
            shutil.copy2(source, lang_dir / source.name)

        lang_files = sorted(lang_dir.glob("*.lang"))
        if len(lang_files) != EXPECTED_LANG_FILES:
            raise RuntimeError(f"Expected {EXPECTED_LANG_FILES} packaged language files, got {len(lang_files)}")
        if (lang_dir / "en_US.lang").exists():
            raise RuntimeError("en_US.lang must not be packaged; upstream JEI owns the English source")

        classes = compile_stub(version, forge_jar, work)
        mcmod = MCMOD_TEMPLATE.read_text(encoding="utf-8").replace("@PROJECT_VERSION@", version)
        parsed_metadata = json.loads(mcmod)
        if parsed_metadata[0]["modid"] != "jei_translation_expansion":
            raise RuntimeError("mcmod.info modid mismatch")
        if parsed_metadata[0]["mcversion"] != "1.8.9":
            raise RuntimeError("mcmod.info Minecraft version mismatch")

        manifest = (
            "Manifest-Version: 1.0\r\n"
            "Implementation-Title: JEI Translation Expansion\r\n"
            f"Implementation-Version: {version}\r\n"
            "Implementation-Vendor: romaintv20-stee-land-More\r\n"
            "\r\n"
        ).encode("utf-8")

        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"jei-translation-expansion-{version}-mc1.8.9-forge.jar"
        output.unlink(missing_ok=True)

        entries: list[tuple[str, bytes]] = [
            ("META-INF/MANIFEST.MF", manifest),
            ("mcmod.info", mcmod.encode("utf-8")),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (ROOT / "NOTICE").read_bytes()),
        ]

        for class_file in sorted(classes.rglob("*.class")):
            entries.append((class_file.relative_to(classes).as_posix(), class_file.read_bytes()))
        for lang_file in lang_files:
            entries.append((f"assets/jei/lang/{lang_file.name}", lang_file.read_bytes()))

        with zipfile.ZipFile(output, "w") as zf:
            for arcname, data in sorted(entries, key=lambda item: item[0]):
                add_bytes(zf, arcname, data)

        with zipfile.ZipFile(output, "r") as zf:
            names = set(zf.namelist())
            if MOD_CLASS_ENTRY not in names:
                raise RuntimeError("built JAR is missing the Forge @Mod class")
            if "mcmod.info" not in names or "META-INF/MANIFEST.MF" not in names:
                raise RuntimeError("built JAR is missing required metadata")
            packaged_lang = [n for n in names if n.startswith("assets/jei/lang/") and n.endswith(".lang")]
            if len(packaged_lang) != EXPECTED_LANG_FILES:
                raise RuntimeError(f"built JAR has {len(packaged_lang)} language files, expected {EXPECTED_LANG_FILES}")

        digest = sha256_file(output)
        return output, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0-dev")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--forge-jar", type=Path, default=DEFAULT_CACHE_DIR / FORGE_FILENAME)
    args = parser.parse_args()

    forge_jar = ensure_forge_jar(args.forge_jar)
    output, digest = build_jar(args.version, forge_jar, args.output_dir)
    print("PASS: built Minecraft 1.8.9 Forge JAR")
    print(f"Output: {output}")
    print(f"SHA256: {digest}")
    print(f"Packaged language resources: {EXPECTED_LANG_FILES} (54 full + 5 upstream supplements)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a reproducible JEI Translation Expansion JAR for Minecraft 1.8.9.

The build uses a tiny client-only Forge @Mod class so FML discovers the JAR and
Minecraft adds its assets to the resource manager. It packages:
- 54 complete locales absent from upstream JEI;
- 5 partial locale supplements containing only keys missing upstream;
- minimal Forge metadata/stub code;
- LICENSE and NOTICE.

To keep CI independent from legacy ForgeGradle/Maven availability, javac compiles
against a tiny compile-only copy of the public @Mod annotation signature. That
stub is never packaged. At runtime Forge provides the real annotation class.

Only runtime-tested builds should later be copied to release-jars/1.8.9/.
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

from reconstruct_1_8_9 import reconstruct_all

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "1.8.9"
JAVA_TEMPLATE = PACKAGING / "src" / "JeiTranslationExpansion.java.in"
FORGE_MOD_STUB = PACKAGING / "compile-stubs" / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
MCMOD_TEMPLATE = PACKAGING / "mcmod.info.in"
SUPPLEMENTS = ROOT / "translations" / "g2-mc1.8.9" / "upstream-supplements"
DEFAULT_OUTPUT_DIR = ROOT / "build" / "releases" / "1.8.9"

MOD_CLASS_ENTRY = "io/github/romaintv20/jeitranslationexpansion/JeiTranslationExpansion.class"
FORGE_STUB_ENTRY = "net/minecraftforge/fml/common/Mod.class"
EXPECTED_FULL_LOCALES = 54
EXPECTED_SUPPLEMENTS = {"de_DE", "fi_FI", "ko_KR", "ru_RU", "zh_CN"}
EXPECTED_LANG_FILES = EXPECTED_FULL_LOCALES + len(EXPECTED_SUPPLEMENTS)
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compile_stub(version: str, work: Path) -> Path:
    src_root = work / "src"
    source = src_root / "io" / "github" / "romaintv20" / "jeitranslationexpansion" / "JeiTranslationExpansion.java"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        JAVA_TEMPLATE.read_text(encoding="utf-8").replace("@PROJECT_VERSION@", version),
        encoding="utf-8",
    )

    compile_stub_source = src_root / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
    compile_stub_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FORGE_MOD_STUB, compile_stub_source)

    classes = work / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "javac",
            "-source", "7",
            "-target", "7",
            "-Xlint:-options",
            "-d", str(classes),
            str(compile_stub_source),
            str(source),
        ],
        check=True,
    )

    class_file = classes / MOD_CLASS_ENTRY
    if not class_file.is_file():
        raise RuntimeError(f"Compiled mod class missing: {class_file}")
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
            raise RuntimeError(f"Unexpected supplement set: {sorted(supplement_locales)}")
        for source in supplement_files:
            shutil.copy2(source, lang_dir / source.name)

        lang_files = sorted(lang_dir.glob("*.lang"))
        if len(lang_files) != EXPECTED_LANG_FILES:
            raise RuntimeError(f"Expected {EXPECTED_LANG_FILES} packaged language files, got {len(lang_files)}")
        if (lang_dir / "en_US.lang").exists():
            raise RuntimeError("en_US.lang must not be packaged; upstream JEI owns the English source")

        classes = compile_stub(version, work)
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
            (MOD_CLASS_ENTRY, (classes / MOD_CLASS_ENTRY).read_bytes()),
        ]
        for lang_file in lang_files:
            entries.append((f"assets/jei/lang/{lang_file.name}", lang_file.read_bytes()))

        with zipfile.ZipFile(output, "w") as zf:
            for arcname, data in sorted(entries, key=lambda item: item[0]):
                add_bytes(zf, arcname, data)

        with zipfile.ZipFile(output, "r") as zf:
            names = set(zf.namelist())
            if MOD_CLASS_ENTRY not in names:
                raise RuntimeError("built JAR is missing the Forge @Mod class")
            if FORGE_STUB_ENTRY in names:
                raise RuntimeError("compile-only Forge annotation stub leaked into built JAR")
            if "mcmod.info" not in names or "META-INF/MANIFEST.MF" not in names:
                raise RuntimeError("built JAR is missing required metadata")
            packaged_lang = [n for n in names if n.startswith("assets/jei/lang/") and n.endswith(".lang")]
            if len(packaged_lang) != EXPECTED_LANG_FILES:
                raise RuntimeError(f"built JAR has {len(packaged_lang)} language files, expected {EXPECTED_LANG_FILES}")

        return output, sha256_file(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="0.1.0-dev")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    output, digest = build_jar(args.version, args.output_dir)
    print("PASS: built Minecraft 1.8.9 Forge JAR")
    print(f"Output: {output}")
    print(f"SHA256: {digest}")
    print(f"Packaged language resources: {EXPECTED_LANG_FILES} (54 full + 5 upstream supplements)")
    print("Forge compile strategy: verified annotation stub, compile-only and not packaged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
'''Build one static-validated JEI Translation Expansion JAR for a completed generation.'''
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "packaging" / "completed-versions.json"
MOD_ID = "jei_translation_expansion"
MOD_NAME = "JEI Translation Expansion"
MOD_CLASS_ENTRY = "io/github/romaintv20/jeitranslationexpansion/JeiTranslationExpansion.class"
FORGE_STUB_ENTRY = "net/minecraftforge/fml/common/Mod.class"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def load_config(minecraft: str) -> tuple[dict, dict]:
    root = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for cfg in root["versions"]:
        if cfg["minecraft"] == minecraft:
            return root, cfg
    raise ValueError(f"Minecraft {minecraft} is not a completed packaging target")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_lang(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in raw:
            raise ValueError(f"{path}:{lineno}: invalid .lang line")
        key, value = raw.split("=", 1)
        key = key.strip()
        if key in data:
            raise ValueError(f"{path}:{lineno}: duplicate key {key}")
        data[key] = value
    return data


def resource_key_count(path: Path, fmt: str) -> int:
    if fmt == "lang":
        return len(parse_lang(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: JSON language root must be an object")
    for key, value in data.items():
        if not key.startswith("_comment") and not isinstance(value, str):
            raise ValueError(f"{path}: non-string language value for {key}")
    return len([key for key in data if not key.startswith("_comment")])


def reconstruct(cfg: dict, work: Path) -> tuple[list[Path], list[Path]]:
    fmt = cfg["format"]
    ext = f".{fmt}"
    mode = cfg.get("reconstruct_mode", "standard")
    if mode == "g1-direct":
        full_dir = ROOT / "translations" / "g1-mc1.8"
        full = sorted(full_dir.glob(f"*{ext}"))
        supplements: list[Path] = []
    elif mode == "g2-special":
        full_dir = work / "reconstructed" / "assets" / "jei" / "lang"
        subprocess.run(
            [sys.executable, str(ROOT / cfg["reconstruct_script"]), "--output", str(full_dir)],
            cwd=ROOT,
            check=True,
        )
        full = sorted(full_dir.glob(f"*{ext}"))
        supplement_dir = ROOT / "translations" / "g2-mc1.8.9" / "upstream-supplements"
        supplements = sorted(supplement_dir.glob(f"*{ext}"))
    else:
        out = work / "reconstructed"
        subprocess.run(
            [sys.executable, str(ROOT / cfg["reconstruct_script"]), "--output", str(out)],
            cwd=ROOT,
            check=True,
        )
        full_dir = out / "full" / "assets" / "jei" / "lang"
        supplement_dir = out / "supplements" / "assets" / "jei" / "lang"
        full = sorted(full_dir.glob(f"*{ext}"))
        supplements = sorted(supplement_dir.glob(f"*{ext}"))

    if len(full) != cfg["full"]:
        raise RuntimeError(f"{cfg['minecraft']}: expected {cfg['full']} full locales, got {len(full)}")
    if len(supplements) != cfg["supplements"]:
        raise RuntimeError(
            f"{cfg['minecraft']}: expected {cfg['supplements']} supplements, got {len(supplements)}"
        )
    overlap = {p.name for p in full} & {p.name for p in supplements}
    if overlap:
        raise RuntimeError(f"{cfg['minecraft']}: full/supplement ownership overlaps: {sorted(overlap)}")
    for path in full:
        count = resource_key_count(path, fmt)
        if count != cfg["keys"]:
            raise RuntimeError(
                f"{cfg['minecraft']} {path.name}: expected {cfg['keys']} complete keys, got {count}"
            )
    for path in supplements:
        count = resource_key_count(path, fmt)
        if count <= 0 or count >= cfg["keys"]:
            raise RuntimeError(f"{cfg['minecraft']} {path.name}: invalid supplement key count {count}")
    return full, supplements


def legacy_source(version: str, cfg: dict) -> str:
    deps = f"required-after:Forge;required-after:{cfg['jei_modid']}@[{cfg['jei']}]"
    lines = [
        "package io.github.romaintv20.jeitranslationexpansion;",
        "",
        "import net.minecraftforge.fml.common.Mod;",
        "",
        "@Mod(",
        "    modid = JeiTranslationExpansion.MOD_ID,",
        "    name = JeiTranslationExpansion.NAME,",
        "    version = JeiTranslationExpansion.VERSION,",
        "    clientSideOnly = true,",
        f'    acceptedMinecraftVersions = "[{cfg["minecraft"]}]",',
        '    acceptableRemoteVersions = "*",',
        f'    dependencies = "{deps}"',
        ")",
        "public final class JeiTranslationExpansion {",
        f'    public static final String MOD_ID = "{MOD_ID}";',
        f'    public static final String NAME = "{MOD_NAME}";',
        f'    public static final String VERSION = "{version}";',
        "",
        "    public JeiTranslationExpansion() {",
        "    }",
        "}",
        "",
    ]
    return "\n".join(lines)


def legacy_stub() -> str:
    return "\n".join([
        "package net.minecraftforge.fml.common;",
        "",
        "import java.lang.annotation.ElementType;",
        "import java.lang.annotation.Retention;",
        "import java.lang.annotation.RetentionPolicy;",
        "import java.lang.annotation.Target;",
        "",
        "@Retention(RetentionPolicy.RUNTIME)",
        "@Target(ElementType.TYPE)",
        "public @interface Mod {",
        "    String modid();",
        '    String name() default "";',
        '    String version() default "";',
        '    String dependencies() default "";',
        "    boolean clientSideOnly() default false;",
        '    String acceptedMinecraftVersions() default "";',
        '    String acceptableRemoteVersions() default "";',
        "}",
        "",
    ])


def modern_source() -> str:
    return "\n".join([
        "package io.github.romaintv20.jeitranslationexpansion;",
        "",
        "import net.minecraftforge.fml.common.Mod;",
        "",
        f'@Mod("{MOD_ID}")',
        "public final class JeiTranslationExpansion {",
        "    public JeiTranslationExpansion() {",
        "    }",
        "}",
        "",
    ])


def modern_stub() -> str:
    return "\n".join([
        "package net.minecraftforge.fml.common;",
        "",
        "import java.lang.annotation.ElementType;",
        "import java.lang.annotation.Retention;",
        "import java.lang.annotation.RetentionPolicy;",
        "import java.lang.annotation.Target;",
        "",
        "@Retention(RetentionPolicy.RUNTIME)",
        "@Target(ElementType.TYPE)",
        "public @interface Mod {",
        "    String value();",
        "}",
        "",
    ])


def compile_entrypoint(cfg: dict, version: str, work: Path) -> Path:
    src = work / "src"
    source = src / "io" / "github" / "romaintv20" / "jeitranslationexpansion" / "JeiTranslationExpansion.java"
    stub = src / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
    source.parent.mkdir(parents=True, exist_ok=True)
    stub.parent.mkdir(parents=True, exist_ok=True)
    if cfg["era"] == "legacy":
        source.write_text(legacy_source(version, cfg), encoding="utf-8")
        stub.write_text(legacy_stub(), encoding="utf-8")
    else:
        source.write_text(modern_source(), encoding="utf-8")
        stub.write_text(modern_stub(), encoding="utf-8")
    classes = work / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["javac", "--release", str(cfg["java_target"]), "-d", str(classes), str(stub), str(source)],
        check=True,
    )
    class_file = classes / MOD_CLASS_ENTRY
    stub_class = classes / FORGE_STUB_ENTRY
    if not class_file.is_file() or not stub_class.is_file():
        raise RuntimeError("javac did not produce the expected classes")
    data = class_file.read_bytes()
    major = struct.unpack(">H", data[6:8])[0]
    expected_major = {7: 51, 8: 52, 16: 60, 17: 61}[cfg["java_target"]]
    if major != expected_major:
        raise RuntimeError(f"unexpected class major {major}, expected {expected_major}")
    if b"Lnet/minecraftforge/fml/common/Mod;" not in data:
        raise RuntimeError("Forge @Mod runtime annotation descriptor is missing")
    return class_file


def mcmod_info(cfg: dict, version: str) -> bytes:
    data = [{
        "modid": MOD_ID,
        "name": MOD_NAME,
        "description": (
            f"Unofficial JEI localization expansion for Minecraft {cfg['minecraft']}. "
            "Translations may be AI-assisted and are validated by project QA."
        ),
        "version": version,
        "mcversion": cfg["minecraft"],
        "url": "https://github.com/romaintv20-stee-land-More/jei-translation-expansion",
        "updateUrl": "",
        "authorList": ["romaintv20-stee-land-More"],
        "credits": (
            "Unofficial localization companion for Just Enough Items (JEI). "
            "AI-assisted translations are explicitly disclosed."
        ),
        "logoFile": "",
        "screenshots": [],
        "dependencies": [],
    }]
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def mods_toml(cfg: dict, version: str) -> bytes:
    text = (
        'modLoader="javafml"\n'
        'loaderVersion="[13,)"\n'
        'license="MIT"\n'
        'displayURL="https://github.com/romaintv20-stee-land-More/jei-translation-expansion"\n'
        'authors="romaintv20-stee-land-More"\n\n'
        '[[mods]]\n'
        f'modId="{MOD_ID}"\n'
        f'version="{version}"\n'
        f'displayName="{MOD_NAME}"\n'
        "description='''\n"
        "Unofficial localization companion for Just Enough Items (JEI).\n"
        "Translations may be AI-assisted and are validated by project QA.\n"
        "'''\n\n"
        f'[[dependencies.{MOD_ID}]]\n'
        'modId="minecraft"\n'
        'mandatory=true\n'
        f'versionRange="[{cfg["minecraft"]}]"\n'
        'ordering="NONE"\n'
        'side="CLIENT"\n\n'
        f'[[dependencies.{MOD_ID}]]\n'
        f'modId="{cfg["jei_modid"]}"\n'
        'mandatory=true\n'
        f'versionRange="[{cfg["jei"]}]"\n'
        'ordering="AFTER"\n'
        'side="CLIENT"\n'
    )
    return text.encode("utf-8")


def add_bytes(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build(cfg: dict, version: str, output_dir: Path) -> tuple[Path, str]:
    if not re.fullmatch(r"[0-9A-Za-z._-]+", version):
        raise ValueError("project version contains unsupported characters")
    with tempfile.TemporaryDirectory(prefix=f"jei-translation-expansion-{cfg['minecraft']}-") as tmp:
        work = Path(tmp)
        full, supplements = reconstruct(cfg, work)
        class_file = compile_entrypoint(cfg, version, work)
        manifest = (
            "Manifest-Version: 1.0\r\n"
            f"Implementation-Title: {MOD_NAME}\r\n"
            f"Implementation-Version: {version}\r\n"
            "Implementation-Vendor: romaintv20-stee-land-More\r\n"
            "\r\n"
        ).encode("utf-8")
        entries: list[tuple[str, bytes]] = [
            ("META-INF/MANIFEST.MF", manifest),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (ROOT / "NOTICE").read_bytes()),
            (MOD_CLASS_ENTRY, class_file.read_bytes()),
        ]
        if cfg["era"] == "legacy":
            entries.append(("mcmod.info", mcmod_info(cfg, version)))
        else:
            entries.append(("META-INF/mods.toml", mods_toml(cfg, version)))
        for path in [*full, *supplements]:
            entries.append((f"assets/jei/lang/{path.name}", path.read_bytes()))

        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"jei-translation-expansion-{version}-mc{cfg['minecraft']}-forge.jar"
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w") as zf:
            for arcname, data in sorted(entries, key=lambda item: item[0]):
                add_bytes(zf, arcname, data)

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            if len(names) != len(set(names)):
                raise RuntimeError("duplicate paths found inside JAR")
            if FORGE_STUB_ENTRY in names:
                raise RuntimeError("compile-only Forge annotation stub leaked into JAR")
            if MOD_CLASS_ENTRY not in names:
                raise RuntimeError("JAR is missing its Forge entrypoint")
            if cfg["era"] == "legacy" and "mcmod.info" not in names:
                raise RuntimeError("legacy JAR is missing mcmod.info")
            if cfg["era"] == "modern" and "META-INF/mods.toml" not in names:
                raise RuntimeError("modern JAR is missing META-INF/mods.toml")
            ext = f".{cfg['format']}"
            language_entries = [
                n for n in names if n.startswith("assets/jei/lang/") and n.endswith(ext)
            ]
            expected = cfg["full"] + cfg["supplements"]
            if len(language_entries) != expected:
                raise RuntimeError(
                    f"JAR contains {len(language_entries)} language files, expected {expected}"
                )
        return output, sha256_file(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minecraft", required=True)
    parser.add_argument("--version")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root, cfg = load_config(args.minecraft)
    version = args.version or root["project_version"]
    output_dir = args.output_dir or (ROOT / "build" / "completed-jars" / cfg["minecraft"])
    output, digest = build(cfg, version, output_dir)
    print(f"PASS: {cfg['generation']} Minecraft {cfg['minecraft']} / JEI {cfg['jei']}")
    print(f"Output: {output}")
    print(f"SHA256: {digest}")
    print(
        f"Resources: {cfg['full']} full + {cfg['supplements']} supplements = "
        f"{cfg['full'] + cfg['supplements']}"
    )
    print(
        f"Complete-locale keys: {cfg['keys']}; format: {cfg['format']}; "
        f"Java target: {cfg['java_target']}"
    )
    print("Status: static-validated release candidate; runtime promotion is separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

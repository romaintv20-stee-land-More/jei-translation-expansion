#!/usr/bin/env python3
"""Build static-validated completed candidates for NeoForge Java-21/25 targets.

This wrapper intentionally leaves the historical Forge builder untouched. It reuses the
same deterministic resource reconstruction and ZIP assembly primitives, but emits a
NeoForge @Mod entrypoint and META-INF/neoforge.mods.toml metadata.
"""
from __future__ import annotations

import struct
import subprocess
import tempfile
import tomllib
import zipfile
from pathlib import Path

import build_completed_jar as base

NEOFORGE_STUB_ENTRY = "net/neoforged/fml/common/Mod.class"
SUPPORTED_JAVA_TARGETS = {21, 25}


def neoforge_source() -> str:
    return "\n".join([
        "package io.github.romaintv20.jeitranslationexpansion;",
        "",
        "import net.neoforged.fml.common.Mod;",
        "",
        f'@Mod("{base.MOD_ID}")',
        "public final class JeiTranslationExpansion {",
        "    public JeiTranslationExpansion() {",
        "    }",
        "}",
        "",
    ])


def neoforge_stub() -> str:
    return "\n".join([
        "package net.neoforged.fml.common;",
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
    if cfg.get("loader") != "neoforge":
        raise ValueError("NeoForge builder requires loader=neoforge")
    src = work / "src"
    source = src / "io" / "github" / "romaintv20" / "jeitranslationexpansion" / "JeiTranslationExpansion.java"
    stub = src / "net" / "neoforged" / "fml" / "common" / "Mod.java"
    source.parent.mkdir(parents=True, exist_ok=True)
    stub.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(neoforge_source(), encoding="utf-8")
    stub.write_text(neoforge_stub(), encoding="utf-8")

    classes = work / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    java_target = int(cfg["java_target"])
    if java_target not in SUPPORTED_JAVA_TARGETS:
        raise ValueError(f"unsupported NeoForge Java target: {java_target}")
    subprocess.run(
        ["javac", "--release", str(java_target), "-d", str(classes), str(stub), str(source)],
        check=True,
    )
    class_file = classes / base.MOD_CLASS_ENTRY
    stub_class = classes / NEOFORGE_STUB_ENTRY
    if not class_file.is_file() or not stub_class.is_file():
        raise RuntimeError("javac did not produce the expected NeoForge entrypoint classes")
    data = class_file.read_bytes()
    major = struct.unpack(">H", data[6:8])[0]
    expected_major = 44 + java_target
    if major != expected_major:
        raise RuntimeError(f"unexpected class major {major}, expected {expected_major}")
    if b"Lnet/neoforged/fml/common/Mod;" not in data:
        raise RuntimeError("NeoForge @Mod runtime annotation descriptor is missing")
    if b"Lnet/minecraftforge/fml/common/Mod;" in data:
        raise RuntimeError("Forge @Mod descriptor leaked into NeoForge entrypoint")
    return class_file


def neoforge_mods_toml(cfg: dict, version: str) -> bytes:
    required = ("neoforge", "loader_version_range", "neoforge_version_range")
    missing = [key for key in required if not cfg.get(key)]
    if missing:
        raise ValueError(f"NeoForge packaging config missing: {', '.join(missing)}")
    text = (
        'modLoader="javafml"\n'
        f'loaderVersion="{cfg["loader_version_range"]}"\n'
        'license="MIT"\n\n'
        '[[mods]]\n'
        f'modId="{base.MOD_ID}"\n'
        f'version="{version}"\n'
        f'displayName="{base.MOD_NAME}"\n'
        'displayURL="https://github.com/romaintv20-stee-land-More/jei-translation-expansion"\n'
        'authors="romaintv20-stee-land-More"\n'
        "description='''\n"
        "Unofficial localization companion for Just Enough Items (JEI).\n"
        "Translations may be AI-assisted and are validated by project QA.\n"
        "'''\n\n"
        f'[[dependencies.{base.MOD_ID}]]\n'
        'modId="neoforge"\n'
        'type="required"\n'
        f'versionRange="{cfg["neoforge_version_range"]}"\n'
        'ordering="NONE"\n'
        'side="CLIENT"\n\n'
        f'[[dependencies.{base.MOD_ID}]]\n'
        'modId="minecraft"\n'
        'type="required"\n'
        f'versionRange="[{cfg["minecraft"]}]"\n'
        'ordering="NONE"\n'
        'side="CLIENT"\n\n'
        f'[[dependencies.{base.MOD_ID}]]\n'
        f'modId="{cfg["jei_modid"]}"\n'
        'type="required"\n'
        f'versionRange="[{cfg["jei"]}]"\n'
        'ordering="AFTER"\n'
        'side="CLIENT"\n'
    )
    encoded = text.encode("utf-8")
    parsed = tomllib.loads(text)
    if parsed.get("modLoader") != "javafml" or parsed.get("loaderVersion") != cfg["loader_version_range"]:
        raise RuntimeError("generated NeoForge metadata failed loader validation")
    mods = parsed.get("mods", [])
    if len(mods) != 1 or mods[0].get("modId") != base.MOD_ID or mods[0].get("version") != version:
        raise RuntimeError("generated NeoForge metadata failed mod identity validation")
    deps = parsed.get("dependencies", {}).get(base.MOD_ID, [])
    dep_ids = {item.get("modId") for item in deps}
    if dep_ids != {"neoforge", "minecraft", cfg["jei_modid"]}:
        raise RuntimeError(f"generated NeoForge dependency set is invalid: {sorted(dep_ids)}")
    return encoded


def build(cfg: dict, version: str, output_dir: Path) -> tuple[Path, str]:
    if cfg.get("loader") != "neoforge":
        raise ValueError("NeoForge builder can only package NeoForge targets")
    java_target = int(cfg["java_target"])
    if java_target not in SUPPORTED_JAVA_TARGETS:
        raise ValueError(f"current NeoForge completed-candidate path does not support Java {java_target}")
    with tempfile.TemporaryDirectory(prefix=f"jei-translation-expansion-{cfg['minecraft']}-neoforge-") as tmp:
        work = Path(tmp)
        full, supplements = base.reconstruct(cfg, work)
        class_file = compile_entrypoint(cfg, version, work)
        metadata = neoforge_mods_toml(cfg, version)
        manifest = (
            "Manifest-Version: 1.0\r\n"
            f"Implementation-Title: {base.MOD_NAME}\r\n"
            f"Implementation-Version: {version}\r\n"
            "Implementation-Vendor: romaintv20-stee-land-More\r\n"
            f"Minecraft-Version: {cfg['minecraft']}\r\n"
            f"JEI-Version: {cfg['jei']}\r\n"
            f"NeoForge-Version: {cfg['neoforge']}\r\n"
            f"Java-Version: {java_target}\r\n"
            "\r\n"
        ).encode("utf-8")
        entries: list[tuple[str, bytes]] = [
            ("META-INF/MANIFEST.MF", manifest),
            ("META-INF/neoforge.mods.toml", metadata),
            ("LICENSE", (base.ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (base.ROOT / "NOTICE").read_bytes()),
            (base.MOD_CLASS_ENTRY, class_file.read_bytes()),
        ]
        for path in [*full, *supplements]:
            entries.append((f"assets/jei/lang/{path.name}", path.read_bytes()))

        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"jei-translation-expansion-{version}-mc{cfg['minecraft']}-neoforge.jar"
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w") as zf:
            for arcname, data in sorted(entries, key=lambda item: item[0]):
                base.add_bytes(zf, arcname, data)

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            if len(names) != len(set(names)):
                raise RuntimeError("duplicate paths found inside NeoForge JAR")
            if NEOFORGE_STUB_ENTRY in names or base.FORGE_STUB_ENTRY in names:
                raise RuntimeError("compile-only annotation stub leaked into NeoForge JAR")
            if base.MOD_CLASS_ENTRY not in names:
                raise RuntimeError("NeoForge JAR is missing its @Mod entrypoint")
            if "META-INF/neoforge.mods.toml" not in names:
                raise RuntimeError("NeoForge JAR is missing META-INF/neoforge.mods.toml")
            if "META-INF/mods.toml" in names or "mcmod.info" in names:
                raise RuntimeError("Forge/legacy metadata leaked into NeoForge JAR")
            parsed_metadata = tomllib.loads(zf.read("META-INF/neoforge.mods.toml").decode("utf-8"))
            if parsed_metadata.get("mods", [{}])[0].get("modId") != base.MOD_ID:
                raise RuntimeError("NeoForge JAR metadata mod id mismatch")
            language_entries = [
                name for name in names
                if name.startswith("assets/jei/lang/") and name.endswith(f".{cfg['format']}")
            ]
            expected = cfg["full"] + cfg["supplements"]
            if len(language_entries) != expected:
                raise RuntimeError(
                    f"NeoForge JAR contains {len(language_entries)} language files, expected {expected}"
                )
        return output, base.sha256_file(output)


base.build = build

if __name__ == "__main__":
    raise SystemExit(base.main())

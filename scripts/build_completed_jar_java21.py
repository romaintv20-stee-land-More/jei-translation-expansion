#!/usr/bin/env python3
"""Run completed-candidate packaging with Java 21 classfile support.

The historical builder remains unchanged for reproducibility. This wrapper replaces only
its entrypoint compiler so current Java-21 Minecraft targets can be packaged while reusing
the same deterministic resource/JAR assembly logic.
"""
from __future__ import annotations

import struct
import subprocess
from pathlib import Path

import build_completed_jar as base


def compile_entrypoint(cfg: dict, version: str, work: Path) -> Path:
    src = work / "src"
    source = src / "io" / "github" / "romaintv20" / "jeitranslationexpansion" / "JeiTranslationExpansion.java"
    stub = src / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
    source.parent.mkdir(parents=True, exist_ok=True)
    stub.parent.mkdir(parents=True, exist_ok=True)
    if cfg["era"] == "legacy":
        source.write_text(base.legacy_source(version, cfg), encoding="utf-8")
        stub.write_text(base.legacy_stub(), encoding="utf-8")
    else:
        source.write_text(base.modern_source(), encoding="utf-8")
        stub.write_text(base.modern_stub(), encoding="utf-8")

    classes = work / "classes"
    classes.mkdir(parents=True, exist_ok=True)
    java_target = int(cfg["java_target"])
    subprocess.run(
        ["javac", "--release", str(java_target), "-d", str(classes), str(stub), str(source)],
        check=True,
    )
    class_file = classes / base.MOD_CLASS_ENTRY
    stub_class = classes / base.FORGE_STUB_ENTRY
    if not class_file.is_file() or not stub_class.is_file():
        raise RuntimeError("javac did not produce the expected classes")
    data = class_file.read_bytes()
    major = struct.unpack(">H", data[6:8])[0]
    expected_major = 44 + java_target
    if major != expected_major:
        raise RuntimeError(f"unexpected class major {major}, expected {expected_major}")
    if b"Lnet/minecraftforge/fml/common/Mod;" not in data:
        raise RuntimeError("Forge @Mod runtime annotation descriptor is missing")
    return class_file


base.compile_entrypoint = compile_entrypoint

if __name__ == "__main__":
    raise SystemExit(base.main())

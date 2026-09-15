#!/usr/bin/env python3
"""Build a non-publishable Fabric JAR for provisional Minecraft 26.3 RC2 QA.

This artifact exists only to validate resource packaging against the current Fabric RC branch.
It must never be copied to candidate-jars/ or registered in packaging/completed-versions.json.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import reconstruct_26_3_rc_2 as pre

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "build" / "provisional-jars" / "26.3-rc-2"
OUTPUT_NAME = "jei-translation-expansion-1.0.0-mc26.3-rc-2-fabric-provisional.jar"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
MOD_ID = "jei_translation_expansion"


def add_bytes(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fabric_metadata() -> bytes:
    data = {
        "schemaVersion": 1,
        "id": MOD_ID,
        "version": "1.0.0",
        "name": "JEI Translation Expansion",
        "description": (
            "Provisional QA-only localization companion for Just Enough Items (JEI) on "
            "Minecraft 26.3-rc-2. Not a publishable project release."
        ),
        "authors": ["romaintv20-stee-land-More"],
        "contact": {
            "homepage": "https://github.com/romaintv20-stee-land-More/jei-translation-expansion",
            "sources": "https://github.com/romaintv20-stee-land-More/jei-translation-expansion",
        },
        "license": "MIT",
        "environment": "client",
        "depends": {
            "fabricloader": ">=0.19.0",
            "minecraft": "=26.3-rc-2",
            "java": ">=25",
            "jei": "=30.32.0",
        },
        "custom": {
            "jei_translation_expansion:status": "provisional-rc-qa-only",
            "jei_translation_expansion:publishable": False,
            "jei_translation_expansion:upstream_commit": pre.PRE_G52_COMMIT,
        },
    }
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build() -> tuple[Path, str]:
    scope = json.loads(pre.SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(pre.POLICY_PATH.read_text(encoding="utf-8"))
    if scope.get("publishable_candidate") is not False:
        raise ValueError("refusing to build provisional JAR after publishability gate changed")
    if policy.get("packaging_registration_allowed") is not False:
        raise ValueError("refusing to build provisional JAR after packaging registration gate changed")

    with tempfile.TemporaryDirectory(prefix="jei-pre-g52-fabric-") as tmp:
        reconstructed = Path(tmp) / "reconstructed"
        full_count, supplement_count, key_count, _ = pre.reconstruct_all(reconstructed)
        if (full_count, supplement_count, key_count) != (63, 26, 334):
            raise ValueError("provisional reconstruction counts changed before packaging")
        full = sorted((reconstructed / "full" / "assets" / "jei" / "lang").glob("*.json"))
        supplements = sorted((reconstructed / "supplements" / "assets" / "jei" / "lang").glob("*.json"))
        if len(full) != 63 or len(supplements) != 26:
            raise ValueError("provisional resource inventory changed before packaging")

        manifest = (
            "Manifest-Version: 1.0\r\n"
            "Implementation-Title: JEI Translation Expansion\r\n"
            "Implementation-Version: 1.0.0\r\n"
            "Implementation-Vendor: romaintv20-stee-land-More\r\n"
            "Minecraft-Version: 26.3-rc-2\r\n"
            "JEI-Version: 30.32.0\r\n"
            "Fabric-Loader-Minimum: 0.19.0\r\n"
            "Java-Version: 25\r\n"
            "Project-Status: provisional-rc-qa-only\r\n"
            "\r\n"
        ).encode("utf-8")
        entries: list[tuple[str, bytes]] = [
            ("META-INF/MANIFEST.MF", manifest),
            ("fabric.mod.json", fabric_metadata()),
            ("LICENSE", (ROOT / "LICENSE").read_bytes()),
            ("NOTICE", (ROOT / "NOTICE").read_bytes()),
        ]
        for path in [*full, *supplements]:
            entries.append((f"assets/jei/lang/{path.name}", path.read_bytes()))

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output = OUTPUT_DIR / OUTPUT_NAME
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w") as zf:
            for arcname, data in sorted(entries, key=lambda item: item[0]):
                add_bytes(zf, arcname, data)

    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("duplicate paths found inside provisional Fabric JAR")
        if "fabric.mod.json" not in names:
            raise RuntimeError("provisional Fabric JAR is missing fabric.mod.json")
        forbidden = {"META-INF/mods.toml", "META-INF/neoforge.mods.toml", "mcmod.info"}
        leaked = forbidden & set(names)
        if leaked:
            raise RuntimeError(f"non-Fabric metadata leaked into provisional JAR: {sorted(leaked)}")
        metadata = json.loads(zf.read("fabric.mod.json").decode("utf-8"))
        if metadata.get("id") != MOD_ID or metadata.get("environment") != "client":
            raise RuntimeError("provisional Fabric metadata identity/environment mismatch")
        expected_deps = {
            "fabricloader": ">=0.19.0",
            "minecraft": "=26.3-rc-2",
            "java": ">=25",
            "jei": "=30.32.0",
        }
        if metadata.get("depends") != expected_deps:
            raise RuntimeError("provisional Fabric dependency metadata mismatch")
        custom = metadata.get("custom", {})
        if custom.get("jei_translation_expansion:publishable") is not False:
            raise RuntimeError("provisional Fabric metadata lost non-publishable marker")
        language_entries = [name for name in names if name.startswith("assets/jei/lang/") and name.endswith(".json")]
        if len(language_entries) != 89:
            raise RuntimeError(f"provisional Fabric JAR contains {len(language_entries)} language resources, expected 89")

    return output, sha256_file(output)


def main() -> int:
    output, digest = build()
    print("PASS: provisional Minecraft 26.3 RC2 Fabric packaging validation")
    print(f"Output: {output}")
    print("Language resources: 89 (63 full + 26 supplements)")
    print("Entrypoint: none (resource-only Fabric mod)")
    print("Publishable: false")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

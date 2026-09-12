#!/usr/bin/env python3
"""Reconstruct Minecraft 1.12.1 / JEI 4.7.8 addon language resources.

G10 is an exact localization inheritance of G9: the English source, Minecraft
asset index, JEI language files and ownership partition are all unchanged.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_12 as g9

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.12" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.12.1" / "en_us.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g10-mc1.12.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.12.1"
DEBUG_PREFIX = "description.jei."


def parse_lang(path: Path) -> dict[str, str]:
    return g9.parse_lang(path)


def target_layout() -> list[tuple[str, str | None]]:
    layout: list[tuple[str, str | None]] = []
    for raw in TARGET_SOURCE.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            layout.append((raw, None))
            continue
        key, _ = raw.split("=", 1)
        layout.append((raw, key.strip()))
    return layout


def reconstruct_g9_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g9.TARGET_SOURCE)
    scope = json.loads(g9.SCOPE_PATH.read_text(encoding="utf-8"))
    return g9.reconstruct_full(target, scope)


def reconstruct_g9_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g9.TARGET_SOURCE)
    scope = json.loads(g9.SCOPE_PATH.read_text(encoding="utf-8"))
    return g9.reconstruct_supplements(target, scope)


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    if base != target:
        raise ValueError("G10 target English must be identical to G9")
    inherited = reconstruct_g9_full()
    expected = set(scope["addon_full_locales"])
    if expected != set(inherited) or len(expected) != 60:
        raise ValueError("G10 full-locale ownership must be identical to G9")
    return {locale: dict(values) for locale, values in inherited.items()}


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    if base != target:
        raise ValueError("G10 target English must be identical to G9")
    inherited = reconstruct_g9_supplements()
    expected = set(scope["selected_upstream_incomplete_locales"])
    if expected != set(inherited) or len(expected) != 18:
        raise ValueError("G10 supplement ownership must be identical to G9")
    return {locale: dict(values) for locale, values in inherited.items()}


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    if policy["unchanged_key_and_value_count"] != 93:
        raise ValueError("G10 must preserve all 93 G9 key/value pairs")
    if not policy["minecraft_asset_index_same_as_base"] or not policy["jei_language_resources_same_as_base"]:
        raise ValueError("G10 policy must record exact G9 asset/language inheritance")
    if policy["selected_scope_count"] != 80:
        raise ValueError("G10 selected scope must remain 80")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (60, 18, 93):
        raise ValueError(f"G10 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G10 output locale is not lowercase")
        path = full_dir / f"{locale}.lang"
        g9.write_full(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G10 full output failed round-trip validation")

    target_order = list(target)
    for locale, values in sorted(supplements.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G10 supplement locale is not lowercase")
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target_order if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G10 supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.12.1-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.12.1 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("G10 resources are exact G9 localization inheritance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

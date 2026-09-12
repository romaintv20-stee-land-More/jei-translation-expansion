#!/usr/bin/env python3
"""Reconstruct Minecraft 1.12 / JEI 4.7.5 addon language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_11_2 as g8

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.11.2" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.12" / "en_us.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g9-mc1.12" / "policy.json"
SV_RECOVERY_PATH = ROOT / "translations" / "g9-mc1.12" / "sv_se-from-g8-upstream.lang"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.12"
DEBUG_PREFIX = "description.jei."
NEW_SELECTED = {"bs_ba", "ig_ng", "kab_kab", "kn_in", "oj_ca", "ta_in", "vec_it", "yo_ng"}
SV_DROPPED = {
    "config.jei.search.resourceIdSearchMode",
    "config.jei.search.resourceIdSearchMode.comment",
    "key.jei.nextPage",
    "key.jei.previousPage",
}


def parse_lang(path: Path) -> dict[str, str]:
    return g8.parse_lang(path)


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


def write_full(path: Path, values: dict[str, str], layout: list[tuple[str, str | None]]) -> None:
    lines: list[str] = []
    for raw, key in layout:
        if key is None:
            lines.append(raw)
        else:
            lines.append(f"{key}={values[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reconstruct_g8_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g8.TARGET_SOURCE)
    scope = json.loads(g8.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g8.DIFF_PATH.read_text(encoding="utf-8"))
    return g8.reconstruct_full(target, scope, diff)


def reconstruct_g8_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g8.TARGET_SOURCE)
    scope = json.loads(g8.SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g8.AUDIT_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g8.DIFF_PATH.read_text(encoding="utf-8"))
    return g8.reconstruct_supplements(target, scope, audit, diff)


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    if base != target:
        raise ValueError("G9 requires the 1.12 English source to be byte-semantic identical to G8")

    g8_full = reconstruct_g8_full()
    expected = set(scope["addon_full_locales"])
    if len(expected) != 60 or not NEW_SELECTED <= expected:
        raise ValueError("G9 full-locale ownership does not match frozen 60-locale scope")
    if set(g8_full) != expected - NEW_SELECTED:
        raise ValueError("G9 inherited full-locale ownership differs unexpectedly from G8")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        if locale in NEW_SELECTED:
            result[locale] = dict(target)
        else:
            result[locale] = dict(g8_full[locale])
        if set(result[locale]) != set(target):
            raise ValueError(f"{locale}: G9 full reconstruction key mismatch")
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    g8_supplements = reconstruct_g8_supplements()
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 18 or "ja_jp" in expected or "sv_se" not in expected:
        raise ValueError("G9 supplement ownership does not match frozen policy")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        if locale == "sv_se":
            values = dict(g8_supplements[locale])
            recovery = parse_lang(SV_RECOVERY_PATH)
            if set(recovery) != SV_DROPPED:
                raise ValueError("G9 Swedish recovery file must contain exactly the four dropped G8 upstream keys")
            if set(values) & set(recovery):
                raise ValueError("G9 Swedish recovery overlaps the inherited G8 supplement")
            values.update(recovery)
            if len(values) != 6:
                raise ValueError(f"sv_se: expected 6 G9 supplement keys, got {len(values)}")
            result[locale] = values
        else:
            if locale not in g8_supplements:
                raise ValueError(f"{locale}: missing inherited G8 supplement")
            result[locale] = dict(g8_supplements[locale])

    if set(result) != expected:
        raise ValueError("G9 supplement locale set does not match frozen scope")
    for locale, values in result.items():
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: debug-only key must not be emitted in a supplement")
        if not set(values) <= set(target):
            raise ValueError(f"{locale}: supplement contains a key absent from G9 target")
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    if policy["resource_filename_case"] != "lowercase":
        raise ValueError("G9 policy must require lowercase resource filenames")
    if policy["unchanged_key_and_value_count"] != 93 or policy["selected_scope_count"] != 80:
        raise ValueError("G9 frozen policy counts changed unexpectedly")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (60, 18, 93):
        raise ValueError(f"G9 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G9 output locale is not lowercase")
        path = full_dir / f"{locale}.lang"
        write_full(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G9 full output failed round-trip validation")

    target_order = list(target)
    for locale, values in sorted(supplements.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G9 supplement locale is not lowercase")
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target_order if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G9 supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.12-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.12 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("New selected languages: 8 documented full-English fallbacks")
    print("Swedish upstream regression: four exact G8 upstream translations restored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

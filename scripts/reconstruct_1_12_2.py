#!/usr/bin/env python3
"""Reconstruct Minecraft 1.12.2 / JEI 4.16.5 addon language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_12_1 as g10

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.12.1" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.12.2" / "en_us.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.12.1-to-1.12.2.json"
POLICY_PATH = ROOT / "translations" / "g11-mc1.12.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.12.2"
DEBUG_PREFIX = "description.jei."
G10_COMMIT = "7f4160ed969fad85e8c4a14809c66402c51592b2"
G11_COMMIT = "f98331af6b1f7d59da01beecacd681c16dd548b9"
RAW_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.lang"


def parse_lang(path: Path) -> dict[str, str]:
    return g10.parse_lang(path)


def parse_lang_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value
    return values


@lru_cache(maxsize=None)
def fetch_upstream_lang(commit: str, locale: str) -> dict[str, str]:
    url = RAW_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G11-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_lang_text(response.read().decode("utf-8"))


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


def reconstruct_g10_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g10.TARGET_SOURCE)
    scope = json.loads(g10.SCOPE_PATH.read_text(encoding="utf-8"))
    return g10.reconstruct_full(target, scope)


def reconstruct_g10_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g10.TARGET_SOURCE)
    scope = json.loads(g10.SCOPE_PATH.read_text(encoding="utf-8"))
    return g10.reconstruct_supplements(target, scope)


def g10_combined_locale(
    locale: str,
    g10_full: dict[str, dict[str, str]],
    g10_supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in g10_full:
        return dict(g10_full[locale])
    values = dict(fetch_upstream_lang(G10_COMMIT, locale))
    if locale in g10_supplements:
        overlap = set(values) & set(g10_supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G10 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(g10_supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    g10_full = reconstruct_g10_full()
    expected = set(scope["addon_full_locales"])
    if len(expected) != 55:
        raise ValueError(f"G11 expected 55 addon-owned full locales, got {len(expected)}")
    if not expected <= set(g10_full):
        raise ValueError("G11 full-locale set must be a subset of G10 full-locale ownership")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        inherited = g10_full[locale]
        values: dict[str, str] = {}
        for key, target_value in target.items():
            if key in base and base[key] == target_value:
                if key not in inherited:
                    raise ValueError(f"{locale}: unchanged G11 key missing from G10 full locale: {key}")
                values[key] = inherited[key]
            else:
                values[key] = target_value
        if set(values) != set(target):
            raise ValueError(f"{locale}: G11 full reconstruction key mismatch")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 24:
        raise ValueError(f"G11 expected 24 supplement locales, got {len(expected)}")

    g10_full = reconstruct_g10_full()
    g10_supplements = reconstruct_g10_supplements()
    result: dict[str, dict[str, str]] = {}

    for locale in sorted(expected):
        upstream = fetch_upstream_lang(G11_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined_g10 = g10_combined_locale(locale, g10_full, g10_supplements)
        values: dict[str, str] = {}
        for key in sorted(missing):
            target_value = target[key]
            if key in base and base[key] == target_value:
                if key not in combined_g10:
                    raise ValueError(f"{locale}: no G10 recovery value for unchanged missing G11 key {key}")
                values[key] = combined_g10[key]
            else:
                values[key] = target_value
        result[locale] = values

    if set(result) != expected:
        raise ValueError("G11 supplement locale set differs from frozen scope")
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    if (len(target), len([k for k in target if not k.startswith(DEBUG_PREFIX)])) != (115, 112):
        raise ValueError("G11 target must contain 115 total / 112 normal keys")
    if (
        diff["unchanged_key_and_value_count"],
        diff["added_key_count"],
        diff["removed_key_count"],
        diff["changed_english_value_count"],
    ) != (41, 33, 11, 41):
        raise ValueError("G11 frozen English diff counts changed")
    if policy["selected_scope_count"] != 80 or policy["reviewed_normal_added_or_changed_key_count"] != 71:
        raise ValueError("G11 frozen policy counts changed")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (55, 24, 115):
        raise ValueError(f"G11 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G11 output locale is not lowercase")
        path = full_dir / f"{locale}.lang"
        write_full(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G11 full output failed round-trip validation")

    target_order = list(target)
    for locale, values in sorted(supplements.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G11 supplement locale is not lowercase")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G11 supplement contains debug-only key")
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target_order if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G11 supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.12.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.12.2 deterministic pinned-upstream reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("Unchanged missing meanings recover exact G10 combined values")
    print("Added/changed missing meanings use conservative G11 target-English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

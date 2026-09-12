#!/usr/bin/env python3
"""Reconstruct Minecraft 1.13.2 / JEI 5.0.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_13 as g12

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.13" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.13.2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.13.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.13-to-1.13.2.json"
POLICY_PATH = ROOT / "translations" / "g13-mc1.13.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.13.2"
DEBUG_PREFIX = "description.jei."
G13_COMMIT = "2d16f4210cbae340ad76b483b4aa8b461561e86f"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"
NEW_G13_LANGUAGES = {"bar", "kk_kz", "moh_ca", "tt_ru"}


def parse_json_text(text: str) -> dict[str, str]:
    return g12.parse_json_text(text)


def parse_json(path: Path) -> dict[str, str]:
    return g12.parse_json(path)


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G13-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def write_json(path: Path, values: dict[str, str]) -> None:
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reconstruct_g12_full() -> dict[str, dict[str, str]]:
    target = g12.parse_json(g12.TARGET_SOURCE)
    scope = json.loads(g12.SCOPE_PATH.read_text(encoding="utf-8"))
    return g12.reconstruct_full(target, scope)


def reconstruct_g12_supplements() -> dict[str, dict[str, str]]:
    target = g12.parse_json(g12.TARGET_SOURCE)
    scope = json.loads(g12.SCOPE_PATH.read_text(encoding="utf-8"))
    return g12.reconstruct_supplements(target, scope)


def g12_selected_locales() -> set[str]:
    scope = json.loads(g12.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def g12_combined_locale(
    locale: str,
    full: dict[str, dict[str, str]],
    supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g12_selected_locales():
        raise KeyError(locale)
    values = dict(g12.fetch_upstream_json(g12.G12_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G12 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def resolve_value(
    locale: str,
    key: str,
    target_value: str,
    base: dict[str, str],
    g12_full: dict[str, dict[str, str]],
    g12_supplements: dict[str, dict[str, str]],
) -> tuple[str, str]:
    if key.startswith(DEBUG_PREFIX) or locale in NEW_G13_LANGUAGES:
        return target_value, "target-English"
    if base.get(key) == target_value and locale in g12_selected_locales():
        combined = g12_combined_locale(locale, g12_full, g12_supplements)
        candidate = combined.get(key)
        if candidate is not None and g12.safe_historical_candidate(target_value, candidate):
            return candidate, "g12-exact-semantic"
    return target_value, "target-English"


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    expected = set(scope["addon_full_locales"])
    if len(expected) != 66:
        raise ValueError(f"G13 expected 66 addon-owned full locales, got {len(expected)}")

    g12_full = reconstruct_g12_full()
    g12_supplements = reconstruct_g12_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        values: dict[str, str] = {}
        for key, target_value in target.items():
            value, _ = resolve_value(locale, key, target_value, base, g12_full, g12_supplements)
            values[key] = value
        if set(values) != set(target):
            raise ValueError(f"{locale}: G13 full reconstruction key mismatch")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 19:
        raise ValueError(f"G13 expected 19 supplement locales, got {len(expected)}")

    g12_full = reconstruct_g12_full()
    g12_supplements = reconstruct_g12_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G13_COMMIT, locale)
        missing = normal_keys - set(upstream)
        values: dict[str, str] = {}
        for key in target:
            if key not in missing:
                continue
            value, _ = resolve_value(locale, key, target[key], base, g12_full, g12_supplements)
            values[key] = value
        result[locale] = values
    if set(result) != expected:
        raise ValueError("G13 supplement locale set differs from frozen scope")
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(target), normal_count) != (106, 103):
        raise ValueError(f"G13 target must contain 106 total / 103 normal keys, got {len(target)}/{normal_count}")
    if (
        diff["unchanged_key_and_value_count"],
        diff["added_key_count"],
        diff["removed_key_count"],
        diff["changed_english_value_count"],
    ) != (101, 1, 0, 4):
        raise ValueError("G13 frozen English diff counts changed")
    if policy["selected_scope_count"] != 87 or policy["english_diff"]["reviewed_normal_added_or_changed_key_count"] != 4:
        raise ValueError("G13 frozen policy counts changed")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (66, 19, 106):
        raise ValueError(f"G13 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G13 output locale is not lowercase")
        path = full_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G13 full JSON failed round-trip validation")

    for locale, values in sorted(supplements.items()):
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G13 supplement contains debug-only key")
        path = supplement_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G13 supplement JSON failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.13.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.13.2 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("Resource format: JSON")
    print("101 exact G12 semantics are eligible for reuse")
    print("Added/changed project-owned meanings use exact G13 target English")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

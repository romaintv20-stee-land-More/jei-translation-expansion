#!/usr/bin/env python3
"""Reconstruct Minecraft 1.15.2 / JEI 6.0.2 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_15_1 as g17

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.15.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.15.2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.15.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.15.1-to-1.15.2.json"
POLICY_PATH = ROOT / "translations" / "g18-mc1.15.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.15.2"
DEBUG_PREFIX = "description.jei."
G18_COMMIT = "1ea77203d8b731c99cea68166b02afeb3d9c6176"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"
NEW_KEY = "gui.jei.category.stoneCutter"

parse_json_text = g17.parse_json_text
parse_json = g17.parse_json
write_json = g17.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G18-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g17_full() -> dict[str, dict[str, str]]:
    target = g17.parse_json(g17.TARGET_SOURCE)
    scope = json.loads(g17.SCOPE_PATH.read_text(encoding="utf-8"))
    return g17.reconstruct_full(target, scope)


def reconstruct_g17_supplements() -> dict[str, dict[str, str]]:
    target = g17.parse_json(g17.TARGET_SOURCE)
    scope = json.loads(g17.SCOPE_PATH.read_text(encoding="utf-8"))
    return g17.reconstruct_supplements(target, scope)


def g17_selected_locales() -> set[str]:
    scope = json.loads(g17.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def g17_combined_locale(
    locale: str,
    full: dict[str, dict[str, str]],
    supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g17_selected_locales():
        raise KeyError(locale)
    values = dict(g17.fetch_upstream_json(g17.G17_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G17 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    expected = set(scope["addon_full_locales"])
    if len(expected) != 66:
        raise ValueError(f"G18 expected 66 addon-owned full locales, got {len(expected)}")
    g17_full = reconstruct_g17_full()
    if expected != set(g17_full):
        raise ValueError("G18 addon-full locale set differs from G17")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        values = dict(g17_full[locale])
        values[NEW_KEY] = target[NEW_KEY]
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    base = parse_json(BASE_SOURCE)
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 18:
        raise ValueError(f"G18 expected 18 supplement locales, got {len(expected)}")
    g17_full = reconstruct_g17_full()
    g17_supplements = reconstruct_g17_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G18_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined = g17_combined_locale(locale, g17_full, g17_supplements)
        values: dict[str, str] = {}
        for key in target:
            if key not in missing:
                continue
            if key in base:
                values[key] = combined[key]
            else:
                values[key] = target[key]
        result[locale] = values
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (109, 110, 107):
        raise ValueError(f"G18 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if set(target) - set(base) != {NEW_KEY} or target[NEW_KEY] != "Stonecutting":
        raise ValueError("G18 must add exactly gui.jei.category.stoneCutter=Stonecutting")
    if any(base[key] != target[key] for key in base):
        raise ValueError("G18 changed a G17 semantic value")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (109, 1, 0, 0):
        raise ValueError("G18 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g17_semantics"]:
        raise ValueError("G18 policy must require exact G17 inheritance for unchanged meanings")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (66, 18, 110):
        raise ValueError(f"G18 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)
    for locale, values in sorted(full.items()):
        write_json(full_dir / f"{locale}.json", values)
    for locale, values in sorted(supplements.items()):
        write_json(supplement_dir / f"{locale}.json", values)
    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.15.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.15.2 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("All 109 G17 semantics are inherited exactly")
    print("Stonecutting uses exact target English wherever the project owns the new key")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

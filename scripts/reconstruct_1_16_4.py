#!/usr/bin/env python3
"""Reconstruct Minecraft 1.16.4 / JEI 7.6.1 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_16_3 as g21

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.16.3" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.16.4" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.4-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.3-to-1.16.4.json"
POLICY_PATH = ROOT / "translations" / "g22-mc1.16.4" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.16.4"
DEBUG_PREFIX = "description.jei."
G22_COMMIT = "8255a01a6db0980f6e03b2b4d9d5f376bef7fd25"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g21.parse_json_text
parse_json = g21.parse_json
write_json = g21.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G22-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g21_full() -> dict[str, dict[str, str]]:
    target = g21.parse_json(g21.TARGET_SOURCE)
    scope = json.loads(g21.SCOPE_PATH.read_text(encoding="utf-8"))
    return g21.reconstruct_full(target, scope)


def reconstruct_g21_supplements() -> dict[str, dict[str, str]]:
    target = g21.parse_json(g21.TARGET_SOURCE)
    scope = json.loads(g21.SCOPE_PATH.read_text(encoding="utf-8"))
    return g21.reconstruct_supplements(target, scope)


def g21_selected_locales() -> set[str]:
    scope = json.loads(g21.SCOPE_PATH.read_text(encoding="utf-8"))
    return set(scope["addon_full_locales"]) | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])


def g21_combined_locale(locale: str, full: dict[str, dict[str, str]], supplements: dict[str, dict[str, str]]) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g21_selected_locales():
        raise KeyError(locale)
    values = dict(g21.fetch_upstream_json(g21.G21_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G21 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    expected = set(scope["addon_full_locales"])
    g21_full = reconstruct_g21_full()
    if len(expected) != 67 or expected != set(g21_full):
        raise ValueError("G22 addon-full ownership must exactly inherit G21's 67 locales")
    return {locale: dict(g21_full[locale]) for locale in sorted(expected)}


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 16:
        raise ValueError(f"G22 expected 16 supplement locales, got {len(expected)}")
    g21_full = reconstruct_g21_full()
    g21_supplements = reconstruct_g21_supplements()
    if not expected.issubset(set(g21_supplements)):
        raise ValueError("G22 supplement locales must be inherited from G21 incomplete-upstream locales")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G22_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined = g21_combined_locale(locale, g21_full, g21_supplements)
        result[locale] = {key: combined[key] for key in target if key in missing}
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (114, 114, 111):
        raise ValueError(f"G22 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if base != target:
        raise ValueError("G22 English source must exactly match G21")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (114, 0, 0, 0):
        raise ValueError("G22 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g21_semantics"]:
        raise ValueError("G22 policy must require exact G21 inheritance")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (67, 16, 114):
        raise ValueError(f"G22 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.16.4-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.16.4 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("All 114 G21 key/value semantics are inherited exactly")
    print("pl_pl and ru_ru supplements are retired because JEI 7.6.1 is complete upstream")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

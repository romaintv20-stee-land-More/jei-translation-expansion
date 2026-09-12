#!/usr/bin/env python3
"""Reconstruct Minecraft 1.16.3 / JEI 7.6.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_16_2 as g20

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.16.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.16.3" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.3-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.2-to-1.16.3.json"
POLICY_PATH = ROOT / "translations" / "g21-mc1.16.3" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.16.3"
DEBUG_PREFIX = "description.jei."
G21_COMMIT = "130181aa9ee3762c6accd7614a03d932486710f9"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g20.parse_json_text
parse_json = g20.parse_json
write_json = g20.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G21-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g20_full() -> dict[str, dict[str, str]]:
    target = g20.parse_json(g20.TARGET_SOURCE)
    scope = json.loads(g20.SCOPE_PATH.read_text(encoding="utf-8"))
    return g20.reconstruct_full(target, scope)


def reconstruct_g20_supplements() -> dict[str, dict[str, str]]:
    target = g20.parse_json(g20.TARGET_SOURCE)
    scope = json.loads(g20.SCOPE_PATH.read_text(encoding="utf-8"))
    return g20.reconstruct_supplements(target, scope)


def g20_selected_locales() -> set[str]:
    scope = json.loads(g20.SCOPE_PATH.read_text(encoding="utf-8"))
    return set(scope["addon_full_locales"]) | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])


def g20_combined_locale(locale: str, full: dict[str, dict[str, str]], supplements: dict[str, dict[str, str]]) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g20_selected_locales():
        raise KeyError(locale)
    values = dict(g20.fetch_upstream_json(g20.G20_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G20 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    expected = set(scope["addon_full_locales"])
    g20_full = reconstruct_g20_full()
    if len(expected) != 67 or expected != set(g20_full):
        raise ValueError("G21 addon-full ownership must exactly inherit G20's 67 locales")
    return {locale: dict(g20_full[locale]) for locale in sorted(expected)}


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 18:
        raise ValueError(f"G21 expected 18 supplement locales, got {len(expected)}")
    g20_full = reconstruct_g20_full()
    g20_supplements = reconstruct_g20_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G21_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined = g20_combined_locale(locale, g20_full, g20_supplements)
        values = {key: combined[key] for key in target if key in missing}
        result[locale] = values
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (114, 114, 111):
        raise ValueError(f"G21 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if base != target:
        raise ValueError("G21 English source must exactly match G20")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (114, 0, 0, 0):
        raise ValueError("G21 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g20_semantics"]:
        raise ValueError("G21 policy must require exact G20 inheritance")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (67, 18, 114):
        raise ValueError(f"G21 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.16.3-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.16.3 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("All 114 G20 key/value semantics are inherited exactly")
    print("sv_se supplement is retired because JEI 7.6.0 is complete upstream")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 1.16.2 / JEI 7.3.2 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_16_1 as g19

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.16.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.16.2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.1-to-1.16.2.json"
POLICY_PATH = ROOT / "translations" / "g20-mc1.16.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.16.2"
DEBUG_PREFIX = "description.jei."
G20_COMMIT = "df46cefb0ade79851101fd32b065a34115fee70c"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"
ADDED_KEYS = {
    "config.jei",
    "config.jei.search.searchAdvancedTooltips",
    "gui.jei.category.smelting.time.seconds",
    "jei.message.ftbguilib",
}

parse_json_text = g19.parse_json_text
parse_json = g19.parse_json
write_json = g19.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G20-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g19_full() -> dict[str, dict[str, str]]:
    target = g19.parse_json(g19.TARGET_SOURCE)
    scope = json.loads(g19.SCOPE_PATH.read_text(encoding="utf-8"))
    return g19.reconstruct_full(target, scope)


def reconstruct_g19_supplements() -> dict[str, dict[str, str]]:
    target = g19.parse_json(g19.TARGET_SOURCE)
    scope = json.loads(g19.SCOPE_PATH.read_text(encoding="utf-8"))
    return g19.reconstruct_supplements(target, scope)


def g19_selected_locales() -> set[str]:
    scope = json.loads(g19.SCOPE_PATH.read_text(encoding="utf-8"))
    return set(scope["addon_full_locales"]) | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])


def g19_combined_locale(locale: str, full: dict[str, dict[str, str]], supplements: dict[str, dict[str, str]]) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g19_selected_locales():
        raise KeyError(locale)
    values = dict(g19.fetch_upstream_json(g19.G19_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G19 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    expected = set(scope["addon_full_locales"])
    g19_full = reconstruct_g19_full()
    if len(expected) != 67 or expected != set(g19_full):
        raise ValueError("G20 addon-full ownership must exactly inherit G19's 67 locales")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        values = dict(g19_full[locale])
        for key in ADDED_KEYS:
            values[key] = target[key]
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 19:
        raise ValueError(f"G20 expected 19 supplement locales, got {len(expected)}")
    g19_full = reconstruct_g19_full()
    g19_supplements = reconstruct_g19_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G20_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined = g19_combined_locale(locale, g19_full, g19_supplements)
        values: dict[str, str] = {}
        for key in target:
            if key not in missing:
                continue
            values[key] = target[key] if key in ADDED_KEYS else combined[key]
        result[locale] = values
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (110, 114, 111):
        raise ValueError(f"G20 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    if added != ADDED_KEYS or removed or changed:
        raise ValueError(f"G20 English delta changed: added={sorted(added)} removed={sorted(removed)} changed={sorted(changed)}")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (110, 4, 0, 0):
        raise ValueError("G20 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g19_semantics"]:
        raise ValueError("G20 policy must require exact G19 inheritance for unchanged meanings")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (67, 19, 114):
        raise ValueError(f"G20 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.16.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.16.2 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("All 110 G19 semantics are inherited exactly")
    print("All four new project-owned G20 meanings use exact target English")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

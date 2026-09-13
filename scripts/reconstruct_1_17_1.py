#!/usr/bin/env python3
"""Reconstruct Minecraft 1.17.1 / JEI 8.3.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_16_5 as g23

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.16.5" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.17.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.17.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.5-to-1.17.1.json"
POLICY_PATH = ROOT / "translations" / "g24-mc1.17.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.17.1"
DEBUG_PREFIX = "description.jei."
G24_COMMIT = "ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g23.parse_json_text
parse_json = g23.parse_json
write_json = g23.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G24-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g23_full() -> dict[str, dict[str, str]]:
    target = g23.parse_json(g23.TARGET_SOURCE)
    scope = json.loads(g23.SCOPE_PATH.read_text(encoding="utf-8"))
    return g23.reconstruct_full(target, scope)


def reconstruct_g23_supplements() -> dict[str, dict[str, str]]:
    target = g23.parse_json(g23.TARGET_SOURCE)
    scope = json.loads(g23.SCOPE_PATH.read_text(encoding="utf-8"))
    return g23.reconstruct_supplements(target, scope)


def g23_selected_locales() -> set[str]:
    scope = json.loads(g23.SCOPE_PATH.read_text(encoding="utf-8"))
    return set(scope["addon_full_locales"]) | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])


def g23_combined_locale(locale: str, full: dict[str, dict[str, str]], supplements: dict[str, dict[str, str]]) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g23_selected_locales():
        raise KeyError(locale)
    values = dict(g23.fetch_upstream_json(g23.G23_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G23 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def inherit_or_target(key: str, base: dict[str, str], target: dict[str, str], previous: dict[str, str]) -> str:
    if key in base and base[key] == target[key]:
        return previous[key]
    return target[key]


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    expected = set(scope["addon_full_locales"])
    g23_full = reconstruct_g23_full()
    if len(expected) != 64:
        raise ValueError(f"G24 expected 64 addon-full locales, got {len(expected)}")
    if expected != set(g23_full) - {"gv_im", "mi_nz"}:
        raise ValueError("G24 addon-full ownership must equal G23 full ownership minus removed Minecraft locales gv_im and mi_nz")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        previous = g23_full[locale]
        result[locale] = {key: inherit_or_target(key, base, target, previous) for key in target}
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 21:
        raise ValueError(f"G24 expected 21 supplement locales, got {len(expected)}")
    g23_full = reconstruct_g23_full()
    g23_supplements = reconstruct_g23_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G24_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous = g23_combined_locale(locale, g23_full, g23_supplements)
        values: dict[str, str] = {}
        for key in target:
            if key not in missing:
                continue
            values[key] = inherit_or_target(key, base, target, previous)
        result[locale] = values
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (119, 141, 135):
        raise ValueError(f"G24 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (87, 24, 2, 30):
        raise ValueError("G24 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g23_semantics"]:
        raise ValueError("G24 policy must require exact G23 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G24 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 21, 141):
        raise ValueError(f"G24 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.17.1-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.17.1 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("87 unchanged G23 key/value semantics are inherited exactly")
    print("24 added and 30 changed G24 English meanings use exact target English when project-owned")
    print("gv_im and mi_nz are not emitted because Minecraft 1.17.1 removed those locale codes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

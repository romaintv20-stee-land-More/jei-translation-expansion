#!/usr/bin/env python3
"""Reconstruct Minecraft 1.16.5 / JEI 7.7.1 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_16_4 as g22

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.16.4" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.16.5" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.16.5-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.16.4-to-1.16.5.json"
POLICY_PATH = ROOT / "translations" / "g23-mc1.16.5" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.16.5"
DEBUG_PREFIX = "description.jei."
G23_COMMIT = "f6bd6ea033084f3d18ad256c9921641dcbd0330f"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g22.parse_json_text
parse_json = g22.parse_json
write_json = g22.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G23-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g22_full() -> dict[str, dict[str, str]]:
    target = g22.parse_json(g22.TARGET_SOURCE)
    scope = json.loads(g22.SCOPE_PATH.read_text(encoding="utf-8"))
    return g22.reconstruct_full(target, scope)


def reconstruct_g22_supplements() -> dict[str, dict[str, str]]:
    target = g22.parse_json(g22.TARGET_SOURCE)
    scope = json.loads(g22.SCOPE_PATH.read_text(encoding="utf-8"))
    return g22.reconstruct_supplements(target, scope)


def g22_selected_locales() -> set[str]:
    scope = json.loads(g22.SCOPE_PATH.read_text(encoding="utf-8"))
    return set(scope["addon_full_locales"]) | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])


def g22_combined_locale(locale: str, full: dict[str, dict[str, str]], supplements: dict[str, dict[str, str]]) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g22_selected_locales():
        raise KeyError(locale)
    values = dict(g22.fetch_upstream_json(g22.G22_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G22 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def inherit_or_target(key: str, base: dict[str, str], target: dict[str, str], previous: dict[str, str]) -> str:
    if key in base and base[key] == target[key]:
        return previous[key]
    return target[key]


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    expected = set(scope["addon_full_locales"])
    g22_full = reconstruct_g22_full()
    if len(expected) != 66:
        raise ValueError(f"G23 expected 66 addon-full locales, got {len(expected)}")
    if expected != set(g22_full) - {"id_id"}:
        raise ValueError("G23 addon-full ownership must equal G22 full ownership minus id_id")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        previous = g22_full[locale]
        result[locale] = {
            key: inherit_or_target(key, base, target, previous)
            for key in target
        }
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 15:
        raise ValueError(f"G23 expected 15 supplement locales, got {len(expected)}")
    g22_full = reconstruct_g22_full()
    g22_supplements = reconstruct_g22_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G23_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous = g22_combined_locale(locale, g22_full, g22_supplements)
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
    if (len(base), len(target), normal_count) != (114, 119, 113):
        raise ValueError(f"G23 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (113, 6, 1, 0):
        raise ValueError("G23 frozen English diff counts changed")
    if diff["removed_keys"] != ["jei.message.ftbguilib"]:
        raise ValueError("G23 removed-key set changed")
    if not policy["translation_reuse"]["reuse_unchanged_g22_semantics"]:
        raise ValueError("G23 policy must require exact G22 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G23 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (66, 15, 119):
        raise ValueError(f"G23 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.16.5-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.16.5 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("113 unchanged G22 key/value semantics are inherited exactly")
    print("Six new G23 keys use exact target English when project-owned; jei.message.ftbguilib is removed")
    print("id_id is now upstream-owned with a missing-key-only supplement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

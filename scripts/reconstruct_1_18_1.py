#!/usr/bin/env python3
"""Reconstruct Minecraft 1.18.1 / JEI 9.4.1 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_18 as g25

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.18" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.18.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.18.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.18-to-1.18.1.json"
POLICY_PATH = ROOT / "translations" / "g26-mc1.18.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.18.1"
DEBUG_PREFIX = "description.jei."
G26_COMMIT = "82a622213dbf2a9df65af4e3cebbccc77ec44deb"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g25.parse_json_text
parse_json = g25.parse_json
write_json = g25.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G26-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g25_full() -> dict[str, dict[str, str]]:
    target = g25.parse_json(g25.TARGET_SOURCE)
    scope = json.loads(g25.SCOPE_PATH.read_text(encoding="utf-8"))
    return g25.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g25_supplements() -> dict[str, dict[str, str]]:
    target = g25.parse_json(g25.TARGET_SOURCE)
    scope = json.loads(g25.SCOPE_PATH.read_text(encoding="utf-8"))
    return g25.reconstruct_supplements(target, scope)


@lru_cache(maxsize=None)
def g25_combined_locale(locale: str) -> dict[str, str]:
    values = dict(g25.fetch_upstream_json(g25.G25_COMMIT, locale))
    supplements = reconstruct_g25_supplements()
    values.update(supplements.get(locale, {}))
    return values


def semantic_sets(base: dict[str, str], target: dict[str, str]) -> tuple[set[str], set[str], set[str], set[str]]:
    unchanged = {k for k in set(base) & set(target) if base[k] == target[k]}
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {k for k in set(base) & set(target) if base[k] != target[k]}
    return unchanged, added, removed, changed


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, _removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(changed)) != (124, 11, 14):
        raise ValueError("G26 frozen semantic partition changed")
    expected = set(scope["addon_full_locales"])
    previous = reconstruct_g25_full()
    if len(expected) != 64 or expected != set(previous):
        raise ValueError("G26 addon-full ownership must be exactly identical to G25")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        values: dict[str, str] = {}
        for key, english in target.items():
            if key in unchanged:
                if key not in old:
                    raise ValueError(f"{locale}: unchanged G26 key missing from G25 full locale: {key}")
                values[key] = old[key]
            else:
                values[key] = english
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, _added, _removed, _changed = semantic_sets(base, target)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 21:
        raise ValueError("G26 supplement ownership must remain exactly 21 selected locales")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G26_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_combined = g25_combined_locale(locale)
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_combined:
                    raise ValueError(f"{locale}: unchanged missing G26 key has no complete G25 value: {key}")
                values[key] = previous_combined[key]
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
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(base), len(target), normal_count) != (141, 149, 143):
        raise ValueError(f"G26 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (124, 11, 3, 14):
        raise ValueError("G26 semantic delta counts changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (124, 11, 3, 14):
        raise ValueError("G26 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g25_semantics"]:
        raise ValueError("G26 policy must require exact G25 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G26 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 21, 149):
        raise ValueError(f"G26 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.18.1-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.18.1 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("124 unchanged G25 key/value semantics are inherited exactly")
    print("25 added/changed project-owned meanings use exact G26 target English")
    print("3 removed G25 keys are not emitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

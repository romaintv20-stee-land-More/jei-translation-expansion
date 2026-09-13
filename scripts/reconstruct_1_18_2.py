#!/usr/bin/env python3
"""Reconstruct Minecraft 1.18.2 / JEI 10.1.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_18_1 as g26

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.18.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.18.2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.18.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.18.1-to-1.18.2.json"
POLICY_PATH = ROOT / "translations" / "g27-mc1.18.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.18.2"
DEBUG_PREFIX = "description.jei."
G27_COMMIT = "530ef6c8d604370bef850f3656a28beab56cbfba"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g26.parse_json_text
parse_json = g26.parse_json
write_json = g26.write_json
semantic_sets = g26.semantic_sets


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G27-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g26_full() -> dict[str, dict[str, str]]:
    target = g26.parse_json(g26.TARGET_SOURCE)
    scope = json.loads(g26.SCOPE_PATH.read_text(encoding="utf-8"))
    return g26.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g26_supplements() -> dict[str, dict[str, str]]:
    target = g26.parse_json(g26.TARGET_SOURCE)
    scope = json.loads(g26.SCOPE_PATH.read_text(encoding="utf-8"))
    return g26.reconstruct_supplements(target, scope)


@lru_cache(maxsize=None)
def g26_combined_locale(locale: str) -> dict[str, str]:
    values = dict(g26.fetch_upstream_json(g26.G26_COMMIT, locale))
    values.update(reconstruct_g26_supplements().get(locale, {}))
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (149, 5, 0, 0):
        raise ValueError("G27 frozen semantic partition changed")
    expected = set(scope["addon_full_locales"])
    previous = reconstruct_g26_full()
    if len(expected) != 64 or expected != set(previous):
        raise ValueError("G27 addon-full ownership must be exactly identical to G26")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        values: dict[str, str] = {}
        for key, english in target.items():
            if key in unchanged:
                if key not in old:
                    raise ValueError(f"{locale}: unchanged G27 key missing from G26 full locale: {key}")
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
        raise ValueError("G27 supplement ownership must remain exactly 21 selected locales")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G27_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_combined = g26_combined_locale(locale)
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_combined:
                    raise ValueError(f"{locale}: unchanged missing G27 key has no complete G26 value: {key}")
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
    if (len(base), len(target), normal_count) != (149, 154, 148):
        raise ValueError(f"G27 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (149, 5, 0, 0):
        raise ValueError("G27 semantic delta counts changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (149, 5, 0, 0):
        raise ValueError("G27 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g26_semantics"]:
        raise ValueError("G27 policy must require exact G26 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G27 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 21, 154):
        raise ValueError(f"G27 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.18.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.18.2 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("149 unchanged G26 key/value semantics are inherited exactly")
    print("5 new project-owned meanings use exact G27 target English")
    print("No G26 keys are removed or changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 1.19.1 / JEI 11.2.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_19 as g28

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.19" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.19.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.19-to-1.19.1.json"
POLICY_PATH = ROOT / "translations" / "g29-mc1.19.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.19.1"
DEBUG_PREFIX = "description.jei."
G29_COMMIT = "90b37d06031c8e113d51e747e3f532f4b9ed047b"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
REMOVED_KEY = "jei.chat.error.command.too.long"

parse_json_text = g28.parse_json_text
parse_json = g28.parse_json
write_json = g28.write_json
semantic_sets = g28.semantic_sets


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G29-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g28_full() -> dict[str, dict[str, str]]:
    target = g28.parse_json(g28.TARGET_SOURCE)
    scope = json.loads(g28.SCOPE_PATH.read_text(encoding="utf-8"))
    return g28.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g28_supplements() -> dict[str, dict[str, str]]:
    target = g28.parse_json(g28.TARGET_SOURCE)
    scope = json.loads(g28.SCOPE_PATH.read_text(encoding="utf-8"))
    return g28.reconstruct_supplements(target, scope)


@lru_cache(maxsize=None)
def g28_combined_locale(locale: str) -> dict[str, str]:
    values = dict(g28.fetch_upstream_json(g28.G28_COMMIT, locale))
    values.update(reconstruct_g28_supplements().get(locale, {}))
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 0, 1, 0):
        raise ValueError("G29 frozen semantic partition changed")
    if removed != {REMOVED_KEY}:
        raise ValueError(f"G29 unexpected removed keys: {sorted(removed)}")
    previous = reconstruct_g28_full()
    expected = set(scope["addon_full_locales"])
    if len(expected) != 64 or expected != set(previous):
        raise ValueError("G29 addon-full ownership must be exactly identical to G28")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        values = {key: old[key] for key in target}
        if set(values) != set(target):
            raise ValueError(f"{locale}: G29 full key set differs from target")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 0, 1, 0):
        raise ValueError("G29 supplement reconstruction requires the frozen G28 semantic delta")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 19:
        raise ValueError("G29 supplement ownership must be exactly 19 selected locales")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G29_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_combined = g28_combined_locale(locale)
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key not in unchanged:
                raise ValueError(f"{locale}: unexpected non-inherited G29 missing key: {key}")
            if key not in previous_combined:
                raise ValueError(f"{locale}: unchanged missing G29 key has no complete G28 value: {key}")
            values[key] = previous_combined[key]
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
    if (len(base), len(target), normal_count) != (154, 153, 147):
        raise ValueError(f"G29 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 0, 1, 0):
        raise ValueError("G29 semantic delta counts changed")
    if removed != {REMOVED_KEY}:
        raise ValueError(f"G29 removed-key set changed: {sorted(removed)}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (153, 0, 1, 0):
        raise ValueError("G29 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g28_semantics"]:
        raise ValueError("G29 policy must require exact G28 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G29 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 19, 153):
        raise ValueError(f"G29 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.19.1-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.19.1 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("153 unchanged G28 key/value semantics are inherited exactly")
    print(f"Removed key is not emitted: {REMOVED_KEY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

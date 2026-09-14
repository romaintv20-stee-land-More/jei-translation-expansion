#!/usr/bin/env python3
"""Reconstruct Minecraft 1.20.6 / JEI 18.0.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_20_4 as g36

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.20.4" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.20.6" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.6-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20.4-to-1.20.6.json"
POLICY_PATH = ROOT / "translations" / "g37-mc1.20.6" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.20.6"
DEBUG_PREFIX = "description.jei."
G37_COMMIT = "7cc7d59043102c4843d422138dd74133edcd7b3c"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g36.parse_json_text
parse_json = g36.parse_json
write_json = g36.write_json
semantic_sets = g36.semantic_sets


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G37-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g36_full() -> dict[str, dict[str, str]]:
    target = g36.parse_json(g36.TARGET_SOURCE)
    scope = json.loads(g36.SCOPE_PATH.read_text(encoding="utf-8"))
    return g36.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g36_supplements() -> dict[str, dict[str, str]]:
    target = g36.parse_json(g36.TARGET_SOURCE)
    scope = json.loads(g36.SCOPE_PATH.read_text(encoding="utf-8"))
    return g36.reconstruct_supplements(target, scope)


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (157, 0, 0, 0):
        raise ValueError("G37 frozen semantic partition changed")

    previous = reconstruct_g36_full()
    expected = set(scope["addon_full_locales"])
    if len(previous) != 67 or expected != set(previous):
        raise ValueError("G37 addon-full ownership must match G36 exactly")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        if set(old) != set(target):
            raise ValueError(f"{locale}: G36 full key set differs from G37 target")
        values: dict[str, str] = {}
        for key in target:
            if key not in unchanged:
                raise ValueError(f"{locale}: unexpected non-unchanged G37 key: {key}")
            values[key] = old[key]
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (157, 0, 0, 0):
        raise ValueError("G37 supplement reconstruction requires 157 unchanged G36 semantics")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    previous = reconstruct_g36_supplements()
    if len(expected) != 22 or expected != set(previous):
        raise ValueError("G37 supplement ownership must match G36 exactly")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G37_COMMIT, locale)
        missing = normal_keys - set(upstream)
        old = previous[locale]
        if set(old) != missing:
            raise ValueError(f"{locale}: G37 missing-key set differs from G36 supplement ownership")
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key not in unchanged:
                raise ValueError(f"{locale}: unexpected non-unchanged G37 missing key: {key}")
            values[key] = old[key]
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
    if (len(base), len(target), normal_count) != (157, 157, 151):
        raise ValueError(f"G37 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (157, 0, 0, 0):
        raise ValueError("G37 semantic delta counts changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (157, 0, 0, 0):
        raise ValueError("G37 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g36_semantics"]:
        raise ValueError("G37 policy must require exact G36 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G37 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (67, 22, 157):
        raise ValueError(f"G37 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.20.6-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.20.6 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("All 157 G36 key/value semantics and owned translation values are inherited exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

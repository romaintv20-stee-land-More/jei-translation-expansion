#!/usr/bin/env python3
"""Reconstruct Minecraft 1.19.3 / JEI 12.3.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_19_2 as g30

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.19.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.19.3" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.19.3-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.19.2-to-1.19.3.json"
POLICY_PATH = ROOT / "translations" / "g31-mc1.19.3" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.19.3"
DEBUG_PREFIX = "description.jei."
G31_COMMIT = "739fde73225d006c83af22db04c5723d9c539dc7"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
NEW_FULL_LOCALES = {"nah", "ry_ua"}

parse_json_text = g30.parse_json_text
parse_json = g30.parse_json
write_json = g30.write_json
semantic_sets = g30.semantic_sets


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G31-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g30_full() -> dict[str, dict[str, str]]:
    target = g30.parse_json(g30.TARGET_SOURCE)
    scope = json.loads(g30.SCOPE_PATH.read_text(encoding="utf-8"))
    return g30.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g30_supplements() -> dict[str, dict[str, str]]:
    target = g30.parse_json(g30.TARGET_SOURCE)
    scope = json.loads(g30.SCOPE_PATH.read_text(encoding="utf-8"))
    return g30.reconstruct_supplements(target, scope)


@lru_cache(maxsize=None)
def g30_combined_locale(locale: str) -> dict[str, str]:
    values = dict(g30.fetch_upstream_json(g30.G30_COMMIT, locale))
    values.update(reconstruct_g30_supplements().get(locale, {}))
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 3, 0, 0):
        raise ValueError("G31 frozen semantic partition changed")

    previous = reconstruct_g30_full()
    expected = set(scope["addon_full_locales"])
    inherited = expected - NEW_FULL_LOCALES
    if len(expected) != 66 or NEW_FULL_LOCALES - expected:
        raise ValueError("G31 addon-full ownership must contain 66 locales including nah and ry_ua")
    if inherited != set(previous):
        raise ValueError("G31 inherited addon-full ownership must be exactly the 64 G30 full locales")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        if locale in NEW_FULL_LOCALES:
            result[locale] = dict(target)
            continue
        old = previous[locale]
        values: dict[str, str] = {}
        for key, english in target.items():
            if key in unchanged:
                if key not in old:
                    raise ValueError(f"{locale}: unchanged G31 key missing from G30 full locale: {key}")
                values[key] = old[key]
            else:
                values[key] = english
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 3, 0, 0):
        raise ValueError("G31 supplement reconstruction requires the frozen G30 semantic delta")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 21:
        raise ValueError("G31 supplement ownership must be exactly 21 selected locales")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G31_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_combined = g30_combined_locale(locale)
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_combined:
                    raise ValueError(f"{locale}: unchanged missing G31 key has no complete G30 value: {key}")
                values[key] = previous_combined[key]
            elif key in added:
                values[key] = target[key]
            else:
                raise ValueError(f"{locale}: unexpected G31 semantic state for missing key: {key}")
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
    if (len(base), len(target), normal_count) != (153, 156, 150):
        raise ValueError(f"G31 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (153, 3, 0, 0):
        raise ValueError("G31 semantic delta counts changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (153, 3, 0, 0):
        raise ValueError("G31 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g30_semantics"]:
        raise ValueError("G31 policy must require exact G30 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G31 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (66, 21, 156):
        raise ValueError(f"G31 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.19.3-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.19.3 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("153 unchanged G30 key/value semantics are inherited exactly")
    print("3 new G31 meanings use exact target English until reviewed translations are available")
    print("Nahuatl and Rusyn use documented complete-English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

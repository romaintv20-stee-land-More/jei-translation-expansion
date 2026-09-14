#!/usr/bin/env python3
"""Reconstruct Minecraft 1.20.4 / JEI 17.3.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_20_2 as g35

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.20.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.20.4" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.20.4-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20.2-to-1.20.4.json"
POLICY_PATH = ROOT / "translations" / "g36-mc1.20.4" / "policy.json"
DELTA_PATH = ROOT / "translations" / "g36-mc1.20.4" / "semantic-delta.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.20.4"
DEBUG_PREFIX = "description.jei."
G36_COMMIT = "282f6faecfd71545243be0a94703bdde90eac4e7"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
CHANGED_KEY = "jei.tooltip.error.crash"
ADDED_KEY = "jei.tooltip.error.render.crash"

parse_json_text = g35.parse_json_text
parse_json = g35.parse_json
write_json = g35.write_json
semantic_sets = g35.semantic_sets


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G36-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g35_full() -> dict[str, dict[str, str]]:
    target = g35.parse_json(g35.TARGET_SOURCE)
    scope = json.loads(g35.SCOPE_PATH.read_text(encoding="utf-8"))
    return g35.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g35_supplements() -> dict[str, dict[str, str]]:
    target = g35.parse_json(g35.TARGET_SOURCE)
    scope = json.loads(g35.SCOPE_PATH.read_text(encoding="utf-8"))
    return g35.reconstruct_supplements(target, scope)


@lru_cache(maxsize=None)
def g35_complete_locale(locale: str) -> dict[str, str]:
    full = reconstruct_g35_full()
    if locale in full:
        return dict(full[locale])
    values = dict(g35.fetch_upstream_json(g35.G35_COMMIT, locale))
    values.update(reconstruct_g35_supplements().get(locale, {}))
    return values


@lru_cache(maxsize=1)
def reviewed_delta() -> dict[str, dict[str, str]]:
    raw = json.loads(DELTA_PATH.read_text(encoding="utf-8"))
    return {str(locale): {str(k): str(v) for k, v in values.items()} for locale, values in raw["locales"].items()}


def translated_value(locale: str, key: str, target: dict[str, str], fallback_locales: set[str]) -> str:
    if locale in fallback_locales:
        return target[key]
    delta = reviewed_delta().get(locale, {})
    if key not in delta:
        raise ValueError(f"{locale}: no reviewed G36 translation for {key}")
    return delta[key]


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (155, 1, 0, 1):
        raise ValueError("G36 frozen semantic partition changed")
    if added != {ADDED_KEY} or changed != {CHANGED_KEY}:
        raise ValueError("G36 changed/added key identities changed")

    previous = reconstruct_g35_full()
    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(previous) != 68 or len(expected) != 67 or set(previous) - expected != {"hu_hu"}:
        raise ValueError("G36 addon-full ownership must equal G35 minus hu_hu")
    if len(fallback_locales) != 31 or not fallback_locales <= expected:
        raise ValueError("G36 full fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        values: dict[str, str] = {}
        for key in target:
            if key in unchanged:
                if key not in old:
                    raise ValueError(f"{locale}: unchanged G36 key absent from G35: {key}")
                values[key] = old[key]
            elif key in {CHANGED_KEY, ADDED_KEY}:
                values[key] = translated_value(locale, key, target, fallback_locales)
            else:
                raise ValueError(f"{locale}: unexpected G36 semantic key: {key}")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (155, 1, 0, 1):
        raise ValueError("G36 supplement semantic partition changed")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 22:
        raise ValueError("G36 supplement ownership must be exactly 22 selected locales")

    result: dict[str, dict[str, str]] = {}
    delta = reviewed_delta()
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G36_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_complete = g35_complete_locale(locale)
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_complete:
                    raise ValueError(f"{locale}: unchanged missing G36 key has no complete G35 value: {key}")
                values[key] = previous_complete[key]
            elif key == ADDED_KEY:
                locale_delta = delta.get(locale, {})
                if key not in locale_delta:
                    raise ValueError(f"{locale}: missing reviewed G36 supplement translation for {key}")
                values[key] = locale_delta[key]
            elif key == CHANGED_KEY:
                raise ValueError(f"{locale}: changed G36 tooltip-crash key unexpectedly missing upstream")
            else:
                raise ValueError(f"{locale}: missing key is outside frozen G36 semantic partition: {key}")
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
    if (len(base), len(target), normal_count) != (156, 157, 151):
        raise ValueError(f"G36 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (155, 1, 0, 1):
        raise ValueError("G36 semantic delta counts changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (155, 1, 0, 1):
        raise ValueError("G36 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g35_semantics"]:
        raise ValueError("G36 policy must require exact G35 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G36 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (67, 22, 157):
        raise ValueError(f"G36 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.20.4-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.20.4 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("155 unchanged G35 key/value semantics are inherited exactly")
    print("2 new/changed normal semantics use reviewed G36 translations or documented English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

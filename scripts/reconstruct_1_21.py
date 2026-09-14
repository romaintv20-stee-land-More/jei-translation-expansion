#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21 / JEI 19.8.2 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_20_6 as g37

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.20.6" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.20.6-to-1.21.json"
POLICY_PATH = ROOT / "translations" / "g38-mc1.21" / "policy.json"
DELTA_PATH = ROOT / "translations" / "g38-mc1.21" / "semantic-delta.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21"
DEBUG_PREFIX = "description.jei."
G38_COMMIT = "02370235626ddb4e479e13e6cde9b6d5466cd5ff"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g37.parse_json_text
parse_json = g37.parse_json
write_json = g37.write_json
semantic_sets = g37.semantic_sets


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G38-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


@lru_cache(maxsize=1)
def reconstruct_g37_full() -> dict[str, dict[str, str]]:
    target = g37.parse_json(g37.TARGET_SOURCE)
    scope = json.loads(g37.SCOPE_PATH.read_text(encoding="utf-8"))
    return g37.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g37_supplements() -> dict[str, dict[str, str]]:
    target = g37.parse_json(g37.TARGET_SOURCE)
    scope = json.loads(g37.SCOPE_PATH.read_text(encoding="utf-8"))
    return g37.reconstruct_supplements(target, scope)


@lru_cache(maxsize=1)
def g37_scope() -> dict:
    return json.loads(g37.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def g37_combined_locale(locale: str) -> dict[str, str]:
    scope = g37_scope()
    full = reconstruct_g37_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return fetch_upstream_json(g37.G37_COMMIT, locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = fetch_upstream_json(g37.G37_COMMIT, locale)
        supplement = reconstruct_g37_supplements()[locale]
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G37")


@lru_cache(maxsize=1)
def reviewed_delta() -> dict[str, dict[str, str]]:
    target = parse_json(TARGET_SOURCE)
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    expected_keys = added | changed
    raw = json.loads(DELTA_PATH.read_text(encoding="utf-8"))
    keys = raw["keys"]
    english = raw["english"]
    if len(keys) != len(set(keys)) or set(keys) != expected_keys:
        raise ValueError("G38 reviewed semantic-delta key set differs from exact added/changed semantics")
    if len(keys) != len(english):
        raise ValueError("G38 semantic-delta key/English arrays have different lengths")
    for key, value in zip(keys, english):
        if target.get(key) != value:
            raise ValueError(f"G38 semantic-delta English source differs for {key}")
    result: dict[str, dict[str, str]] = {}
    for locale, values in raw["locales"].items():
        if len(values) != len(keys):
            raise ValueError(f"{locale}: G38 semantic-delta value count differs from key count")
        result[locale] = dict(zip(keys, values))
    return result


def resolve_new_or_changed(locale: str, key: str, target_english: str, fallback_locales: set[str]) -> str:
    if locale in fallback_locales:
        return target_english
    delta = reviewed_delta().get(locale, {})
    return delta.get(key, target_english)


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 19, 0, 1):
        raise ValueError("G38 frozen semantic partition changed")

    previous = reconstruct_g37_full()
    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(previous) != 67 or expected != set(previous):
        raise ValueError("G38 addon-full ownership must match G37 exactly")
    if len(fallback_locales) != 31 or not fallback_locales <= expected:
        raise ValueError("G38 full-English fallback ownership changed")

    translated_full = expected - fallback_locales
    if set(reviewed_delta()) != translated_full:
        raise ValueError("G38 reviewed semantic delta must cover exactly the 36 translated/AI-assisted full locales")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        if set(old) != set(base):
            raise ValueError(f"{locale}: G37 full key set differs from G38 base")
        values: dict[str, str] = {}
        for key, english in target.items():
            if key in unchanged:
                values[key] = old[key]
            elif key in added or key in changed:
                values[key] = resolve_new_or_changed(locale, key, english, fallback_locales)
            else:
                raise ValueError(f"{locale}: unresolved G38 semantic key: {key}")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 21 or "ja_jp" in expected:
        raise ValueError("G38 supplement ownership must contain 21 locales and retire ja_jp")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G38_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_complete = g37_combined_locale(locale)
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_complete:
                    raise ValueError(f"{locale}: unchanged G38 missing key absent from G37 complete view: {key}")
                values[key] = previous_complete[key]
            elif key in added or key in changed:
                values[key] = reviewed_delta().get(locale, {}).get(key, target[key])
            else:
                raise ValueError(f"{locale}: unresolved G38 supplement semantic key: {key}")
        if set(values) & set(upstream):
            raise ValueError(f"{locale}: G38 supplement would override upstream-owned keys")
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
    if (len(base), len(target), normal_count) != (157, 176, 170):
        raise ValueError(f"G38 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 19, 0, 1):
        raise ValueError("G38 semantic delta counts changed")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (156, 19, 0, 1):
        raise ValueError("G38 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g37_semantics"]:
        raise ValueError("G38 policy must require exact G37 reuse for unchanged meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G38 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (67, 21, 176):
        raise ValueError(f"G38 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.21-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.21 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("156 G37 meanings inherit exactly; 20 new/changed G38 meanings use reviewed translations or explicit English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

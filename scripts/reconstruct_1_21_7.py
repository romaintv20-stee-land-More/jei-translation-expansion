#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.7 / JEI 23.1.0 resources deterministically."""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21_6 as g42

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.6" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.7" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.7-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.6-to-1.21.7.json"
POLICY_PATH = ROOT / "translations" / "g43-mc1.21.7" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.7"
DEBUG_PREFIX = "description.jei."
G43_COMMIT = "ee33b5d69f6cf9167c32c2e84fdc69fa1b008440"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
NEW_GRINDSTONE_KEY = "gui.jei.category.grindstone"
REINTRODUCED_EXPERIENCE_KEY = "gui.jei.category.grindstone.experience"
ADDED_G43_KEYS = {NEW_GRINDSTONE_KEY, REINTRODUCED_EXPERIENCE_KEY}
MALFORMED_FULL_OVERRIDES = {"uk_ua"}

parse_json = g42.parse_json
write_json = g42.write_json
semantic_sets = g42.semantic_sets
preserves_runtime_literals = g42.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_g43_upstream(locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=G43_COMMIT, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G43-reconstruct"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError(f"{locale}: missing pinned G43 upstream locale") from exc
        raise
    try:
        return clean_mapping(json.loads(text))
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        return clean_mapping(json.loads(g42.g41.repair_uk_ua_text(text)))


@lru_cache(maxsize=1)
def g42_scope() -> dict:
    return json.loads(g42.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g42_full() -> dict[str, dict[str, str]]:
    target = parse_json(g42.TARGET_SOURCE)
    full, _ = g42.reconstruct_full(target, g42_scope())
    return full


@lru_cache(maxsize=1)
def g42_supplements() -> dict[str, dict[str, str]]:
    target = parse_json(g42.TARGET_SOURCE)
    supplements, _ = g42.reconstruct_supplements(target, g42_scope())
    return supplements


@lru_cache(maxsize=None)
def g42_combined_locale(locale: str) -> dict[str, str]:
    scope = g42_scope()
    if locale in g42_full():
        return dict(g42_full()[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g42.fetch_g42_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = g42.fetch_g42_upstream(locale)
        supplement = g42_supplements()[locale]
        if set(upstream) & set(supplement):
            raise ValueError(f"{locale}: G42 combined ownership overlap")
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G42")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (289, 2, 0, 0):
        raise ValueError("G43 frozen semantic partition changed")
    if added != ADDED_G43_KEYS:
        raise ValueError(f"G43 added key set changed: {sorted(added)}")
    return unchanged, added, removed, changed


def resolve_unchanged(locale: str, key: str, english: str) -> tuple[str, str]:
    previous = g42_combined_locale(locale)
    if key not in previous:
        raise ValueError(f"{locale}: unchanged key absent from G42: {key}")
    value = previous[key]
    return (value, "g42") if preserves_runtime_literals(english, value) else (english, "english")


def resolve_added(locale: str, key: str, english: str) -> tuple[str, str]:
    if key == NEW_GRINDSTONE_KEY:
        return english, "english"
    if key != REINTRODUCED_EXPERIENCE_KEY:
        raise ValueError(f"{locale}: unknown G43 added key: {key}")
    g41_source = parse_json(g42.g41.TARGET_SOURCE)
    if g41_source.get(key) != english:
        raise ValueError("G43 reintroduced grindstone experience no longer exactly matches G41 English")
    historical = g42.g41_combined_locale(locale).get(key)
    if historical is not None and preserves_runtime_literals(english, historical):
        return historical, "g41-same-key"
    return english, "english"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if removed or changed or added != ADDED_G43_KEYS:
        raise ValueError("G43 semantic contract changed")
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    malformed = set(scope.get("malformed_upstream_full_override_locales", []))
    if malformed != MALFORMED_FULL_OVERRIDES or "uk_ua" not in expected:
        raise ValueError("G43 malformed upstream ownership changed")
    if len(fallback) != 30 or not fallback <= expected or "uk_ua" in fallback:
        raise ValueError("G43 documented fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        if locale in fallback:
            result[locale] = dict(target)
            stats[locale] = {"g42":0,"g41-same-key":0,"upstream-repair":0,"english":len(target),"documented-fallback":len(target)}
            continue
        repaired = fetch_g43_upstream(locale) if locale == "uk_ua" else {}
        values: dict[str, str] = {}
        count = {"g42":0,"g41-same-key":0,"upstream-repair":0,"english":0,"documented-fallback":0}
        for key, english in target.items():
            if key.startswith(DEBUG_PREFIX):
                value, source = english, "english"
            elif key in repaired and preserves_runtime_literals(english, repaired[key]):
                value, source = repaired[key], "upstream-repair"
            elif key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved target key {key}")
            values[key] = value
            count[source] += 1
        if set(values) != set(target):
            raise ValueError(f"{locale}: full G43 key set mismatch")
        result[locale] = values
        stats[locale] = count
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if removed or changed or added != ADDED_G43_KEYS:
        raise ValueError("G43 supplement semantic contract changed")
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(scope["selected_upstream_incomplete_locales"]):
        if locale == "uk_ua":
            raise ValueError("uk_ua must be a full repair override, not a supplement")
        upstream = fetch_g43_upstream(locale)
        missing = normal - set(upstream)
        values: dict[str, str] = {}
        count = {"g42":0,"g41-same-key":0,"english":0,"upstream-owned":len(normal & set(upstream))}
        for key in sorted(missing):
            english = target[key]
            if key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved supplement key {key}")
            values[key] = value
            count[source] += 1
        if not values or set(values) & set(upstream):
            raise ValueError(f"{locale}: invalid G43 supplement ownership")
        result[locale] = values
        stats[locale] = count
    return result, stats


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int, dict]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    normal_count = len([k for k in target if not k.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (289, 291, 285):
        raise ValueError("G43 source counts changed")
    if (diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"), diff.get("removed_key_count"), diff.get("changed_english_value_count")) != (289, 2, 0, 0):
        raise ValueError("G43 frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g42_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G43 reuse policy changed")
    if not reuse.get("historical_same_key_same_english_reuse_allowed"):
        raise ValueError("G43 historical exact-reuse policy missing")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if len(full) + len(supplements) + len(complete) != 90:
        raise ValueError("G43 ownership total changed")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supp_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supp_dir.mkdir(parents=True, exist_ok=True)
    for locale, values in sorted(full.items()):
        write_json(full_dir / f"{locale}.json", values)
    for locale, values in sorted(supplements.items()):
        write_json(supp_dir / f"{locale}.json", values)

    provenance = {
        "schema_version":1,
        "generation":"g43-mc1.21.7",
        "cross_key_reuse_allowed":False,
        "added_g43_keys":sorted(ADDED_G43_KEYS),
        "full_locales":full_stats,
        "supplement_locales":supplement_stats,
    }
    write_json(output / "provenance.json", provenance)
    return len(full), len(supplements), len(target), provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()
    full, supplements, keys, _ = reconstruct_all(args.output, clean=not args.no_clean)
    print(f"Output: {args.output}")
    print(f"Full addon/override locales: {full}")
    print(f"Missing-key-only upstream supplements: {supplements}")
    print(f"Keys per complete locale: {keys}")
    print("G42 -> G43: 289 unchanged meanings + 2 added grindstone meanings")
    print("uk_ua remains a valid full repair override because pinned upstream JSON is malformed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

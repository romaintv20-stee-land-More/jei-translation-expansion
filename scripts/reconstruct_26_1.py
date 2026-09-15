#!/usr/bin/env python3
"""Reconstruct Minecraft 26.1 / JEI 29.2.0 language resources deterministically."""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import bootstrap_26_1 as bootstrap
import reconstruct_1_21_11 as g47

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.11" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "26.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-26.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.11-to-26.1.json"
POLICY_PATH = ROOT / "translations" / "g48-mc26.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "26.1"
DEBUG_PREFIX = "description.jei."
G48_COMMIT = "16c0e3b3fcb8cd4093617a691de6f3d1c137e1ca"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
ADDED_G48_KEYS = set(bootstrap.EXPECTED_ADDED)
REMOVED_G47_KEYS = set(bootstrap.EXPECTED_REMOVED)
CHANGED_G48_KEYS = set(bootstrap.EXPECTED_CHANGED)

parse_json = g47.parse_json
write_json = g47.write_json
semantic_sets = g47.semantic_sets
preserves_runtime_literals = g47.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_locale(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G48-reconstruct"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {}
        raise
    try:
        return clean_mapping(json.loads(text))
    except json.JSONDecodeError:
        return {}


def fetch_g48_upstream(locale: str) -> dict[str, str]:
    values = fetch_locale(G48_COMMIT, locale)
    if not values:
        raise ValueError(f"{locale}: missing or invalid pinned G48 upstream locale")
    return values


@lru_cache(maxsize=1)
def g47_scope() -> dict:
    return json.loads(g47.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g47_full() -> dict[str, dict[str, str]]:
    values, _ = g47.reconstruct_full(parse_json(g47.TARGET_SOURCE), g47_scope())
    return values


@lru_cache(maxsize=1)
def g47_supplements() -> dict[str, dict[str, str]]:
    values, _ = g47.reconstruct_supplements(parse_json(g47.TARGET_SOURCE), g47_scope())
    return values


@lru_cache(maxsize=None)
def g47_combined_locale(locale: str) -> dict[str, str]:
    scope = g47_scope()
    if locale in g47_full():
        return dict(g47_full()[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g47.fetch_g47_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        combined = dict(g47.fetch_g47_upstream(locale))
        combined.update(g47_supplements()[locale])
        return combined
    raise KeyError(f"{locale}: not selected in G47")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (294, 9, 34, 6):
        raise ValueError("G48 frozen semantic partition changed")
    if added != ADDED_G48_KEYS or removed != REMOVED_G47_KEYS or changed != CHANGED_G48_KEYS:
        raise ValueError("G48 frozen semantic key sets changed")
    return unchanged, added, removed, changed


def resolve_unchanged(locale: str, key: str, english: str) -> tuple[str, str]:
    previous = g47_combined_locale(locale)
    if key not in previous:
        raise ValueError(f"{locale}: unchanged G48 key absent from G47 complete view: {key}")
    value = previous[key]
    return (value, "g47") if preserves_runtime_literals(english, value) else (english, "english")


def resolve_target_owned(key: str, english: str) -> tuple[str, str]:
    if key not in ADDED_G48_KEYS and key not in CHANGED_G48_KEYS:
        raise ValueError(f"unexpected G48 target-owned semantic key: {key}")
    return english, "english"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, _, changed = semantic_partition()
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(expected) != 64 or scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G48 full ownership changed")
    if len(fallback) != 30 or not fallback <= expected:
        raise ValueError("G48 fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        if locale in fallback:
            result[locale] = dict(target)
            stats[locale] = {"g47": 0, "english": len(target), "documented-fallback": len(target)}
            continue
        values: dict[str, str] = {}
        count = {"g47": 0, "english": 0, "documented-fallback": 0}
        for key, english in target.items():
            if key.startswith(DEBUG_PREFIX):
                value, source = english, "english"
            elif key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added or key in changed:
                value, source = resolve_target_owned(key, english)
            else:
                raise ValueError(f"{locale}: unresolved G48 key {key}")
            values[key] = value
            count[source] += 1
        if set(values) != set(target) or set(values) & REMOVED_G47_KEYS:
            raise ValueError(f"{locale}: invalid G48 full key set")
        result[locale] = values
        stats[locale] = count
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, _, changed = semantic_partition()
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 25 or "uk_ua" not in expected:
        raise ValueError("G48 supplement ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g48_upstream(locale)
        missing = normal - set(upstream)
        override_keys = set(scope.get("upstream_literal_safety_overrides", {}).get(locale, []))
        for key in override_keys:
            if key not in normal or key not in upstream or preserves_runtime_literals(target[key], upstream[key]):
                raise ValueError(f"{locale}: invalid/unneeded G48 safety override {key}")
        needed = missing | override_keys
        values: dict[str, str] = {}
        count = {
            "g47": 0,
            "english": 0,
            "upstream-owned": len(normal & set(upstream)),
            "upstream-safety-overrides": len(override_keys),
        }
        for key in sorted(needed):
            english = target[key]
            if key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added or key in changed:
                value, source = resolve_target_owned(key, english)
            else:
                raise ValueError(f"{locale}: unresolved G48 supplement key {key}")
            values[key] = value
            count[source] += 1
        if not values or (set(values) & set(upstream)) != override_keys:
            raise ValueError(f"{locale}: invalid G48 supplement ownership")
        if any(key.startswith(DEBUG_PREFIX) for key in values) or set(values) & REMOVED_G47_KEYS:
            raise ValueError(f"{locale}: invalid G48 supplement key")
        result[locale] = values
        stats[locale] = count
    return result, stats


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int, dict]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    unchanged, added, removed, changed = semantic_partition()
    normal_count = len([k for k in target if not k.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (334, 309, 303):
        raise ValueError("G48 source counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (294, 9, 34, 6):
        raise ValueError("G48 semantic partition changed")
    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (294, 9, 34, 6):
        raise ValueError("G48 frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g47_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G48 reuse policy changed")
    if not reuse.get("project_owned_added_or_changed_keys_use_exact_target_english"):
        raise ValueError("G48 added/changed-key fallback policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supplements), len(complete)) != (64, 25, 1) or complete != {"en_us"}:
        raise ValueError("G48 ownership total changed")

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
        "schema_version": 1,
        "generation": "g48-mc26.1",
        "upstream_commit": G48_COMMIT,
        "cross_key_reuse_allowed": False,
        "public_distribution_configured": True,
        "added_g48_keys": sorted(added),
        "removed_g47_keys": sorted(removed),
        "changed_g48_keys": sorted(changed),
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "g47": sum(x["g47"] for x in full_stats.values()) + sum(x["g47"] for x in supplement_stats.values()),
            "english": sum(x["english"] for x in full_stats.values()) + sum(x["english"] for x in supplement_stats.values()),
            "upstream-safety-overrides": sum(x.get("upstream-safety-overrides", 0) for x in supplement_stats.values()),
        },
    }
    write_json(output / "provenance.json", provenance)
    return len(full), len(supplements), len(target), provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-clean", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    full, supplements, keys, provenance = reconstruct_all(args.output, clean=not args.no_clean)
    print("PASS: Minecraft 26.1 deterministic reconstruction")
    print(f"Full addon locales: {full}")
    print(f"Upstream supplement locales: {supplements}")
    print(f"Keys per complete addon locale: {keys}")
    print(f"Exact G47 semantic reuses: {provenance['totals']['g47']}")
    print(f"Exact target-English values emitted: {provenance['totals']['english']}")
    print("Cross-key reuse: forbidden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 26.1.1 / JEI 29.4.0 language resources deterministically."""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_26_1 as g48

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "26.1.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-26.1.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "26.1-to-26.1.1.json"
POLICY_PATH = ROOT / "translations" / "g49-mc26.1.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "26.1.1"
DEBUG_PREFIX = "description.jei."
G49_COMMIT = "5a2ecc40c438e9137a8b64b2d9b48c095fc24c23"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json = g48.parse_json
write_json = g48.write_json
preserves_runtime_literals = g48.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_locale(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G49-reconstruct"})
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


def fetch_g49_upstream(locale: str) -> dict[str, str]:
    values = fetch_locale(G49_COMMIT, locale)
    if not values:
        raise ValueError(f"{locale}: missing or invalid pinned G49 upstream locale")
    return values


@lru_cache(maxsize=1)
def g48_scope() -> dict:
    return json.loads(g48.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g48_full() -> dict[str, dict[str, str]]:
    values, _ = g48.reconstruct_full(parse_json(g48.TARGET_SOURCE), g48_scope())
    return values


@lru_cache(maxsize=1)
def g48_supplements() -> dict[str, dict[str, str]]:
    values, _ = g48.reconstruct_supplements(parse_json(g48.TARGET_SOURCE), g48_scope())
    return values


@lru_cache(maxsize=None)
def g48_combined_locale(locale: str) -> dict[str, str]:
    scope = g48_scope()
    full = g48_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g48.fetch_g48_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        combined = dict(g48.fetch_g48_upstream(locale))
        combined.update(g48_supplements()[locale])
        return combined
    raise KeyError(f"{locale}: not selected in G48")


def verify_semantics() -> dict[str, str]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    if len(base) != 309 or len(target) != 309 or base != target:
        raise ValueError("G49 target must be exactly semantically identical to G48 (309 keys)")
    return target


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(expected) != 64 or len(fallback) != 30 or not fallback <= expected:
        raise ValueError("G49 full/fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        previous = g48_combined_locale(locale)
        values: dict[str, str] = {}
        reused = 0
        english = 0
        for key, target_english in target.items():
            candidate = previous.get(key, target_english)
            if key.startswith(DEBUG_PREFIX) or not preserves_runtime_literals(target_english, candidate):
                values[key] = target_english
                english += 1
            else:
                values[key] = candidate
                reused += 1
        if set(values) != set(target):
            raise ValueError(f"{locale}: invalid G49 full key set")
        result[locale] = values
        stats[locale] = {
            "g48": reused,
            "english": english,
            "documented-fallback": len(target) if locale in fallback else 0,
        }
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 25 or "uk_ua" not in expected:
        raise ValueError("G49 supplement ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g49_upstream(locale)
        missing = normal - set(upstream)
        override_keys = set(scope.get("upstream_literal_safety_overrides", {}).get(locale, []))
        for key in override_keys:
            if key not in normal or key not in upstream or preserves_runtime_literals(target[key], upstream[key]):
                raise ValueError(f"{locale}: invalid/unneeded G49 safety override {key}")
        needed = missing | override_keys
        previous = g48_combined_locale(locale)
        values: dict[str, str] = {}
        reused = 0
        english = 0
        for key in sorted(needed):
            target_english = target[key]
            candidate = previous.get(key, target_english)
            if preserves_runtime_literals(target_english, candidate):
                values[key] = candidate
                reused += 1
            else:
                values[key] = target_english
                english += 1
        if not values or (set(values) & set(upstream)) != override_keys:
            raise ValueError(f"{locale}: invalid G49 supplement ownership")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G49 supplement contains debug-only key")
        result[locale] = values
        stats[locale] = {
            "g48": reused,
            "english": english,
            "upstream-owned": len(normal & set(upstream)),
            "upstream-safety-overrides": len(override_keys),
        }
    return result, stats


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int, dict]:
    target = verify_semantics()
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    normal_count = len([k for k in target if not k.startswith(DEBUG_PREFIX)])
    if normal_count != 303:
        raise ValueError("G49 normal key count changed")
    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (309, 0, 0, 0):
        raise ValueError("G49 frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g48_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G49 reuse policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supplements), len(complete)) != (64, 25, 1) or complete != {"en_us"}:
        raise ValueError("G49 ownership total changed")

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
        "generation": "g49-mc26.1.1",
        "upstream_commit": G49_COMMIT,
        "cross_key_reuse_allowed": False,
        "all_target_semantics_unchanged_from_g48": True,
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "g48": sum(x["g48"] for x in full_stats.values()) + sum(x["g48"] for x in supplement_stats.values()),
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
    args = parser.parse_args()
    full, supplements, keys, provenance = reconstruct_all(args.output, clean=not args.no_clean)
    print("PASS: Minecraft 26.1.1 deterministic reconstruction")
    print(f"Full addon locales: {full}")
    print(f"Upstream supplement locales: {supplements}")
    print(f"Keys per complete addon locale: {keys}")
    print(f"Exact G48 semantic reuses: {provenance['totals']['g48']}")
    print(f"Exact target-English values emitted: {provenance['totals']['english']}")
    print("Cross-key reuse: forbidden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

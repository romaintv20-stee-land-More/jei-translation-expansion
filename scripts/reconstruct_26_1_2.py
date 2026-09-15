#!/usr/bin/env python3
"""Reconstruct Minecraft 26.1.2 / JEI 29.37.0 language resources deterministically."""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_26_1_1 as g49

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.1.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "26.1.2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-26.1.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "26.1.1-to-26.1.2.json"
POLICY_PATH = ROOT / "translations" / "g50-mc26.1.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "26.1.2"
DEBUG_PREFIX = "description.jei."
G50_COMMIT = "d7c73ed63a7a25a9ad416428eafef3a3dcf0f1c8"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json = g49.parse_json
write_json = g49.write_json
preserves_runtime_literals = g49.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_locale(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G50-reconstruct"})
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


def fetch_g50_upstream(locale: str) -> dict[str, str]:
    values = fetch_locale(G50_COMMIT, locale)
    if not values:
        raise ValueError(f"{locale}: missing or invalid pinned G50 upstream locale")
    return values


@lru_cache(maxsize=1)
def g49_scope() -> dict:
    return json.loads(g49.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g49_full() -> dict[str, dict[str, str]]:
    values, _ = g49.reconstruct_full(parse_json(g49.TARGET_SOURCE), g49_scope())
    return values


@lru_cache(maxsize=1)
def g49_supplements() -> dict[str, dict[str, str]]:
    values, _ = g49.reconstruct_supplements(parse_json(g49.TARGET_SOURCE), g49_scope())
    return values


@lru_cache(maxsize=None)
def g49_combined_locale(locale: str) -> dict[str, str]:
    scope = g49_scope()
    full = g49_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        if locale == "en_us":
            return parse_json(g49.TARGET_SOURCE)
        return g49.fetch_g49_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        combined = dict(g49.fetch_g49_upstream(locale))
        combined.update(g49_supplements()[locale])
        return combined
    raise KeyError(f"{locale}: not selected in G49")


def semantic_reusable(base: dict[str, str], target: dict[str, str], key: str) -> bool:
    return key in base and base[key] == target[key]


def verify_semantics() -> tuple[dict[str, str], dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    normal = [k for k in target if not k.startswith(DEBUG_PREFIX)]
    unchanged = [k for k in set(base) & set(target) if base[k] == target[k]]
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = [k for k in set(base) & set(target) if base[k] != target[k]]
    if (len(base), len(target), len(normal)) != (309, 334, 328):
        raise ValueError("G50 English source counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (294, 34, 9, 6):
        raise ValueError("G50 semantic delta changed")
    return base, target


def reconstruct_full(base: dict[str, str], target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(expected) != 63 or len(fallback) != 30 or not fallback <= expected:
        raise ValueError("G50 full/fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        previous = g49_combined_locale(locale)
        values: dict[str, str] = {}
        reused = 0
        english = 0
        novel = 0
        for key, target_english in target.items():
            if key.startswith(DEBUG_PREFIX):
                values[key] = target_english
                english += 1
                continue
            if semantic_reusable(base, target, key):
                candidate = previous.get(key, target_english)
                if preserves_runtime_literals(target_english, candidate):
                    values[key] = candidate
                    reused += 1
                    continue
            values[key] = target_english
            english += 1
            if not semantic_reusable(base, target, key):
                novel += 1
        if set(values) != set(target):
            raise ValueError(f"{locale}: invalid G50 full key set")
        result[locale] = values
        stats[locale] = {
            "g49-exact-semantic": reused,
            "target-English": english,
            "novel-or-changed-English": novel,
            "documented-fallback": len(target) if locale in fallback else 0,
        }
    return result, stats


def reconstruct_supplements(base: dict[str, str], target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 26 or "fil_ph" not in expected or "uk_ua" not in expected:
        raise ValueError("G50 supplement ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g50_upstream(locale)
        missing = normal - set(upstream)
        override_keys = set(scope.get("upstream_literal_safety_overrides", {}).get(locale, []))
        for key in override_keys:
            if key not in normal or key not in upstream or preserves_runtime_literals(target[key], upstream[key]):
                raise ValueError(f"{locale}: invalid/unneeded G50 safety override {key}")
        needed = missing | override_keys
        previous = g49_combined_locale(locale)
        values: dict[str, str] = {}
        reused = 0
        english = 0
        novel = 0
        for key in sorted(needed):
            target_english = target[key]
            candidate = previous.get(key, target_english)
            if semantic_reusable(base, target, key) and preserves_runtime_literals(target_english, candidate):
                values[key] = candidate
                reused += 1
            else:
                values[key] = target_english
                english += 1
                if not semantic_reusable(base, target, key):
                    novel += 1
        if not values or (set(values) & set(upstream)) != override_keys:
            raise ValueError(f"{locale}: invalid G50 supplement ownership")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G50 supplement contains debug-only key")
        result[locale] = values
        stats[locale] = {
            "g49-exact-semantic": reused,
            "target-English": english,
            "novel-or-changed-English": novel,
            "upstream-owned": len(normal & set(upstream)),
            "upstream-safety-overrides": len(override_keys),
        }
    return result, stats


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int, dict]:
    base, target = verify_semantics()
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (294, 34, 9, 6):
        raise ValueError("G50 frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_only_exact_same_key_same_english") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G50 reuse policy changed")

    full, full_stats = reconstruct_full(base, target, scope)
    supplements, supplement_stats = reconstruct_supplements(base, target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supplements), len(complete)) != (63, 26, 1) or complete != {"en_us"}:
        raise ValueError("G50 ownership total changed")

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
        "generation": "g50-mc26.1.2",
        "upstream_commit": G50_COMMIT,
        "cross_key_reuse_allowed": False,
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "g49-exact-semantic": sum(x["g49-exact-semantic"] for x in full_stats.values()) + sum(x["g49-exact-semantic"] for x in supplement_stats.values()),
            "target-English": sum(x["target-English"] for x in full_stats.values()) + sum(x["target-English"] for x in supplement_stats.values()),
            "novel-or-changed-English": sum(x["novel-or-changed-English"] for x in full_stats.values()) + sum(x["novel-or-changed-English"] for x in supplement_stats.values()),
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
    print("PASS: Minecraft 26.1.2 deterministic reconstruction")
    print(f"Full addon locales: {full}")
    print(f"Upstream supplement locales: {supplements}")
    print(f"Keys per complete addon locale: {keys}")
    print(f"Exact G49 semantic reuses: {provenance['totals']['g49-exact-semantic']}")
    print(f"Exact target-English values emitted: {provenance['totals']['target-English']}")
    print(f"Novel/changed meanings using target English: {provenance['totals']['novel-or-changed-English']}")
    print("Cross-key reuse: forbidden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

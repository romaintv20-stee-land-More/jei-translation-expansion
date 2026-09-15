#!/usr/bin/env python3
"""Reconstruct provisional Minecraft 26.3 RC2 JEI translations deterministically.

This prepares translation data only. It must not be used to register a completed G52 package.
"""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_26_2 as g51

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "provisional" / "sources" / "26.3-rc-2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "provisional" / "minecraft-26.3-rc-2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "provisional" / "diffs" / "26.2-to-26.3-rc-2.json"
POLICY_PATH = ROOT / "translations" / "pre-g52-mc26.3-rc2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "provisional-26.3-rc-2"
DEBUG_PREFIX = "description.jei."
PRE_G52_COMMIT = "58362ffb5baa95580549d6825811e7363964a271"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json = g51.parse_json
write_json = g51.write_json
preserves_runtime_literals = g51.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_locale(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-pre-G52-reconstruct"})
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


def fetch_target_upstream(locale: str) -> dict[str, str]:
    values = fetch_locale(PRE_G52_COMMIT, locale)
    if not values:
        raise ValueError(f"{locale}: missing or invalid pinned provisional upstream locale")
    return values


@lru_cache(maxsize=1)
def g51_scope() -> dict:
    return json.loads(g51.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g51_full() -> dict[str, dict[str, str]]:
    base, target = g51.verify_semantics()
    values, _ = g51.reconstruct_full(base, target, g51_scope())
    return values


@lru_cache(maxsize=1)
def g51_supplements() -> dict[str, dict[str, str]]:
    base, target = g51.verify_semantics()
    values, _ = g51.reconstruct_supplements(base, target, g51_scope())
    return values


@lru_cache(maxsize=None)
def g51_combined_locale(locale: str) -> dict[str, str]:
    scope = g51_scope()
    full = g51_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        if locale == "en_us":
            return parse_json(g51.TARGET_SOURCE)
        return g51.fetch_g51_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        combined = dict(g51.fetch_g51_upstream(locale))
        combined.update(g51_supplements()[locale])
        return combined
    raise KeyError(f"{locale}: not selected in G51")


def verify_semantics() -> tuple[dict[str, str], dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    normal = [k for k in target if not k.startswith(DEBUG_PREFIX)]
    unchanged = [k for k in set(base) & set(target) if base[k] == target[k]]
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = [k for k in set(base) & set(target) if base[k] != target[k]]
    if (len(base), len(target), len(normal)) != (334, 334, 328):
        raise ValueError("provisional 26.3 RC2 English source counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (334, 0, 0, 0):
        raise ValueError("provisional 26.3 RC2 semantic delta changed")
    return base, target


def reconstruct_full(base: dict[str, str], target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(expected) != 63 or len(fallback) != 30 or not fallback <= expected:
        raise ValueError("provisional 26.3 RC2 full/fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        previous = g51_combined_locale(locale)
        values: dict[str, str] = {}
        reused = 0
        english = 0
        for key, target_english in target.items():
            candidate = previous.get(key, target_english)
            if preserves_runtime_literals(target_english, candidate):
                values[key] = candidate
                reused += 1
            else:
                values[key] = target_english
                english += 1
        if set(values) != set(target):
            raise ValueError(f"{locale}: invalid provisional full key set")
        if locale in fallback and values != target:
            raise ValueError(f"{locale}: documented fallback is not exact target English")
        result[locale] = values
        stats[locale] = {
            "g51-exact-semantic": reused,
            "target-English": english,
            "documented-fallback": len(target) if locale in fallback else 0,
        }
    return result, stats


def reconstruct_supplements(base: dict[str, str], target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 26:
        raise ValueError("provisional supplement ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_target_upstream(locale)
        missing = normal - set(upstream)
        override_keys = set(scope.get("upstream_literal_safety_overrides", {}).get(locale, []))
        for key in override_keys:
            if key not in normal or key not in upstream or preserves_runtime_literals(target[key], upstream[key]):
                raise ValueError(f"{locale}: invalid/unneeded provisional safety override {key}")
        needed = missing | override_keys
        previous = g51_combined_locale(locale)
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
            raise ValueError(f"{locale}: invalid provisional supplement ownership")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: provisional supplement contains debug-only key")
        result[locale] = values
        stats[locale] = {
            "g51-exact-semantic": reused,
            "target-English": english,
            "upstream-owned": len(normal & set(upstream)),
            "upstream-safety-overrides": len(override_keys),
        }
    return result, stats


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int, dict]:
    base, target = verify_semantics()
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if scope.get("not_a_completed_generation") is not True or scope.get("publishable_candidate") is not False:
        raise ValueError("provisional release gate was removed")
    if policy.get("packaging_registration_allowed") is not False or policy.get("runtime_promotion_allowed") is not False:
        raise ValueError("provisional policy unexpectedly permits packaging/promotion")
    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (334, 0, 0, 0):
        raise ValueError("provisional frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_only_exact_same_key_same_english") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("provisional reuse policy changed")

    full, full_stats = reconstruct_full(base, target, scope)
    supplements, supplement_stats = reconstruct_supplements(base, target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supplements), len(complete)) != (63, 26, 1) or complete != {"en_us"}:
        raise ValueError("provisional ownership total changed")

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
        "generation": "pre-g52-mc26.3-rc2",
        "status": "provisional-only",
        "upstream_commit": PRE_G52_COMMIT,
        "cross_key_reuse_allowed": False,
        "packaging_registration_allowed": False,
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "g51-exact-semantic": sum(x["g51-exact-semantic"] for x in full_stats.values()) + sum(x["g51-exact-semantic"] for x in supplement_stats.values()),
            "target-English": sum(x["target-English"] for x in full_stats.values()) + sum(x["target-English"] for x in supplement_stats.values()),
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
    print("PASS: provisional Minecraft 26.3 RC2 deterministic reconstruction")
    print(f"Full addon locales: {full}")
    print(f"Upstream supplement locales: {supplements}")
    print(f"Keys per complete addon locale: {keys}")
    print(f"Exact G51 semantic reuses: {provenance['totals']['g51-exact-semantic']}")
    print(f"Exact target-English values emitted: {provenance['totals']['target-English']}")
    print("All 334 target English semantics are identical to G51")
    print("Cross-key reuse: forbidden")
    print("Packaging registration: forbidden while target remains provisional")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.10 / JEI 26.2.0 language resources deterministically."""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21_9 as g45

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.9" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.10" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.10-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.9-to-1.21.10.json"
POLICY_PATH = ROOT / "translations" / "g46-mc1.21.10" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.10"
DEBUG_PREFIX = "description.jei."
G46_COMMIT = "621ddf003a8eceffcba0fd808a955e280f87a4c0"
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
ADDED_G46_KEYS = {
    "jei.config.client.tooltips.enableRecipesGuiIngredientsSummary",
    "jei.config.client.tooltips.enableRecipesGuiIngredientsSummary.description",
    "jei.tooltip.recipe.tooltips.craft.ingredients",
}

parse_json = g45.parse_json
write_json = g45.write_json
semantic_sets = g45.semantic_sets
preserves_runtime_literals = g45.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_locale(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G46-reconstruct"})
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


def fetch_g46_upstream(locale: str) -> dict[str, str]:
    values = fetch_locale(G46_COMMIT, locale)
    if not values:
        raise ValueError(f"{locale}: missing or invalid pinned G46 upstream locale")
    return values


@lru_cache(maxsize=1)
def g45_scope() -> dict:
    return json.loads(g45.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g45_full() -> dict[str, dict[str, str]]:
    values, _ = g45.reconstruct_full(parse_json(g45.TARGET_SOURCE), g45_scope())
    return values


@lru_cache(maxsize=1)
def g45_supplements() -> dict[str, dict[str, str]]:
    values, _ = g45.reconstruct_supplements(parse_json(g45.TARGET_SOURCE), g45_scope())
    return values


@lru_cache(maxsize=None)
def g45_combined_locale(locale: str) -> dict[str, str]:
    scope = g45_scope()
    if locale in g45_full():
        return dict(g45_full()[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g45.fetch_g45_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        combined = dict(g45.fetch_g45_upstream(locale))
        combined.update(g45_supplements()[locale])
        return combined
    raise KeyError(f"{locale}: not selected in G45")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (305, 3, 0, 0):
        raise ValueError("G46 frozen semantic partition changed")
    if added != ADDED_G46_KEYS:
        raise ValueError("G46 added-key set changed")
    return unchanged, added, removed, changed


@lru_cache(maxsize=1)
def donor_english() -> dict[str, str]:
    return fetch_locale(DONOR_COMMIT, "en_us")


def resolve_unchanged(locale: str, key: str, english: str) -> tuple[str, str]:
    previous = g45_combined_locale(locale)
    if key not in previous:
        raise ValueError(f"{locale}: unchanged G46 key absent from G45 complete view: {key}")
    value = previous[key]
    return (value, "g45") if preserves_runtime_literals(english, value) else (english, "english")


def resolve_added(locale: str, key: str, english: str) -> tuple[str, str]:
    if donor_english().get(key) == english:
        donor = fetch_locale(DONOR_COMMIT, locale)
        value = donor.get(key)
        if value is not None and preserves_runtime_literals(english, value):
            return value, "future-donor"
    return english, "english"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if changed or removed or added != ADDED_G46_KEYS:
        raise ValueError("G46 full semantic contract changed")
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    if len(expected) != 64 or scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G46 full ownership changed")
    if len(fallback) != 30 or not fallback <= expected or "uk_ua" in expected:
        raise ValueError("G46 fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        if locale in fallback:
            result[locale] = dict(target)
            stats[locale] = {"g45": 0, "future-donor": 0, "english": len(target), "documented-fallback": len(target)}
            continue
        values: dict[str, str] = {}
        count = {"g45": 0, "future-donor": 0, "english": 0, "documented-fallback": 0}
        for key, english in target.items():
            if key.startswith(DEBUG_PREFIX):
                value, source = english, "english"
            elif key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved G46 key {key}")
            values[key] = value
            count[source] += 1
        if set(values) != set(target):
            raise ValueError(f"{locale}: invalid G46 full key set")
        result[locale] = values
        stats[locale] = count
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if changed or removed or added != ADDED_G46_KEYS:
        raise ValueError("G46 supplement semantic contract changed")
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 25 or "uk_ua" not in expected:
        raise ValueError("G46 supplement ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g46_upstream(locale)
        missing = normal - set(upstream)
        override_keys = set(scope.get("upstream_literal_safety_overrides", {}).get(locale, []))
        for key in override_keys:
            if key not in normal or key not in upstream or preserves_runtime_literals(target[key], upstream[key]):
                raise ValueError(f"{locale}: invalid/unneeded G46 safety override {key}")
        needed = missing | override_keys
        values: dict[str, str] = {}
        count = {"g45": 0, "future-donor": 0, "english": 0, "upstream-owned": len(normal & set(upstream)), "upstream-safety-overrides": len(override_keys)}
        for key in sorted(needed):
            english = target[key]
            if key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved G46 supplement key {key}")
            values[key] = value
            count[source] += 1
        if not values or (set(values) & set(upstream)) != override_keys:
            raise ValueError(f"{locale}: invalid G46 supplement ownership")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: debug key in G46 supplement")
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
    if (len(base), len(target), normal_count) != (305, 308, 302):
        raise ValueError("G46 source counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (305, 3, 0, 0):
        raise ValueError("G46 semantic partition changed")
    if (diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"), diff.get("removed_key_count"), diff.get("changed_english_value_count")) != (305, 3, 0, 0):
        raise ValueError("G46 frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g45_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G46 reuse policy changed")
    if reuse.get("future_donor_commit") != DONOR_COMMIT or not reuse.get("future_donor_allowed_only_for_exact_same_key_same_english"):
        raise ValueError("G46 donor policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if (len(full), len(supplements), len(complete)) != (64, 25, 1):
        raise ValueError("G46 ownership total changed")

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
        "generation": "g46-mc1.21.10",
        "cross_key_reuse_allowed": False,
        "future_donor_commit": DONOR_COMMIT,
        "added_g46_keys": sorted(added),
        "uk_ua_is_valid_upstream_supplement": "uk_ua" in supplements,
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "g45": sum(x["g45"] for x in full_stats.values()) + sum(x["g45"] for x in supplement_stats.values()),
            "future-donor": sum(x["future-donor"] for x in full_stats.values()) + sum(x["future-donor"] for x in supplement_stats.values()),
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
    print(f"Output: {args.output}")
    print(f"Full addon locales: {full}")
    print(f"Missing-key/safety-override upstream supplements: {supplements}")
    print(f"Keys per complete locale: {keys}")
    print("G45 -> G46: 305 unchanged + 3 added + 0 removed + 0 changed")
    print("uk_ua is valid upstream in G46 and is supplement-owned, not a full repair override")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    if args.check:
        print("PASS: Minecraft 1.21.10 deterministic reconstruction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

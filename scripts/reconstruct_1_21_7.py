#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.7 / JEI 23.1.0 JSON language resources.

G43 keeps every G42 key+English meaning unchanged and adds two grindstone keys. The
reintroduced grindstone-experience key may reuse the exact same-key/same-English G41 value;
the new grindstone category uses pinned upstream ownership where available and otherwise an
explicit English fallback. Cross-key reuse is never allowed.
"""
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


@lru_cache(max=1)
def _unused_cache_sentinel():
    return None


@lru_cache(maxsize=1)
def reconstruct_g42_full() -> dict[str, dict[str, str]]:
    target = parse_json(g42.TARGET_SOURCE)
    scope = json.loads(g42.SCOPE_PATH.read_text(encoding="utf-8"))
    full, _ = g42.reconstruct_full(target, scope)
    return full


@lru_cache(maxsize=1)
def reconstruct_g42_supplements() -> dict[str, dict[str, str]]:
    target = parse_json(g42.TARGET_SOURCE)
    scope = json.loads(g42.SCOPE_PATH.read_text(encoding="utf-8"))
    supplements, _ = g42.reconstruct_supplements(target, scope)
    return supplements


@lru_cache(maxsize=1)
def g42_scope() -> dict:
    return json.loads(g42.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def g42_combined_locale(locale: str) -> dict[str, str]:
    scope = g42_scope()
    full = reconstruct_g42_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g42.fetch_g42_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = g42.fetch_g42_upstream(locale)
        supplement = reconstruct_g42_supplements()[locale]
        if set(upstream) & set(supplement):
            raise ValueError(f"{locale}: G42 combined view has ownership overlap")
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
        raise ValueError(f"G43 frozen added key set changed: {sorted(added)}")
    return unchanged, added, removed, changed


def resolve_unchanged(previous_value: str, target_english: str) -> tuple[str, str]:
    if preserves_runtime_literals(target_english, previous_value):
        return previous_value, "inherited_g42"
    return target_english, "english_fallback"


def resolve_reintroduced_experience(locale: str, target_english: str) -> tuple[str, str]:
    historical = g42.g41_combined_locale(locale)
    value = historical.get(REINTRODUCED_EXPERIENCE_KEY)
    g41_source = parse_json(g42.g41.TARGET_SOURCE)
    if g41_source.get(REINTRODUCED_EXPERIENCE_KEY) != target_english:
        raise ValueError("G43 grindstone-experience English no longer matches G41 exactly")
    if value is not None and preserves_runtime_literals(target_english, value):
        return value, "historical_same_key_g41"
    return target_english, "english_fallback"


def resolve_added(locale: str, key: str, target_english: str) -> tuple[str, str]:
    if key == REINTRODUCED_EXPERIENCE_KEY:
        return resolve_reintroduced_experience(locale, target_english)
    if key == NEW_GRINDSTONE_KEY:
        return target_english, "english_fallback"
    raise ValueError(f"{locale}: unknown G43 added key {key}")


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if removed or changed or added != ADDED_G43_KEYS:
        raise ValueError("G43 is frozen as 289 unchanged meanings plus two added grindstone meanings")

    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if set(scope.get("malformed_upstream_full_override_locales", [])) != MALFORMED_FULL_OVERRIDES:
        raise ValueError("G43 malformed-upstream full override ownership changed")
    if "uk_ua" not in expected or "uk_ua" in fallback_locales:
        raise ValueError("G43 uk_ua full-repair ownership changed")
    if len(fallback_locales) != 30 or not fallback_locales <= expected:
        raise ValueError("G43 documented full-English fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        if locale in fallback_locales:
            result[locale] = dict(target)
            stats[locale] = {
                "inherited_g42": 0,
                "historical_same_key_g41": 0,
                "repaired_upstream": 0,
                "english_fallback": len(target),
                "documented_full_english_fallback": len(target),
            }
            continue

        previous = g42_combined_locale(locale)
        if locale == "uk_ua":
            repaired_upstream = fetch_g43_upstream(locale)
            values: dict[str, str] = {}
            counts = {"inherited_g42":0,"historical_same_key_g41":0,"repaired_upstream":0,"english_fallback":0,"documented_full_english_fallback":0}
            for key, english in target.items():
                if key.startswith(DEBUG_PREFIX):
                    values[key] = english
                    counts["english_fallback"] += 1
                elif key in repaired_upstream and preserves_runtime_literals(english, repaired_upstream[key]):
                    values[key] = repaired_upstream[key]
                    counts["repaired_upstream"] += 1
                elif key in unchanged:
                    if key not in previous:
                        raise ValueError(f"uk_ua: unchanged G43 key absent from G42 combined view: {key}")
                    value, source = resolve_unchanged(previous[key], english)
                    values[key] = value
                    counts[source] += 1
                elif key in added:
                    value, source = resolve_added(locale, key, english)
                    values[key] = value
                    counts[source] += 1
                else:
                    raise ValueError(f"uk_ua: unresolved G43 semantic key: {key}")
            result[locale] = values
            stats[locale] = counts
            continue

        values: dict[str, str] = {}
        counts = {"inherited_g42":0,"historical_same_key_g41":0,"repaired_upstream":0,"english_fallback":0,"documented_full_english_fallback":0}
        for key, english in target.items():
            if key in unchanged:
                if key not in previous:
                    raise ValueError(f"{locale}: unchanged G43 key absent from G42 complete view: {key}")
                value, source = resolve_unchanged(previous[key], english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved G43 semantic key: {key}")
            values[key] = value
            counts[source] += 1
        result[locale] = values
        stats[locale] = counts
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if removed or changed or added != ADDED_G43_KEYS:
        raise ValueError("G43 supplement reconstruction expects two added grindstone meanings")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if "uk_ua" in expected:
        raise ValueError("uk_ua must not be a G43 supplement")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g43_upstream(locale)
        missing = normal_keys - set(upstream)
        previous_complete = g42_combined_locale(locale)
        values: dict[str, str] = {}
        counts = {"inherited_g42":0,"historical_same_key_g41":0,"english_fallback":0,"upstream_owned":len(normal_keys & set(upstream))}
        for key in sorted(missing):
            english = target[key]
            if key in unchanged:
                if key not in previous_complete:
                    raise ValueError(f"{locale}: unchanged G43 missing key absent from G42 complete view: {key}")
                value, source = resolve_unchanged(previous_complete[key], english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: G43 supplement contains unresolved semantic key {key}")
            values[key] = value
            counts[source] += 1
        if not values:
            raise ValueError(f"{locale}: marked incomplete upstream but needs no G43 supplement")
        if set(values) & set(upstream):
            raise ValueError(f"{locale}: G43 supplement would override upstream-owned keys")
        result[locale] = values
        stats[locale] = counts
    return result, stats


def provenance_summary(full_stats: dict[str, dict[str, int]], supplement_stats: dict[str, dict[str, int]]) -> dict:
    fallback_full = {k:v for k,v in full_stats.items() if v["documented_full_english_fallback"] > 0}
    translated_or_repaired_full = {k:v for k,v in full_stats.items() if v["documented_full_english_fallback"] == 0}
    return {
        "schema_version": 1,
        "generation": "g43-mc1.21.7",
        "resolution_order": [
            "pinned-upstream-ownership",
            "frozen-minimal-uk_ua-syntax-repair-full-override",
            "exact-safe-g42-inheritance-for-unchanged-same-key-meanings",
            "exact-safe-g41-same-key-reuse-for-reintroduced-grindstone-experience",
            "exact-g43-english-fallback-for-new-or-unsafe-values",
        ],
        "cross_key_reuse_allowed": False,
        "malformed_upstream_full_overrides": ["uk_ua"],
        "added_g43_keys": sorted(ADDED_G43_KEYS),
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "translated_or_repaired_full_inherited_g42": sum(v["inherited_g42"] for v in translated_or_repaired_full.values()),
            "translated_or_repaired_full_historical_same_key_g41": sum(v["historical_same_key_g41"] for v in translated_or_repaired_full.values()),
            "translated_or_repaired_full_repaired_upstream": sum(v["repaired_upstream"] for v in translated_or_repaired_full.values()),
            "translated_or_repaired_full_english_fallback": sum(v["english_fallback"] for v in translated_or_repaired_full.values()),
            "documented_full_fallback_values": sum(v["documented_full_english_fallback"] for v in fallback_full.values()),
            "supplement_inherited_g42": sum(v["inherited_g42"] for v in supplement_stats.values()),
            "supplement_historical_same_key_g41": sum(v["historical_same_key_g41"] for v in supplement_stats.values()),
            "supplement_english_fallback": sum(v["english_fallback"] for v in supplement_stats.values()),
            "supplement_upstream_owned_normal_values": sum(v["upstream_owned"] for v in supplement_stats.values()),
        },
    }


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int, dict]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    unchanged, added, removed, changed = semantic_partition()

    if (len(base), len(target), normal_count) != (289, 291, 285):
        raise ValueError(f"G43 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"), diff.get("removed_key_count"), diff.get("changed_english_value_count")) != (289, 2, 0, 0):
        raise ValueError("G43 frozen English diff counts changed")
    if added != ADDED_G43_KEYS or removed or changed:
        raise ValueError("G43 frozen semantic partition changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g42_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G43 policy must require exact G42 reuse and forbid cross-key reuse")
    if not reuse.get("historical_same_key_same_english_reuse_allowed"):
        raise ValueError("G43 policy must explicitly allow exact historical same-key reuse")
    override = policy.get("malformed_upstream_override", {})
    if set(override.get("locales", [])) != MALFORMED_FULL_OVERRIDES or not override.get("full_override_required"):
        raise ValueError("G43 malformed-upstream override policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if len(full) + len(supplements) + len(complete) != 90:
        raise ValueError(f"G43 ownership total changed: full={len(full)} supplements={len(supplements)} complete={len(complete)}")

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

    provenance = provenance_summary(full_stats, supplement_stats)
    write_json(output / "provenance.json", provenance)
    return len(full), len(supplements), len(target), provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()
    full, supplements, keys, provenance = reconstruct_all(args.output, clean=not args.no_clean)
    print(f"Output: {args.output}")
    print(f"Full addon/override locales: {full}")
    print(f"Missing-key-only upstream supplements: {supplements}")
    print(f"Keys per complete locale: {keys}")
    print("G42 -> G43: 289 unchanged meanings + 2 added grindstone meanings")
    print("uk_ua remains a valid full repair override because the pinned upstream JSON is malformed")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

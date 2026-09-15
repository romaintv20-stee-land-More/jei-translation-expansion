#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.6 / JEI 22.0.0 JSON language resources.

G42 removes one G41 semantic key and changes no surviving English values. Exact same-key
G41 values may therefore be reused for every surviving meaning when runtime literals remain
safe. The pinned upstream uk_ua.json is still malformed, so Ukrainian remains an explicit
valid full repair override rather than a supplement against broken JSON.
"""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21_5 as g41

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.5" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.6" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.6-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.5-to-1.21.6.json"
POLICY_PATH = ROOT / "translations" / "g42-mc1.21.6" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.6"
DEBUG_PREFIX = "description.jei."
G42_COMMIT = "2a57409c2af0ce9716749a0329166a41cbcf453f"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
REMOVED_G42_KEYS = {"gui.jei.category.grindstone.experience"}
MALFORMED_FULL_OVERRIDES = {"uk_ua"}

parse_json_text = g41.parse_json_text
parse_json = g41.parse_json
write_json = g41.write_json
semantic_sets = g41.semantic_sets
preserves_runtime_literals = g41.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


@lru_cache(maxsize=None)
def fetch_g42_upstream(locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=G42_COMMIT, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G42-reconstruct"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError(f"{locale}: missing pinned G42 upstream locale") from exc
        raise
    try:
        return clean_mapping(json.loads(text))
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        return clean_mapping(json.loads(g41.repair_uk_ua_text(text)))


@lru_cache(maxsize=1)
def reconstruct_g41_full() -> dict[str, dict[str, str]]:
    target = g41.parse_json(g41.TARGET_SOURCE)
    scope = json.loads(g41.SCOPE_PATH.read_text(encoding="utf-8"))
    full, _ = g41.reconstruct_full(target, scope)
    return full


@lru_cache(maxsize=1)
def reconstruct_g41_supplements() -> dict[str, dict[str, str]]:
    target = g41.parse_json(g41.TARGET_SOURCE)
    scope = json.loads(g41.SCOPE_PATH.read_text(encoding="utf-8"))
    supplements, _ = g41.reconstruct_supplements(target, scope)
    return supplements


@lru_cache(maxsize=1)
def g41_scope() -> dict:
    return json.loads(g41.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def g41_combined_locale(locale: str) -> dict[str, str]:
    scope = g41_scope()
    full = reconstruct_g41_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g41.fetch_g41_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = g41.fetch_g41_upstream(locale)
        supplement = reconstruct_g41_supplements()[locale]
        if set(upstream) & set(supplement):
            raise ValueError(f"{locale}: G41 combined view has ownership overlap")
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G41")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (289, 0, 1, 0):
        raise ValueError("G42 frozen semantic partition changed")
    if removed != REMOVED_G42_KEYS:
        raise ValueError(f"G42 frozen removed key set changed: {sorted(removed)}")
    return unchanged, added, removed, changed


def resolve_unchanged(previous_value: str, target_english: str) -> tuple[str, str]:
    if preserves_runtime_literals(target_english, previous_value):
        return previous_value, "inherited"
    return target_english, "english-fallback"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if added or changed or removed != REMOVED_G42_KEYS:
        raise ValueError("G42 is frozen as 289 unchanged meanings plus one removed meaning")

    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if set(scope.get("malformed_upstream_full_override_locales", [])) != MALFORMED_FULL_OVERRIDES:
        raise ValueError("G42 malformed-upstream full override ownership changed")
    if "uk_ua" not in expected or "uk_ua" in fallback_locales:
        raise ValueError("G42 uk_ua full-repair ownership changed")
    if len(fallback_locales) != 30 or not fallback_locales <= expected:
        raise ValueError("G42 documented full-English fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        if locale in fallback_locales:
            result[locale] = dict(target)
            stats[locale] = {
                "inherited": 0,
                "repaired_upstream": 0,
                "english_fallback": len(target),
                "documented_full_english_fallback": len(target),
            }
            continue

        previous = g41_combined_locale(locale)
        if locale == "uk_ua":
            repaired_upstream = fetch_g42_upstream(locale)
            values: dict[str, str] = {}
            inherited_count = repaired_count = fallback_count = 0
            for key, english in target.items():
                if key.startswith(DEBUG_PREFIX):
                    values[key] = english
                    fallback_count += 1
                elif key in repaired_upstream and preserves_runtime_literals(english, repaired_upstream[key]):
                    values[key] = repaired_upstream[key]
                    repaired_count += 1
                elif key in unchanged:
                    if key not in previous:
                        raise ValueError(f"uk_ua: unchanged G42 key absent from G41 combined view: {key}")
                    value, source = resolve_unchanged(previous[key], english)
                    values[key] = value
                    if source == "inherited":
                        inherited_count += 1
                    else:
                        fallback_count += 1
                else:
                    raise ValueError(f"uk_ua: unresolved G42 semantic key: {key}")
            result[locale] = values
            stats[locale] = {
                "inherited": inherited_count,
                "repaired_upstream": repaired_count,
                "english_fallback": fallback_count,
                "documented_full_english_fallback": 0,
            }
            continue

        values: dict[str, str] = {}
        inherited_count = fallback_count = 0
        for key, english in target.items():
            if key not in unchanged:
                raise ValueError(f"{locale}: non-unchanged target key unexpectedly survived into G42: {key}")
            if key not in previous:
                raise ValueError(f"{locale}: unchanged G42 key absent from G41 complete view: {key}")
            value, source = resolve_unchanged(previous[key], english)
            values[key] = value
            if source == "inherited":
                inherited_count += 1
            else:
                fallback_count += 1
        result[locale] = values
        stats[locale] = {
            "inherited": inherited_count,
            "repaired_upstream": 0,
            "english_fallback": fallback_count,
            "documented_full_english_fallback": 0,
        }
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if added or changed or removed != REMOVED_G42_KEYS:
        raise ValueError("G42 supplement reconstruction expects removal-only semantic delta")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if "uk_ua" in expected:
        raise ValueError("uk_ua must not be a G42 supplement")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g42_upstream(locale)
        missing = normal_keys - set(upstream)
        previous_complete = g41_combined_locale(locale)
        values: dict[str, str] = {}
        inherited_count = fallback_count = 0
        for key in sorted(missing):
            if key not in unchanged:
                raise ValueError(f"{locale}: G42 supplement contains unresolved semantic key {key}")
            if key not in previous_complete:
                raise ValueError(f"{locale}: unchanged G42 missing key absent from G41 complete view: {key}")
            value, source = resolve_unchanged(previous_complete[key], target[key])
            values[key] = value
            if source == "inherited":
                inherited_count += 1
            else:
                fallback_count += 1
        if not values:
            raise ValueError(f"{locale}: marked incomplete upstream but needs no G42 supplement")
        if set(values) & set(upstream):
            raise ValueError(f"{locale}: G42 supplement would override upstream-owned keys")
        result[locale] = values
        stats[locale] = {
            "inherited": inherited_count,
            "english_fallback": fallback_count,
            "upstream_owned": len(normal_keys & set(upstream)),
        }
    return result, stats


def provenance_summary(full_stats: dict[str, dict[str, int]], supplement_stats: dict[str, dict[str, int]]) -> dict:
    fallback_full = {k: v for k, v in full_stats.items() if v["documented_full_english_fallback"] > 0}
    translated_or_repaired_full = {k: v for k, v in full_stats.items() if v["documented_full_english_fallback"] == 0}
    return {
        "schema_version": 1,
        "generation": "g42-mc1.21.6",
        "resolution_order": [
            "pinned-upstream-ownership",
            "frozen-minimal-uk_ua-syntax-repair-full-override",
            "exact-safe-g41-inheritance-for-unchanged-same-key-meanings",
            "exact-g42-english-fallback-for-unsafe-values",
        ],
        "cross_key_reuse_allowed": False,
        "malformed_upstream_full_overrides": ["uk_ua"],
        "removed_g42_keys": sorted(REMOVED_G42_KEYS),
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "translated_or_repaired_full_inherited": sum(v["inherited"] for v in translated_or_repaired_full.values()),
            "translated_or_repaired_full_repaired_upstream": sum(v["repaired_upstream"] for v in translated_or_repaired_full.values()),
            "translated_or_repaired_full_english_fallback": sum(v["english_fallback"] for v in translated_or_repaired_full.values()),
            "documented_full_fallback_values": sum(v["documented_full_english_fallback"] for v in fallback_full.values()),
            "supplement_inherited": sum(v["inherited"] for v in supplement_stats.values()),
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

    if (len(base), len(target), normal_count) != (290, 289, 283):
        raise ValueError(f"G42 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (
        diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"),
        diff.get("removed_key_count"), diff.get("changed_english_value_count")
    ) != (289, 0, 1, 0):
        raise ValueError("G42 frozen English diff counts changed")
    if added or changed or removed != REMOVED_G42_KEYS:
        raise ValueError("G42 frozen semantic partition changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g41_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G42 policy must require exact G41 reuse and forbid cross-key reuse")
    override = policy.get("malformed_upstream_override", {})
    if set(override.get("locales", [])) != MALFORMED_FULL_OVERRIDES or not override.get("full_override_required"):
        raise ValueError("G42 malformed-upstream override policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if len(full) + len(supplements) + len(complete) != 90:
        raise ValueError(
            f"G42 ownership total changed: full={len(full)} supplements={len(supplements)} complete={len(complete)}"
        )

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
    print("G41 -> G42: 289 unchanged meanings + 1 removed meaning")
    print("uk_ua remains a valid full repair override because the pinned upstream JSON is malformed")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

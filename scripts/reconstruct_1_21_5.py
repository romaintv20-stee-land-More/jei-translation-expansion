#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.5 / JEI 21.4.0 JSON language resources.

G41 keeps all 288 G40 key+English meanings unchanged and adds two new meanings.
The pinned upstream uk_ua.json is malformed, so G41 emits a valid full repair override
for Ukrainian instead of attempting a runtime supplement against broken JSON.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21_4 as g40

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.4" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.5" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.5-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.4-to-1.21.5.json"
POLICY_PATH = ROOT / "translations" / "g41-mc1.21.5" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.5"
DEBUG_PREFIX = "description.jei."
G41_COMMIT = "0772287a157beb93f438ee10f88afe402e262856"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
NEW_G41_KEYS = {
    "gui.jei.category.grindstone.experience",
    "jei.message.missing.recipes.from.server",
}
MALFORMED_FULL_OVERRIDES = {"uk_ua"}

parse_json_text = g40.parse_json_text
parse_json = g40.parse_json
write_json = g40.write_json
semantic_sets = g40.semantic_sets
preserves_runtime_literals = g40.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def repair_uk_ua_text(text: str) -> str:
    repaired, count = re.subn(
        r'("jei\.alias\.villager\.spawn\.egg"\s*:\s*"HMMM")\s*(\n\s*"modmenu\.descriptionTranslation\.jei")',
        r"\1,\2",
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("uk_ua: expected missing-comma repair point not found")
    repaired, count = re.subn(r",\s*}\s*$", "\n}\n", repaired, count=1)
    if count != 1:
        raise ValueError("uk_ua: expected trailing-comma repair point not found")
    return repaired


@lru_cache(maxsize=None)
def fetch_g41_upstream(locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=G41_COMMIT, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G41-reconstruct"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError(f"{locale}: missing pinned G41 upstream locale") from exc
        raise
    try:
        return clean_mapping(json.loads(text))
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        return clean_mapping(json.loads(repair_uk_ua_text(text)))


@lru_cache(maxsize=1)
def reconstruct_g40_full() -> dict[str, dict[str, str]]:
    target = g40.parse_json(g40.TARGET_SOURCE)
    scope = json.loads(g40.SCOPE_PATH.read_text(encoding="utf-8"))
    full, _ = g40.reconstruct_full(target, scope)
    return full


@lru_cache(maxsize=1)
def reconstruct_g40_supplements() -> dict[str, dict[str, str]]:
    target = g40.parse_json(g40.TARGET_SOURCE)
    scope = json.loads(g40.SCOPE_PATH.read_text(encoding="utf-8"))
    supplements, _ = g40.reconstruct_supplements(target, scope)
    return supplements


@lru_cache(maxsize=1)
def g40_scope() -> dict:
    return json.loads(g40.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def g40_combined_locale(locale: str) -> dict[str, str]:
    scope = g40_scope()
    full = reconstruct_g40_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g40.fetch_upstream_json(g40.G40_COMMIT, locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = g40.fetch_upstream_json(g40.G40_COMMIT, locale)
        supplement = reconstruct_g40_supplements()[locale]
        if set(upstream) & set(supplement):
            raise ValueError(f"{locale}: G40 combined view has ownership overlap")
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G40")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (288, 2, 0, 0):
        raise ValueError("G41 frozen semantic partition changed")
    if added != NEW_G41_KEYS:
        raise ValueError("G41 frozen added key set changed")
    return unchanged, added, removed, changed


def resolve_unchanged(previous_value: str, target_english: str) -> tuple[str, str]:
    if preserves_runtime_literals(target_english, previous_value):
        return previous_value, "inherited"
    return target_english, "english-fallback"


def resolve_added(target_english: str) -> tuple[str, str]:
    return target_english, "english-fallback"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_partition()
    if removed or changed:
        raise ValueError("G41 is frozen with no removed or changed-English keys")

    previous_full = reconstruct_g40_full()
    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(expected) != 65 or MALFORMED_FULL_OVERRIDES != {"uk_ua"} or "uk_ua" not in expected:
        raise ValueError("G41 frozen full-locale ownership changed")
    if set(previous_full) != expected - MALFORMED_FULL_OVERRIDES:
        raise ValueError("G41 non-Ukrainian full ownership must exactly inherit the 64 G40 full locales")
    if len(fallback_locales) != 30 or not fallback_locales <= expected or "uk_ua" in fallback_locales:
        raise ValueError("G41 frozen documented fallback ownership changed")

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

        if locale == "uk_ua":
            repaired_upstream = fetch_g41_upstream(locale)
            previous = g40_combined_locale(locale)
            values: dict[str, str] = {}
            inherited_count = repaired_count = fallback_count = 0
            for key, english in target.items():
                if key.startswith(DEBUG_PREFIX):
                    values[key] = english
                    fallback_count += 1
                    continue
                if key in repaired_upstream and preserves_runtime_literals(english, repaired_upstream[key]):
                    values[key] = repaired_upstream[key]
                    repaired_count += 1
                elif key in unchanged:
                    if key not in previous:
                        raise ValueError(f"uk_ua: unchanged G41 key absent from G40 combined view: {key}")
                    value, source = resolve_unchanged(previous[key], english)
                    values[key] = value
                    if source == "inherited":
                        inherited_count += 1
                    else:
                        fallback_count += 1
                elif key in added:
                    values[key], _ = resolve_added(english)
                    fallback_count += 1
                else:
                    raise ValueError(f"uk_ua: unresolved G41 semantic key: {key}")
            result[locale] = values
            stats[locale] = {
                "inherited": inherited_count,
                "repaired_upstream": repaired_count,
                "english_fallback": fallback_count,
                "documented_full_english_fallback": 0,
            }
            continue

        old = previous_full[locale]
        if set(old) != set(base):
            raise ValueError(f"{locale}: G40 complete key set differs from G41 base source")
        values: dict[str, str] = {}
        inherited_count = fallback_count = 0
        for key, english in target.items():
            if key in unchanged:
                value, source = resolve_unchanged(old[key], english)
            elif key in added:
                value, source = resolve_added(english)
            else:
                raise ValueError(f"{locale}: unresolved G41 semantic key: {key}")
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
    if removed or changed:
        raise ValueError("G41 is frozen with no removed or changed-English keys")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 24 or "uk_ua" in expected or "ja_jp" not in expected:
        raise ValueError("G41 supplement ownership must contain 24 locales, include ja_jp, and exclude uk_ua")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g41_upstream(locale)
        missing = normal_keys - set(upstream)
        previous_complete = g40_combined_locale(locale)
        values: dict[str, str] = {}
        inherited_count = fallback_count = 0
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_complete:
                    raise ValueError(f"{locale}: unchanged G41 missing key absent from G40 complete view: {key}")
                value, source = resolve_unchanged(previous_complete[key], target[key])
            elif key in added:
                value, source = resolve_added(target[key])
            else:
                raise ValueError(f"{locale}: unresolved G41 supplement semantic key: {key}")
            values[key] = value
            if source == "inherited":
                inherited_count += 1
            else:
                fallback_count += 1
        if set(values) & set(upstream):
            raise ValueError(f"{locale}: G41 supplement would override upstream-owned keys")
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
        "generation": "g41-mc1.21.5",
        "resolution_order": [
            "pinned-upstream-ownership",
            "frozen-minimal-uk_ua-syntax-repair-full-override",
            "exact-safe-g40-inheritance-for-unchanged-same-key-meanings",
            "exact-g41-english-fallback-for-new-or-unsafe-values",
        ],
        "cross_key_reuse_allowed": False,
        "malformed_upstream_full_overrides": ["uk_ua"],
        "new_g41_keys": sorted(NEW_G41_KEYS),
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

    if (len(base), len(target), normal_count) != (288, 290, 284):
        raise ValueError(f"G41 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (288, 2, 0, 0):
        raise ValueError("G41 frozen English diff counts changed")
    reuse = policy["translation_reuse"]
    if not reuse["reuse_exact_unchanged_g40_semantics"] or reuse["cross_key_reuse_allowed"]:
        raise ValueError("G41 policy must require exact G40 reuse and forbid cross-key reuse")
    if set(policy["malformed_upstream_override"]["locales"]) != MALFORMED_FULL_OVERRIDES:
        raise ValueError("G41 malformed-upstream override policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    if len(full) != 65 or len(supplements) != 24:
        raise ValueError(f"G41 ownership counts changed: full={len(full)} supplements={len(supplements)}")

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
    print("G40 -> G41: 288 unchanged meanings + 2 added meanings")
    print("uk_ua is emitted as a valid full repair override because the pinned upstream JSON is malformed")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

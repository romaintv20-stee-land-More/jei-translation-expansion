#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.4 / JEI 20.0.0 JSON language resources.

G40 is a deliberately small semantic delta from G39:
- 285 keys keep the exact same key and English meaning and may inherit G39 values;
- the old generic Fuel category key is removed;
- three new fuel-category keys require same-key reviewed treatment;
- cross-key reuse from the removed generic Fuel key is forbidden.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import urllib.error
import urllib.request
from collections import Counter
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21_1 as g39

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.4" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.4-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.1-to-1.21.4.json"
POLICY_PATH = ROOT / "translations" / "g40-mc1.21.4" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.4"
DEBUG_PREFIX = "description.jei."
G40_COMMIT = "26845e0d2a248b0084481b4a433ef7b32152d4c6"
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|CTRL|,d|\d+\$[sdif]|[sdif]|%)")
TECHNICAL_TOKENS = ("JEI", "Minecraft", "/give", "modId[:name[:meta]]", "mB")
NEW_G40_KEYS = {
    "gui.jei.category.blasting_fuel",
    "gui.jei.category.smelting_fuel",
    "gui.jei.category.smoking_fuel",
}
REMOVED_G40_KEYS = {"gui.jei.category.fuel"}

parse_json_text = g39.parse_json_text
parse_json = g39.parse_json
write_json = g39.write_json
semantic_sets = g39.semantic_sets


def placeholders(value: str) -> Counter[str]:
    return Counter(PLACEHOLDER_RE.findall(value))


def contains_technical_token(value: str, token: str) -> bool:
    if token.isalnum():
        return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", value) is not None
    return token in value


def preserves_runtime_literals(english: str, translated: str) -> bool:
    if placeholders(translated) != placeholders(english):
        return False
    return all(
        not contains_technical_token(english, token) or contains_technical_token(translated, token)
        for token in TECHNICAL_TOKENS
    )


@lru_cache(maxsize=None)
def fetch_json_optional(commit: str, locale: str) -> dict[str, str] | None:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G40-reconstruct"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    try:
        return parse_json_text(text)
    except json.JSONDecodeError:
        return None


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    result = fetch_json_optional(commit, locale)
    if result is None:
        raise ValueError(f"{locale}: expected valid upstream JSON at {commit}")
    return result


@lru_cache(maxsize=1)
def donor_english() -> dict[str, str]:
    result = fetch_json_optional(DONOR_COMMIT, "en_us")
    if result is None:
        raise ValueError("G40 donor English source is unavailable or invalid")
    return result


@lru_cache(maxsize=None)
def donor_locale(locale: str) -> dict[str, str] | None:
    return fetch_json_optional(DONOR_COMMIT, locale)


@lru_cache(maxsize=1)
def reconstruct_g39_full() -> dict[str, dict[str, str]]:
    target = g39.parse_json(g39.TARGET_SOURCE)
    scope = json.loads(g39.SCOPE_PATH.read_text(encoding="utf-8"))
    full, _ = g39.reconstruct_full(target, scope)
    return full


@lru_cache(maxsize=1)
def reconstruct_g39_supplements() -> dict[str, dict[str, str]]:
    target = g39.parse_json(g39.TARGET_SOURCE)
    scope = json.loads(g39.SCOPE_PATH.read_text(encoding="utf-8"))
    supplements, _ = g39.reconstruct_supplements(target, scope)
    return supplements


@lru_cache(maxsize=1)
def g39_scope() -> dict:
    return json.loads(g39.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def g39_combined_locale(locale: str) -> dict[str, str]:
    scope = g39_scope()
    full = reconstruct_g39_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return fetch_upstream_json(g39.G39_COMMIT, locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = fetch_upstream_json(g39.G39_COMMIT, locale)
        supplement = reconstruct_g39_supplements()[locale]
        if set(upstream) & set(supplement):
            raise ValueError(f"{locale}: G39 combined view has ownership overlap")
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G39")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (285, 3, 1, 0):
        raise ValueError("G40 frozen semantic partition changed")
    if added != NEW_G40_KEYS or removed != REMOVED_G40_KEYS:
        raise ValueError("G40 frozen added/removed key set changed")
    return unchanged, added, removed, changed


def exact_donor_value(locale: str, key: str, target_english: str) -> str | None:
    if key.startswith(DEBUG_PREFIX):
        return None
    donor_en = donor_english()
    if donor_en.get(key) != target_english:
        return None
    values = donor_locale(locale)
    if values is None:
        return None
    candidate = values.get(key)
    if candidate is None or not preserves_runtime_literals(target_english, candidate):
        return None
    return candidate


def resolve_unchanged(key: str, previous_value: str, target_english: str) -> tuple[str, str]:
    if key.startswith(DEBUG_PREFIX):
        if previous_value == target_english:
            return previous_value, "inherited"
        return target_english, "english-fallback"
    if preserves_runtime_literals(target_english, previous_value):
        return previous_value, "inherited"
    return target_english, "english-fallback"


def resolve_added(locale: str, key: str, target_english: str) -> tuple[str, str]:
    if key not in NEW_G40_KEYS:
        raise ValueError(f"{key}: unexpected G40 added semantic")
    donor = exact_donor_value(locale, key, target_english)
    if donor is not None:
        return donor, "donor"
    return target_english, "english-fallback"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_partition()
    if changed:
        raise ValueError("G40 is frozen with no changed English values")
    previous = reconstruct_g39_full()
    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if expected != set(previous):
        raise ValueError("G40 addon-full ownership must exactly match G39")
    if len(expected) != 64 or len(fallback_locales) != 30 or not fallback_locales <= expected:
        raise ValueError("G40 frozen full-locale ownership counts changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        if set(old) != set(base):
            raise ValueError(f"{locale}: G39 complete key set differs from G40 base source")
        if locale in fallback_locales:
            result[locale] = dict(target)
            stats[locale] = {
                "inherited": 0,
                "donor": 0,
                "english_fallback": len(target),
                "documented_full_english_fallback": len(target),
            }
            continue

        values: dict[str, str] = {}
        inherited_count = donor_count = fallback_count = 0
        for key, english in target.items():
            if key in unchanged:
                value, source = resolve_unchanged(key, old[key], english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved G40 semantic key: {key}")
            values[key] = value
            if source == "inherited":
                inherited_count += 1
            elif source == "donor":
                donor_count += 1
            else:
                fallback_count += 1
        result[locale] = values
        stats[locale] = {
            "inherited": inherited_count,
            "donor": donor_count,
            "english_fallback": fallback_count,
            "documented_full_english_fallback": 0,
        }
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if changed:
        raise ValueError("G40 is frozen with no changed English values")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 25 or "ja_jp" not in expected:
        raise ValueError("G40 supplement ownership must contain 25 locales including ja_jp")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G40_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_complete = g39_combined_locale(locale)
        values: dict[str, str] = {}
        inherited_count = donor_count = fallback_count = 0
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_complete:
                    raise ValueError(f"{locale}: unchanged G40 missing key absent from G39 complete view: {key}")
                value, source = resolve_unchanged(key, previous_complete[key], target[key])
            elif key in added:
                value, source = resolve_added(locale, key, target[key])
            else:
                raise ValueError(f"{locale}: unresolved G40 supplement semantic key: {key}")
            values[key] = value
            if source == "inherited":
                inherited_count += 1
            elif source == "donor":
                donor_count += 1
            else:
                fallback_count += 1
        if set(values) & set(upstream):
            raise ValueError(f"{locale}: G40 supplement would override upstream-owned keys")
        result[locale] = values
        stats[locale] = {
            "inherited": inherited_count,
            "donor": donor_count,
            "english_fallback": fallback_count,
            "upstream_owned": len(normal_keys & set(upstream)),
        }
    if set(result["ja_jp"]) != NEW_G40_KEYS:
        raise ValueError("ja_jp G40 supplement must contain exactly the three new fuel-category keys")
    return result, stats


def provenance_summary(full_stats: dict[str, dict[str, int]], supplement_stats: dict[str, dict[str, int]]) -> dict:
    translated_full = {k: v for k, v in full_stats.items() if v["documented_full_english_fallback"] == 0}
    return {
        "schema_version": 1,
        "generation": "g40-mc1.21.4",
        "donor_commit": DONOR_COMMIT,
        "resolution_order": [
            "pinned-upstream",
            "exact-safe-g39-inheritance",
            "exact-safe-later-jei-donor-for-new-same-key-meaning",
            "exact-g40-english-fallback",
        ],
        "cross_key_reuse_allowed": False,
        "removed_generic_fuel_key_reused_for_new_keys": False,
        "literal_safety": {
            "placeholder_multiset_must_match": True,
            "technical_tokens_must_be_preserved": list(TECHNICAL_TOKENS),
            "unsafe_reuse_falls_back_to_exact_english": True,
        },
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "translated_full_inherited": sum(v["inherited"] for v in translated_full.values()),
            "translated_full_donor": sum(v["donor"] for v in translated_full.values()),
            "translated_full_english_fallback": sum(v["english_fallback"] for v in translated_full.values()),
            "documented_full_fallback_values": sum(v["documented_full_english_fallback"] for v in full_stats.values()),
            "supplement_inherited": sum(v["inherited"] for v in supplement_stats.values()),
            "supplement_donor": sum(v["donor"] for v in supplement_stats.values()),
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

    if (len(base), len(target), normal_count) != (286, 288, 282):
        raise ValueError(f"G40 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (285, 3, 1, 0):
        raise ValueError("G40 frozen English diff counts changed")
    reuse = policy["translation_reuse"]
    if not reuse["reuse_exact_unchanged_g39_semantics"] or reuse["cross_key_reuse_allowed"]:
        raise ValueError("G40 policy must require exact G39 reuse and forbid cross-key reuse")
    if not reuse.get("runtime_literals_must_be_preserved", False):
        raise ValueError("G40 policy must reject inherited values that lose runtime literals")
    donor_policy = policy["later_upstream_backport_policy"]
    if donor_policy["donor_snapshot"] != DONOR_COMMIT:
        raise ValueError("G40 donor snapshot differs from deterministic reconstruction donor")
    if not donor_policy["allowed_only_if_same_key_and_exact_same_english_value"]:
        raise ValueError("G40 donor policy must require exact same-key + same-English semantics")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 25, 288):
        raise ValueError(
            f"G40 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}"
        )
    if set(full) & set(supplements):
        raise ValueError("G40 full/supplement ownership overlaps")

    provenance = provenance_summary(full_stats, supplement_stats)
    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        path = full_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G40 full JSON failed round-trip validation")

    for locale, values in sorted(supplements.items()):
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G40 supplement contains debug-only key")
        path = supplement_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G40 supplement JSON failed round-trip validation")

    write_json(output / "provenance.json", provenance)
    return len(full), len(supplements), len(target), provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.21.4-reconstruct-") as tmp:
            full_count, supplement_count, key_count, provenance = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.21.4 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count, provenance = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("G39 -> G40: 285 unchanged meanings, 3 added fuel-category meanings, 1 removed generic Fuel key")
    print("Cross-key reuse is forbidden; new fuel-category keys use exact same-key donor values or exact G40 English fallback")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.9 / JEI 25.0.1 language resources deterministically."""
from __future__ import annotations

import argparse
import json
import shutil
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21_8 as g44

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.8" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.9" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.9-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.8-to-1.21.9.json"
POLICY_PATH = ROOT / "translations" / "g45-mc1.21.9" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.9"
DEBUG_PREFIX = "description.jei."
G45_COMMIT = "bdfdb4c09026c4fb488805ff729c66ae48ede875"
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"
REMOVED_G45_KEYS = {
    "jei.key.category.overlays",
    "jei.key.category.recipe.gui",
    "jei.key.category.cheat.mode",
    "jei.key.category.hover.config.button",
    "jei.key.category.edit.mode",
    "jei.key.category.mouse.hover",
    "jei.key.category.search",
    "jei.key.category.dev.tools",
}
ADDED_G45_KEYS = {
    "key.category.jei.overlays",
    "key.category.jei.recipe.gui",
    "key.category.jei.cheat.mode",
    "key.category.jei.hover.config.button",
    "key.category.jei.edit.mode",
    "key.category.jei.mouse.hover",
    "key.category.jei.search",
    "key.category.jei.dev.tools",
}
MALFORMED_FULL_OVERRIDES = {"uk_ua"}
UPSTREAM_LITERAL_SAFETY_OVERRIDES = {
    "ar_sa": {"jei.config.client.search.description"},
}

parse_json = g44.parse_json
write_json = g44.write_json
semantic_sets = g44.semantic_sets
preserves_runtime_literals = g44.preserves_runtime_literals


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def repair_uk_ua(text: str) -> str:
    return g44.repair_uk_ua(text)


@lru_cache(maxsize=None)
def fetch_locale(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G45-reconstruct"})
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
        if locale != "uk_ua":
            raise
        return clean_mapping(json.loads(repair_uk_ua(text)))


def fetch_g45_upstream(locale: str) -> dict[str, str]:
    values = fetch_locale(G45_COMMIT, locale)
    if not values:
        raise ValueError(f"{locale}: missing pinned G45 upstream locale")
    return values


@lru_cache(maxsize=1)
def g44_scope() -> dict:
    return json.loads(g44.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def g44_full() -> dict[str, dict[str, str]]:
    target = parse_json(g44.TARGET_SOURCE)
    full, _ = g44.reconstruct_full(target, g44_scope())
    return full


@lru_cache(maxsize=1)
def g44_supplements() -> dict[str, dict[str, str]]:
    target = parse_json(g44.TARGET_SOURCE)
    supplements, _ = g44.reconstruct_supplements(target, g44_scope())
    return supplements


@lru_cache(maxsize=None)
def g44_combined_locale(locale: str) -> dict[str, str]:
    scope = g44_scope()
    if locale in g44_full():
        return dict(g44_full()[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return g44.fetch_g44_upstream(locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = g44.fetch_g44_upstream(locale)
        supplement = g44_supplements()[locale]
        overlap = set(upstream) & set(supplement)
        if overlap:
            raise ValueError(f"{locale}: G44 combined ownership overlap: {sorted(overlap)}")
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G44")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (297, 8, 8, 0):
        raise ValueError("G45 frozen semantic partition changed")
    if added != ADDED_G45_KEYS or removed != REMOVED_G45_KEYS:
        raise ValueError("G45 key-category migration set changed")
    return unchanged, added, removed, changed


@lru_cache(maxsize=1)
def donor_english() -> dict[str, str]:
    return fetch_locale(DONOR_COMMIT, "en_us")


def resolve_unchanged(locale: str, key: str, english: str) -> tuple[str, str]:
    previous = g44_combined_locale(locale)
    if key not in previous:
        raise ValueError(f"{locale}: unchanged G45 key absent from G44 complete view: {key}")
    value = previous[key]
    if preserves_runtime_literals(english, value):
        return value, "g44"
    return english, "english"


def resolve_added(locale: str, key: str, english: str) -> tuple[str, str]:
    # These are renamed localization IDs. Reusing the old-key value would violate
    # the project's no-cross-key rule, even when the English text is identical.
    donor_en = donor_english()
    if donor_en.get(key) != english:
        return english, "english"
    donor = fetch_locale(DONOR_COMMIT, locale)
    value = donor.get(key)
    if value is not None and preserves_runtime_literals(english, value):
        return value, "future-donor"
    return english, "english"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if changed or added != ADDED_G45_KEYS or removed != REMOVED_G45_KEYS:
        raise ValueError("G45 full reconstruction semantic contract changed")
    expected = set(scope["addon_full_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    malformed = set(scope.get("malformed_upstream_full_override_locales", []))
    if len(expected) != 65 or malformed != MALFORMED_FULL_OVERRIDES or "uk_ua" not in expected:
        raise ValueError("G45 full/override ownership changed")
    if len(fallback) != 30 or not fallback <= expected or "uk_ua" in fallback:
        raise ValueError("G45 documented full-English fallback ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        if locale in fallback:
            result[locale] = dict(target)
            stats[locale] = {"g44":0,"future-donor":0,"upstream-repair":0,"english":len(target),"documented-fallback":len(target)}
            continue

        repaired = fetch_g45_upstream(locale) if locale == "uk_ua" else {}
        values: dict[str, str] = {}
        count = {"g44":0,"future-donor":0,"upstream-repair":0,"english":0,"documented-fallback":0}
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
                raise ValueError(f"{locale}: unresolved G45 target key {key}")
            values[key] = value
            count[source] += 1
        if set(values) != set(target) or set(values) & REMOVED_G45_KEYS:
            raise ValueError(f"{locale}: invalid G45 full key set")
        result[locale] = values
        stats[locale] = count
    return result, stats


def reconstruct_supplements(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    unchanged, added, removed, changed = semantic_partition()
    if changed or added != ADDED_G45_KEYS or removed != REMOVED_G45_KEYS:
        raise ValueError("G45 supplement semantic contract changed")
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 24 or "uk_ua" in expected:
        raise ValueError("G45 supplement ownership changed")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_g45_upstream(locale)
        missing = normal - set(upstream)
        override_keys = set(UPSTREAM_LITERAL_SAFETY_OVERRIDES.get(locale, set()))
        for key in override_keys:
            if key not in normal or key not in upstream:
                raise ValueError(f"{locale}: invalid explicit G45 upstream safety override key {key}")
            if preserves_runtime_literals(target[key], upstream[key]):
                raise ValueError(f"{locale}: G45 safety override is no longer needed for {key}")
        needed = missing | override_keys
        values: dict[str, str] = {}
        count = {
            "g44":0, "future-donor":0, "english":0,
            "upstream-owned":len(normal & set(upstream)),
            "upstream-safety-overrides":len(override_keys),
        }
        for key in sorted(needed):
            english = target[key]
            if key in unchanged:
                value, source = resolve_unchanged(locale, key, english)
            elif key in added:
                value, source = resolve_added(locale, key, english)
            else:
                raise ValueError(f"{locale}: unresolved G45 supplement key {key}")
            values[key] = value
            count[source] += 1
        overlap = set(values) & set(upstream)
        if not values or overlap != override_keys or set(values) & REMOVED_G45_KEYS:
            raise ValueError(f"{locale}: invalid G45 supplement ownership")
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
    if (len(base), len(target), normal_count) != (305, 305, 299):
        raise ValueError("G45 source counts changed")
    if (len(unchanged), len(added), len(removed), len(changed)) != (297, 8, 8, 0):
        raise ValueError("G45 semantic partition changed")
    if (diff.get("unchanged_key_and_value_count"), diff.get("added_key_count"), diff.get("removed_key_count"), diff.get("changed_english_value_count")) != (297, 8, 8, 0):
        raise ValueError("G45 frozen diff changed")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g44_semantics") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G45 reuse policy changed")
    if not reuse.get("category_renames_must_not_reuse_old_key_values"):
        raise ValueError("G45 renamed-key no-reuse policy changed")
    if reuse.get("future_donor_commit") != DONOR_COMMIT or not reuse.get("future_donor_allowed_only_for_exact_same_key_same_english"):
        raise ValueError("G45 exact future-donor policy changed")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    complete = set(scope["selected_upstream_complete_locales"])
    if len(full) + len(supplements) + len(complete) != 90:
        raise ValueError("G45 ownership total changed")

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
        "generation": "g45-mc1.21.9",
        "cross_key_reuse_allowed": False,
        "renamed_category_keys_reuse_old_values": False,
        "future_donor_commit": DONOR_COMMIT,
        "added_g45_keys": sorted(added),
        "removed_g45_keys": sorted(removed),
        "full_locales": full_stats,
        "supplement_locales": supplement_stats,
        "totals": {
            "g44": sum(x["g44"] for x in full_stats.values()) + sum(x["g44"] for x in supplement_stats.values()),
            "future-donor": sum(x["future-donor"] for x in full_stats.values()) + sum(x["future-donor"] for x in supplement_stats.values()),
            "english": sum(x["english"] for x in full_stats.values()) + sum(x["english"] for x in supplement_stats.values()),
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
    print(f"Output: {args.output}")
    print(f"Full addon/override locales: {full}")
    print(f"Missing-key-only upstream supplements: {supplements}")
    print(f"Keys per complete locale: {keys}")
    print("G44 -> G45: 297 unchanged + 8 added + 8 removed + 0 changed")
    print("Renamed category keys are not reused cross-key")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

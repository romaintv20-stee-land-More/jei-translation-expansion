#!/usr/bin/env python3
"""Reconstruct Minecraft 1.21.1 / JEI 19.21.1 JSON language resources.

Resolution order is deliberately strict:
1. preserve pinned G39 upstream ownership;
2. inherit only exact same-key + same-English G38 meanings;
3. for new/changed meanings, use a pinned later-JEI donor only when that donor has
   the exact same key and exact same English source value;
4. otherwise use exact G39 English as an explicit safe fallback.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_21 as g38

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21-to-1.21.1.json"
POLICY_PATH = ROOT / "translations" / "g39-mc1.21.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.21.1"
DEBUG_PREFIX = "description.jei."
G39_COMMIT = "28eb51f58d2798512a2ef75cf8b29189228573ad"
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/Common/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g38.parse_json_text
parse_json = g38.parse_json
write_json = g38.write_json
semantic_sets = g38.semantic_sets


@lru_cache(maxsize=None)
def fetch_json_optional(commit: str, locale: str) -> dict[str, str] | None:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G39-reconstruct"})
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
        raise ValueError("G39 donor English source is unavailable or invalid")
    return result


@lru_cache(maxsize=None)
def donor_locale(locale: str) -> dict[str, str] | None:
    return fetch_json_optional(DONOR_COMMIT, locale)


@lru_cache(maxsize=1)
def reconstruct_g38_full() -> dict[str, dict[str, str]]:
    target = g38.parse_json(g38.TARGET_SOURCE)
    scope = json.loads(g38.SCOPE_PATH.read_text(encoding="utf-8"))
    return g38.reconstruct_full(target, scope)


@lru_cache(maxsize=1)
def reconstruct_g38_supplements() -> dict[str, dict[str, str]]:
    target = g38.parse_json(g38.TARGET_SOURCE)
    scope = json.loads(g38.SCOPE_PATH.read_text(encoding="utf-8"))
    return g38.reconstruct_supplements(target, scope)


@lru_cache(maxsize=1)
def g38_scope() -> dict:
    return json.loads(g38.SCOPE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def g38_combined_locale(locale: str) -> dict[str, str]:
    scope = g38_scope()
    full = reconstruct_g38_full()
    if locale in full:
        return dict(full[locale])
    if locale in set(scope["selected_upstream_complete_locales"]):
        return fetch_upstream_json(g38.G38_COMMIT, locale)
    if locale in set(scope["selected_upstream_incomplete_locales"]):
        upstream = fetch_upstream_json(g38.G38_COMMIT, locale)
        supplement = reconstruct_g38_supplements()[locale]
        return {**upstream, **supplement}
    raise KeyError(f"{locale}: not selected in G38")


@lru_cache(maxsize=1)
def semantic_partition() -> tuple[set[str], set[str], set[str], set[str]]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    unchanged, added, removed, changed = semantic_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (76, 167, 57, 43):
        raise ValueError("G39 frozen semantic partition changed")
    return unchanged, added, removed, changed


def exact_donor_value(locale: str, key: str, target_english: str) -> str | None:
    donor_en = donor_english()
    if donor_en.get(key) != target_english:
        return None
    values = donor_locale(locale)
    if values is None:
        return None
    return values.get(key)


def resolve_changed_or_added(locale: str, key: str, target_english: str) -> tuple[str, str]:
    donor = exact_donor_value(locale, key, target_english)
    if donor is not None:
        return donor, "donor"
    return target_english, "english-fallback"


def reconstruct_full(target: dict[str, str], scope: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, int]]]:
    base = parse_json(BASE_SOURCE)
    unchanged, added, removed, changed = semantic_partition()
    previous = reconstruct_g38_full()
    expected = set(scope["addon_full_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    previous_full = set(previous)
    if len(expected) != 64 or not expected <= previous_full:
        raise ValueError("G39 addon-full ownership must be the 64 retained G38 addon-full locales")
    if previous_full - expected != {"kk_kz", "no_no", "vi_vn"}:
        raise ValueError("G39 addon-full migration must move exactly kk_kz, no_no and vi_vn upstream")
    if len(fallback_locales) != 30 or not fallback_locales <= expected:
        raise ValueError("G39 documented full-English fallback ownership must contain 30 addon-full locales")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        old = previous[locale]
        if set(old) != set(base):
            raise ValueError(f"{locale}: G38 complete key set differs from G39 base source")
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
                values[key] = old[key]
                inherited_count += 1
            elif key in added or key in changed:
                value, source = resolve_changed_or_added(locale, key, english)
                values[key] = value
                if source == "donor":
                    donor_count += 1
                else:
                    fallback_count += 1
            else:
                raise ValueError(f"{locale}: unresolved G39 semantic key: {key}")
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
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 24 or not {"kk_kz", "no_no", "vi_vn"} <= expected:
        raise ValueError("G39 supplement ownership must contain 24 locales including kk_kz, no_no and vi_vn")

    result: dict[str, dict[str, str]] = {}
    stats: dict[str, dict[str, int]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G39_COMMIT, locale)
        missing = normal_keys - set(upstream)
        previous_complete = g38_combined_locale(locale)
        values: dict[str, str] = {}
        inherited_count = donor_count = fallback_count = 0
        for key in sorted(missing):
            if key in unchanged:
                if key not in previous_complete:
                    raise ValueError(f"{locale}: unchanged G39 missing key absent from G38 complete view: {key}")
                values[key] = previous_complete[key]
                inherited_count += 1
            elif key in added or key in changed:
                value, source = resolve_changed_or_added(locale, key, target[key])
                values[key] = value
                if source == "donor":
                    donor_count += 1
                else:
                    fallback_count += 1
            else:
                raise ValueError(f"{locale}: unresolved G39 supplement semantic key: {key}")
        if set(values) & set(upstream):
            raise ValueError(f"{locale}: G39 supplement would override upstream-owned keys")
        result[locale] = values
        stats[locale] = {
            "inherited": inherited_count,
            "donor": donor_count,
            "english_fallback": fallback_count,
            "upstream_owned": len(normal_keys & set(upstream)),
        }
    return result, stats


def provenance_summary(full_stats: dict[str, dict[str, int]], supplement_stats: dict[str, dict[str, int]]) -> dict:
    translated_full = {k: v for k, v in full_stats.items() if v["documented_full_english_fallback"] == 0}
    return {
        "schema_version": 1,
        "generation": "g39-mc1.21.1",
        "donor_commit": DONOR_COMMIT,
        "resolution_order": ["pinned-upstream", "exact-g38-inheritance", "exact-later-jei-donor", "exact-g39-english-fallback"],
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
    if (len(base), len(target), normal_count) != (176, 286, 280):
        raise ValueError(f"G39 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (76, 167, 57, 43):
        raise ValueError("G39 frozen English diff counts changed")
    reuse = policy["translation_reuse"]
    if not reuse["reuse_exact_unchanged_g38_semantics"] or reuse["cross_key_reuse_allowed"]:
        raise ValueError("G39 policy must require exact G38 reuse and forbid cross-key reuse")
    donor_policy = policy["later_upstream_backport_policy"]
    if not donor_policy["allowed_only_if_same_key_and_exact_same_english_value"]:
        raise ValueError("G39 donor policy must require exact key+English semantics")

    full, full_stats = reconstruct_full(target, scope)
    supplements, supplement_stats = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 24, 286):
        raise ValueError(f"G39 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    summary = provenance_summary(full_stats, supplement_stats)
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
    (output / "PROVENANCE.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(full), len(supplements), len(target), summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.21.1-reconstruct-") as tmp:
            full_count, supplement_count, key_count, summary = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.21.1 deterministic JSON reconstruction baseline")
    else:
        full_count, supplement_count, key_count, summary = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    totals = summary["totals"]
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print(f"Translated-full exact donor values: {totals['translated_full_donor']}")
    print(f"Translated-full unresolved values using exact English fallback: {totals['translated_full_english_fallback']}")
    print(f"Supplement exact donor values: {totals['supplement_donor']}")
    print(f"Supplement unresolved values using exact English fallback: {totals['supplement_english_fallback']}")
    print("G39 remains a major semantic migration: English fallbacks are explicit provenance, never counted as translated values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 1.15.1 / JEI 6.0.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_14_4 as g16

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.14.4" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.15.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.15.1-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.14.4-to-1.15.1.json"
POLICY_PATH = ROOT / "translations" / "g17-mc1.15.1" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.15.1"
DEBUG_PREFIX = "description.jei."
G17_COMMIT = "381a0d7df6ffd282f9eda4da41a299fdbea02352"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"
REMOVED_G16_FULL = {"kab_kab", "moh_ca", "nuk", "oj_ca", "scn"}
NEW_G17_FULL = {"lmo"}

parse_json_text = g16.parse_json_text
parse_json = g16.parse_json
write_json = g16.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G17-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g16_full() -> dict[str, dict[str, str]]:
    target = g16.parse_json(g16.TARGET_SOURCE)
    scope = json.loads(g16.SCOPE_PATH.read_text(encoding="utf-8"))
    return g16.reconstruct_full(target, scope)


def reconstruct_g16_supplements() -> dict[str, dict[str, str]]:
    target = g16.parse_json(g16.TARGET_SOURCE)
    scope = json.loads(g16.SCOPE_PATH.read_text(encoding="utf-8"))
    return g16.reconstruct_supplements(target, scope)


def g16_selected_locales() -> set[str]:
    scope = json.loads(g16.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def g16_combined_locale(
    locale: str,
    full: dict[str, dict[str, str]],
    supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g16_selected_locales():
        raise KeyError(locale)
    values = dict(g16.fetch_upstream_json(g16.G16_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G16 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    expected = set(scope["addon_full_locales"])
    if len(expected) != 66:
        raise ValueError(f"G17 expected 66 addon-owned full locales, got {len(expected)}")
    g16_full = reconstruct_g16_full()
    inherited_expected = set(g16_full) - REMOVED_G16_FULL
    if expected - NEW_G17_FULL != inherited_expected:
        raise ValueError("G17 inherited addon-full locale set differs from G16 minus removed Minecraft codes")
    result = {locale: dict(g16_full[locale]) for locale in sorted(inherited_expected)}
    result["lmo"] = dict(target)
    for locale, values in result.items():
        if set(values) != set(target):
            raise ValueError(f"{locale}: invalid G17 complete key set")
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 16:
        raise ValueError(f"G17 expected 16 supplement locales, got {len(expected)}")
    g16_full = reconstruct_g16_full()
    g16_supplements = reconstruct_g16_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G17_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined = g16_combined_locale(locale, g16_full, g16_supplements)
        result[locale] = {key: combined[key] for key in target if key in missing}
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    if target != base:
        raise ValueError("G17 English must be semantically identical to G16")
    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(target), normal_count) != (109, 106):
        raise ValueError(f"G17 target must contain 109 total / 106 normal keys, got {len(target)}/{normal_count}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (109, 0, 0, 0):
        raise ValueError("G17 frozen English diff counts changed")
    if not policy["translation_reuse"]["all_semantics_reuse_g16"]:
        raise ValueError("G17 policy must require strict G16 semantic inheritance")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (66, 16, 109):
        raise ValueError(f"G17 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.15.1-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.15.1 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("All 109 G16 semantics are inherited exactly")
    print("lmo uses the documented exact-English full fallback")
    print("sv_se newly missing upstream category values are recovered from pinned G16 combined resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

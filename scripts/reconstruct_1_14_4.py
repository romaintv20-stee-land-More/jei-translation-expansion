#!/usr/bin/env python3
"""Reconstruct Minecraft 1.14.4 / JEI 6.0.1 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_14_3 as g15

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.14.3" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.14.4" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.14.4-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.14.3-to-1.14.4.json"
POLICY_PATH = ROOT / "translations" / "g16-mc1.14.4" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.14.4"
DEBUG_PREFIX = "description.jei."
G16_COMMIT = "de8b6a10eba45899be1c62694c9f27a435ae8c2c"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g15.parse_json_text
parse_json = g15.parse_json
write_json = g15.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G16-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g15_full() -> dict[str, dict[str, str]]:
    target = g15.parse_json(g15.TARGET_SOURCE)
    scope = json.loads(g15.SCOPE_PATH.read_text(encoding="utf-8"))
    return g15.reconstruct_full(target, scope)


def reconstruct_g15_supplements() -> dict[str, dict[str, str]]:
    target = g15.parse_json(g15.TARGET_SOURCE)
    scope = json.loads(g15.SCOPE_PATH.read_text(encoding="utf-8"))
    return g15.reconstruct_supplements(target, scope)


def g15_selected_locales() -> set[str]:
    scope = json.loads(g15.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def g15_combined_locale(
    locale: str,
    full: dict[str, dict[str, str]],
    supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g15_selected_locales():
        raise KeyError(locale)
    values = dict(g15.fetch_upstream_json(g15.G15_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G15 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    expected = set(scope["addon_full_locales"])
    if len(expected) != 70:
        raise ValueError(f"G16 expected 70 addon-owned full locales, got {len(expected)}")
    g15_full = reconstruct_g15_full()
    if expected != set(g15_full):
        raise ValueError("G16 addon-full locale set differs from G15")
    result = {locale: dict(g15_full[locale]) for locale in sorted(expected)}
    for locale, values in result.items():
        if set(values) != set(target):
            raise ValueError(f"{locale}: invalid strict G15 inheritance key set")
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 16:
        raise ValueError(f"G16 expected 16 supplement locales, got {len(expected)}")
    g15_full = reconstruct_g15_full()
    g15_supplements = reconstruct_g15_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G16_COMMIT, locale)
        missing = normal_keys - set(upstream)
        combined = g15_combined_locale(locale, g15_full, g15_supplements)
        result[locale] = {key: combined[key] for key in target if key in missing}
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    if target != base:
        raise ValueError("G16 English must be semantically identical to G15")
    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(target), normal_count) != (109, 106):
        raise ValueError(f"G16 target must contain 109 total / 106 normal keys, got {len(target)}/{normal_count}")
    if (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"]
    ) != (109, 0, 0, 0):
        raise ValueError("G16 frozen English diff counts changed")
    if not policy["translation_reuse"]["all_semantics_reuse_g15"]:
        raise ValueError("G16 policy must require strict G15 inheritance")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (70, 16, 109):
        raise ValueError(f"G16 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.14.4-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.14.4 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("All 109 G15 semantics are inherited exactly")
    print("de_de and ru_ru supplements are retired because pinned G16 upstream is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

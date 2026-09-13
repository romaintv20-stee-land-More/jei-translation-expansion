#!/usr/bin/env python3
"""Reconstruct Minecraft 1.18 / JEI 9.0.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_17_1 as g24

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.17.1" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.18" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.18-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.17.1-to-1.18.json"
POLICY_PATH = ROOT / "translations" / "g25-mc1.18" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.18"
DEBUG_PREFIX = "description.jei."
G25_COMMIT = "2df668b5ac4a8473b9837ad2785d0f5a4fb845a6"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"

parse_json_text = g24.parse_json_text
parse_json = g24.parse_json
write_json = g24.write_json


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G25-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def reconstruct_g24_full() -> dict[str, dict[str, str]]:
    target = g24.parse_json(g24.TARGET_SOURCE)
    scope = json.loads(g24.SCOPE_PATH.read_text(encoding="utf-8"))
    return g24.reconstruct_full(target, scope)


def reconstruct_g24_supplements() -> dict[str, dict[str, str]]:
    target = g24.parse_json(g24.TARGET_SOURCE)
    scope = json.loads(g24.SCOPE_PATH.read_text(encoding="utf-8"))
    return g24.reconstruct_supplements(target, scope)


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    if base != target:
        raise ValueError("G25 English source must be exactly identical to G24")
    expected = set(scope["addon_full_locales"])
    previous = reconstruct_g24_full()
    if len(expected) != 64 or expected != set(previous):
        raise ValueError("G25 addon-full ownership must be exactly identical to G24")
    return {locale: dict(values) for locale, values in sorted(previous.items())}


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    previous = reconstruct_g24_supplements()
    if len(expected) != 21 or expected != set(previous):
        raise ValueError("G25 supplement ownership must be exactly identical to G24")
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G25_COMMIT, locale)
        g24_upstream = g24.fetch_upstream_json(g24.G24_COMMIT, locale)
        if upstream != g24_upstream:
            raise ValueError(f"{locale}: G25 upstream locale differs from G24 despite frozen no-language-file port")
        missing = normal_keys - set(upstream)
        if set(previous[locale]) != missing:
            raise ValueError(f"{locale}: G25 missing-key set differs from inherited G24 supplement")
        result[locale] = dict(previous[locale])
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    base = parse_json(BASE_SOURCE)
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(base), len(target), normal_count) != (141, 141, 135):
        raise ValueError(f"G25 source counts changed: base={len(base)} target={len(target)} normal={normal_count}")
    if base != target:
        raise ValueError("G25 target English must remain byte-semantically identical to G24")
    if (diff["unchanged_key_and_value_count"], diff["added_key_count"], diff["removed_key_count"], diff["changed_english_value_count"]) != (141, 0, 0, 0):
        raise ValueError("G25 frozen English diff counts changed")
    if not policy["translation_reuse"]["reuse_unchanged_g24_semantics"]:
        raise ValueError("G25 policy must require exact G24 reuse for all meanings")
    if policy["translation_reuse"]["cross_key_reuse_allowed"]:
        raise ValueError("G25 policy must forbid cross-key translation reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (64, 21, 141):
        raise ValueError(f"G25 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.18-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.18 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")
    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete addon locale: {key_count}")
    print("All 141 G24 key/value semantics are inherited exactly")
    print("G25 upstream locale resources are unchanged from G24 at the pinned port endpoint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconstruct Minecraft 1.13 / JEI 4.14.4 JSON language resources."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_12_1 as g10
import reconstruct_1_12_2 as g11

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.12.2" / "en_us.lang"
HISTORICAL_SOURCE = ROOT / "upstream" / "sources" / "1.12.1" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.13" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.13-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.12.2-to-1.13.json"
POLICY_PATH = ROOT / "translations" / "g12-mc1.13" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.13"
DEBUG_PREFIX = "description.jei."
G12_COMMIT = "380bc11efb548abd804c65b763c911ebf9d06e2c"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"
LOCALE_ALIASES = {"ksh": "ksh_de"}
NEW_G12_LANGUAGES = {"nuk", "ovd", "szl"}
PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|CTRL|,d|\d+\$[sdif]|[sdif]|%)")
TECHNICAL_TOKENS = (
    "JEI",
    "Minecraft",
    "/give",
    "modId[:name[:meta]]",
    "mB",
)


def parse_lang(path: Path) -> dict[str, str]:
    return g11.parse_lang(path)


def parse_json_text(text: str) -> dict[str, str]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("language JSON root must be an object")
    values: dict[str, str] = {}
    for key, value in data.items():
        if key.startswith("_comment"):
            continue
        if not isinstance(value, str):
            raise ValueError(f"language JSON value for {key} is not a string")
        values[key] = value
    return values


def parse_json(path: Path) -> dict[str, str]:
    return parse_json_text(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G12-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def write_json(path: Path, values: dict[str, str]) -> None:
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reconstruct_g11_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g11.TARGET_SOURCE)
    scope = json.loads(g11.SCOPE_PATH.read_text(encoding="utf-8"))
    return g11.reconstruct_full(target, scope)


def reconstruct_g11_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g11.TARGET_SOURCE)
    scope = json.loads(g11.SCOPE_PATH.read_text(encoding="utf-8"))
    return g11.reconstruct_supplements(target, scope)


def g11_selected_locales() -> set[str]:
    scope = json.loads(g11.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def g11_combined_locale(
    locale: str,
    full: dict[str, dict[str, str]],
    supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g11_selected_locales():
        raise KeyError(locale)
    values = dict(g11.fetch_upstream_lang(g11.G11_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G11 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def reconstruct_g10_full() -> dict[str, dict[str, str]]:
    return g11.reconstruct_g10_full()


def reconstruct_g10_supplements() -> dict[str, dict[str, str]]:
    return g11.reconstruct_g10_supplements()


def g10_selected_locales() -> set[str]:
    scope = json.loads(g10.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def historical_locale(locale: str) -> str:
    return LOCALE_ALIASES.get(locale, locale)


def safe_historical_candidate(target_value: str, candidate: str) -> bool:
    """Reject inherited values that lose runtime placeholders or fixed technical literals."""
    if sorted(PLACEHOLDER_RE.findall(target_value)) != sorted(PLACEHOLDER_RE.findall(candidate)):
        return False
    for token in TECHNICAL_TOKENS:
        if token in target_value and token not in candidate:
            return False
    return True


def resolve_historical_value(
    locale: str,
    key: str,
    target_value: str,
    base: dict[str, str],
    historical: dict[str, str],
    g11_full: dict[str, dict[str, str]],
    g11_supplements: dict[str, dict[str, str]],
    g10_full: dict[str, dict[str, str]],
    g10_supplements: dict[str, dict[str, str]],
) -> tuple[str, str]:
    if key.startswith(DEBUG_PREFIX) or locale in NEW_G12_LANGUAGES:
        return target_value, "target-English"

    source_locale = historical_locale(locale)
    if source_locale in g11_selected_locales() and base.get(key) == target_value:
        combined = g11_combined_locale(source_locale, g11_full, g11_supplements)
        if key in combined and safe_historical_candidate(target_value, combined[key]):
            return combined[key], "g11-exact-semantic"

    if source_locale in g10_selected_locales() and historical.get(key) == target_value:
        combined = g11.g10_combined_locale(source_locale, g10_full, g10_supplements)
        if key in combined and safe_historical_candidate(target_value, combined[key]):
            return combined[key], "g10-exact-semantic-reversion"

    return target_value, "target-English"


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    historical = parse_lang(HISTORICAL_SOURCE)
    expected = set(scope["addon_full_locales"])
    if len(expected) != 62:
        raise ValueError(f"G12 expected 62 addon-owned full locales, got {len(expected)}")

    g11_full = reconstruct_g11_full()
    g11_supplements = reconstruct_g11_supplements()
    g10_full = reconstruct_g10_full()
    g10_supplements = reconstruct_g10_supplements()

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        values: dict[str, str] = {}
        for key, target_value in target.items():
            value, _ = resolve_historical_value(
                locale,
                key,
                target_value,
                base,
                historical,
                g11_full,
                g11_supplements,
                g10_full,
                g10_supplements,
            )
            values[key] = value
        if set(values) != set(target):
            raise ValueError(f"{locale}: G12 full reconstruction key mismatch")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    historical = parse_lang(HISTORICAL_SOURCE)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 12:
        raise ValueError(f"G12 expected 12 supplement locales, got {len(expected)}")

    g11_full = reconstruct_g11_full()
    g11_supplements = reconstruct_g11_supplements()
    g10_full = reconstruct_g10_full()
    g10_supplements = reconstruct_g10_supplements()

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G12_COMMIT, locale)
        missing = normal_keys - set(upstream)
        values: dict[str, str] = {}
        for key in target:
            if key not in missing:
                continue
            value, _ = resolve_historical_value(
                locale,
                key,
                target[key],
                base,
                historical,
                g11_full,
                g11_supplements,
                g10_full,
                g10_supplements,
            )
            values[key] = value
        result[locale] = values

    if set(result) != expected:
        raise ValueError("G12 supplement locale set differs from frozen scope")
    return result


def reuse_statistics(target: dict[str, str], scope: dict) -> dict[str, int]:
    base = parse_lang(BASE_SOURCE)
    historical = parse_lang(HISTORICAL_SOURCE)
    g11_full = reconstruct_g11_full()
    g11_supplements = reconstruct_g11_supplements()
    g10_full = reconstruct_g10_full()
    g10_supplements = reconstruct_g10_supplements()
    counts = {"g11-exact-semantic": 0, "g10-exact-semantic-reversion": 0, "target-English": 0}
    for locale in sorted(scope["addon_full_locales"]):
        for key, target_value in target.items():
            _, source = resolve_historical_value(
                locale,
                key,
                target_value,
                base,
                historical,
                g11_full,
                g11_supplements,
                g10_full,
                g10_supplements,
            )
            counts[source] += 1
    return counts


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    if (len(target), len([key for key in target if not key.startswith(DEBUG_PREFIX)])) != (105, 102):
        raise ValueError("G12 target must contain 105 total / 102 normal semantic keys")
    if (
        diff["unchanged_key_and_value_count"],
        diff["added_key_count"],
        diff["removed_key_count"],
        diff["changed_english_value_count"],
    ) != (59, 4, 14, 42):
        raise ValueError("G12 frozen English diff counts changed")
    if policy["selected_scope_count"] != 83 or policy["english_diff"]["reviewed_normal_added_or_changed_key_count"] != 43:
        raise ValueError("G12 frozen policy counts changed")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (62, 12, 105):
        raise ValueError(f"G12 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G12 output locale is not lowercase")
        path = full_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G12 full JSON failed round-trip validation")

    for locale, values in sorted(supplements.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G12 supplement locale is not lowercase")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G12 supplement contains debug-only key")
        path = supplement_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G12 supplement JSON failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.13-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.13 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("Resource format: JSON")
    print("Exact semantics reuse G11 first, then exact G10 semantic reversions")
    print("Historical values that lose placeholders/technical literals are rejected")
    print("Other changed/new project-owned meanings use target-English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

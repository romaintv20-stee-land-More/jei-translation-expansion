#!/usr/bin/env python3
"""Reconstruct Minecraft 1.14.2 / JEI 6.0.0 JSON language resources."""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import reconstruct_1_13_2 as g13

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.13.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.14.2" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.14.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.13.2-to-1.14.2.json"
POLICY_PATH = ROOT / "translations" / "g14-mc1.14.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.14.2"
DEBUG_PREFIX = "description.jei."
G14_COMMIT = "f1fd2f1d20cf86d9644e907a641f99873b4d8888"
RAW_JSON_TEMPLATE = "https://raw.githubusercontent.com/mezz/JustEnoughItems/{commit}/src/main/resources/assets/jei/lang/{locale}.json"
NEW_G14_LANGUAGES = {"ba_ru", "scn", "tl_ph", "yi_de"}
NEW_G14_KEYS = {
    "gui.jei.category.blasting",
    "gui.jei.category.campfire",
    "gui.jei.category.smoking",
}


def parse_json_text(text: str) -> dict[str, str]:
    return g13.parse_json_text(text)


def parse_json(path: Path) -> dict[str, str]:
    return g13.parse_json(path)


@lru_cache(maxsize=None)
def fetch_upstream_json(commit: str, locale: str) -> dict[str, str]:
    url = RAW_JSON_TEMPLATE.format(commit=commit, locale=locale)
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G14-reconstruct"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_json_text(response.read().decode("utf-8"))


def write_json(path: Path, values: dict[str, str]) -> None:
    path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reconstruct_g13_full() -> dict[str, dict[str, str]]:
    target = g13.parse_json(g13.TARGET_SOURCE)
    scope = json.loads(g13.SCOPE_PATH.read_text(encoding="utf-8"))
    return g13.reconstruct_full(target, scope)


def reconstruct_g13_supplements() -> dict[str, dict[str, str]]:
    target = g13.parse_json(g13.TARGET_SOURCE)
    scope = json.loads(g13.SCOPE_PATH.read_text(encoding="utf-8"))
    return g13.reconstruct_supplements(target, scope)


def g13_selected_locales() -> set[str]:
    scope = json.loads(g13.SCOPE_PATH.read_text(encoding="utf-8"))
    return (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )


def g13_combined_locale(
    locale: str,
    full: dict[str, dict[str, str]],
    supplements: dict[str, dict[str, str]],
) -> dict[str, str]:
    if locale in full:
        return dict(full[locale])
    if locale not in g13_selected_locales():
        raise KeyError(locale)
    values = dict(g13.fetch_upstream_json(g13.G13_COMMIT, locale))
    if locale in supplements:
        overlap = set(values) & set(supplements[locale])
        if overlap:
            raise ValueError(f"{locale}: G13 supplement overlaps upstream keys: {sorted(overlap)}")
        values.update(supplements[locale])
    return values


def resolve_value(
    locale: str,
    key: str,
    target_value: str,
    base: dict[str, str],
    g13_full: dict[str, dict[str, str]],
    g13_supplements: dict[str, dict[str, str]],
) -> tuple[str, str]:
    if key.startswith(DEBUG_PREFIX) or locale in NEW_G14_LANGUAGES:
        return target_value, "target-English"
    if base.get(key) == target_value and locale in g13_selected_locales():
        combined = g13_combined_locale(locale, g13_full, g13_supplements)
        candidate = combined.get(key)
        if candidate is not None and g13.g12.safe_historical_candidate(target_value, candidate):
            return candidate, "g13-exact-semantic"
    return target_value, "target-English"


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    expected = set(scope["addon_full_locales"])
    if len(expected) != 70:
        raise ValueError(f"G14 expected 70 addon-owned full locales, got {len(expected)}")

    g13_full = reconstruct_g13_full()
    g13_supplements = reconstruct_g13_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        values: dict[str, str] = {}
        for key, target_value in target.items():
            value, _ = resolve_value(locale, key, target_value, base, g13_full, g13_supplements)
            values[key] = value
        if set(values) != set(target):
            raise ValueError(f"{locale}: G14 full reconstruction key mismatch")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_json(BASE_SOURCE)
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    expected = set(scope["selected_upstream_incomplete_locales"])
    if len(expected) != 19:
        raise ValueError(f"G14 expected 19 supplement locales, got {len(expected)}")

    g13_full = reconstruct_g13_full()
    g13_supplements = reconstruct_g13_supplements()
    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        upstream = fetch_upstream_json(G14_COMMIT, locale)
        missing = normal_keys - set(upstream)
        values: dict[str, str] = {}
        for key in target:
            if key not in missing:
                continue
            value, _ = resolve_value(locale, key, target[key], base, g13_full, g13_supplements)
            values[key] = value
        result[locale] = values
    if set(result) != expected:
        raise ValueError("G14 supplement locale set differs from frozen scope")
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_json(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    normal_count = len([key for key in target if not key.startswith(DEBUG_PREFIX)])
    if (len(target), normal_count) != (109, 106):
        raise ValueError(f"G14 target must contain 109 total / 106 normal keys, got {len(target)}/{normal_count}")
    if (
        diff["unchanged_key_and_value_count"],
        diff["added_key_count"],
        diff["removed_key_count"],
        diff["changed_english_value_count"],
    ) != (106, 3, 0, 0):
        raise ValueError("G14 frozen English diff counts changed")
    if set(diff["added_keys"]) != NEW_G14_KEYS:
        raise ValueError("G14 frozen added-key set changed")
    if policy["selected_scope_count"] != 91 or policy["english_diff"]["reviewed_normal_added_or_changed_key_count"] != 3:
        raise ValueError("G14 frozen policy counts changed")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope)
    if (len(full), len(supplements), len(target)) != (70, 19, 109):
        raise ValueError(f"G14 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}")

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
            raise ValueError(f"{locale}: G14 full JSON failed round-trip validation")

    for locale, values in sorted(supplements.items()):
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: G14 supplement contains debug-only key")
        path = supplement_dir / f"{locale}.json"
        write_json(path, values)
        if parse_json(path) != values:
            raise ValueError(f"{locale}: G14 supplement JSON failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.14.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.14.2 deterministic JSON reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("Resource format: JSON")
    print("106 exact G13 semantics are eligible for reuse")
    print("Three new cooking-category meanings use exact G14 target English when project-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

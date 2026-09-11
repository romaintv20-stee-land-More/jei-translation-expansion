#!/usr/bin/env python3
"""Reconstruct Minecraft 1.11 / JEI 4.1.1 addon language resources.

G7 has no English semantic changes from G6: all 87 JEI key/value pairs are
identical. The generation therefore reuses the complete G6 project result,
while adapting resource filenames to lowercase and respecting changed JEI
upstream ownership:
- 52 complete addon-owned locales, emitted with lowercase filenames;
- 15 persistent incomplete upstream locales reuse their exact G6 supplements;
- de_de receives 16 translations preserved from pinned JEI 3.14.8 de_DE;
- sv_se is now complete upstream and receives no addon file.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_10_2 as g6

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.10.2" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.11" / "en_us.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.11-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.11-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g7-mc1.11" / "policy.json"
DE_REUSE_PATH = ROOT / "translations" / "g7-mc1.11" / "de_de-from-g6-upstream.lang"
G6_AUDIT_PATH = ROOT / "upstream" / "minecraft-1.10.2-language-audit.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.11"
DEBUG_PREFIX = "description.jei."


def parse_lang(path: Path) -> dict[str, str]:
    return g6.parse_lang(path)


def target_layout() -> list[tuple[str, str | None]]:
    layout: list[tuple[str, str | None]] = []
    for raw in TARGET_SOURCE.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            layout.append((raw, None))
            continue
        key, _ = raw.split("=", 1)
        layout.append((raw, key.strip()))
    return layout


def lower_lookup(items: set[str] | list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        lowered = item.lower()
        if lowered in result and result[lowered] != item:
            raise ValueError(f"locale case normalization collision: {result[lowered]} vs {item}")
        result[lowered] = item
    return result


def reconstruct_g6_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g6.TARGET_SOURCE)
    scope = json.loads(g6.SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g6.POLICY_PATH.read_text(encoding="utf-8"))
    return g6.reconstruct_full(target, scope, policy)


def reconstruct_g6_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g6.TARGET_SOURCE)
    scope = json.loads(g6.SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g6.AUDIT_PATH.read_text(encoding="utf-8"))
    return g6.reconstruct_supplements(target, scope, audit)


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    if base != target:
        raise ValueError("G7 English source is no longer identical to G6")

    g6_full = reconstruct_g6_full()
    lookup = lower_lookup(set(g6_full))
    expected = set(scope["addon_full_locales"])
    if expected - set(lookup):
        raise ValueError(f"G7 full locales missing from G6 reconstruction: {sorted(expected - set(lookup))}")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        values = dict(g6_full[lookup[locale]])
        if set(values) != set(target):
            raise ValueError(f"{locale}: inherited G6 full file has wrong key set")
        for key, english in target.items():
            if key.startswith(DEBUG_PREFIX) and values[key] != english:
                raise ValueError(f"{locale}: debug-only key must retain target English")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict, audit: dict) -> dict[str, dict[str, str]]:
    g6_supplements = reconstruct_g6_supplements()
    g6_lookup = lower_lookup(set(g6_supplements))
    expected = set(scope["selected_upstream_incomplete_locales"])
    persistent = set(audit["persistent_incomplete_locales_from_g6"])
    if persistent != expected - {"de_de"}:
        raise ValueError("G7 persistent supplement set does not equal target incomplete set minus de_de")
    if "sv_se" in expected:
        raise ValueError("G7 must not emit a supplement for complete upstream sv_se")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(persistent):
        if locale not in g6_lookup:
            raise ValueError(f"{locale}: persistent G7 supplement absent from G6 supplements")
        result[locale] = dict(g6_supplements[g6_lookup[locale]])

    de_values = parse_lang(DE_REUSE_PATH)
    de_expected = set(
        audit["ownership_changes_from_g6"]["became_incomplete"]["de_de"]["missing_normal_keys"]
    )
    if set(de_values) != de_expected:
        raise ValueError(
            "de_de preserved G6 upstream translations do not match exact G7 missing-key set: "
            f"expected={sorted(de_expected)}, actual={sorted(de_values)}"
        )
    result["de_de"] = de_values

    for locale, values in result.items():
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: supplement unexpectedly contains debug-only key")
        if any(key not in target for key in values):
            raise ValueError(f"{locale}: supplement contains a key absent from G7 target")

    if set(result) != expected:
        raise ValueError("G7 supplement output locale set does not match scope")
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    if policy["resource_filename_case"] != "lowercase":
        raise ValueError("G7 policy must require lowercase resource filenames")
    if not policy["reuse_all_87_base_key_values"]:
        raise ValueError("G7 policy unexpectedly disables full G6 semantic reuse")

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope, audit)
    if len(full) != scope["addon_full_locale_count"]:
        raise ValueError("G7 full locale count does not match scope")
    if len(supplements) != scope["selected_upstream_incomplete_locale_count"]:
        raise ValueError("G7 supplement locale count does not match scope")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G7 output locale is not lowercase")
        path = full_dir / f"{locale}.lang"
        g6.g4.write_lang(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G7 full output failed round-trip validation")

    target_order = list(target)
    for locale, values in sorted(supplements.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G7 supplement locale is not lowercase")
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target_order if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G7 supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.11-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.11 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("Resource filenames: lowercase")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

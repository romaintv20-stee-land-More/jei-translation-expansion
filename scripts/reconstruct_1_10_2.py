#!/usr/bin/env python3
"""Reconstruct Minecraft 1.10.2 / JEI 3.14.8 addon language resources.

G6 has substantially different upstream ownership from G5. It emits:
- 52 complete addon-owned locale files;
- exact missing-key-only supplements for 16 selected JEI upstream locales;
- no files for the four selected locales that are complete upstream.

Safe reuse policy:
- unchanged key + English value: reuse G5 project translation when available;
- gui.jei.category.craftingTable: restore G4 translation because the English
  meaning returns exactly to G4 "Crafting";
- all other G6-added/changed strings: exact target English fallback unless an
  already-validated project translation is available under the rules above.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_9_4 as g4
import reconstruct_1_10 as g5

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.10" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.10.2" / "en_US.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.10.2-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.10.2-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g6-mc1.10.2" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.10.2"
DEBUG_PREFIX = "description.jei."
CRAFTING_KEY = "gui.jei.category.craftingTable"


def parse_lang(path: Path) -> dict[str, str]:
    return g5.parse_lang(path)


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


def source_sets(base: dict[str, str], target: dict[str, str]) -> tuple[set[str], set[str], set[str], set[str]]:
    base_keys = set(base)
    target_keys = set(target)
    added = target_keys - base_keys
    removed = base_keys - target_keys
    changed = {key for key in base_keys & target_keys if base[key] != target[key]}
    unchanged = {key for key in base_keys & target_keys if base[key] == target[key]}
    return added, removed, changed, unchanged


def reconstruct_g5_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g5.TARGET_SOURCE)
    scope = json.loads(g5.G5_SCOPE_PATH.read_text(encoding="utf-8"))
    return g5.reconstruct_full(target, scope)


def reconstruct_g5_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g5.TARGET_SOURCE)
    scope = json.loads(g5.G5_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g5.G5_AUDIT_PATH.read_text(encoding="utf-8"))
    return g5.reconstruct_supplements(target, scope, audit)


def reconstruct_g4_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g4.TARGET_SOURCE)
    scope = json.loads(g4.G4_SCOPE_PATH.read_text(encoding="utf-8"))
    return g4.reconstruct_full(target, scope)


def reconstruct_g4_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g4.TARGET_SOURCE)
    scope = json.loads(g4.G4_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g4.G4_AUDIT_PATH.read_text(encoding="utf-8"))
    return g4.reconstruct_supplements(target, scope, audit)


def reconstruct_full(target: dict[str, str], scope: dict, policy: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    added, removed, changed, unchanged = source_sets(base, target)
    if (len(unchanged), len(added), len(removed), len(changed)) != (53, 25, 16, 9):
        raise ValueError(
            "unexpected G5 -> G6 diff counts: "
            f"unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}"
        )

    g5_full = reconstruct_g5_full()
    g4_full = reconstruct_g4_full()
    full_locales = set(scope["addon_full_locales"])
    fallback_locales = set(policy["documented_full_english_fallback_locales"])
    if not full_locales <= set(g5_full):
        raise ValueError(f"G6 full locales absent from G5 full reconstruction: {sorted(full_locales - set(g5_full))}")
    if not fallback_locales <= full_locales:
        raise ValueError("documented full English fallback locale is not addon-owned in G6")

    g4_target = parse_lang(g4.TARGET_SOURCE)
    if target[CRAFTING_KEY] != g4_target[CRAFTING_KEY]:
        raise ValueError("G6 Crafting English value no longer matches G4 semantic-reversion source")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(full_locales):
        if locale in fallback_locales:
            result[locale] = dict(target)
            continue

        values: dict[str, str] = {}
        for key, english in target.items():
            if key.startswith(DEBUG_PREFIX):
                values[key] = english
            elif key in unchanged:
                values[key] = g5_full[locale][key]
            elif key == CRAFTING_KEY and locale in g4_full:
                values[key] = g4_full[locale][key]
            else:
                values[key] = english
        if set(values) != set(target):
            raise ValueError(f"{locale}: incomplete G6 full reconstruction")
        result[locale] = values

    return result


def project_owned_g5_value(
    locale: str,
    key: str,
    g5_full: dict[str, dict[str, str]],
    g5_supplements: dict[str, dict[str, str]],
) -> str | None:
    if locale in g5_full and key in g5_full[locale]:
        return g5_full[locale][key]
    if locale in g5_supplements and key in g5_supplements[locale]:
        return g5_supplements[locale][key]
    return None


def project_owned_g4_value(
    locale: str,
    key: str,
    g4_full: dict[str, dict[str, str]],
    g4_supplements: dict[str, dict[str, str]],
) -> str | None:
    if locale in g4_full and key in g4_full[locale]:
        return g4_full[locale][key]
    if locale in g4_supplements and key in g4_supplements[locale]:
        return g4_supplements[locale][key]
    return None


def reconstruct_supplements(target: dict[str, str], scope: dict, audit: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    _, _, _, unchanged = source_sets(base, target)
    g5_full = reconstruct_g5_full()
    g5_supplements = reconstruct_g5_supplements()
    g4_full = reconstruct_g4_full()
    g4_supplements = reconstruct_g4_supplements()

    expected_locales = set(scope["selected_upstream_incomplete_locales"])
    audited = audit["selected_upstream_locale_completeness"]
    if expected_locales != {locale for locale, item in audited.items() if item["missing_normal"] > 0}:
        raise ValueError("G6 supplement locale set differs from audited selected incomplete locale set")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        missing = list(audited[locale]["missing_normal_keys"])
        values: dict[str, str] = {}
        for key in missing:
            english = target[key]
            if key in unchanged:
                reused = project_owned_g5_value(locale, key, g5_full, g5_supplements)
                values[key] = reused if reused is not None else english
            elif key == CRAFTING_KEY:
                reused = project_owned_g4_value(locale, key, g4_full, g4_supplements)
                values[key] = reused if reused is not None else english
            else:
                values[key] = english
        if set(values) != set(missing):
            raise ValueError(f"{locale}: supplement does not match audited missing-key set")
        if any(key.startswith(DEBUG_PREFIX) for key in values):
            raise ValueError(f"{locale}: supplement unexpectedly includes debug-only key")
        result[locale] = values
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    full = reconstruct_full(target, scope, policy)
    supplements = reconstruct_supplements(target, scope, audit)

    if len(full) != scope["addon_full_locale_count"]:
        raise ValueError("G6 full locale count does not match scope")
    if len(supplements) != scope["selected_upstream_incomplete_locale_count"]:
        raise ValueError("G6 supplement locale count does not match scope")

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        path = full_dir / f"{locale}.lang"
        g4.write_lang(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G6 full output failed round-trip validation")

    target_order = list(target)
    for locale, values in sorted(supplements.items()):
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target_order if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G6 supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.10.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.10.2 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

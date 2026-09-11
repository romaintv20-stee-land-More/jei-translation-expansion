#!/usr/bin/env python3
"""Reconstruct Minecraft 1.9 / JEI 3.3.3 addon language resources.

Outputs two resource sets:
- full/: the 63 locales that are absent from JEI upstream and therefore need a
  complete addon-owned locale file;
- supplements/: missing-key-only files for the five selected locales that JEI
  already ships incompletely.

Inherited full locales are reconstructed from G1 + G2 + the audited three-key
G3 delta. Newly selected locales use reviewed full files where available and a
strictly documented English fallback otherwise.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_8_9 as g2

ROOT = Path(__file__).resolve().parents[1]
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.9" / "en_US.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.9-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.9-language-audit.json"
G3_DIR = ROOT / "translations" / "g3-mc1.9"
INHERITED_DELTA = G3_DIR / "inherited-delta.tsv"
SUPPLEMENT_DELTA = G3_DIR / "upstream-supplement-delta.tsv"
NEW_FULL_DIR = G3_DIR / "new-full"
NEW_FULL_POLICY = G3_DIR / "new-full-policy.json"
G2_SUPPLEMENTS = ROOT / "translations" / "g2-mc1.8.9" / "upstream-supplements"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.9"
DEBUG_PREFIX = "description.jei."


def parse_lang(path: Path) -> dict[str, str]:
    return g2.parse_lang(path)


def read_tsv(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or reader.fieldnames[0] != "locale":
            raise ValueError(f"{path}: invalid TSV header")
        keys = reader.fieldnames[1:]
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            locale = (row.get("locale") or "").strip()
            if not locale or locale in rows:
                raise ValueError(f"{path}: empty or duplicate locale {locale!r}")
            values = {key: row.get(key, "") for key in keys}
            if any(value == "" for value in values.values()):
                raise ValueError(f"{path}: empty value in {locale}")
            rows[locale] = values
    return keys, rows


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


def write_lang(path: Path, values: dict[str, str], layout: list[tuple[str, str | None]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for raw, key in layout:
        if key is None:
            lines.append(raw)
        else:
            if key not in values:
                raise ValueError(f"{path}: missing value for {key}")
            lines.append(f"{key}={values[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reconstruct_inherited(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    g2_source = parse_lang(g2.TARGET_SOURCE)
    g2_deltas = g2.load_delta_rows()
    delta_keys, g3_deltas = read_tsv(INHERITED_DELTA)

    added = set(target) - set(g2_source)
    changed = {key for key in set(target) & set(g2_source) if target[key] != g2_source[key]}
    expected_delta_keys = added | changed
    if set(delta_keys) != expected_delta_keys:
        raise ValueError(
            f"G3 inherited delta header mismatch: {sorted(delta_keys)} != "
            f"{sorted(expected_delta_keys)}"
        )

    expected_locales = set(scope["inherited_addon_locales"])
    if set(g3_deltas) != expected_locales:
        raise ValueError("G3 inherited locale set does not match frozen scope")

    complete_locales: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        if locale not in g2_deltas:
            raise ValueError(f"{locale}: missing G2 delta")
        complete_g2 = g2.reconstruct_locale(locale, g2_deltas[locale], set(g2_source))
        complete = {key: value for key, value in complete_g2.items() if key in target}
        complete.update(g3_deltas[locale])
        if set(complete) != set(target):
            raise ValueError(f"{locale}: reconstructed G3 key set mismatch")
        complete_locales[locale] = complete
    return complete_locales


def reconstruct_new_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    policy = json.loads(NEW_FULL_POLICY.read_text(encoding="utf-8"))
    translated = set(policy["translated_ai_assisted_locales"])
    fallbacks = set(policy["documented_english_fallback_locales"])
    expected = set(scope["new_full_translation_locales"])
    if translated & fallbacks:
        raise ValueError("new-full policy has locales in both translated and fallback sets")
    if translated | fallbacks != expected:
        raise ValueError(
            "new-full policy does not cover frozen new-locale scope: "
            f"missing={sorted(expected - (translated | fallbacks))}, "
            f"extra={sorted((translated | fallbacks) - expected)}"
        )

    found_files = {path.stem for path in NEW_FULL_DIR.glob("*.lang")}
    if found_files != translated:
        raise ValueError(
            f"new-full translated file set mismatch: expected={sorted(translated)}, "
            f"found={sorted(found_files)}"
        )

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(translated):
        data = parse_lang(NEW_FULL_DIR / f"{locale}.lang")
        if set(data) != set(target):
            missing = sorted(set(target) - set(data))
            extra = sorted(set(data) - set(target))
            raise ValueError(f"{locale}: full new locale mismatch; missing={missing}, extra={extra}")
        result[locale] = data

    for locale in sorted(fallbacks):
        result[locale] = dict(target)
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict, audit: dict) -> dict[str, dict[str, str]]:
    delta_keys, deltas = read_tsv(SUPPLEMENT_DELTA)
    if set(delta_keys) != {"jei.tooltip.shapeless.recipe", "key.jei.focusSearch"}:
        raise ValueError("unexpected G3 upstream supplement delta key set")

    expected_locales = set(scope["upstream_missing_key_supplement_locales"])
    if set(deltas) != expected_locales:
        raise ValueError("G3 supplement-delta locale set does not match frozen scope")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        old_path = G2_SUPPLEMENTS / f"{locale}.lang"
        if not old_path.is_file():
            raise ValueError(f"{locale}: missing G2 upstream supplement")
        merged = parse_lang(old_path)
        overlap = set(merged) & set(deltas[locale])
        if overlap:
            raise ValueError(f"{locale}: G2 supplement unexpectedly overlaps G3 new keys: {overlap}")
        merged.update(deltas[locale])

        if any(key.startswith(DEBUG_PREFIX) for key in merged):
            raise ValueError(f"{locale}: supplement must not contain debug-only keys")
        if not set(merged) <= set(target):
            raise ValueError(f"{locale}: supplement contains a key not present in target English")

        expected_missing = audit["jei_upstream_locale_completeness"][locale]["missing_normal"]
        if len(merged) != expected_missing:
            raise ValueError(
                f"{locale}: supplement count {len(merged)} does not match audited "
                f"missing-normal count {expected_missing}"
            )
        result[locale] = merged
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    inherited = reconstruct_inherited(target, scope)
    new_full = reconstruct_new_full(target, scope)
    full = {**inherited, **new_full}
    expected_full = set(scope["addon_full_locales"])
    if set(full) != expected_full:
        raise ValueError("combined full-addon locale set does not match frozen scope")

    supplements = reconstruct_supplements(target, scope, audit)

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        path = full_dir / f"{locale}.lang"
        write_lang(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: full output failed round-trip validation")

    # Partial supplements intentionally contain only missing keys and do not use
    # the full source layout, because upstream JEI remains the protected base.
    for locale, values in sorted(supplements.items()):
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="reconstruct to a temporary directory and verify without keeping output",
    )
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.9-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.9 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

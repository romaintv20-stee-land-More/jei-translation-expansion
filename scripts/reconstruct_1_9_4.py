#!/usr/bin/env python3
"""Reconstruct Minecraft 1.9.4 / JEI 3.6.8 addon language resources.

G4 inherits the complete Minecraft 1.9 (G3) addon resources only where the
English key/value pair is unchanged. Four keys require translation/review for
all addon-owned full locales: three added keys and one changed English value.

For JEI-owned locales, supplements are rebuilt against the exact JEI 3.6.8
missing-key sets. This deliberately drops old addon supplement entries when JEI
has gained an upstream translation for them.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_9 as g3

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.9" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.9.4" / "en_US.lang"
G3_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.9-language-scope.json"
G3_AUDIT_PATH = ROOT / "upstream" / "minecraft-1.9-language-audit.json"
G4_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.9.4-language-scope.json"
G4_AUDIT_PATH = ROOT / "upstream" / "minecraft-1.9.4-language-audit.json"
G4_DIR = ROOT / "translations" / "g4-mc1.9.4"
G4_DELTA = G4_DIR / "delta.tsv"
G4_SUPPLEMENT_DELTA_DIR = G4_DIR / "upstream-supplement-delta"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.9.4"
DEBUG_PREFIX = "description.jei."

ADDED_KEYS = {
    "jei.tooltip.cheat.mode",
    "config.jei.advanced.hideLaggyModelsEnabled",
    "config.jei.advanced.hideLaggyModelsEnabled.comment",
}
CHANGED_KEYS = {"gui.jei.category.craftingTable"}

# Exact selected-locale missing-key sets at JEI 3.6.8. de/fi/ko are derived
# from their verified G3 supplement sets plus the three G4 additions. ru/zh are
# intentionally reduced because JEI gained many upstream translations.
RU_CURRENT_MISSING = {
    "config.jei.advanced.hideLaggyModelsEnabled",
    "config.jei.advanced.hideLaggyModelsEnabled.comment",
    "config.jei.advanced.colorSearchEnabled",
    "config.jei.advanced.colorSearchEnabled.comment",
}
ZH_CURRENT_MISSING = set(ADDED_KEYS)
FR_CURRENT_MISSING = set(ADDED_KEYS)


def parse_lang(path: Path) -> dict[str, str]:
    return g3.parse_lang(path)


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


def source_delta_keys(base: dict[str, str], target: dict[str, str]) -> tuple[set[str], set[str], set[str]]:
    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    return added, removed, changed


def reconstruct_g3_full() -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    scope = json.loads(G3_SCOPE_PATH.read_text(encoding="utf-8"))
    inherited = g3.reconstruct_inherited(base, scope)
    new_full = g3.reconstruct_new_full(base, scope)
    full = {**inherited, **new_full}
    if set(full) != set(scope["addon_full_locales"]):
        raise ValueError("G3 full locale set mismatch before G4 inheritance")
    return full


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    added, removed, changed = source_delta_keys(base, target)
    if added != ADDED_KEYS or removed or changed != CHANGED_KEYS:
        raise ValueError(
            "unexpected 1.9 -> 1.9.4 source diff: "
            f"added={sorted(added)}, removed={sorted(removed)}, changed={sorted(changed)}"
        )

    delta_keys, deltas = g3.read_tsv(G4_DELTA)
    expected_delta_keys = added | changed
    if set(delta_keys) != expected_delta_keys:
        raise ValueError(
            f"G4 delta header mismatch: {sorted(delta_keys)} != {sorted(expected_delta_keys)}"
        )

    g3_full = reconstruct_g3_full()
    expected_locales = set(json.loads(G3_SCOPE_PATH.read_text(encoding="utf-8"))["addon_full_locales"])
    if scope["scope_unchanged_from_minecraft_1_9"] is not True:
        raise ValueError("G4 scope must explicitly inherit the unchanged Minecraft 1.9 language scope")
    if scope["addon_full_locale_count"] != len(expected_locales):
        raise ValueError("G4 addon full locale count does not match inherited G3 scope")
    if set(deltas) != expected_locales:
        raise ValueError("G4 delta locale set does not match the 63 G3 addon-owned locales")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        complete = {key: value for key, value in g3_full[locale].items() if key in target}
        complete.update(deltas[locale])
        if set(complete) != set(target):
            missing = sorted(set(target) - set(complete))
            extra = sorted(set(complete) - set(target))
            raise ValueError(f"{locale}: reconstructed G4 key mismatch; missing={missing}, extra={extra}")
        result[locale] = complete
    return result


def expected_supplement_key_sets(g3_supplements: dict[str, dict[str, str]]) -> dict[str, set[str]]:
    return {
        "de_DE": set(g3_supplements["de_DE"]) | ADDED_KEYS,
        "fi_FI": set(g3_supplements["fi_FI"]) | ADDED_KEYS,
        "fr_FR": set(FR_CURRENT_MISSING),
        "ko_KR": set(g3_supplements["ko_KR"]) | ADDED_KEYS,
        "ru_RU": set(RU_CURRENT_MISSING),
        "zh_CN": set(ZH_CURRENT_MISSING),
    }


def reconstruct_supplements(target: dict[str, str], scope: dict, audit: dict) -> dict[str, dict[str, str]]:
    g3_target = parse_lang(BASE_SOURCE)
    g3_scope = json.loads(G3_SCOPE_PATH.read_text(encoding="utf-8"))
    g3_audit = json.loads(G3_AUDIT_PATH.read_text(encoding="utf-8"))
    g3_supplements = g3.reconstruct_supplements(g3_target, g3_scope, g3_audit)

    expected_sets = expected_supplement_key_sets(g3_supplements)
    expected_locales = set(scope["upstream_missing_key_supplement_locales"])
    if expected_locales != set(expected_sets):
        raise ValueError("G4 supplement locale set does not match audited selected upstream locales")

    actual_delta_files = {path.stem for path in G4_SUPPLEMENT_DELTA_DIR.glob("*.lang")}
    if actual_delta_files != expected_locales:
        raise ValueError(
            f"G4 supplement delta file set mismatch: expected={sorted(expected_locales)}, "
            f"actual={sorted(actual_delta_files)}"
        )

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        expected_keys = expected_sets[locale]

        # Reuse only G3 addon-owned values that are still absent from JEI 3.6.8.
        merged = {
            key: value
            for key, value in g3_supplements.get(locale, {}).items()
            if key in expected_keys
        }

        # G4 deltas add newly missing keys and may revise a previously addon-owned
        # missing key whose English meaning changed (ko_KR craftingTable).
        g4_delta = parse_lang(G4_SUPPLEMENT_DELTA_DIR / f"{locale}.lang")
        if not set(g4_delta) <= expected_keys:
            extra = sorted(set(g4_delta) - expected_keys)
            raise ValueError(f"{locale}: G4 supplement delta contains non-missing keys: {extra}")
        merged.update(g4_delta)

        if set(merged) != expected_keys:
            missing = sorted(expected_keys - set(merged))
            extra = sorted(set(merged) - expected_keys)
            raise ValueError(f"{locale}: G4 supplement mismatch; missing={missing}, extra={extra}")
        if any(key.startswith(DEBUG_PREFIX) for key in merged):
            raise ValueError(f"{locale}: supplement must not contain debug-only keys")
        if not set(merged) <= set(target):
            raise ValueError(f"{locale}: supplement contains a key absent from target English")

        expected_count = audit["jei_upstream_locale_completeness"][locale]["missing_normal"]
        if len(merged) != expected_count:
            raise ValueError(
                f"{locale}: supplement count {len(merged)} does not match audited "
                f"missing-normal count {expected_count}"
            )
        result[locale] = merged

    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(G4_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(G4_AUDIT_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope, audit)

    if len(full) != scope["addon_full_locale_count"]:
        raise ValueError("G4 reconstructed full locale count does not match scope")
    if len(supplements) != scope["upstream_missing_key_supplement_locale_count"]:
        raise ValueError("G4 reconstructed supplement count does not match scope")

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
            raise ValueError(f"{locale}: full G4 output failed round-trip validation")

    for locale, values in sorted(supplements.items()):
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G4 supplement output failed round-trip validation")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.9.4-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.9.4 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

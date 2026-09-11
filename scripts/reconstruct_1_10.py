#!/usr/bin/env python3
"""Reconstruct Minecraft 1.10 / JEI 3.7.1 addon language resources.

G5 reuses every unchanged G4 key/value pair, drops the two keys removed from
JEI 3.7.1, and restores gui.jei.category.craftingTable from G3 because its
English meaning reverts exactly from "Crafting" to "Crafting Table".

No new translation is authored in G5.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_9 as g3
import reconstruct_1_9_4 as g4

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.9.4" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.10" / "en_US.lang"
G5_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.10-language-scope.json"
G5_AUDIT_PATH = ROOT / "upstream" / "minecraft-1.10-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g5-mc1.10" / "policy.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.10"
DEBUG_PREFIX = "description.jei."

REMOVED_KEYS = {
    "config.jei.advanced.hideLaggyModelsEnabled",
    "config.jei.advanced.hideLaggyModelsEnabled.comment",
}
CRAFTING_KEY = "gui.jei.category.craftingTable"
CHANGED_KEYS = {CRAFTING_KEY}


def parse_lang(path: Path) -> dict[str, str]:
    return g4.parse_lang(path)


def source_delta_keys(base: dict[str, str], target: dict[str, str]) -> tuple[set[str], set[str], set[str]]:
    return g4.source_delta_keys(base, target)


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


def reconstruct_g4_full() -> dict[str, dict[str, str]]:
    target = parse_lang(BASE_SOURCE)
    scope = json.loads(g4.G4_SCOPE_PATH.read_text(encoding="utf-8"))
    return g4.reconstruct_full(target, scope)


def reconstruct_g3_full() -> dict[str, dict[str, str]]:
    return g4.reconstruct_g3_full()


def reconstruct_full(target: dict[str, str], scope: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    added, removed, changed = source_delta_keys(base, target)
    if added or removed != REMOVED_KEYS or changed != CHANGED_KEYS:
        raise ValueError(
            "unexpected 1.9.4 -> 1.10 source diff: "
            f"added={sorted(added)}, removed={sorted(removed)}, changed={sorted(changed)}"
        )

    # The changed English value is an exact return to the G3 value. That makes
    # the old G3 translation the safest and most reproducible source.
    g3_source = parse_lang(g4.BASE_SOURCE)
    if target[CRAFTING_KEY] != g3_source[CRAFTING_KEY]:
        raise ValueError("1.10 craftingTable English value no longer matches G3 semantic source")

    g4_full = reconstruct_g4_full()
    g3_full = reconstruct_g3_full()
    expected_locales = set(json.loads(g4.G3_SCOPE_PATH.read_text(encoding="utf-8"))["addon_full_locales"])

    if scope["scope_unchanged_from_minecraft_1_9"] is not True:
        raise ValueError("G5 scope must explicitly inherit the frozen Minecraft 1.9 language scope")
    if scope["addon_full_locale_count"] != len(expected_locales):
        raise ValueError("G5 addon full locale count does not match inherited scope")
    if set(g4_full) != expected_locales or set(g3_full) != expected_locales:
        raise ValueError("G3/G4 full locale sets do not match the G5 inherited scope")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        complete = {key: value for key, value in g4_full[locale].items() if key in target}
        complete[CRAFTING_KEY] = g3_full[locale][CRAFTING_KEY]
        if set(complete) != set(target):
            missing = sorted(set(target) - set(complete))
            extra = sorted(set(complete) - set(target))
            raise ValueError(f"{locale}: reconstructed G5 key mismatch; missing={missing}, extra={extra}")
        result[locale] = complete
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict, audit: dict) -> dict[str, dict[str, str]]:
    g4_target = parse_lang(BASE_SOURCE)
    g4_scope = json.loads(g4.G4_SCOPE_PATH.read_text(encoding="utf-8"))
    g4_audit = json.loads(g4.G4_AUDIT_PATH.read_text(encoding="utf-8"))
    g4_supplements = g4.reconstruct_supplements(g4_target, g4_scope, g4_audit)

    g3_target = parse_lang(g4.BASE_SOURCE)
    g3_scope = json.loads(g4.G3_SCOPE_PATH.read_text(encoding="utf-8"))
    g3_audit = json.loads(g4.G3_AUDIT_PATH.read_text(encoding="utf-8"))
    g3_supplements = g3.reconstruct_supplements(g3_target, g3_scope, g3_audit)

    expected_locales = set(scope["upstream_missing_key_supplement_locales"])
    if expected_locales != set(g4_supplements):
        raise ValueError("G5 supplement locale set differs from G4 selected upstream locale set")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected_locales):
        merged = {key: value for key, value in g4_supplements[locale].items() if key in target}

        # ko_KR does not own this key upstream. G4 changed it to the generic
        # "Crafting" translation; G5 restores the G3 "Crafting Table" value.
        if CRAFTING_KEY in merged:
            if CRAFTING_KEY not in g3_supplements.get(locale, {}):
                raise ValueError(f"{locale}: missing G3 semantic-reversion source for {CRAFTING_KEY}")
            merged[CRAFTING_KEY] = g3_supplements[locale][CRAFTING_KEY]

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

    # High-value ownership/semantic regression guards.
    if set(result["ru_RU"]) != {
        "config.jei.advanced.colorSearchEnabled",
        "config.jei.advanced.colorSearchEnabled.comment",
    }:
        raise ValueError("ru_RU G5 supplement is not the exact two-key color-search set")
    if set(result["fr_FR"]) != {"jei.tooltip.cheat.mode"}:
        raise ValueError("fr_FR G5 supplement must contain only jei.tooltip.cheat.mode")
    if set(result["zh_CN"]) != {"jei.tooltip.cheat.mode"}:
        raise ValueError("zh_CN G5 supplement must contain only jei.tooltip.cheat.mode")
    if result["ko_KR"].get(CRAFTING_KEY) != "제작대":
        raise ValueError("ko_KR G5 craftingTable translation was not restored from G3")

    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(G5_SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(G5_AUDIT_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    full = reconstruct_full(target, scope)
    supplements = reconstruct_supplements(target, scope, audit)

    if len(full) != scope["addon_full_locale_count"]:
        raise ValueError("G5 reconstructed full locale count does not match scope")
    if len(supplements) != scope["upstream_missing_key_supplement_locale_count"]:
        raise ValueError("G5 reconstructed supplement count does not match scope")

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
            raise ValueError(f"{locale}: full G5 output failed round-trip validation")

    for locale, values in sorted(supplements.items()):
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G5 supplement output failed round-trip validation")

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
        with tempfile.TemporaryDirectory(prefix="jei-1.10-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.10 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

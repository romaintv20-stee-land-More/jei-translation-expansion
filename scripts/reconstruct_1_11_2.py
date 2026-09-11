#!/usr/bin/env python3
"""Reconstruct Minecraft 1.11.2 / JEI 4.5.1 addon language resources.

G8 reuses every G7 translation whose JEI key and English value are unchanged.
Seven new keys plus one changed English meaning are conservatively realized as
target-English fallbacks for addon-owned full locales. Upstream supplements are
rebuilt against the exact JEI 4.5.1 missing-key sets: unchanged missing keys
reuse deterministic G7 supplement values when available, while G8 reviewed
keys use target English fallback.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import reconstruct_1_11 as g7

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.11" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.11.2" / "en_us.lang"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.11.2-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.11.2-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g8-mc1.11.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.11-to-1.11.2.json"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.11.2"
DEBUG_PREFIX = "description.jei."


def parse_lang(path: Path) -> dict[str, str]:
    return g7.parse_lang(path)


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


def reconstruct_g7_full() -> dict[str, dict[str, str]]:
    target = parse_lang(g7.TARGET_SOURCE)
    scope = json.loads(g7.SCOPE_PATH.read_text(encoding="utf-8"))
    return g7.reconstruct_full(target, scope)


def reconstruct_g7_supplements() -> dict[str, dict[str, str]]:
    target = parse_lang(g7.TARGET_SOURCE)
    scope = json.loads(g7.SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(g7.AUDIT_PATH.read_text(encoding="utf-8"))
    return g7.reconstruct_supplements(target, scope, audit)


def diff_sets(base: dict[str, str], target: dict[str, str], diff: dict) -> tuple[set[str], set[str], set[str]]:
    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    reviewed = set(diff["reviewed_added_or_changed_keys"])
    removed = set(diff["removed_keys"])
    if len(unchanged) != 85 or len(reviewed) != 8 or len(removed) != 1:
        raise ValueError("G8 diff-set counts do not match frozen 85/8/1 policy")
    if set(target) != unchanged | reviewed | ({key for key in target if key.startswith(DEBUG_PREFIX)} - unchanged - reviewed):
        # Debug keys are already in unchanged, so this mainly protects against an unreviewed target key.
        unexpected = set(target) - unchanged - reviewed
        if unexpected:
            raise ValueError(f"unreviewed G8 target keys: {sorted(unexpected)}")
    return unchanged, reviewed, removed


def reconstruct_full(target: dict[str, str], scope: dict, diff: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    unchanged, reviewed, _removed = diff_sets(base, target, diff)
    g7_full = reconstruct_g7_full()
    expected = set(scope["addon_full_locales"])
    if expected != set(g7_full):
        raise ValueError("G8 full addon locale ownership differs unexpectedly from G7")

    result: dict[str, dict[str, str]] = {}
    for locale in sorted(expected):
        base_values = g7_full[locale]
        values: dict[str, str] = {}
        for key, english in target.items():
            if key.startswith(DEBUG_PREFIX):
                values[key] = english
            elif key in unchanged:
                if key not in base_values:
                    raise ValueError(f"{locale}: unchanged G8 key missing from G7 full file: {key}")
                values[key] = base_values[key]
            elif key in reviewed:
                values[key] = english
            else:
                raise ValueError(f"{locale}: G8 target key has no realization rule: {key}")
        if set(values) != set(target):
            raise ValueError(f"{locale}: G8 full reconstruction key mismatch")
        result[locale] = values
    return result


def reconstruct_supplements(target: dict[str, str], scope: dict, audit: dict, diff: dict) -> dict[str, dict[str, str]]:
    base = parse_lang(BASE_SOURCE)
    unchanged, reviewed, _removed = diff_sets(base, target, diff)
    g7_supplements = reconstruct_g7_supplements()
    expected = set(scope["selected_upstream_incomplete_locales"])
    completeness = audit["selected_upstream_locale_completeness"]
    result: dict[str, dict[str, str]] = {}

    for locale in sorted(expected):
        missing = set(completeness[locale]["missing_normal_keys"])
        if not missing:
            raise ValueError(f"{locale}: marked incomplete but audit missing set is empty")
        old_values = g7_supplements.get(locale, {})
        values: dict[str, str] = {}
        for key in sorted(missing):
            if key.startswith(DEBUG_PREFIX):
                raise ValueError(f"{locale}: audit unexpectedly requests debug-only supplement key {key}")
            if key in unchanged and key in old_values:
                values[key] = old_values[key]
            elif key in reviewed:
                values[key] = target[key]
            elif key in unchanged:
                # This would mean JEI dropped an old upstream translation that the project did not
                # previously own. English is the only deterministic safe fallback.
                values[key] = target[key]
            else:
                raise ValueError(f"{locale}: missing target key has no G8 supplement rule: {key}")
        if set(values) != missing:
            raise ValueError(f"{locale}: G8 supplement does not equal exact audited missing set")
        result[locale] = values

    if set(result) != expected:
        raise ValueError("G8 supplement locale set does not match frozen scope")
    return result


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int, int]:
    target = parse_lang(TARGET_SOURCE)
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    layout = target_layout()

    if policy["resource_filename_case"] != "lowercase":
        raise ValueError("G8 policy must require lowercase resource filenames")
    if policy["unchanged_key_and_value_count"] != 85 or len(policy["reviewed_keys"]) != 8:
        raise ValueError("G8 policy diff counts changed unexpectedly")

    full = reconstruct_full(target, scope, diff)
    supplements = reconstruct_supplements(target, scope, audit, diff)
    if len(full) != 52 or len(supplements) != 19 or len(target) != 93:
        raise ValueError(
            f"G8 reconstruction counts changed: full={len(full)} supplements={len(supplements)} keys={len(target)}"
        )

    if clean and output.exists():
        shutil.rmtree(output)
    full_dir = output / "full" / "assets" / "jei" / "lang"
    supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
    full_dir.mkdir(parents=True, exist_ok=True)
    supplement_dir.mkdir(parents=True, exist_ok=True)

    for locale, values in sorted(full.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G8 output locale is not lowercase")
        path = full_dir / f"{locale}.lang"
        g7.g6.g4.write_lang(path, values, layout)
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G8 full output failed round-trip validation")

    target_order = list(target)
    for locale, values in sorted(supplements.items()):
        if locale != locale.lower():
            raise ValueError(f"{locale}: G8 supplement locale is not lowercase")
        path = supplement_dir / f"{locale}.lang"
        lines = [f"{key}={values[key]}" for key in target_order if key in values]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if parse_lang(path) != values:
            raise ValueError(f"{locale}: G8 supplement output failed round-trip validation")

    return len(full), len(supplements), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.11.2-reconstruct-") as tmp:
            full_count, supplement_count, key_count = reconstruct_all(Path(tmp))
        print("PASS: Minecraft 1.11.2 deterministic reconstruction")
    else:
        full_count, supplement_count, key_count = reconstruct_all(args.output)
        print(f"Output: {args.output}")

    print(f"Full addon locales: {full_count}")
    print(f"Missing-key-only upstream supplements: {supplement_count}")
    print(f"Keys per complete locale: {key_count}")
    print("Reviewed G8 keys use documented target-English fallback when project-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

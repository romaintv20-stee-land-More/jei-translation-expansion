#!/usr/bin/env python3
"""Validate the G4 Minecraft 1.9.4 / JEI 3.6.8 translation deltas."""
from __future__ import annotations

import json
from pathlib import Path

import reconstruct_1_9 as g3
import reconstruct_1_9_4 as g4

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "translations" / "g4-mc1.9.4" / "policy.json"


def main() -> int:
    errors: list[str] = []
    base = g4.parse_lang(g4.BASE_SOURCE)
    target = g4.parse_lang(g4.TARGET_SOURCE)
    g3_scope = json.loads(g4.G3_SCOPE_PATH.read_text(encoding="utf-8"))
    g4_scope = json.loads(g4.G4_SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    added, removed, changed = g4.source_delta_keys(base, target)
    expected_delta_keys = added | changed
    if added != g4.ADDED_KEYS:
        errors.append(f"unexpected added keys: {sorted(added)}")
    if removed:
        errors.append(f"unexpected removed keys: {sorted(removed)}")
    if changed != g4.CHANGED_KEYS:
        errors.append(f"unexpected changed-value keys: {sorted(changed)}")

    delta_keys, rows = g3.read_tsv(g4.G4_DELTA)
    if set(delta_keys) != expected_delta_keys:
        errors.append(
            f"delta header mismatch: expected={sorted(expected_delta_keys)}, actual={sorted(delta_keys)}"
        )

    expected_locales = set(g3_scope["addon_full_locales"])
    if set(rows) != expected_locales:
        errors.append(
            f"delta locale set mismatch: missing={sorted(expected_locales - set(rows))}, "
            f"extra={sorted(set(rows) - expected_locales)}"
        )

    fallback_locales = set(policy["documented_full_english_fallback_locales"])
    if fallback_locales != set(g4_scope["documented_full_english_fallback_locales"]):
        errors.append("policy fallback locale set differs from G4 scope")
    if len(fallback_locales) != policy["full_english_fallback_locale_count"]:
        errors.append("policy fallback locale count mismatch")

    for locale, values in rows.items():
        if set(values) != expected_delta_keys:
            errors.append(f"{locale}: delta key set mismatch")
            continue
        english_equal = sum(values[key] == target[key] for key in expected_delta_keys)
        if locale in fallback_locales:
            if english_equal != len(expected_delta_keys):
                errors.append(f"{locale}: documented fallback G4 delta is not fully English")
        elif english_equal == len(expected_delta_keys):
            errors.append(f"{locale}: unexpected full-English G4 delta")

    expected_supplement_locales = set(g4_scope["upstream_missing_key_supplement_locales"])
    actual_supplement_locales = {path.stem for path in g4.G4_SUPPLEMENT_DELTA_DIR.glob("*.lang")}
    if actual_supplement_locales != expected_supplement_locales:
        errors.append(
            "G4 upstream supplement delta file set mismatch: "
            f"expected={sorted(expected_supplement_locales)}, actual={sorted(actual_supplement_locales)}"
        )

    # Validate each G4 supplement-delta file against the keys that are allowed to
    # change/add at this generation. Older still-missing keys are inherited by
    # reconstruct_1_9_4.py and should not be needlessly duplicated here.
    allowed_delta_keys = {
        "de_DE": set(g4.ADDED_KEYS),
        "fi_FI": set(g4.ADDED_KEYS),
        "fr_FR": set(g4.ADDED_KEYS),
        "ko_KR": set(g4.ADDED_KEYS) | set(g4.CHANGED_KEYS),
        "ru_RU": {
            "config.jei.advanced.hideLaggyModelsEnabled",
            "config.jei.advanced.hideLaggyModelsEnabled.comment",
        },
        "zh_CN": set(g4.ADDED_KEYS),
    }
    for locale in sorted(expected_supplement_locales):
        values = g4.parse_lang(g4.G4_SUPPLEMENT_DELTA_DIR / f"{locale}.lang")
        if set(values) != allowed_delta_keys[locale]:
            errors.append(
                f"{locale}: supplement delta keys mismatch: expected={sorted(allowed_delta_keys[locale])}, "
                f"actual={sorted(values)}"
            )
        for key, value in values.items():
            if not value:
                errors.append(f"{locale}: empty supplement delta value for {key}")
            if key not in target:
                errors.append(f"{locale}: unknown target key {key}")

    if policy["g4_reviewed_keys_per_full_locale"] != len(expected_delta_keys):
        errors.append("policy G4 reviewed-key count mismatch")
    if set(policy["g4_reviewed_keys"]) != expected_delta_keys:
        errors.append("policy G4 reviewed-key list mismatch")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.9.4 delta validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.9.4 / JEI 3.6.8 G4 delta QA")
    print(f"Full addon locales: {len(rows)}")
    print(f"Reviewed entries per full locale: {len(expected_delta_keys)}")
    print(f"Documented full-English fallbacks: {len(fallback_locales)}")
    print(f"Upstream supplement delta locales: {len(expected_supplement_locales)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

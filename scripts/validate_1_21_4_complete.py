#!/usr/bin/env python3
"""Validate complete reconstructed G40 / Minecraft 1.21.4 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_4 as g40


def main() -> int:
    errors: list[str] = []
    target = g40.parse_json(g40.TARGET_SOURCE)
    normal_keys = {key for key in target if not key.startswith(g40.DEBUG_PREFIX)}
    scope = json.loads(g40.SCOPE_PATH.read_text(encoding="utf-8"))
    full_expected = set(scope["addon_full_locales"])
    supplement_expected = set(scope["selected_upstream_incomplete_locales"])
    complete_upstream = set(scope["selected_upstream_complete_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])

    with tempfile.TemporaryDirectory(prefix="jei-g40-complete-") as tmp:
        output = Path(tmp)
        try:
            full_count, supplement_count, key_count, provenance = g40.reconstruct_all(output)
        except Exception as exc:
            print(f"FAIL: G40 reconstruction raised: {exc}")
            return 1

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {path.stem: path for path in full_dir.glob("*.json")}
        supplement_files = {path.stem: path for path in supplement_dir.glob("*.json")}

        if (full_count, supplement_count, key_count) != (64, 25, 288):
            errors.append(f"reconstruction counts changed: {full_count}/{supplement_count}/{key_count}")
        if set(full_files) != full_expected:
            errors.append("reconstructed full locale set differs from frozen scope")
        if set(supplement_files) != supplement_expected:
            errors.append("reconstructed supplement locale set differs from frozen scope")
        if set(full_files) & set(supplement_files):
            errors.append("reconstructed full/supplement locale ownership overlaps")

        for locale, path in sorted(full_files.items()):
            values = g40.parse_json(path)
            if set(values) != set(target):
                missing = sorted(set(target) - set(values))
                extra = sorted(set(values) - set(target))
                errors.append(f"{locale}: full key set mismatch missing={missing} extra={extra}")
                continue
            if g40.REMOVED_G40_KEYS & set(values):
                errors.append(f"{locale}: removed generic Fuel key leaked into G40 full output")
            for key, english in target.items():
                value = values[key]
                if key.startswith(g40.DEBUG_PREFIX) and value != english:
                    errors.append(f"{locale}: debug-only key is not exact G40 English: {key}")
                if not g40.preserves_runtime_literals(english, value):
                    errors.append(f"{locale}: runtime literal mismatch at {key}")
            if locale in fallback_locales and values != target:
                errors.append(f"{locale}: documented full-English fallback locale is not exact target English")

        for locale, path in sorted(supplement_files.items()):
            values = g40.parse_json(path)
            try:
                upstream = g40.fetch_upstream_json(g40.G40_COMMIT, locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch pinned upstream locale: {exc}")
                continue
            expected_missing = normal_keys - set(upstream)
            if set(values) != expected_missing:
                missing = sorted(expected_missing - set(values))
                extra = sorted(set(values) - expected_missing)
                errors.append(f"{locale}: supplement mismatch missing={missing} extra={extra}")
            if set(values) & set(upstream):
                errors.append(f"{locale}: supplement overrides upstream-owned key")
            if any(key.startswith(g40.DEBUG_PREFIX) for key in values):
                errors.append(f"{locale}: supplement contains debug-only key")
            if g40.REMOVED_G40_KEYS & set(values):
                errors.append(f"{locale}: removed generic Fuel key leaked into supplement")
            for key, value in values.items():
                if key not in target:
                    errors.append(f"{locale}: supplement contains non-target key {key}")
                    continue
                if not g40.preserves_runtime_literals(target[key], value):
                    errors.append(f"{locale}: supplement runtime literal mismatch at {key}")
            merged_normal = normal_keys & (set(upstream) | set(values))
            if merged_normal != normal_keys:
                errors.append(f"{locale}: upstream + supplement does not cover all G40 normal keys")

        ja = g40.parse_json(supplement_files["ja_jp"]) if "ja_jp" in supplement_files else {}
        if set(ja) != g40.NEW_G40_KEYS:
            errors.append("ja_jp supplement must contain exactly the three new fuel-category keys")

        for locale in sorted(complete_upstream):
            try:
                upstream = g40.fetch_upstream_json(g40.G40_COMMIT, locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch complete pinned upstream locale: {exc}")
                continue
            missing = normal_keys - set(upstream)
            if missing:
                errors.append(f"{locale}: complete upstream locale is missing {len(missing)} normal keys")

        if full_expected | supplement_expected | complete_upstream != (
            set(scope["addon_full_locales"])
            | set(scope["selected_upstream_incomplete_locales"])
            | set(scope["selected_upstream_complete_locales"])
        ):
            errors.append("selected ownership union changed unexpectedly")
        if len(full_expected | supplement_expected | complete_upstream) != 90:
            errors.append("G40 selected ownership does not total 90 locales")

        prov_path = output / "provenance.json"
        if not prov_path.exists():
            errors.append("G40 provenance.json was not generated")
        else:
            disk_provenance = json.loads(prov_path.read_text(encoding="utf-8"))
            if disk_provenance != provenance:
                errors.append("G40 provenance return value differs from written provenance.json")
            if disk_provenance.get("generation") != "g40-mc1.21.4":
                errors.append("G40 provenance generation id is wrong")
            if disk_provenance.get("cross_key_reuse_allowed") is not False:
                errors.append("G40 provenance must explicitly forbid cross-key reuse")
            if disk_provenance.get("removed_generic_fuel_key_reused_for_new_keys") is not False:
                errors.append("G40 provenance must record that removed generic Fuel was not reused for new keys")

    if errors:
        print(f"FAIL: {len(errors)} G40 complete-resource validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.4 / JEI 20.0.0 complete reconstructed resources")
    print("64 addon-full locales + 25 missing-key-only supplements + 1 complete upstream locale")
    print("288 keys per complete addon-owned locale; 282 normal target keys")
    print("Runtime placeholders and fixed technical tokens are preserved")
    print("The removed generic Fuel key is never emitted by G40 addon resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

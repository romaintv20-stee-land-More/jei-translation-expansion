#!/usr/bin/env python3
"""Validate complete reconstructed G41 / Minecraft 1.21.5 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_5 as g41

EXPECTED_FIVE_MISSING = set(g41.g40.NEW_G40_KEYS) | set(g41.NEW_G41_KEYS)


def main() -> int:
    errors: list[str] = []
    target = g41.parse_json(g41.TARGET_SOURCE)
    normal_keys = {key for key in target if not key.startswith(g41.DEBUG_PREFIX)}
    scope = json.loads(g41.SCOPE_PATH.read_text(encoding="utf-8"))
    full_expected = set(scope["addon_full_locales"])
    supplement_expected = set(scope["selected_upstream_incomplete_locales"])
    complete_upstream = set(scope["selected_upstream_complete_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])

    with tempfile.TemporaryDirectory(prefix="jei-g41-complete-") as tmp:
        output = Path(tmp)
        try:
            full_count, supplement_count, key_count, provenance = g41.reconstruct_all(output)
        except Exception as exc:
            print(f"FAIL: G41 reconstruction raised: {exc}")
            return 1

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {path.stem: path for path in full_dir.glob("*.json")}
        supplement_files = {path.stem: path for path in supplement_dir.glob("*.json")}

        if (full_count, supplement_count, key_count) != (65, 24, 290):
            errors.append(f"reconstruction counts changed: {full_count}/{supplement_count}/{key_count}")
        if set(full_files) != full_expected:
            errors.append("reconstructed full locale set differs from frozen scope")
        if set(supplement_files) != supplement_expected:
            errors.append("reconstructed supplement locale set differs from frozen scope")
        if set(full_files) & set(supplement_files):
            errors.append("reconstructed full/supplement locale ownership overlaps")
        if "uk_ua" not in full_files or "uk_ua" in supplement_files:
            errors.append("uk_ua must be emitted only as a full override")

        for locale, path in sorted(full_files.items()):
            values = g41.parse_json(path)
            if set(values) != set(target):
                missing = sorted(set(target) - set(values))
                extra = sorted(set(values) - set(target))
                errors.append(f"{locale}: full key set mismatch missing={missing} extra={extra}")
                continue
            for key, english in target.items():
                value = values[key]
                if key.startswith(g41.DEBUG_PREFIX) and value != english:
                    errors.append(f"{locale}: debug-only key is not exact G41 English: {key}")
                if not g41.preserves_runtime_literals(english, value):
                    errors.append(f"{locale}: runtime literal mismatch at {key}")
            if locale in fallback_locales and values != target:
                errors.append(f"{locale}: documented full-English fallback locale is not exact target English")

        if "uk_ua" in full_files:
            uk = g41.parse_json(full_files["uk_ua"])
            repaired_upstream = g41.fetch_g41_upstream("uk_ua")
            previous = g41.g40_combined_locale("uk_ua")
            for key in sorted(normal_keys & set(repaired_upstream)):
                if g41.preserves_runtime_literals(target[key], repaired_upstream[key]) and uk[key] != repaired_upstream[key]:
                    errors.append(f"uk_ua: repaired pinned upstream value was not preserved at {key}")
            for key in sorted((normal_keys - set(repaired_upstream)) & set(g41.semantic_partition()[0])):
                expected, _ = g41.resolve_unchanged(previous[key], target[key])
                if uk[key] != expected:
                    errors.append(f"uk_ua: unchanged missing key did not inherit exact safe G40 combined value at {key}")
            for key in g41.NEW_G41_KEYS:
                if uk[key] != target[key]:
                    errors.append(f"uk_ua: new G41 key must use exact English fallback at {key}")

        for locale, path in sorted(supplement_files.items()):
            values = g41.parse_json(path)
            try:
                upstream = g41.fetch_g41_upstream(locale)
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
            if any(key.startswith(g41.DEBUG_PREFIX) for key in values):
                errors.append(f"{locale}: supplement contains debug-only key")
            for key, value in values.items():
                if key not in target:
                    errors.append(f"{locale}: supplement contains non-target key {key}")
                    continue
                if not g41.preserves_runtime_literals(target[key], value):
                    errors.append(f"{locale}: supplement runtime literal mismatch at {key}")
            merged_normal = normal_keys & (set(upstream) | set(values))
            if merged_normal != normal_keys:
                errors.append(f"{locale}: upstream + supplement does not cover all G41 normal keys")

        if "ja_jp" in supplement_files:
            ja = g41.parse_json(supplement_files["ja_jp"])
            if set(ja) != EXPECTED_FIVE_MISSING:
                errors.append(f"ja_jp supplement must contain exactly the five frozen keys, got {sorted(ja)}")
            for key in g41.NEW_G41_KEYS:
                if ja.get(key) != target[key]:
                    errors.append(f"ja_jp: new G41 key must use exact English fallback at {key}")

        for locale in sorted(complete_upstream):
            try:
                upstream = g41.fetch_g41_upstream(locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch complete pinned upstream locale: {exc}")
                continue
            missing = normal_keys - set(upstream)
            if missing:
                errors.append(f"{locale}: complete upstream locale is missing {len(missing)} normal keys")

        if len(full_expected | supplement_expected | complete_upstream) != 90:
            errors.append("G41 selected ownership does not total 90 locales")

        prov_path = output / "provenance.json"
        if not prov_path.exists():
            errors.append("G41 provenance.json was not generated")
        else:
            disk_provenance = json.loads(prov_path.read_text(encoding="utf-8"))
            if disk_provenance != provenance:
                errors.append("G41 provenance return value differs from written provenance.json")
            if disk_provenance.get("generation") != "g41-mc1.21.5":
                errors.append("G41 provenance generation id is wrong")
            if disk_provenance.get("cross_key_reuse_allowed") is not False:
                errors.append("G41 provenance must explicitly forbid cross-key reuse")
            if disk_provenance.get("malformed_upstream_full_overrides") != ["uk_ua"]:
                errors.append("G41 provenance must record the uk_ua full repair override")
            if set(disk_provenance.get("new_g41_keys", [])) != g41.NEW_G41_KEYS:
                errors.append("G41 provenance new-key set changed")

    if errors:
        print(f"FAIL: {len(errors)} G41 complete-resource validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.5 / JEI 21.4.0 complete reconstructed resources")
    print("65 addon/full-override locales + 24 missing-key-only supplements + 1 complete upstream locale")
    print("290 keys per complete addon-owned locale; 284 normal target keys")
    print("Runtime placeholders and fixed technical tokens are preserved")
    print("uk_ua is a valid full repair override; ja_jp is a five-key missing-only supplement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate complete reconstructed G42 / Minecraft 1.21.6 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_6 as g42


def main() -> int:
    errors: list[str] = []
    target = g42.parse_json(g42.TARGET_SOURCE)
    normal_keys = {key for key in target if not key.startswith(g42.DEBUG_PREFIX)}
    scope = json.loads(g42.SCOPE_PATH.read_text(encoding="utf-8"))
    full_expected = set(scope["addon_full_locales"])
    supplement_expected = set(scope["selected_upstream_incomplete_locales"])
    complete_upstream = set(scope["selected_upstream_complete_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])

    with tempfile.TemporaryDirectory(prefix="jei-g42-complete-") as tmp:
        output = Path(tmp)
        try:
            full_count, supplement_count, key_count, provenance = g42.reconstruct_all(output)
        except Exception as exc:
            print(f"FAIL: G42 reconstruction raised: {exc}")
            return 1

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {path.stem: path for path in full_dir.glob("*.json")}
        supplement_files = {path.stem: path for path in supplement_dir.glob("*.json")}

        if (full_count, supplement_count, key_count) != (len(full_expected), len(supplement_expected), 289):
            errors.append(
                f"reconstruction counts changed: full={full_count}/{len(full_expected)} "
                f"supplements={supplement_count}/{len(supplement_expected)} keys={key_count}/289"
            )
        if set(full_files) != full_expected:
            errors.append("reconstructed full locale set differs from frozen scope")
        if set(supplement_files) != supplement_expected:
            errors.append("reconstructed supplement locale set differs from frozen scope")
        if set(full_files) & set(supplement_files):
            errors.append("reconstructed full/supplement locale ownership overlaps")
        if len(full_expected | supplement_expected | complete_upstream) != 90:
            errors.append("G42 selected ownership does not total 90 locales")
        if "uk_ua" not in full_files or "uk_ua" in supplement_files:
            errors.append("uk_ua must be emitted only as a full override")

        for locale, path in sorted(full_files.items()):
            values = g42.parse_json(path)
            if set(values) != set(target):
                missing = sorted(set(target) - set(values))
                extra = sorted(set(values) - set(target))
                errors.append(f"{locale}: full key set mismatch missing={missing} extra={extra}")
                continue
            if set(values) & g42.REMOVED_G42_KEYS:
                errors.append(f"{locale}: removed G42 key leaked into full output")
            for key, english in target.items():
                value = values[key]
                if key.startswith(g42.DEBUG_PREFIX) and value != english:
                    errors.append(f"{locale}: debug-only key is not exact G42 English: {key}")
                if not g42.preserves_runtime_literals(english, value):
                    errors.append(f"{locale}: runtime literal mismatch at {key}")
            if locale in fallback_locales and values != target:
                errors.append(f"{locale}: documented full-English fallback locale is not exact target English")

        if "uk_ua" in full_files:
            uk = g42.parse_json(full_files["uk_ua"])
            repaired_upstream = g42.fetch_g42_upstream("uk_ua")
            previous = g42.g41_combined_locale("uk_ua")
            unchanged = g42.semantic_partition()[0]
            for key in sorted(normal_keys & set(repaired_upstream)):
                if g42.preserves_runtime_literals(target[key], repaired_upstream[key]) and uk[key] != repaired_upstream[key]:
                    errors.append(f"uk_ua: repaired pinned upstream value was not preserved at {key}")
            for key in sorted((normal_keys - set(repaired_upstream)) & unchanged):
                expected, _ = g42.resolve_unchanged(previous[key], target[key])
                if uk[key] != expected:
                    errors.append(f"uk_ua: unchanged missing key did not inherit exact safe G41 combined value at {key}")
            if set(uk) & g42.REMOVED_G42_KEYS:
                errors.append("uk_ua: removed grindstone-experience key leaked into repaired full override")

        for locale, path in sorted(supplement_files.items()):
            values = g42.parse_json(path)
            try:
                upstream = g42.fetch_g42_upstream(locale)
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
            if set(values) & g42.REMOVED_G42_KEYS:
                errors.append(f"{locale}: removed G42 key leaked into supplement")
            if any(key.startswith(g42.DEBUG_PREFIX) for key in values):
                errors.append(f"{locale}: supplement contains debug-only key")
            previous = g42.g41_combined_locale(locale)
            for key, value in values.items():
                if key not in target:
                    errors.append(f"{locale}: supplement contains non-target key {key}")
                    continue
                if not g42.preserves_runtime_literals(target[key], value):
                    errors.append(f"{locale}: supplement runtime literal mismatch at {key}")
                    continue
                expected, _ = g42.resolve_unchanged(previous[key], target[key])
                if value != expected:
                    errors.append(f"{locale}: supplement does not reuse exact safe G41 same-key value at {key}")
            merged_normal = normal_keys & (set(upstream) | set(values))
            if merged_normal != normal_keys:
                errors.append(f"{locale}: upstream + supplement does not cover all G42 normal keys")

        for locale in sorted(complete_upstream):
            try:
                upstream = g42.fetch_g42_upstream(locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch complete pinned upstream locale: {exc}")
                continue
            missing = normal_keys - set(upstream)
            if missing:
                errors.append(f"{locale}: complete upstream locale is missing {len(missing)} normal keys")

        prov_path = output / "provenance.json"
        if not prov_path.exists():
            errors.append("G42 provenance.json was not generated")
        else:
            disk_provenance = json.loads(prov_path.read_text(encoding="utf-8"))
            if disk_provenance != provenance:
                errors.append("G42 provenance return value differs from written provenance.json")
            if disk_provenance.get("generation") != "g42-mc1.21.6":
                errors.append("G42 provenance generation id is wrong")
            if disk_provenance.get("cross_key_reuse_allowed") is not False:
                errors.append("G42 provenance must explicitly forbid cross-key reuse")
            if disk_provenance.get("malformed_upstream_full_overrides") != ["uk_ua"]:
                errors.append("G42 provenance must record the uk_ua full repair override")
            if set(disk_provenance.get("removed_g42_keys", [])) != g42.REMOVED_G42_KEYS:
                errors.append("G42 provenance removed-key set changed")

    if errors:
        print(f"FAIL: {len(errors)} G42 complete-resource validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.21.6 / JEI 22.0.0 complete reconstructed resources")
    print(f"{len(full_expected)} addon/full-override locales + {len(supplement_expected)} missing-key-only supplements + {len(complete_upstream)} complete upstream locales")
    print("289 keys per complete addon-owned locale; 283 normal target keys")
    print("Runtime placeholders and fixed technical tokens are preserved")
    print("uk_ua remains a valid full repair override; the removed G41 semantic key is not emitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

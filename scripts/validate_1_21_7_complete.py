#!/usr/bin/env python3
"""Validate complete reconstructed G43 / Minecraft 1.21.7 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_7 as g43


def expected_owned_value(locale: str, key: str, english: str) -> str:
    unchanged, added, _, _ = g43.semantic_partition()
    if key in unchanged:
        return g43.resolve_unchanged(locale, key, english)[0]
    if key in added:
        return g43.resolve_added(locale, key, english)[0]
    raise ValueError(f"{locale}: unresolved G43 key {key}")


def main() -> int:
    errors: list[str] = []
    target = g43.parse_json(g43.TARGET_SOURCE)
    normal_keys = {k for k in target if not k.startswith(g43.DEBUG_PREFIX)}
    scope = json.loads(g43.SCOPE_PATH.read_text(encoding="utf-8"))
    full_expected = set(scope["addon_full_locales"])
    supplement_expected = set(scope["selected_upstream_incomplete_locales"])
    complete_upstream = set(scope["selected_upstream_complete_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])

    with tempfile.TemporaryDirectory(prefix="jei-g43-complete-") as tmp:
        output = Path(tmp)
        try:
            full_count, supplement_count, key_count, provenance = g43.reconstruct_all(output)
        except Exception as exc:
            print(f"FAIL: G43 reconstruction raised: {exc}")
            return 1

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {p.stem:p for p in full_dir.glob("*.json")}
        supplement_files = {p.stem:p for p in supplement_dir.glob("*.json")}

        if (full_count, supplement_count, key_count) != (len(full_expected), len(supplement_expected), 291):
            errors.append(
                f"reconstruction counts changed: full={full_count}/{len(full_expected)} "
                f"supplements={supplement_count}/{len(supplement_expected)} keys={key_count}/291"
            )
        if set(full_files) != full_expected:
            errors.append("reconstructed full locale set differs from frozen scope")
        if set(supplement_files) != supplement_expected:
            errors.append("reconstructed supplement locale set differs from frozen scope")
        if set(full_files) & set(supplement_files):
            errors.append("reconstructed full/supplement locale ownership overlaps")
        if len(full_expected | supplement_expected | complete_upstream) != 90:
            errors.append("G43 selected ownership does not total 90 locales")
        if "uk_ua" not in full_files or "uk_ua" in supplement_files:
            errors.append("uk_ua must be emitted only as a full repair override")

        for locale, path in sorted(full_files.items()):
            values = g43.parse_json(path)
            if set(values) != set(target):
                errors.append(
                    f"{locale}: full key set mismatch missing={sorted(set(target)-set(values))} "
                    f"extra={sorted(set(values)-set(target))}"
                )
                continue
            for key, english in target.items():
                value = values[key]
                if key.startswith(g43.DEBUG_PREFIX) and value != english:
                    errors.append(f"{locale}: debug-only key is not exact G43 English: {key}")
                if not g43.preserves_runtime_literals(english, value):
                    errors.append(f"{locale}: runtime literal mismatch at {key}")
            if locale in fallback_locales and values != target:
                errors.append(f"{locale}: documented full-English fallback is not exact target English")

        if "uk_ua" in full_files:
            uk = g43.parse_json(full_files["uk_ua"])
            repaired = g43.fetch_g43_upstream("uk_ua")
            for key in sorted(normal_keys & set(repaired)):
                if g43.preserves_runtime_literals(target[key], repaired[key]) and uk[key] != repaired[key]:
                    errors.append(f"uk_ua: repaired pinned upstream value was not preserved at {key}")
            for key in sorted(normal_keys - set(repaired)):
                expected = expected_owned_value("uk_ua", key, target[key])
                if uk[key] != expected:
                    errors.append(f"uk_ua: missing repaired-upstream key resolved incorrectly at {key}")

        unchanged, added, _, _ = g43.semantic_partition()
        for locale, path in sorted(supplement_files.items()):
            values = g43.parse_json(path)
            try:
                upstream = g43.fetch_g43_upstream(locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch pinned upstream locale: {exc}")
                continue
            expected_missing = normal_keys - set(upstream)
            if set(values) != expected_missing:
                errors.append(
                    f"{locale}: supplement mismatch missing={sorted(expected_missing-set(values))} "
                    f"extra={sorted(set(values)-expected_missing)}"
                )
            if set(values) & set(upstream):
                errors.append(f"{locale}: supplement overrides upstream-owned key")
            if any(k.startswith(g43.DEBUG_PREFIX) for k in values):
                errors.append(f"{locale}: supplement contains debug-only key")
            for key, value in values.items():
                if key not in target:
                    errors.append(f"{locale}: supplement contains non-target key {key}")
                    continue
                if not g43.preserves_runtime_literals(target[key], value):
                    errors.append(f"{locale}: supplement runtime literal mismatch at {key}")
                    continue
                if key not in unchanged and key not in added:
                    errors.append(f"{locale}: supplement contains unresolved semantic key {key}")
                    continue
                expected = expected_owned_value(locale, key, target[key])
                if value != expected:
                    errors.append(f"{locale}: supplement resolution differs from frozen G43 policy at {key}")
            if normal_keys & (set(upstream) | set(values)) != normal_keys:
                errors.append(f"{locale}: upstream + supplement does not cover all G43 normal keys")

        for locale in sorted(complete_upstream):
            try:
                upstream = g43.fetch_g43_upstream(locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch complete pinned upstream locale: {exc}")
                continue
            missing = normal_keys - set(upstream)
            if missing:
                errors.append(f"{locale}: complete upstream locale is missing {len(missing)} normal keys")

        prov_path = output / "provenance.json"
        if not prov_path.exists():
            errors.append("G43 provenance.json was not generated")
        else:
            disk = json.loads(prov_path.read_text(encoding="utf-8"))
            if disk != provenance:
                errors.append("G43 provenance return value differs from written provenance.json")
            if disk.get("generation") != "g43-mc1.21.7":
                errors.append("G43 provenance generation id is wrong")
            if disk.get("cross_key_reuse_allowed") is not False:
                errors.append("G43 provenance must explicitly forbid cross-key reuse")
            if set(disk.get("added_g43_keys", [])) != g43.ADDED_G43_KEYS:
                errors.append("G43 provenance added-key set changed")

    if errors:
        print(f"FAIL: {len(errors)} G43 complete-resource validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.21.7 / JEI 23.1.0 complete reconstructed resources")
    print(f"{len(full_expected)} addon/full-override locales + {len(supplement_expected)} missing-key-only supplements + {len(complete_upstream)} complete upstream locales")
    print("291 keys per complete addon-owned locale; 285 normal target keys")
    print("Runtime placeholders and fixed technical tokens are preserved; cross-key reuse is forbidden")
    print("uk_ua remains a valid full repair override; grindstone.experience historical reuse is exact same-key/same-English only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

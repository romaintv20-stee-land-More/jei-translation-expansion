#!/usr/bin/env python3
"""Validate complete reconstructed G44 / Minecraft 1.21.8 resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_8 as g44


def main() -> int:
    errors: list[str] = []
    target = g44.parse_json(g44.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g44.DEBUG_PREFIX)}
    scope = json.loads(g44.SCOPE_PATH.read_text(encoding="utf-8"))
    full_expected = set(scope["addon_full_locales"])
    supplement_expected = set(scope["selected_upstream_incomplete_locales"])
    complete_upstream = set(scope["selected_upstream_complete_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    unchanged, added, removed, changed = g44.semantic_partition()

    with tempfile.TemporaryDirectory(prefix="jei-g44-complete-") as tmp:
        output = Path(tmp)
        try:
            full_count, supplement_count, key_count, provenance = g44.reconstruct_all(output)
        except Exception as exc:
            print(f"FAIL: G44 reconstruction raised: {exc}")
            return 1

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {p.stem: p for p in full_dir.glob("*.json")}
        supplement_files = {p.stem: p for p in supplement_dir.glob("*.json")}

        if (full_count, supplement_count, key_count) != (65, 24, 305):
            errors.append(f"reconstruction counts changed: {full_count}/{supplement_count}/{key_count}")
        if set(full_files) != full_expected:
            errors.append("reconstructed full locale set differs from frozen scope")
        if set(supplement_files) != supplement_expected:
            errors.append("reconstructed supplement locale set differs from frozen scope")
        if set(full_files) & set(supplement_files):
            errors.append("full/supplement ownership overlaps")
        if len(full_expected | supplement_expected | complete_upstream) != 90:
            errors.append("selected ownership does not total 90")
        if "uk_ua" not in full_files or "uk_ua" in supplement_files:
            errors.append("uk_ua must be emitted only as a full repair override")

        for locale, path in sorted(full_files.items()):
            values = g44.parse_json(path)
            if set(values) != set(target):
                errors.append(f"{locale}: full key set differs from target")
                continue
            if set(values) & g44.REMOVED_G44_KEYS:
                errors.append(f"{locale}: removed G44 key leaked into full output")
            for key, english in target.items():
                value = values[key]
                if key.startswith(g44.DEBUG_PREFIX) and value != english:
                    errors.append(f"{locale}: debug-only key is not exact target English: {key}")
                if not g44.preserves_runtime_literals(english, value):
                    errors.append(f"{locale}: runtime literal mismatch at {key}")
            if locale in fallback and values != target:
                errors.append(f"{locale}: documented full-English fallback is not exact target English")

            if locale not in fallback:
                previous = g44.g43_combined_locale(locale)
                for key in unchanged:
                    expected, _ = g44.resolve_unchanged(locale, key, target[key])
                    if values[key] != expected and not (locale == "uk_ua" and key in g44.fetch_g44_upstream("uk_ua") and values[key] == g44.fetch_g44_upstream("uk_ua")[key]):
                        errors.append(f"{locale}: unchanged same-key semantic did not follow frozen resolution at {key}")
                for key in added:
                    if locale == "uk_ua":
                        repaired = g44.fetch_g44_upstream("uk_ua")
                        if key in repaired and g44.preserves_runtime_literals(target[key], repaired[key]):
                            expected = repaired[key]
                        else:
                            expected, _ = g44.resolve_added(locale, key, target[key])
                    else:
                        expected, _ = g44.resolve_added(locale, key, target[key])
                    if values[key] != expected:
                        errors.append(f"{locale}: added semantic resolution mismatch at {key}")

        for locale, path in sorted(supplement_files.items()):
            values = g44.parse_json(path)
            try:
                upstream = g44.fetch_g44_upstream(locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch pinned upstream locale: {exc}")
                continue
            expected_missing = normal - set(upstream)
            if set(values) != expected_missing:
                errors.append(f"{locale}: supplement key set differs from exact missing normal keys")
            if set(values) & set(upstream):
                errors.append(f"{locale}: supplement overrides upstream-owned key")
            if set(values) & g44.REMOVED_G44_KEYS:
                errors.append(f"{locale}: removed G44 key leaked into supplement")
            if any(k.startswith(g44.DEBUG_PREFIX) for k in values):
                errors.append(f"{locale}: supplement contains debug-only key")
            for key, value in values.items():
                english = target[key]
                if not g44.preserves_runtime_literals(english, value):
                    errors.append(f"{locale}: supplement runtime literal mismatch at {key}")
                    continue
                if key in unchanged:
                    expected, _ = g44.resolve_unchanged(locale, key, english)
                elif key in added:
                    expected, _ = g44.resolve_added(locale, key, english)
                else:
                    errors.append(f"{locale}: supplement contains unresolved semantic key {key}")
                    continue
                if value != expected:
                    errors.append(f"{locale}: supplement resolution mismatch at {key}")
            if normal & (set(upstream) | set(values)) != normal:
                errors.append(f"{locale}: upstream + supplement does not cover all normal G44 keys")

        for locale in sorted(complete_upstream):
            try:
                upstream = g44.fetch_g44_upstream(locale)
            except Exception as exc:
                errors.append(f"{locale}: cannot fetch complete upstream locale: {exc}")
                continue
            if normal - set(upstream):
                errors.append(f"{locale}: complete upstream locale is missing normal keys")

        prov_path = output / "provenance.json"
        if not prov_path.exists():
            errors.append("G44 provenance.json was not generated")
        else:
            disk = json.loads(prov_path.read_text(encoding="utf-8"))
            if disk != provenance:
                errors.append("G44 provenance return value differs from written file")
            if disk.get("generation") != "g44-mc1.21.8" or disk.get("cross_key_reuse_allowed") is not False:
                errors.append("G44 provenance identity/cross-key policy changed")
            if disk.get("future_donor_commit") != g44.DONOR_COMMIT:
                errors.append("G44 provenance future donor changed")
            if set(disk.get("removed_g44_keys", [])) != g44.REMOVED_G44_KEYS:
                errors.append("G44 provenance removed-key set changed")

    if errors:
        print(f"FAIL: {len(errors)} G44 complete-resource validation error(s)")
        for error in errors[:200]:
            print(f"- {error}")
        if len(errors) > 200:
            print(f"- ... {len(errors)-200} additional error(s) suppressed")
        return 1

    print("PASS: Minecraft 1.21.8 / JEI 24.2.0 complete reconstructed resources")
    print("65 addon/full-override locales + 24 missing-key-only supplements + 1 complete upstream locale")
    print("305 keys per complete addon-owned locale; 299 normal target keys")
    print("290 unchanged same-key meanings inherit G43; 15 additions use exact future donor values only when same-key/same-English; 1 removed key is never emitted")
    print(f"Provenance totals: {json.dumps(provenance['totals'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

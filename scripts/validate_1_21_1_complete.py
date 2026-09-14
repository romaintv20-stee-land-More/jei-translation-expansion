#!/usr/bin/env python3
"""Validate complete G39 Minecraft 1.21.1 / JEI 19.21.1 reconstructed JSON resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_1 as g39
import validate_1_14_2_complete as baseqa


def main() -> int:
    errors: list[str] = []
    base = g39.parse_json(g39.BASE_SOURCE)
    target = g39.parse_json(g39.TARGET_SOURCE)
    normal = {k for k in target if not k.startswith(g39.DEBUG_PREFIX)}
    unchanged, added, removed, changed = g39.semantic_partition()
    changed_or_added = added | changed
    scope = json.loads(g39.SCOPE_PATH.read_text(encoding="utf-8"))
    fallback_locales = set(scope["documented_full_english_fallback_locales"])

    full, full_stats = g39.reconstruct_full(target, scope)
    supplements, supplement_stats = g39.reconstruct_supplements(target, scope)
    g38_full = g39.reconstruct_g38_full()

    if (len(full), len(supplements), len(target), len(normal)) != (64, 24, 286, 280):
        errors.append(
            f"G39 counts changed: full={len(full)} supplements={len(supplements)} "
            f"target={len(target)} normal={len(normal)}"
        )
    if (len(unchanged), len(added), len(removed), len(changed)) != (76, 167, 57, 43):
        errors.append("G39 semantic partition changed")
    if len(fallback_locales) != 30 or len(set(full) - fallback_locales) != 34:
        errors.append("G39 full ownership must remain 30 documented English fallbacks + 34 translated/AI-assisted locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full G39 key set differs from target")
            continue
        stats = full_stats.get(locale)
        if stats is None:
            errors.append(f"{locale}: missing full-locale provenance stats")
            continue

        if locale in fallback_locales:
            if values != target:
                errors.append(f"{locale}: documented complete-English fallback is not exact G39 target English")
            expected_stats = {
                "inherited": 0,
                "donor": 0,
                "english_fallback": len(target),
                "documented_full_english_fallback": len(target),
            }
            if stats != expected_stats:
                errors.append(f"{locale}: documented fallback provenance differs from exact-English policy")
            for key, value in values.items():
                baseqa.validate_value(locale, key, target[key], value, errors)
            continue

        old = g38_full.get(locale)
        if old is None:
            errors.append(f"{locale}: retained G39 full locale is absent from G38 addon-full resources")
            continue
        if set(old) != set(base):
            errors.append(f"{locale}: G38 base key set differs before G39 inheritance")
            continue

        inherited_count = donor_count = fallback_count = 0
        for key, value in values.items():
            if key in unchanged:
                expected = old[key]
                inherited_count += 1
                if value != expected:
                    errors.append(f"{locale}: unchanged G39 value differs from exact G38 value for {key}")
            elif key in changed_or_added:
                expected, source = g39.resolve_changed_or_added(locale, key, target[key])
                if value != expected:
                    errors.append(f"{locale}: new/changed G39 value differs from deterministic resolution for {key}")
                if source == "donor":
                    donor_count += 1
                elif source == "english-fallback":
                    fallback_count += 1
                else:
                    errors.append(f"{locale}: unknown G39 provenance source {source!r} for {key}")
            else:
                errors.append(f"{locale}: unexpected semantic key in complete G39 output: {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)

        expected_stats = {
            "inherited": inherited_count,
            "donor": donor_count,
            "english_fallback": fallback_count,
            "documented_full_english_fallback": 0,
        }
        if stats != expected_stats:
            errors.append(f"{locale}: full provenance stats differ from independently recomputed sources")
        if inherited_count != 76 or inherited_count + donor_count + fallback_count != 286:
            errors.append(f"{locale}: translated full provenance does not account for exactly 286 target values")

    for locale, values in supplements.items():
        upstream = g39.fetch_upstream_json(g39.G39_COMMIT, locale)
        missing = normal - set(upstream)
        previous_complete = g39.g38_combined_locale(locale)
        stats = supplement_stats.get(locale)
        if stats is None:
            errors.append(f"{locale}: missing supplement provenance stats")
            continue
        if set(values) != missing:
            errors.append(f"{locale}: supplement keys differ from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(k.startswith(g39.DEBUG_PREFIX) for k in values):
            errors.append(f"{locale}: supplement contains debug-only key")

        inherited_count = donor_count = fallback_count = 0
        for key, value in values.items():
            if key in unchanged:
                expected = previous_complete.get(key)
                inherited_count += 1
                if expected is None:
                    errors.append(f"{locale}: unchanged supplement key absent from complete G38 view: {key}")
                elif value != expected:
                    errors.append(f"{locale}: unchanged supplement differs from exact G38 combined value for {key}")
            elif key in changed_or_added:
                expected, source = g39.resolve_changed_or_added(locale, key, target[key])
                if value != expected:
                    errors.append(f"{locale}: new/changed supplement differs from deterministic G39 resolution for {key}")
                if source == "donor":
                    donor_count += 1
                elif source == "english-fallback":
                    fallback_count += 1
                else:
                    errors.append(f"{locale}: unknown supplement provenance source {source!r} for {key}")
            else:
                errors.append(f"{locale}: supplement contains unexpected semantic key {key}")
            baseqa.validate_value(locale, key, target[key], value, errors)

        upstream_owned = len(normal & set(upstream))
        expected_stats = {
            "inherited": inherited_count,
            "donor": donor_count,
            "english_fallback": fallback_count,
            "upstream_owned": upstream_owned,
        }
        if stats != expected_stats:
            errors.append(f"{locale}: supplement provenance stats differ from independently recomputed sources")
        if inherited_count + donor_count + fallback_count != len(missing):
            errors.append(f"{locale}: supplement provenance does not account for every missing key")
        if upstream_owned + len(missing) != 280:
            errors.append(f"{locale}: upstream ownership + supplement does not cover exactly 280 normal G39 keys")
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all normal G39 target keys")

    complete_set = set(scope["selected_upstream_complete_locales"])
    if complete_set != {"en_us", "ja_jp"}:
        errors.append(f"G39 complete upstream ownership changed: {sorted(complete_set)}")
    for locale in complete_set:
        upstream = g39.fetch_upstream_json(g39.G39_COMMIT, locale)
        if normal - set(upstream):
            errors.append(f"{locale}: expected complete upstream in G39")

    full_set = set(full)
    supplement_set = set(supplements)
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G39 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 90:
        errors.append("G39 ownership partitions do not cover exactly 90 selected languages")
    if not {"kk_kz", "no_no", "vi_vn"} <= supplement_set:
        errors.append("G39 must package kk_kz, no_no and vi_vn as missing-key-only supplements")

    expected_resolution_order = [
        "pinned-upstream",
        "exact-g38-inheritance",
        "exact-later-jei-donor",
        "exact-g39-english-fallback",
    ]
    summary = g39.provenance_summary(full_stats, supplement_stats)
    if summary["donor_commit"] != g39.DONOR_COMMIT:
        errors.append("G39 provenance summary donor commit differs from deterministic donor")
    if summary["resolution_order"] != expected_resolution_order:
        errors.append("G39 provenance resolution order changed")
    totals = summary["totals"]
    if totals["translated_full_inherited"] != 34 * 76:
        errors.append("G39 translated-full inherited total must be exactly 34 * 76")
    if (
        totals["translated_full_inherited"]
        + totals["translated_full_donor"]
        + totals["translated_full_english_fallback"]
        != 34 * 286
    ):
        errors.append("G39 translated-full provenance totals do not cover exactly 34 complete locales")
    if totals["documented_full_fallback_values"] != 30 * 286:
        errors.append("G39 documented full-English fallback total must be exactly 30 * 286")
    if (
        totals["supplement_inherited"]
        + totals["supplement_donor"]
        + totals["supplement_english_fallback"]
        + totals["supplement_upstream_owned_normal_values"]
        != 24 * 280
    ):
        errors.append("G39 supplement provenance totals do not cover exactly 24 complete normal-key views")

    with tempfile.TemporaryDirectory(prefix="jei-1.21.1-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count, written_summary = g39.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = sorted(full_dir.glob("*.json"))
        supplement_files = sorted(supplement_dir.glob("*.json"))
        if full_count != 64 or len(full_files) != 64 or {p.stem for p in full_files} != full_set:
            errors.append("G39 full output file set differs from frozen ownership")
        if supplement_count != 24 or len(supplement_files) != 24 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G39 supplement output file set differs from frozen ownership")
        if key_count != 286:
            errors.append("G39 output key count must be 286")
        for path in full_files + supplement_files:
            try:
                g39.parse_json(path)
            except Exception as exc:
                errors.append(f"{path.name}: invalid reconstructed JSON: {exc}")
        provenance_path = output / "PROVENANCE.json"
        if not provenance_path.is_file():
            errors.append("G39 reconstruction did not emit PROVENANCE.json")
        else:
            parsed_summary = json.loads(provenance_path.read_text(encoding="utf-8"))
            if parsed_summary != written_summary or written_summary != summary:
                errors.append("G39 written provenance differs from in-memory deterministic provenance")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.21.1 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 19.21.1 / Minecraft 1.21.1 complete JSON translation QA")
    print("Complete addon locales: 64")
    print("Translated/AI-assisted full locales: 34")
    print("Documented complete English fallbacks: 30")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 24")
    print("Keys per complete addon locale: 286 (280 normal + 6 debug)")
    print(f"Translated-full donor values: {totals['translated_full_donor']}")
    print(f"Translated-full explicit English fallbacks: {totals['translated_full_english_fallback']}")
    print(f"Supplement donor values: {totals['supplement_donor']}")
    print(f"Supplement explicit English fallbacks: {totals['supplement_english_fallback']}")
    print("Every emitted value is independently checked against exact G38 inheritance, exact-semantic donor reuse, or explicit G39 English fallback.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

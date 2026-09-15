#!/usr/bin/env python3
"""Validate complete reconstructed Minecraft 1.21.9 / JEI 25.0.1 resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_9 as g45


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    target = g45.parse_json(g45.TARGET_SOURCE)
    scope = load(g45.SCOPE_PATH)
    normal = {k for k in target if not k.startswith(g45.DEBUG_PREFIX)}
    full_locales = set(scope["addon_full_locales"])
    supplement_locales = set(scope["selected_upstream_incomplete_locales"])
    complete_locales = set(scope["selected_upstream_complete_locales"])
    fallback_locales = set(scope["documented_full_english_fallback_locales"])

    if (len(target), len(normal)) != (305, 299):
        raise ValueError("G45 target key counts changed")
    if (len(full_locales), len(supplement_locales), len(complete_locales)) != (65, 24, 1):
        raise ValueError("G45 ownership counts changed")
    if full_locales & supplement_locales or full_locales & complete_locales or supplement_locales & complete_locales:
        raise ValueError("G45 ownership sets overlap")
    if len(full_locales | supplement_locales | complete_locales) != 90:
        raise ValueError("G45 ownership does not cover 90 locales")
    if complete_locales != {"en_us"} or set(scope["malformed_upstream_full_override_locales"]) != {"uk_ua"}:
        raise ValueError("G45 special ownership changed")

    with tempfile.TemporaryDirectory(prefix="jei-g45-complete-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count, provenance = g45.reconstruct_all(output)
        if (full_count, supplement_count, key_count) != (65, 24, 305):
            raise ValueError(f"G45 reconstruction counts changed: {full_count}/{supplement_count}/{key_count}")

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        actual_full = {p.stem for p in full_dir.glob("*.json")}
        actual_supp = {p.stem for p in supplement_dir.glob("*.json")}
        if actual_full != full_locales:
            raise ValueError(f"G45 full locale file set mismatch: missing={sorted(full_locales-actual_full)} extra={sorted(actual_full-full_locales)}")
        if actual_supp != supplement_locales:
            raise ValueError(f"G45 supplement locale file set mismatch: missing={sorted(supplement_locales-actual_supp)} extra={sorted(actual_supp-supplement_locales)}")

        for locale in sorted(full_locales):
            values = g45.parse_json(full_dir / f"{locale}.json")
            if set(values) != set(target):
                raise ValueError(f"{locale}: G45 full file does not exactly match target key set")
            if set(values) & g45.REMOVED_G45_KEYS:
                raise ValueError(f"{locale}: removed G44 category key leaked into G45 full file")
            for key, english in target.items():
                if not g45.preserves_runtime_literals(english, values[key]):
                    raise ValueError(f"{locale}: placeholder/technical literal mismatch for {key}")
            if locale in fallback_locales and values != target:
                raise ValueError(f"{locale}: documented G45 English fallback is not exact target English")

        for locale in sorted(supplement_locales):
            upstream = g45.fetch_g45_upstream(locale)
            supplement = g45.parse_json(supplement_dir / f"{locale}.json")
            missing = normal - set(upstream)
            override_keys = set(g45.UPSTREAM_LITERAL_SAFETY_OVERRIDES.get(locale, set()))
            expected = missing | override_keys
            if set(supplement) != expected:
                raise ValueError(f"{locale}: G45 supplement is not exactly missing keys plus approved safety overrides")
            overlap = set(supplement) & set(upstream)
            if overlap != override_keys:
                raise ValueError(f"{locale}: unexpected G45 upstream-owned supplement overlap: {sorted(overlap)}")
            for key in override_keys:
                if g45.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: approved G45 safety override is no longer required for {key}")
                if not g45.preserves_runtime_literals(target[key], supplement[key]):
                    raise ValueError(f"{locale}: G45 safety override remains unsafe for {key}")
            if any(key.startswith(g45.DEBUG_PREFIX) for key in supplement):
                raise ValueError(f"{locale}: G45 supplement contains debug-only keys")
            if set(supplement) & g45.REMOVED_G45_KEYS:
                raise ValueError(f"{locale}: removed G44 category key leaked into G45 supplement")
            combined = {**upstream, **supplement}
            if normal - set(combined):
                raise ValueError(f"{locale}: G45 effective resource stack is missing normal keys")
            for key in normal:
                if not g45.preserves_runtime_literals(target[key], combined[key]):
                    raise ValueError(f"{locale}: effective placeholder/technical literal mismatch for {key}")

        for locale in sorted(complete_locales):
            upstream = g45.fetch_g45_upstream(locale)
            if normal - set(upstream):
                raise ValueError(f"{locale}: locale marked complete upstream is missing normal keys")
            for key in normal:
                if not g45.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: complete upstream literal mismatch for {key}")

        repaired_uk = g45.parse_json(full_dir / "uk_ua.json")
        pinned_uk = g45.fetch_g45_upstream("uk_ua")
        for key in set(pinned_uk) & set(target):
            if key.startswith(g45.DEBUG_PREFIX):
                continue
            if g45.preserves_runtime_literals(target[key], pinned_uk[key]) and repaired_uk[key] != pinned_uk[key]:
                raise ValueError(f"uk_ua: valid repaired upstream value was not preserved for {key}")

        if provenance.get("cross_key_reuse_allowed") is not False or provenance.get("renamed_category_keys_reuse_old_values") is not False:
            raise ValueError("G45 provenance permits forbidden cross-key reuse")
        if set(provenance.get("added_g45_keys", [])) != g45.ADDED_G45_KEYS:
            raise ValueError("G45 provenance added-key set changed")
        if set(provenance.get("removed_g45_keys", [])) != g45.REMOVED_G45_KEYS:
            raise ValueError("G45 provenance removed-key set changed")
        if provenance.get("future_donor_commit") != g45.DONOR_COMMIT:
            raise ValueError("G45 provenance donor pin changed")

    print("PASS: Minecraft 1.21.9 complete deterministic reconstruction")
    print("65 full/repair locales + 24 missing-key-only supplements + 1 complete upstream locale = 90")
    print("305 keys per complete locale; no removed category key leaks")
    print("Renamed category translations never use cross-key inheritance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

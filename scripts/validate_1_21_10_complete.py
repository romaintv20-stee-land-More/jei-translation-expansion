#!/usr/bin/env python3
"""Validate complete reconstructed Minecraft 1.21.10 / JEI 26.2.0 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_10 as g46


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    target = g46.parse_json(g46.TARGET_SOURCE)
    scope = json.loads(g46.SCOPE_PATH.read_text(encoding="utf-8"))
    normal = {k for k in target if not k.startswith(g46.DEBUG_PREFIX)}
    expected_full = set(scope["addon_full_locales"])
    expected_supp = set(scope["selected_upstream_incomplete_locales"])
    expected_complete = set(scope["selected_upstream_complete_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    overrides = {locale: set(keys) for locale, keys in scope.get("upstream_literal_safety_overrides", {}).items()}

    if (len(expected_full), len(expected_supp), len(expected_complete)) != (64, 25, 1) or expected_complete != {"en_us"}:
        raise ValueError("G46 frozen ownership changed")
    if "uk_ua" not in expected_supp or "uk_ua" in expected_full:
        raise ValueError("G46 uk_ua must be a valid incomplete upstream locale")

    with tempfile.TemporaryDirectory(prefix="jei-g46-complete-") as tmp:
        output = Path(tmp)
        full_count, supp_count, key_count, provenance = g46.reconstruct_all(output)
        if (full_count, supp_count, key_count) != (64, 25, 308):
            raise ValueError(f"G46 reconstruction counts changed: {full_count}/{supp_count}/{key_count}")

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supp_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {p.stem for p in full_dir.glob("*.json")}
        supp_files = {p.stem for p in supp_dir.glob("*.json")}
        if full_files != expected_full or supp_files != expected_supp:
            raise ValueError("G46 reconstructed locale file sets differ from frozen ownership")

        for locale in sorted(expected_full):
            values = load_json(full_dir / f"{locale}.json")
            if set(values) != set(target):
                raise ValueError(f"{locale}: G46 full key set mismatch")
            if locale in fallback and values != target:
                raise ValueError(f"{locale}: documented G46 fallback is not exact target English")
            for key, english in target.items():
                if not g46.preserves_runtime_literals(english, values[key]):
                    raise ValueError(f"{locale}: G46 full value breaks runtime literals for {key}")

        for locale in sorted(expected_supp):
            upstream = g46.fetch_g46_upstream(locale)
            supplement = load_json(supp_dir / f"{locale}.json")
            if any(k.startswith(g46.DEBUG_PREFIX) for k in supplement):
                raise ValueError(f"{locale}: G46 supplement contains debug-only key")
            if not set(supplement) <= normal:
                raise ValueError(f"{locale}: G46 supplement contains non-target-normal key")
            missing = normal - set(upstream)
            override_keys = overrides.get(locale, set())
            expected_keys = missing | override_keys
            if set(supplement) != expected_keys:
                raise ValueError(
                    f"{locale}: G46 supplement key set mismatch; expected {len(expected_keys)}, got {len(supplement)}"
                )
            if (set(supplement) & set(upstream)) != override_keys:
                raise ValueError(f"{locale}: G46 supplement overlaps upstream outside frozen safety overrides")
            for key in override_keys:
                if g46.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: unnecessary frozen G46 safety override for {key}")
            combined = dict(upstream)
            combined.update(supplement)
            if not normal <= set(combined):
                raise ValueError(f"{locale}: G46 combined normal coverage incomplete")
            for key in normal:
                if not g46.preserves_runtime_literals(target[key], combined[key]):
                    raise ValueError(f"{locale}: G46 combined value breaks runtime literals for {key}")

        upstream_en = g46.fetch_g46_upstream("en_us")
        if not normal <= set(upstream_en):
            raise ValueError("en_us: G46 complete upstream locale lost normal coverage")
        for key in normal:
            if upstream_en[key] != target[key]:
                raise ValueError(f"en_us: G46 upstream English differs from frozen target for {key}")

        uk_upstream = g46.fetch_g46_upstream("uk_ua")
        uk_missing = normal - set(uk_upstream)
        if uk_missing != g46.ADDED_G46_KEYS:
            raise ValueError(f"uk_ua: G46 missing-key set changed: {sorted(uk_missing)}")
        uk_supp = load_json(supp_dir / "uk_ua.json")
        if not g46.ADDED_G46_KEYS <= set(uk_supp):
            raise ValueError("uk_ua: G46 supplement does not cover all three new meanings")

        if provenance.get("cross_key_reuse_allowed") is not False:
            raise ValueError("G46 provenance permits cross-key reuse")
        if provenance.get("future_donor_commit") != g46.DONOR_COMMIT:
            raise ValueError("G46 provenance donor changed")
        if provenance.get("uk_ua_is_valid_upstream_supplement") is not True:
            raise ValueError("G46 provenance lost uk_ua validity transition")
        if set(provenance.get("added_g46_keys", [])) != g46.ADDED_G46_KEYS:
            raise ValueError("G46 provenance added-key set changed")
        if provenance.get("totals", {}).get("upstream-safety-overrides") != scope.get("upstream_literal_safety_override_count"):
            raise ValueError("G46 provenance safety-override total mismatch")

    print("PASS: Minecraft 1.21.10 complete deterministic reconstruction")
    print("Full addon locales: 64")
    print("Upstream supplement locales: 25")
    print("Complete upstream locales: 1 (en_us)")
    print("Keys per complete addon locale: 308")
    print("uk_ua is valid upstream; its three new G46 meanings are supplied as missing-key supplement content")
    print("All emitted/combined values preserve required placeholders and technical literals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate complete reconstructed Minecraft 1.21.11 / JEI 27.3.0 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_1_21_11 as g47


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    target = g47.parse_json(g47.TARGET_SOURCE)
    scope = json.loads(g47.SCOPE_PATH.read_text(encoding="utf-8"))
    normal = {k for k in target if not k.startswith(g47.DEBUG_PREFIX)}
    expected_full = set(scope["addon_full_locales"])
    expected_supp = set(scope["selected_upstream_incomplete_locales"])
    expected_complete = set(scope["selected_upstream_complete_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    overrides = {locale: set(keys) for locale, keys in scope.get("upstream_literal_safety_overrides", {}).items()}

    if (len(expected_full), len(expected_supp), len(expected_complete)) != (64, 25, 1) or expected_complete != {"en_us"}:
        raise ValueError("G47 frozen ownership changed")
    if "uk_ua" not in expected_supp or scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G47 selected upstream validity/ownership changed")

    with tempfile.TemporaryDirectory(prefix="jei-g47-complete-") as tmp:
        output = Path(tmp)
        full_count, supp_count, key_count, provenance = g47.reconstruct_all(output)
        if (full_count, supp_count, key_count) != (64, 25, 308):
            raise ValueError(f"G47 reconstruction counts changed: {full_count}/{supp_count}/{key_count}")

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supp_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = {p.stem for p in full_dir.glob("*.json")}
        supp_files = {p.stem for p in supp_dir.glob("*.json")}
        if full_files != expected_full or supp_files != expected_supp:
            raise ValueError("G47 reconstructed locale file sets differ from frozen ownership")

        for locale in sorted(expected_full):
            values = load_json(full_dir / f"{locale}.json")
            if set(values) != set(target) or set(values) & g47.REMOVED_G46_KEYS:
                raise ValueError(f"{locale}: G47 full key set mismatch")
            if locale in fallback and values != target:
                raise ValueError(f"{locale}: documented G47 fallback is not exact target English")
            for key, english in target.items():
                if not g47.preserves_runtime_literals(english, values[key]):
                    raise ValueError(f"{locale}: G47 full value breaks runtime literals for {key}")
            for key in g47.ADDED_G47_KEYS:
                if values[key] != target[key]:
                    raise ValueError(f"{locale}: project-owned G47 Identifier key is not exact target English: {key}")

        for locale in sorted(expected_supp):
            upstream = g47.fetch_g47_upstream(locale)
            supplement = load_json(supp_dir / f"{locale}.json")
            if any(k.startswith(g47.DEBUG_PREFIX) for k in supplement):
                raise ValueError(f"{locale}: G47 supplement contains debug-only key")
            if not set(supplement) <= normal or set(supplement) & g47.REMOVED_G46_KEYS:
                raise ValueError(f"{locale}: G47 supplement contains invalid target key")
            missing = normal - set(upstream)
            override_keys = overrides.get(locale, set())
            expected_keys = missing | override_keys
            if set(supplement) != expected_keys:
                raise ValueError(f"{locale}: G47 supplement key set mismatch; expected {len(expected_keys)}, got {len(supplement)}")
            if (set(supplement) & set(upstream)) != override_keys:
                raise ValueError(f"{locale}: G47 supplement overlaps upstream outside frozen safety overrides")
            for key in override_keys:
                if g47.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: unnecessary frozen G47 safety override for {key}")
            combined = dict(upstream)
            combined.update(supplement)
            if not normal <= set(combined):
                raise ValueError(f"{locale}: G47 combined normal coverage incomplete")
            for key in normal:
                if not g47.preserves_runtime_literals(target[key], combined[key]):
                    raise ValueError(f"{locale}: G47 combined value breaks runtime literals for {key}")
            for key in g47.ADDED_G47_KEYS & set(supplement):
                if supplement[key] != target[key]:
                    raise ValueError(f"{locale}: project-owned missing Identifier key is not exact target English: {key}")

        upstream_en = g47.fetch_g47_upstream("en_us")
        if not normal <= set(upstream_en):
            raise ValueError("en_us: G47 complete upstream locale lost normal coverage")
        for key in normal:
            if upstream_en[key] != target[key]:
                raise ValueError(f"en_us: G47 upstream English differs from frozen target for {key}")

        if provenance.get("cross_key_reuse_allowed") is not False:
            raise ValueError("G47 provenance permits cross-key reuse")
        if provenance.get("upstream_jei_target_is_maven_only") is not True:
            raise ValueError("G47 provenance lost Maven-only publication context")
        if set(provenance.get("added_g47_keys", [])) != g47.ADDED_G47_KEYS:
            raise ValueError("G47 provenance added-key set changed")
        if set(provenance.get("removed_g46_keys", [])) != g47.REMOVED_G46_KEYS:
            raise ValueError("G47 provenance removed-key set changed")
        if provenance.get("totals", {}).get("upstream-safety-overrides") != scope.get("upstream_literal_safety_override_count"):
            raise ValueError("G47 provenance safety-override total mismatch")

    print("PASS: Minecraft 1.21.11 complete deterministic reconstruction")
    print("Full addon locales: 64")
    print("Upstream supplement locales: 25")
    print("Complete upstream locales: 1 (en_us)")
    print("Keys per complete addon locale: 308")
    print("All emitted/combined values preserve required placeholders and technical literals")
    print("Identifier localization IDs are treated as new keys; no Resource Location cross-key reuse occurred")
    print("Upstream JEI 1.21.11 is Maven-only; public packaging remains a separate decision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

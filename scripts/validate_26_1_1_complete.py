#!/usr/bin/env python3
"""Validate complete reconstructed Minecraft 26.1.1 / JEI 29.4.0 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_26_1_1 as g49


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    target = g49.parse_json(g49.TARGET_SOURCE)
    base = g49.parse_json(g49.BASE_SOURCE)
    scope = json.loads(g49.SCOPE_PATH.read_text(encoding="utf-8"))
    normal = {k for k in target if not k.startswith(g49.DEBUG_PREFIX)}
    full = set(scope["addon_full_locales"])
    supp = set(scope["selected_upstream_incomplete_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    overrides = {locale: set(keys) for locale, keys in scope.get("upstream_literal_safety_overrides", {}).items()}

    if base != target or len(target) != 309 or len(normal) != 303:
        raise ValueError("G49 frozen source is no longer exactly identical to G48")
    if (len(full), len(supp), len(complete)) != (64, 25, 1) or complete != {"en_us"}:
        raise ValueError("G49 frozen ownership changed")
    if "uk_ua" not in supp or scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G49 selected upstream validity/ownership changed")

    with tempfile.TemporaryDirectory(prefix="jei-g49-complete-") as tmp:
        output = Path(tmp)
        full_count, supp_count, key_count, provenance = g49.reconstruct_all(output)
        if (full_count, supp_count, key_count) != (64, 25, 309):
            raise ValueError(f"G49 reconstruction counts changed: {full_count}/{supp_count}/{key_count}")

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supp_dir = output / "supplements" / "assets" / "jei" / "lang"
        if {p.stem for p in full_dir.glob("*.json")} != full:
            raise ValueError("G49 reconstructed full locale file set differs from frozen ownership")
        if {p.stem for p in supp_dir.glob("*.json")} != supp:
            raise ValueError("G49 reconstructed supplement locale file set differs from frozen ownership")

        for locale in sorted(full):
            values = load_json(full_dir / f"{locale}.json")
            if set(values) != set(target):
                raise ValueError(f"{locale}: G49 full key set mismatch")
            if locale in fallback and values != target:
                raise ValueError(f"{locale}: documented G49 fallback is not exact target English")
            for key, english in target.items():
                if not g49.preserves_runtime_literals(english, values[key]):
                    raise ValueError(f"{locale}: G49 full value breaks runtime literals for {key}")

        for locale in sorted(supp):
            upstream = g49.fetch_g49_upstream(locale)
            supplement = load_json(supp_dir / f"{locale}.json")
            if any(k.startswith(g49.DEBUG_PREFIX) for k in supplement):
                raise ValueError(f"{locale}: G49 supplement contains debug-only key")
            if not set(supplement) <= normal:
                raise ValueError(f"{locale}: G49 supplement contains invalid target key")
            missing = normal - set(upstream)
            override_keys = overrides.get(locale, set())
            expected_keys = missing | override_keys
            if set(supplement) != expected_keys:
                raise ValueError(f"{locale}: G49 supplement key set mismatch; expected {len(expected_keys)}, got {len(supplement)}")
            if (set(supplement) & set(upstream)) != override_keys:
                raise ValueError(f"{locale}: G49 supplement overlaps upstream outside frozen safety overrides")
            for key in override_keys:
                if g49.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: unnecessary frozen G49 safety override for {key}")
            combined = dict(upstream)
            combined.update(supplement)
            if not normal <= set(combined):
                raise ValueError(f"{locale}: G49 combined normal coverage incomplete")
            for key in normal:
                if not g49.preserves_runtime_literals(target[key], combined[key]):
                    raise ValueError(f"{locale}: G49 combined value breaks runtime literals for {key}")

        upstream_en = g49.fetch_g49_upstream("en_us")
        if not normal <= set(upstream_en):
            raise ValueError("en_us: G49 complete upstream locale lost normal coverage")
        for key in normal:
            if upstream_en[key] != target[key]:
                raise ValueError(f"en_us: G49 upstream English differs from frozen target for {key}")

        if provenance.get("cross_key_reuse_allowed") is not False:
            raise ValueError("G49 provenance permits cross-key reuse")
        if provenance.get("all_target_semantics_unchanged_from_g48") is not True:
            raise ValueError("G49 provenance lost identical-semantics guarantee")
        if provenance.get("upstream_commit") != g49.G49_COMMIT:
            raise ValueError("G49 provenance endpoint mismatch")
        if provenance.get("totals", {}).get("upstream-safety-overrides") != scope.get("upstream_literal_safety_override_count"):
            raise ValueError("G49 provenance safety-override total mismatch")

    print("PASS: Minecraft 26.1.1 complete deterministic reconstruction")
    print("Full addon locales: 64")
    print("Upstream supplement locales: 25")
    print("Complete upstream locales: 1 (en_us)")
    print("Keys per complete addon locale: 309")
    print("All 309 English semantics are unchanged from G48")
    print("All emitted/combined values preserve required placeholders and technical literals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate complete provisional Minecraft 26.3 RC2 reconstructed language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_26_3_rc_2 as pre


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base, target = pre.verify_semantics()
    scope = json.loads(pre.SCOPE_PATH.read_text(encoding="utf-8"))
    normal = {k for k in target if not k.startswith(pre.DEBUG_PREFIX)}
    full = set(scope["addon_full_locales"])
    supp = set(scope["selected_upstream_incomplete_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    overrides = {locale: set(keys) for locale, keys in scope.get("upstream_literal_safety_overrides", {}).items()}

    if base != target or (len(target), len(normal)) != (334, 328):
        raise ValueError("provisional frozen English semantics changed")
    if (len(full), len(supp), len(complete)) != (63, 26, 1) or complete != {"en_us"}:
        raise ValueError("provisional frozen ownership changed")
    if len(fallback) != 30 or not fallback <= full:
        raise ValueError("provisional documented fallback ownership changed")
    if scope.get("publishable_candidate") is not False:
        raise ValueError("provisional target unexpectedly became publishable without re-audit")

    with tempfile.TemporaryDirectory(prefix="jei-pre-g52-complete-") as tmp:
        output = Path(tmp)
        full_count, supp_count, key_count, provenance = pre.reconstruct_all(output)
        if (full_count, supp_count, key_count) != (63, 26, 334):
            raise ValueError(f"provisional reconstruction counts changed: {full_count}/{supp_count}/{key_count}")

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supp_dir = output / "supplements" / "assets" / "jei" / "lang"
        if {p.stem for p in full_dir.glob("*.json")} != full:
            raise ValueError("provisional reconstructed full locale set differs from frozen ownership")
        if {p.stem for p in supp_dir.glob("*.json")} != supp:
            raise ValueError("provisional reconstructed supplement locale set differs from frozen ownership")

        for locale in sorted(full):
            values = load_json(full_dir / f"{locale}.json")
            if set(values) != set(target):
                raise ValueError(f"{locale}: provisional full key set mismatch")
            if locale in fallback and values != target:
                raise ValueError(f"{locale}: provisional fallback is not exact target English")
            for key, english in target.items():
                if not pre.preserves_runtime_literals(english, values[key]):
                    raise ValueError(f"{locale}: provisional full value breaks runtime literals for {key}")

        for locale in sorted(supp):
            upstream = pre.fetch_target_upstream(locale)
            supplement = load_json(supp_dir / f"{locale}.json")
            if any(k.startswith(pre.DEBUG_PREFIX) for k in supplement):
                raise ValueError(f"{locale}: provisional supplement contains debug-only key")
            if not set(supplement) <= normal:
                raise ValueError(f"{locale}: provisional supplement contains invalid target key")
            missing = normal - set(upstream)
            override_keys = overrides.get(locale, set())
            expected_keys = missing | override_keys
            if set(supplement) != expected_keys:
                raise ValueError(f"{locale}: provisional supplement key set mismatch; expected {len(expected_keys)}, got {len(supplement)}")
            if (set(supplement) & set(upstream)) != override_keys:
                raise ValueError(f"{locale}: provisional supplement overlaps upstream outside safety overrides")
            for key in override_keys:
                if pre.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: unnecessary provisional safety override for {key}")
            combined = dict(upstream)
            combined.update(supplement)
            if not normal <= set(combined):
                raise ValueError(f"{locale}: provisional combined normal coverage incomplete")
            for key in normal:
                if not pre.preserves_runtime_literals(target[key], combined[key]):
                    raise ValueError(f"{locale}: provisional combined value breaks runtime literals for {key}")

        upstream_en = pre.fetch_target_upstream("en_us")
        if not normal <= set(upstream_en):
            raise ValueError("en_us: provisional complete upstream locale lost normal coverage")
        for key in normal:
            if upstream_en[key] != target[key]:
                raise ValueError(f"en_us: provisional upstream English differs from frozen target for {key}")

        if provenance.get("cross_key_reuse_allowed") is not False:
            raise ValueError("provisional provenance permits cross-key reuse")
        if provenance.get("packaging_registration_allowed") is not False:
            raise ValueError("provisional provenance permits packaging registration")
        if provenance.get("upstream_commit") != pre.PRE_G52_COMMIT:
            raise ValueError("provisional provenance snapshot mismatch")
        if provenance.get("totals", {}).get("upstream-safety-overrides") != scope.get("upstream_literal_safety_override_count"):
            raise ValueError("provisional provenance safety-override total mismatch")

    print("PASS: provisional Minecraft 26.3 RC2 complete deterministic reconstruction")
    print("Full addon locales: 63")
    print("Upstream supplement locales: 26")
    print("Complete upstream locales: 1 (en_us)")
    print("Keys per complete addon locale: 334")
    print("All emitted/combined values preserve required placeholders and technical literals")
    print("No final G52 package is authorized from this RC snapshot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

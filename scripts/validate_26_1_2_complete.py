#!/usr/bin/env python3
"""Validate complete reconstructed Minecraft 26.1.2 / JEI 29.37.0 language resources."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reconstruct_26_1_2 as g50


def load_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = g50.parse_json(g50.BASE_SOURCE)
    target = g50.parse_json(g50.TARGET_SOURCE)
    scope = json.loads(g50.SCOPE_PATH.read_text(encoding="utf-8"))
    normal = {k for k in target if not k.startswith(g50.DEBUG_PREFIX)}
    full = set(scope["addon_full_locales"])
    supp = set(scope["selected_upstream_incomplete_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    fallback = set(scope["documented_full_english_fallback_locales"])
    overrides = {locale: set(keys) for locale, keys in scope.get("upstream_literal_safety_overrides", {}).items()}
    reusable = {k for k in set(base) & set(target) if base[k] == target[k]}
    novel_or_changed = set(target) - reusable

    if (len(base), len(target), len(normal)) != (309, 334, 328):
        raise ValueError("G50 frozen source counts changed")
    if len(reusable) != 294 or len(novel_or_changed) != 40:
        raise ValueError("G50 semantic partition changed")
    if (len(full), len(supp), len(complete)) != (63, 26, 1) or complete != {"en_us"}:
        raise ValueError("G50 frozen ownership changed")
    if "fil_ph" not in supp or scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G50 selected upstream validity/ownership changed")

    with tempfile.TemporaryDirectory(prefix="jei-g50-complete-") as tmp:
        output = Path(tmp)
        full_count, supp_count, key_count, provenance = g50.reconstruct_all(output)
        if (full_count, supp_count, key_count) != (63, 26, 334):
            raise ValueError(f"G50 reconstruction counts changed: {full_count}/{supp_count}/{key_count}")

        full_dir = output / "full" / "assets" / "jei" / "lang"
        supp_dir = output / "supplements" / "assets" / "jei" / "lang"
        if {p.stem for p in full_dir.glob("*.json")} != full:
            raise ValueError("G50 reconstructed full locale file set differs from frozen ownership")
        if {p.stem for p in supp_dir.glob("*.json")} != supp:
            raise ValueError("G50 reconstructed supplement locale file set differs from frozen ownership")

        for locale in sorted(full):
            values = load_json(full_dir / f"{locale}.json")
            if set(values) != set(target):
                raise ValueError(f"{locale}: G50 full key set mismatch")
            if locale in fallback and values != target:
                raise ValueError(f"{locale}: documented G50 fallback is not exact target English")
            for key, english in target.items():
                if not g50.preserves_runtime_literals(english, values[key]):
                    raise ValueError(f"{locale}: G50 full value breaks runtime literals for {key}")
                if key in novel_or_changed and values[key] != english:
                    raise ValueError(f"{locale}: G50 novel/changed full value was reused without semantic identity for {key}")

        for locale in sorted(supp):
            upstream = g50.fetch_g50_upstream(locale)
            supplement = load_json(supp_dir / f"{locale}.json")
            if any(k.startswith(g50.DEBUG_PREFIX) for k in supplement):
                raise ValueError(f"{locale}: G50 supplement contains debug-only key")
            if not set(supplement) <= normal:
                raise ValueError(f"{locale}: G50 supplement contains invalid target key")
            missing = normal - set(upstream)
            override_keys = overrides.get(locale, set())
            expected_keys = missing | override_keys
            if set(supplement) != expected_keys:
                raise ValueError(f"{locale}: G50 supplement key set mismatch; expected {len(expected_keys)}, got {len(supplement)}")
            if (set(supplement) & set(upstream)) != override_keys:
                raise ValueError(f"{locale}: G50 supplement overlaps upstream outside frozen safety overrides")
            for key in override_keys:
                if g50.preserves_runtime_literals(target[key], upstream[key]):
                    raise ValueError(f"{locale}: unnecessary frozen G50 safety override for {key}")
            for key in set(supplement) & novel_or_changed:
                if supplement[key] != target[key]:
                    raise ValueError(f"{locale}: G50 novel/changed supplement value was reused without semantic identity for {key}")
            combined = dict(upstream)
            combined.update(supplement)
            if not normal <= set(combined):
                raise ValueError(f"{locale}: G50 combined normal coverage incomplete")
            for key in normal:
                if not g50.preserves_runtime_literals(target[key], combined[key]):
                    raise ValueError(f"{locale}: G50 combined value breaks runtime literals for {key}")

        upstream_en = g50.fetch_g50_upstream("en_us")
        if not normal <= set(upstream_en):
            raise ValueError("en_us: G50 complete upstream locale lost normal coverage")
        for key in normal:
            if upstream_en[key] != target[key]:
                raise ValueError(f"en_us: G50 upstream English differs from frozen target for {key}")

        if provenance.get("cross_key_reuse_allowed") is not False:
            raise ValueError("G50 provenance permits cross-key reuse")
        if provenance.get("upstream_commit") != g50.G50_COMMIT:
            raise ValueError("G50 provenance snapshot mismatch")
        if provenance.get("totals", {}).get("upstream-safety-overrides") != scope.get("upstream_literal_safety_override_count"):
            raise ValueError("G50 provenance safety-override total mismatch")

    print("PASS: Minecraft 26.1.2 complete deterministic reconstruction")
    print("Full addon locales: 63")
    print("Upstream supplement locales: 26")
    print("Complete upstream locales: 1 (en_us)")
    print("Keys per complete addon locale: 334")
    print("294 exact G49 semantics are eligible for reuse; 40 added/changed meanings are not reused")
    print("All emitted/combined values preserve required placeholders and technical literals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

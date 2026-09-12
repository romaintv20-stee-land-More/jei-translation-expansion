#!/usr/bin/env python3
"""Validate complete G14 Minecraft 1.14.2 / JEI 6.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from pathlib import Path

import reconstruct_1_14_2 as g14

PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|CTRL|,d|\d+\$[sdif]|[sdif]|%)")
TECHNICAL_TOKENS = ("JEI", "Minecraft", "/give", "modId[:name[:meta]]", "mB")


def placeholders(value: str) -> Counter[str]:
    return Counter(PLACEHOLDER_RE.findall(value))


def validate_value(locale: str, key: str, english: str, translated: str, errors: list[str]) -> None:
    if placeholders(translated) != placeholders(english):
        errors.append(f"{locale}: placeholder mismatch for {key}")
    for token in TECHNICAL_TOKENS:
        if token in english and token not in translated:
            errors.append(f"{locale}: missing technical token {token!r} in {key}")
    if key.startswith(g14.DEBUG_PREFIX) and translated != english:
        errors.append(f"{locale}: debug-only key must remain exact target English: {key}")


def main() -> int:
    errors: list[str] = []
    base = g14.parse_json(g14.BASE_SOURCE)
    target = g14.parse_json(g14.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g14.DEBUG_PREFIX)}
    scope = json.loads(g14.SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g14.POLICY_PATH.read_text(encoding="utf-8"))

    full = g14.reconstruct_full(target, scope)
    supplements = g14.reconstruct_supplements(target, scope)
    g13_full = g14.reconstruct_g13_full()
    g13_supplements = g14.reconstruct_g13_supplements()

    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    added = set(target) - set(base)
    if (len(full), len(supplements), len(target), len(normal), len(unchanged), len(added)) != (70, 19, 109, 106, 106, 3):
        errors.append(
            "G14 complete counts changed: "
            f"full={len(full)} supplements={len(supplements)} total={len(target)} normal={len(normal)} "
            f"unchanged={len(unchanged)} added={len(added)}"
        )
    if added != g14.NEW_G14_KEYS:
        errors.append("G14 complete added-key set changed")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 31 or not fallback_locales <= set(full):
        errors.append("G14 documented full-English fallback set must contain 31 addon-full locales")
    if not g14.NEW_G14_LANGUAGES <= fallback_locales:
        errors.append("G14 new selected languages must all be documented complete-English fallbacks")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full JSON key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete English fallback is not exact target English")
        for key, value in values.items():
            expected, _ = g14.resolve_value(locale, key, target[key], base, g13_full, g13_supplements)
            if value != expected:
                errors.append(f"{locale}: incorrect G14 semantic-reuse policy for {key}")
            validate_value(locale, key, target[key], value, errors)
        for key in g14.NEW_G14_KEYS:
            if values.get(key) != target[key]:
                errors.append(f"{locale}: new G14 category key must use exact target English: {key}")

    for locale, values in supplements.items():
        upstream = g14.fetch_upstream_json(g14.G14_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(f"{locale}: supplement key set differs from exact pinned-upstream missing set")
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g14.DEBUG_PREFIX) or key.startswith("_comment") for key in values):
            errors.append(f"{locale}: supplement contains debug/comment-only key")
        if not g14.NEW_G14_KEYS <= set(values):
            errors.append(f"{locale}: supplement must include all three new G14 cooking-category keys")
        for key, value in values.items():
            expected, _ = g14.resolve_value(locale, key, target[key], base, g13_full, g13_supplements)
            if value != expected:
                errors.append(f"{locale}: supplement differs from deterministic G14 policy for {key}")
            validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 106 normal target keys")
        for key in g14.NEW_G14_KEYS:
            if values.get(key) != target[key]:
                errors.append(f"{locale}: project-owned new G14 category key must be exact target English: {key}")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G14 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 91:
        errors.append("G14 emitted ownership partitions do not cover exactly 91 selected languages")
    if complete_set != {"en_us", "pl_pl"}:
        errors.append("G14 complete upstream ownership must be exactly en_us + pl_pl")

    with tempfile.TemporaryDirectory(prefix="jei-1.14.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g14.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = sorted(full_dir.glob("*.json"))
        supplement_files = sorted(supplement_dir.glob("*.json"))
        if full_count != 70 or len(full_files) != 70 or {p.stem for p in full_files} != full_set:
            errors.append("G14 full JSON output file set differs from frozen ownership")
        if supplement_count != 19 or len(supplement_files) != 19 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G14 supplement JSON output file set differs from frozen ownership")
        if key_count != 109:
            errors.append("G14 complete JSON output key count must be 109")
        for path in full_files + supplement_files:
            try:
                parsed = g14.parse_json(path)
            except Exception as exc:
                errors.append(f"{path.name}: invalid reconstructed JSON: {exc}")
                continue
            if any(key.startswith("_comment") for key in parsed):
                errors.append(f"{path.name}: reconstructed JSON unexpectedly contains comment metadata")

    if policy["translated_or_ai_assisted_full_locale_count"] != 39:
        errors.append("G14 translated/AI-assisted full locale count must remain 39")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.14.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 6.0.0 / Minecraft 1.14.2 complete JSON translation QA")
    print("Complete addon locales: 70")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 31")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 109")
    print("106 unchanged G13 semantics are deterministically inherited")
    print("Three new cooking categories are exact target-English when project-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

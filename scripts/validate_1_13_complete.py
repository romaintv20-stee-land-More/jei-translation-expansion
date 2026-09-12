#!/usr/bin/env python3
"""Validate complete G12 Minecraft 1.13 / JEI 4.14.4 reconstructed JSON resources."""
from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from pathlib import Path

import reconstruct_1_13 as g12

PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|CTRL|,d|\d+\$[sdif]|[sdif]|%)")
TECHNICAL_TOKENS = (
    "JEI",
    "Minecraft",
    "/give",
    "modId[:name[:meta]]",
    "mB",
)


def placeholders(value: str) -> Counter[str]:
    return Counter(PLACEHOLDER_RE.findall(value))


def validate_value(locale: str, key: str, english: str, translated: str, errors: list[str]) -> None:
    if placeholders(translated) != placeholders(english):
        errors.append(
            f"{locale}: placeholder mismatch for {key}: "
            f"{sorted(placeholders(translated).elements())} != {sorted(placeholders(english).elements())}"
        )
    for token in TECHNICAL_TOKENS:
        if token in english and token not in translated:
            errors.append(f"{locale}: missing technical token {token!r} in {key}")
    if key.startswith(g12.DEBUG_PREFIX) and translated != english:
        errors.append(f"{locale}: debug-only key must remain exact target English: {key}")


def main() -> int:
    errors: list[str] = []
    target = g12.parse_json(g12.TARGET_SOURCE)
    base = g12.parse_lang(g12.BASE_SOURCE)
    historical = g12.parse_lang(g12.HISTORICAL_SOURCE)
    normal = {key for key in target if not key.startswith(g12.DEBUG_PREFIX)}
    scope = json.loads(g12.SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g12.POLICY_PATH.read_text(encoding="utf-8"))

    full = g12.reconstruct_full(target, scope)
    supplements = g12.reconstruct_supplements(target, scope)
    g11_full = g12.reconstruct_g11_full()
    g11_supplements = g12.reconstruct_g11_supplements()
    g10_full = g12.reconstruct_g10_full()
    g10_supplements = g12.reconstruct_g10_supplements()

    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    added = set(target) - set(base)
    changed_debug = {key for key in changed if key.startswith(g12.DEBUG_PREFIX)}
    reviewed_normal = added | (changed - changed_debug)

    if (len(full), len(supplements), len(target), len(normal), len(unchanged), len(reviewed_normal)) != (62, 12, 105, 102, 59, 43):
        errors.append(
            "G12 complete counts changed: "
            f"full={len(full)} supplements={len(supplements)} total={len(target)} normal={len(normal)} "
            f"unchanged={len(unchanged)} reviewed_normal={len(reviewed_normal)}"
        )

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 23 or not fallback_locales <= set(full):
        errors.append("G12 documented full-English fallback set must contain 23 addon-full locales")
    if not g12.NEW_G12_LANGUAGES <= fallback_locales:
        errors.append("G12 new selected languages must all be documented full-English fallbacks")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full JSON key set differs from target")
            continue
        if any(key.startswith("_comment") for key in values):
            errors.append(f"{locale}: semantic output must not contain JSON comment metadata keys")
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete English fallback is not exact target English")

        for key, value in values.items():
            expected, _ = g12.resolve_historical_value(
                locale,
                key,
                target[key],
                base,
                historical,
                g11_full,
                g11_supplements,
                g10_full,
                g10_supplements,
            )
            if value != expected:
                errors.append(f"{locale}: incorrect G12 semantic-reuse policy for {key}")
            validate_value(locale, key, target[key], value, errors)

    for locale, values in supplements.items():
        upstream = g12.fetch_upstream_json(g12.G12_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(
                f"{locale}: supplement key set differs from exact pinned-upstream missing set; "
                f"expected={len(missing)} actual={len(values)}"
            )
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g12.DEBUG_PREFIX) or key.startswith("_comment") for key in values):
            errors.append(f"{locale}: supplement contains debug/comment-only key")

        for key, value in values.items():
            expected, _ = g12.resolve_historical_value(
                locale,
                key,
                target[key],
                base,
                historical,
                g11_full,
                g11_supplements,
                g10_full,
                g10_supplements,
            )
            if value != expected:
                errors.append(f"{locale}: supplement differs from deterministic G12 semantic policy for {key}")
            validate_value(locale, key, target[key], value, errors)

        combined_normal = (set(upstream) | set(values)) & normal
        if combined_normal != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 102 normal target keys")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G12 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 83:
        errors.append("G12 emitted ownership partitions do not cover exactly 83 selected languages")

    expected_complete = {"de_de", "en_us", "fr_fr", "ja_jp", "pl_pl", "pt_br", "ru_ru", "sv_se", "zh_cn"}
    if complete_set != expected_complete:
        errors.append("G12 complete upstream ownership set changed")

    returned_to_full = {"hu_hu", "id_id", "no_no", "vi_vn"}
    if not returned_to_full <= full_set:
        errors.append("G12 removed-upstream locales hu_hu/id_id/no_no/vi_vn must return to full addon ownership")
    if "tr_tr" not in supplement_set:
        errors.append("G12 tr_tr must remain an upstream supplement locale")
    if "ksh" not in full_set or "ksh_de" in full_set | supplement_set | complete_set:
        errors.append("G12 must emit renamed Kölsch locale ksh and never ksh_de")

    # The two new Tag keys are distinct localization keys and must not inherit old Ore Dictionary values.
    for locale in full_set:
        if locale not in fallback_locales:
            for key in ("config.jei.search.tagSearchMode", "config.jei.search.tagSearchMode.comment", "jei.tooltip.recipe.tag"):
                if key in target and key not in historical:
                    if full[locale][key] != target[key]:
                        errors.append(f"{locale}: new Tag key incorrectly inherited a cross-key translation: {key}")

    with tempfile.TemporaryDirectory(prefix="jei-1.13-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g12.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = sorted(full_dir.glob("*.json"))
        supplement_files = sorted(supplement_dir.glob("*.json"))
        if full_count != 62 or len(full_files) != 62 or {p.stem for p in full_files} != full_set:
            errors.append("G12 full JSON output file set differs from frozen ownership")
        if supplement_count != 12 or len(supplement_files) != 12 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G12 supplement JSON output file set differs from frozen ownership")
        if key_count != 105:
            errors.append("G12 complete JSON output key count must be 105")
        for path in full_files + supplement_files:
            try:
                parsed = g12.parse_json(path)
            except Exception as exc:
                errors.append(f"{path.name}: invalid reconstructed JSON: {exc}")
                continue
            if any(key.startswith("_comment") for key in parsed):
                errors.append(f"{path.name}: reconstructed JSON unexpectedly contains comment metadata")

    if policy["translated_or_ai_assisted_full_locale_count"] != 39:
        errors.append("G12 translated/AI-assisted full locale count must remain 39")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.13 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 4.14.4 / Minecraft 1.13 complete JSON translation QA")
    print("Complete addon locales: 62")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 23")
    print("Selected complete upstream locales: 9")
    print("Missing-key-only upstream supplements: 12")
    print("Keys per complete addon locale: 105")
    print("Exact G11 semantics reused first; exact G10 semantic reversions reused second")
    print("New Tag keys remain distinct from removed Ore Dictionary keys")
    print("Locale-code migration validated: ksh_de -> ksh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

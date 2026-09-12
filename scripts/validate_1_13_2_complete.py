#!/usr/bin/env python3
"""Validate complete G13 Minecraft 1.13.2 / JEI 5.0.0 reconstructed JSON resources."""
from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from pathlib import Path

import reconstruct_1_13_2 as g13

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
    if key.startswith(g13.DEBUG_PREFIX) and translated != english:
        errors.append(f"{locale}: debug-only key must remain exact target English: {key}")


def main() -> int:
    errors: list[str] = []
    base = g13.parse_json(g13.BASE_SOURCE)
    target = g13.parse_json(g13.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g13.DEBUG_PREFIX)}
    scope = json.loads(g13.SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g13.POLICY_PATH.read_text(encoding="utf-8"))

    full = g13.reconstruct_full(target, scope)
    supplements = g13.reconstruct_supplements(target, scope)
    g12_full = g13.reconstruct_g12_full()
    g12_supplements = g13.reconstruct_g12_supplements()

    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    added = set(target) - set(base)
    changed_debug = {key for key in changed if key.startswith(g13.DEBUG_PREFIX)}
    reviewed_normal = added | (changed - changed_debug)

    if (len(full), len(supplements), len(target), len(normal), len(unchanged), len(reviewed_normal)) != (66, 19, 106, 103, 101, 4):
        errors.append(
            "G13 complete counts changed: "
            f"full={len(full)} supplements={len(supplements)} total={len(target)} normal={len(normal)} "
            f"unchanged={len(unchanged)} reviewed_normal={len(reviewed_normal)}"
        )

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 27 or not fallback_locales <= set(full):
        errors.append("G13 documented full-English fallback set must contain 27 addon-full locales")
    if not g13.NEW_G13_LANGUAGES <= fallback_locales:
        errors.append("G13 new selected languages must all be documented complete-English fallbacks")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full JSON key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete English fallback is not exact target English")
        for key, value in values.items():
            expected, _ = g13.resolve_value(locale, key, target[key], base, g12_full, g12_supplements)
            if value != expected:
                errors.append(f"{locale}: incorrect G13 semantic-reuse policy for {key}")
            validate_value(locale, key, target[key], value, errors)

        # The three changed normal meanings are deliberately target-English when addon-owned.
        for key in (
            "config.jei.search.resourceIdSearchMode.comment",
            "gui.jei.editMode.description.hide",
            "gui.jei.editMode.description.hide.wild",
            "key.jei.toggleEditMode",
        ):
            if values.get(key) != target[key]:
                errors.append(f"{locale}: changed/added G13 key must use exact target English: {key}")

    formerly_complete = {"de_de", "fr_fr", "ja_jp", "pt_br", "ru_ru", "sv_se", "zh_cn"}
    for locale, values in supplements.items():
        upstream = g13.fetch_upstream_json(g13.G13_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(
                f"{locale}: supplement key set differs from exact pinned-upstream missing set; "
                f"expected={len(missing)} actual={len(values)}"
            )
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g13.DEBUG_PREFIX) or key.startswith("_comment") for key in values):
            errors.append(f"{locale}: supplement contains debug/comment-only key")
        for key, value in values.items():
            expected, _ = g13.resolve_value(locale, key, target[key], base, g12_full, g12_supplements)
            if value != expected:
                errors.append(f"{locale}: supplement differs from deterministic G13 policy for {key}")
            validate_value(locale, key, target[key], value, errors)
        if ((set(upstream) | set(values)) & normal) != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 103 normal target keys")

        if locale in formerly_complete:
            if values != {"key.jei.toggleEditMode": target["key.jei.toggleEditMode"]}:
                errors.append(f"{locale}: formerly complete G12 locale must need only target-English key.jei.toggleEditMode")

    if supplements.get("uk_ua") is not None and len(supplements["uk_ua"]) != 9:
        errors.append(f"uk_ua: expected 9 G13 supplement keys, got {len(supplements['uk_ua'])}")
    for locale in {"ar_sa", "bg_bg", "cs_cz", "el_gr", "es_es", "fi_fi", "he_il", "it_it", "ko_kr", "lt_lt", "tr_tr"}:
        if locale in supplements and len(supplements[locale]) != 11:
            errors.append(f"{locale}: expected 11 G13 supplement keys, got {len(supplements[locale])}")

    # Explicit placeholder-regression guard for the G12 %CTRL -> G13 %s change.
    for locale, values in full.items():
        for key in ("gui.jei.editMode.description.hide", "gui.jei.editMode.description.hide.wild"):
            if "%s" not in values[key] or "%CTRL" in values[key]:
                errors.append(f"{locale}: G13 runtime placeholder migration failed for {key}")
    for locale, values in supplements.items():
        for key in ("gui.jei.editMode.description.hide", "gui.jei.editMode.description.hide.wild"):
            if key in values and ("%s" not in values[key] or "%CTRL" in values[key]):
                errors.append(f"{locale}: G13 supplement runtime placeholder migration failed for {key}")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G13 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 87:
        errors.append("G13 emitted ownership partitions do not cover exactly 87 selected languages")
    if complete_set != {"en_us", "pl_pl"}:
        errors.append("G13 complete upstream ownership must be exactly en_us + pl_pl")

    with tempfile.TemporaryDirectory(prefix="jei-1.13.2-complete-qa-") as tmp:
        output = Path(tmp)
        full_count, supplement_count, key_count = g13.reconstruct_all(output)
        full_dir = output / "full" / "assets" / "jei" / "lang"
        supplement_dir = output / "supplements" / "assets" / "jei" / "lang"
        full_files = sorted(full_dir.glob("*.json"))
        supplement_files = sorted(supplement_dir.glob("*.json"))
        if full_count != 66 or len(full_files) != 66 or {p.stem for p in full_files} != full_set:
            errors.append("G13 full JSON output file set differs from frozen ownership")
        if supplement_count != 19 or len(supplement_files) != 19 or {p.stem for p in supplement_files} != supplement_set:
            errors.append("G13 supplement JSON output file set differs from frozen ownership")
        if key_count != 106:
            errors.append("G13 complete JSON output key count must be 106")
        for path in full_files + supplement_files:
            try:
                parsed = g13.parse_json(path)
            except Exception as exc:
                errors.append(f"{path.name}: invalid reconstructed JSON: {exc}")
                continue
            if any(key.startswith("_comment") for key in parsed):
                errors.append(f"{path.name}: reconstructed JSON unexpectedly contains comment metadata")

    if policy["translated_or_ai_assisted_full_locale_count"] != 39:
        errors.append("G13 translated/AI-assisted full locale count must remain 39")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.13.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 5.0.0 / Minecraft 1.13.2 complete JSON translation QA")
    print("Complete addon locales: 66")
    print("Inherited translated/AI-assisted full locales: 39")
    print("Documented complete English fallbacks: 27")
    print("Selected complete upstream locales: 2")
    print("Missing-key-only upstream supplements: 19")
    print("Keys per complete addon locale: 106")
    print("101 unchanged G12 semantics are deterministically inherited")
    print("G13 %CTRL -> %s placeholder migration is locked")
    print("Seven former complete upstream locales receive only toggleEditMode")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

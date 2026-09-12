#!/usr/bin/env python3
"""Validate complete G11 Minecraft 1.12.2 / JEI 4.16.5 reconstructed resources."""
from __future__ import annotations

import json
import re
from collections import Counter

import reconstruct_1_12_2 as g11

PLACEHOLDER_RE = re.compile(r"%(?:MODNAME|CTRL|,d|\d+\$[sdif]|[sdif]|%)")


def placeholders(value: str) -> Counter[str]:
    return Counter(PLACEHOLDER_RE.findall(value))


def main() -> int:
    errors: list[str] = []
    base = g11.parse_lang(g11.BASE_SOURCE)
    target = g11.parse_lang(g11.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(g11.DEBUG_PREFIX)}
    scope = json.loads(g11.SCOPE_PATH.read_text(encoding="utf-8"))
    full = g11.reconstruct_full(target, scope)
    supplements = g11.reconstruct_supplements(target, scope)
    g10_full = g11.reconstruct_g10_full()
    g10_supplements = g11.reconstruct_g10_supplements()

    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    reviewed = set(target) - unchanged
    reviewed_normal = {key for key in reviewed if not key.startswith(g11.DEBUG_PREFIX)}

    if (len(full), len(supplements), len(target), len(normal), len(unchanged), len(reviewed_normal)) != (55, 24, 115, 112, 41, 71):
        errors.append(
            "G11 complete counts changed: "
            f"full={len(full)} supplements={len(supplements)} total={len(target)} normal={len(normal)} "
            f"unchanged={len(unchanged)} reviewed_normal={len(reviewed_normal)}"
        )

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 20 or not fallback_locales <= set(full):
        errors.append("G11 documented full-English fallback set must contain 20 addon full locales")

    for locale, values in full.items():
        if set(values) != set(target):
            errors.append(f"{locale}: full file key set differs from target")
            continue
        if locale in fallback_locales and values != target:
            errors.append(f"{locale}: documented complete English fallback is not exact target English")
        if locale not in g10_full:
            errors.append(f"{locale}: G11 full locale has no G10 inheritance source")
            continue
        for key, value in values.items():
            expected = g10_full[locale][key] if key in unchanged else target[key]
            if value != expected:
                errors.append(f"{locale}: incorrect G11 full value policy for {key}")
            if placeholders(value) != placeholders(target[key]):
                errors.append(f"{locale}: placeholder mismatch for {key}")

    for locale, values in supplements.items():
        upstream = g11.fetch_upstream_lang(g11.G11_COMMIT, locale)
        missing = normal - set(upstream)
        if set(values) != missing:
            errors.append(
                f"{locale}: supplement key set differs from exact pinned-upstream missing set; "
                f"expected={len(missing)} actual={len(values)}"
            )
        if set(values) & set(upstream):
            errors.append(f"{locale}: supplement overrides an upstream-owned key")
        if any(key.startswith(g11.DEBUG_PREFIX) for key in values):
            errors.append(f"{locale}: supplement contains debug-only key")

        combined_g10 = g11.g10_combined_locale(locale, g10_full, g10_supplements)
        for key, value in values.items():
            if key in unchanged:
                if key not in combined_g10:
                    errors.append(f"{locale}: unchanged supplement key lacks G10 combined recovery source: {key}")
                elif value != combined_g10[key]:
                    errors.append(f"{locale}: unchanged supplement key does not preserve exact G10 value: {key}")
            else:
                if value != target[key]:
                    errors.append(f"{locale}: reviewed missing meaning must use exact G11 English fallback: {key}")
            if placeholders(value) != placeholders(target[key]):
                errors.append(f"{locale}: supplement placeholder mismatch for {key}")

        combined_normal = (set(upstream) | set(values)) & normal
        if combined_normal != normal:
            errors.append(f"{locale}: upstream + supplement does not cover all 112 normal target keys")

    full_set = set(full)
    supplement_set = set(supplements)
    complete_set = set(scope["selected_upstream_complete_locales"])
    if full_set & supplement_set or full_set & complete_set or supplement_set & complete_set:
        errors.append("G11 emitted ownership partitions overlap")
    if len(full_set | supplement_set | complete_set) != 80:
        errors.append("G11 emitted ownership partitions do not cover exactly 80 selected languages")
    if complete_set != {"en_us"}:
        errors.append("G11 complete upstream ownership must contain only en_us")

    moved = {"hu_hu", "id_id", "no_no", "tr_tr", "vi_vn"}
    if not moved <= supplement_set:
        errors.append("G11 five full-to-upstream ownership migrations are not all supplement locales")
    if "ja_jp" not in supplement_set:
        errors.append("G11 ja_jp must be a supplement locale after losing complete upstream coverage")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.12.2 complete validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: JEI 4.16.5 / Minecraft 1.12.2 complete translation QA")
    print("Complete addon locales: 55")
    print("Inherited translated/AI-assisted full locales: 35")
    print("Documented complete English fallbacks: 20")
    print("Selected complete upstream locales: 1")
    print("Missing-key-only upstream supplements: 24")
    print("Keys per complete addon locale: 115")
    print("Exact unchanged translations preserved: 41 key/value meanings")
    print("Reviewed normal meanings using conservative fallback when missing upstream: 71")
    print("Ownership migrations validated: hu_hu, id_id, no_no, tr_tr, vi_vn and ja_jp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

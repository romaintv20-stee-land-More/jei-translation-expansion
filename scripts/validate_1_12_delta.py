#!/usr/bin/env python3
"""Validate G9 Minecraft 1.12 / JEI 4.7.5 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_12 as g9

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.12-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g9-mc1.12" / "policy.json"
G8_AUDIT_PATH = ROOT / "upstream" / "minecraft-1.11.2-language-audit.json"
PINNED_COMMIT = "6bce08ef068fc0d7ce80ef07512caf85ccd4cab4"
G8_COMMIT = "11023c1f4449b82d0b88366001b058e6949b40ab"
RAW_G9 = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
RAW_G8 = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{G8_COMMIT}/src/main/resources/assets/jei/lang"
DEBUG_PREFIX = "description.jei."
SV_DROPPED = {
    "config.jei.search.resourceIdSearchMode",
    "config.jei.search.resourceIdSearchMode.comment",
    "key.jei.nextPage",
    "key.jei.previousPage",
}


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G9-QA"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def parse_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value
    return values


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    g8_audit = json.loads(G8_AUDIT_PATH.read_text(encoding="utf-8"))
    base = g9.parse_lang(g9.BASE_SOURCE)
    target = g9.parse_lang(g9.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    if base != target:
        errors.append("G9 English source must be identical to G8")
    if (len(target), len(normal)) != (93, 90):
        errors.append(f"G9 English counts changed: total={len(target)} normal={len(normal)}")
    if policy["unchanged_key_and_value_count"] != 93 or policy["new_semantic_translation_entry_count"] != 0:
        errors.append("G9 policy must record 93 unchanged pairs and zero semantic translation delta")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    if (len(full), len(complete), len(incomplete), len(full | complete | incomplete)) != (60, 2, 18, 80):
        errors.append("G9 ownership partition must be 60 full + 2 complete upstream + 18 supplements = 80")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G9 ownership partitions overlap")
    if complete != {"en_us", "ja_jp"}:
        errors.append(f"G9 complete selected upstream locales changed: {sorted(complete)}")
    if set(scope["new_selected_primary_languages"]) != g9.NEW_SELECTED:
        errors.append("G9 new selected language set differs from reconstruction policy")
    if not g9.NEW_SELECTED <= full:
        errors.append("all eight newly selected G9 languages must be addon-owned full locales")
    if scope["raw_language_count"] != 107 or scope["selected_scope_count"] != 80:
        errors.append("G9 raw/selected scope counts must remain 107/80")
    if set(policy["documented_full_english_fallback_locales"]) != set(scope["documented_full_english_fallback_locales"]):
        errors.append("G9 fallback locale lists differ between scope and policy")

    try:
        remote_target = parse_text(fetch_bytes(f"{RAW_G9}/en_us.lang").decode("utf-8"))
        if remote_target != target:
            errors.append("stored G9 English source differs from pinned JEI 4.7.5")

        g8_completeness = g8_audit["selected_upstream_locale_completeness"]
        for locale in sorted(complete | incomplete):
            live = parse_text(fetch_bytes(f"{RAW_G9}/{locale}.lang").decode("utf-8"))
            live_missing = set(normal - set(live))
            if locale == "ja_jp":
                expected_missing: set[str] = set()
            elif locale == "sv_se":
                expected_missing = set(g8_completeness[locale]["missing_normal_keys"]) | SV_DROPPED
            else:
                expected_missing = set(g8_completeness[locale]["missing_normal_keys"])
            if live_missing != expected_missing:
                errors.append(
                    f"{locale}: live G9 missing-key set differs from frozen reconstruction rule; "
                    f"expected={sorted(expected_missing)} live={sorted(live_missing)}"
                )

        recovery = g9.parse_lang(g9.SV_RECOVERY_PATH)
        g8_sv = parse_text(fetch_bytes(f"{RAW_G8}/sv_se.lang").decode("utf-8"))
        if set(recovery) != SV_DROPPED:
            errors.append("G9 Swedish recovery file must contain exactly the four dropped keys")
        for key in SV_DROPPED:
            if recovery.get(key) != g8_sv.get(key):
                errors.append(f"sv_se: recovery value is not exact pinned G8 upstream value for {key}")
    except Exception as exc:
        errors.append(f"failed live G9/G8 upstream verification: {exc}")

    if audit["minecraft_asset_index"]["raw_language_count_including_en_us"] != 107:
        errors.append("G9 frozen audit raw Minecraft language count changed")
    if audit["selected_scope_count"] != 80 or audit["addon_full_locale_count"] != 60:
        errors.append("G9 frozen audit scope/ownership counts changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.12 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.12 / JEI 4.7.5 G9 source, scope and ownership QA")
    print("English: 93 keys / 90 normal / 3 debug; all 93 unchanged from G8")
    print("Minecraft raw/selected: 107 / 80")
    print("New selected real-world languages: 8")
    print("Selected upstream: 20 (2 complete + 18 supplements)")
    print("Addon-owned full locales: 60")
    print("ja_jp complete upstream; sv_se four-key upstream regression recovered from pinned G8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

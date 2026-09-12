#!/usr/bin/env python3
"""Validate G10 Minecraft 1.12.1 / JEI 4.7.8 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_12_1 as g10

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.12.1-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12.1-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g10-mc1.12.1" / "policy.json"
G9_SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12-language-scope.json"
PINNED_COMMIT = "7f4160ed969fad85e8c4a14809c66402c51592b2"
G9_COMMIT = "6bce08ef068fc0d7ce80ef07512caf85ccd4cab4"
RAW_G10 = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
RAW_G9 = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{G9_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + PINNED_COMMIT
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G10-QA"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch_bytes(url).decode("utf-8"))


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
    g9_scope = json.loads(G9_SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    base = g10.parse_lang(g10.BASE_SOURCE)
    target = g10.parse_lang(g10.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    if base != target:
        errors.append("G10 English source differs from G9")
    if (len(target), len(normal)) != (93, 90):
        errors.append(f"G10 English counts changed: total={len(target)} normal={len(normal)}")
    if policy["unchanged_key_and_value_count"] != 93 or policy["new_semantic_translation_entry_count"] != 0:
        errors.append("G10 policy must freeze 93 unchanged pairs and zero new semantic entries")

    ownership_fields = [
        "addon_full_locales", "selected_upstream_complete_locales", "selected_upstream_incomplete_locales",
        "documented_full_english_fallback_locales"
    ]
    for field in ownership_fields:
        if scope[field] != g9_scope[field]:
            errors.append(f"G10 {field} differs from G9")
    if (scope["raw_language_count"], scope["selected_scope_count"], scope["addon_full_locale_count"]) != (107, 80, 60):
        errors.append("G10 frozen scope counts must remain 107/80/60")
    if not scope["minecraft_asset_index_same_as_1_12"]:
        errors.append("G10 must record exact Minecraft 1.12 asset-index reuse")

    try:
        live_locales = sorted(
            Path(item["name"]).stem.lower()
            for item in fetch_json(CONTENTS_URL)
            if item.get("type") == "file" and item.get("name", "").endswith(".lang")
        )
        if len(live_locales) != 23:
            errors.append(f"expected 23 JEI 4.7.8 upstream language files, got {len(live_locales)}")
        for locale in live_locales:
            g10_values = parse_text(fetch_bytes(f"{RAW_G10}/{locale}.lang").decode("utf-8"))
            g9_values = parse_text(fetch_bytes(f"{RAW_G9}/{locale}.lang").decode("utf-8"))
            if g10_values != g9_values:
                errors.append(f"{locale}: JEI language resource changed unexpectedly from G9 to G10")
        if parse_text(fetch_bytes(f"{RAW_G10}/en_us.lang").decode("utf-8")) != target:
            errors.append("stored G10 English source differs from pinned JEI 4.7.8")
    except Exception as exc:
        errors.append(f"failed live JEI 4.7.8/G9 comparison: {exc}")

    if audit["minecraft_asset_index"]["sha1"] != "a21e1ded1a24ea1548dd8db0cf30b6acb02655a9":
        errors.append("G10 frozen Minecraft asset-index SHA changed")
    if not audit["minecraft_asset_index"]["same_as_minecraft_1_12"]:
        errors.append("G10 frozen audit must state exact 1.12 asset-index reuse")
    if not audit["jei_language_resources_changed_from_1_12_endpoint"] is False:
        errors.append("G10 frozen audit must state no JEI language resource changes")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    if (len(full), len(complete), len(incomplete), len(full | complete | incomplete)) != (60, 2, 18, 80):
        errors.append("G10 ownership partition must be 60 full + 2 complete + 18 supplements = 80")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G10 ownership partitions overlap")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.12.1 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.12.1 / JEI 4.7.8 G10 source, scope and ownership QA")
    print("English: 93 keys / 90 normal / 3 debug; all 93 unchanged from G9")
    print("Minecraft raw/selected: 107 / 80; exact 1.12 asset index reused")
    print("JEI language resources: unchanged from G9")
    print("Selected upstream: 20 (2 complete + 18 supplements)")
    print("Addon-owned full locales: 60")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

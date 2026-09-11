#!/usr/bin/env python3
"""Validate G8 Minecraft 1.11.2 / JEI 4.5.1 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_11_2 as g8

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.11.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.11.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g8-mc1.11.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.11-to-1.11.2.json"
PINNED_COMMIT = "11023c1f4449b82d0b88366001b058e6949b40ab"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
MC_ASSET_INDEX = "https://piston-meta.mojang.com/v1/packages/c64959fe73672e9b053b157f57b6aba318d0b3b5/1.11.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G8-QA"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch_bytes(url).decode("utf-8"))


def parse_lang_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value
    return values


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    base = g8.parse_lang(g8.BASE_SOURCE)
    target = g8.parse_lang(g8.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])
    if (len(target), len(normal), len(unchanged), len(added), len(removed), len(changed)) != (93, 90, 85, 7, 1, 1):
        errors.append(
            "G8 English counts changed: "
            f"total={len(target)} normal={len(normal)} unchanged={len(unchanged)} "
            f"added={len(added)} removed={len(removed)} changed={len(changed)}"
        )
    if added != sorted(diff["added_keys"]):
        errors.append("G8 added-key set differs from frozen diff")
    if removed != sorted(diff["removed_keys"]):
        errors.append("G8 removed-key set differs from frozen diff")
    if changed != sorted(diff["changed_english_values"]):
        errors.append("G8 changed-value key set differs from frozen diff")
    if changed != ["key.jei.recipeBack"]:
        errors.append("G8 expected only key.jei.recipeBack to change English meaning")
    if set(policy["reviewed_keys"]) != set(diff["reviewed_added_or_changed_keys"]):
        errors.append("G8 policy reviewed-key set differs from exact diff")

    try:
        remote = parse_lang_text(fetch_bytes(f"{RAW_BASE}/en_us.lang").decode("utf-8"))
        if remote != target:
            errors.append("stored G8 English source differs from pinned JEI 4.5.1")
        listing = fetch_json(CONTENTS_URL)
        live_locales = sorted(
            Path(item["name"]).stem
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".lang")
        )
        if live_locales != sorted(audit["jei_upstream_locales"]):
            errors.append("pinned JEI 4.5.1 locale list differs from frozen audit")
        if any(locale != locale.lower() for locale in live_locales):
            errors.append("JEI 4.5.1 locale filenames must remain lowercase")

        completeness = audit["selected_upstream_locale_completeness"]
        selected = set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])
        for locale in sorted(selected):
            values = parse_lang_text(fetch_bytes(f"{RAW_BASE}/{locale}.lang").decode("utf-8"))
            missing = sorted(normal - set(values))
            expected = sorted(completeness[locale]["missing_normal_keys"])
            if missing != expected:
                errors.append(f"{locale}: live missing-key set differs from frozen G8 audit")
    except Exception as exc:
        errors.append(f"failed to verify pinned JEI 4.5.1 upstream: {exc}")

    try:
        asset_index = fetch_json(MC_ASSET_INDEX)
        mc_codes = {
            Path(name).stem.lower()
            for name in asset_index.get("objects", {})
            if name.startswith("minecraft/lang/") and name.endswith(".lang")
        } | {"en_us"}
        if len(mc_codes) != 95:
            errors.append(f"expected 95 Minecraft 1.11.2 language codes, got {len(mc_codes)}")
        if scope["raw_language_count"] != 95 or scope["selected_scope_count"] != 72:
            errors.append("G8 raw/selected scope counts changed")
        if not scope["minecraft_asset_index_same_as_1_11"]:
            errors.append("G8 must record the exact shared Minecraft 1.11 asset index")
    except Exception as exc:
        errors.append(f"failed to verify Minecraft 1.11.2 asset index: {exc}")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    if (len(full), len(complete), len(incomplete)) != (52, 1, 19):
        errors.append("G8 ownership partition must be 52 full + 1 complete upstream + 19 supplements")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G8 ownership partitions overlap")
    if len(full | complete | incomplete) != 72:
        errors.append("G8 ownership partition does not cover exactly 72 selected languages")
    if complete != {"en_us"}:
        errors.append("G8 expected en_us to be the only complete selected upstream locale")
    if not {"ru_ru", "sv_se", "uk_ua"}.issubset(incomplete):
        errors.append("G8 expected ru_ru, sv_se and uk_ua to become supplement locales")
    if any(locale != locale.lower() for locale in full | complete | incomplete):
        errors.append("G8 scope contains non-lowercase runtime locale identifiers")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.11.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.11.2 / JEI 4.5.1 G8 source, scope and ownership QA")
    print("English: 93 keys / 90 normal / 3 debug")
    print("G7 -> G8: 85 unchanged, 7 added, 1 removed, 1 changed")
    print("Minecraft raw/selected: 95 / 72; exact 1.11 asset index reused")
    print("Selected upstream: 20 (1 complete + 19 supplements)")
    print("Addon-owned full locales: 52")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

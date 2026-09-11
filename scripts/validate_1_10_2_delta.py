#!/usr/bin/env python3
"""Validate G6 Minecraft 1.10.2 / JEI 3.14.8 source, scope and ownership."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import reconstruct_1_10_2 as g6

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.10.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.10.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g6-mc1.10.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.10-to-1.10.2.json"
PINNED_COMMIT = "446af20eaa73d260517f0adc737232437363f78d"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
MC_ASSET_INDEX = "https://piston-meta.mojang.com/v1/packages/7c2800b458376b8fc0b738382fb7784328fddda9/1.10.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G6-QA"})
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


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    base = g6.parse_lang(g6.BASE_SOURCE)
    target = g6.parse_lang(g6.TARGET_SOURCE)
    added, removed, changed, unchanged = g6.source_sets(base, target)
    normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    if len(target) != 87 or len(normal) != 84:
        errors.append(f"target key counts changed: total={len(target)}, normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (53, 25, 16, 9):
        errors.append(
            f"G5->G6 diff count mismatch: unchanged={len(unchanged)}, added={len(added)}, "
            f"removed={len(removed)}, changed={len(changed)}"
        )
    if set(diff["added_keys"]) != added or set(diff["removed_keys"]) != removed:
        errors.append("static diff manifest added/removed sets do not match source")
    if set(diff["changed_english_values"]) != changed:
        errors.append("static diff manifest changed-value set does not match source")
    if diff["unchanged_key_and_value_count"] != len(unchanged):
        errors.append("static diff manifest unchanged count mismatch")

    if target[g6.CRAFTING_KEY] != "Crafting":
        errors.append("G6 Crafting semantic-reversion target changed unexpectedly")
    fallback_review = set(policy["conservative_review_fallback_keys"])
    if fallback_review != (added | changed) - {g6.CRAFTING_KEY}:
        errors.append("G6 conservative review fallback set is not exactly added+changed minus Crafting")
    if len(fallback_review) != 33:
        errors.append("G6 conservative review fallback key count must be 33")

    # Minecraft 1.10.2 shares the exact 1.10 asset index.
    try:
        asset_index = fetch_json(MC_ASSET_INDEX)
        mc_codes = {
            Path(name).stem
            for name in asset_index.get("objects", {})
            if name.startswith("minecraft/lang/") and name.endswith(".lang")
        } | {"en_US"}
        if len(mc_codes) != 94:
            errors.append(f"expected 94 Minecraft language codes, got {len(mc_codes)}")
        if scope["raw_language_count"] != len(mc_codes) or scope["selected_scope_count"] != 72:
            errors.append("G6 Minecraft/scope counts mismatch")
    except Exception as exc:
        errors.append(f"failed to verify Minecraft asset index: {exc}")

    # Verify exact pinned upstream files, blob SHAs, completeness and ownership.
    live_values: dict[str, dict[str, str]] = {}
    try:
        listing = fetch_json(CONTENTS_URL)
        live_locales = sorted(
            Path(item["name"]).stem
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".lang")
        )
        if live_locales != sorted(audit["jei_upstream_locales"]):
            errors.append("pinned JEI upstream locale list differs from audit manifest")
        for locale in live_locales:
            data = fetch_bytes(f"{RAW_BASE}/{locale}.lang")
            if git_blob_sha(data) != audit["jei_upstream_blob_shas"][locale]:
                errors.append(f"{locale}: pinned upstream blob SHA mismatch")
            live_values[locale] = parse_lang_text(data.decode("utf-8"))

        selected_complete = set(scope["selected_upstream_complete_locales"])
        selected_incomplete = set(scope["selected_upstream_incomplete_locales"])
        selected_upstream = selected_complete | selected_incomplete
        if len(selected_upstream) != 20 or selected_complete != {"de_DE", "en_US", "ru_RU", "uk_UA"}:
            errors.append("G6 selected upstream ownership set changed")
        if len(selected_incomplete) != 16:
            errors.append("G6 selected incomplete upstream count must be 16")

        audit_comp = audit["selected_upstream_locale_completeness"]
        for locale in sorted(selected_upstream):
            values = live_values[locale]
            missing = normal - set(values)
            expected = set(audit_comp[locale]["missing_normal_keys"])
            if missing != expected:
                errors.append(
                    f"{locale}: live missing set differs from audit: "
                    f"expected={sorted(expected)}, actual={sorted(missing)}"
                )
            if len(normal & set(values)) != audit_comp[locale]["normal_present"]:
                errors.append(f"{locale}: live present count differs from audit")
            if locale in selected_complete and missing:
                errors.append(f"{locale}: marked complete upstream but is missing keys")
            if locale in selected_incomplete and not missing:
                errors.append(f"{locale}: marked incomplete upstream but is complete")
    except Exception as exc:
        errors.append(f"failed to verify pinned JEI upstream ownership: {exc}")

    full_locales = set(scope["addon_full_locales"])
    if len(full_locales) != 52:
        errors.append("G6 addon full locale count must be 52")
    if full_locales & set(scope["selected_upstream_complete_locales"]):
        errors.append("G6 addon full locales overlap complete upstream locales")
    if full_locales & set(scope["selected_upstream_incomplete_locales"]):
        errors.append("G6 addon full locales overlap supplement locales")
    if len(full_locales | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])) != 72:
        errors.append("G6 ownership partition does not cover exactly 72 selected languages")

    if policy["full_addon_locale_count"] != 52 or policy["selected_upstream_supplement_locale_count"] != 16:
        errors.append("G6 policy ownership counts mismatch")
    if policy["documented_full_english_fallback_count"] != 12:
        errors.append("G6 full-English fallback locale count must remain 12")
    if policy["translated_or_ai_assisted_full_locale_count"] != 40:
        errors.append("G6 translated/AI-assisted full locale count must be 40")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.10.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.10.2 / JEI 3.14.8 G6 source, scope and ownership QA")
    print("English: 87 keys / 84 normal / 3 debug")
    print("G5 -> G6: 53 unchanged, 25 added, 16 removed, 9 changed")
    print("Minecraft raw/selected: 94 / 72")
    print("Selected upstream: 20 (4 complete + 16 supplements)")
    print("Addon-owned full locales: 52")
    print("Conservative added/changed fallback keys: 33")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

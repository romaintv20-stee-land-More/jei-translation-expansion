#!/usr/bin/env python3
"""Validate G11 Minecraft 1.12.2 / JEI 4.16.5 source, scope and ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_12_2 as g11

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.12.2-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.12.2-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g11-mc1.12.2" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.12.1-to-1.12.2.json"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + g11.G11_COMMIT
DEBUG_PREFIX = "description.jei."


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G11-QA"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    errors: list[str] = []
    base = g11.parse_lang(g11.BASE_SOURCE)
    target = g11.parse_lang(g11.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    added = set(target) - set(base)
    removed = set(base) - set(target)
    changed = {key for key in set(base) & set(target) if base[key] != target[key]}
    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    changed_debug = {key for key in changed if key.startswith(DEBUG_PREFIX)}
    reviewed_normal = added | (changed - changed_debug)

    if (len(target), len(normal)) != (115, 112):
        errors.append(f"G11 English counts changed: total={len(target)} normal={len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed), len(changed_debug), len(reviewed_normal)) != (41, 33, 11, 41, 3, 71):
        errors.append(
            "G11 English diff changed: "
            f"unchanged={len(unchanged)} added={len(added)} removed={len(removed)} "
            f"changed={len(changed)} changed_debug={len(changed_debug)} reviewed_normal={len(reviewed_normal)}"
        )
    if set(diff["added_keys"]) != added or set(diff["removed_keys"]) != removed or set(diff["changed_english_values"]) != changed:
        errors.append("G11 diff manifest key sets differ from computed source diff")
    for key, pair in diff["changed_english_values"].items():
        if pair != [base[key], target[key]]:
            errors.append(f"G11 diff manifest old/new value mismatch for {key}")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    if (len(full), len(complete), len(incomplete), len(full | complete | incomplete)) != (55, 1, 24, 80):
        errors.append("G11 ownership partition must be 55 full + 1 complete + 24 supplements = 80")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G11 ownership partitions overlap")
    if complete != {"en_us"}:
        errors.append(f"G11 complete selected upstream set changed: {sorted(complete)}")
    if set(scope["jei_upstream_unselected_or_nonmatching_locales"]) != {"kk_kz", "pt_pt", "zh_tw"}:
        errors.append("G11 unselected JEI locale set changed")
    if scope["raw_language_count"] != 107 or scope["selected_scope_count"] != 80:
        errors.append("G11 Minecraft raw/selected scope counts must remain 107/80")
    if "kk_kz" in full | complete | incomplete:
        errors.append("kk_kz must remain outside scope because Minecraft 1.12.2 does not expose that asset locale")

    try:
        remote_english = g11.fetch_upstream_lang(g11.G11_COMMIT, "en_us")
        if remote_english != target:
            errors.append("stored G11 English source differs from pinned JEI 4.16.5")
        listing = fetch_json(CONTENTS_URL)
        live_locales = {
            Path(item["name"]).stem.lower()
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".lang")
        }
        if len(live_locales) != 28:
            errors.append(f"expected 28 JEI 4.16.5 locale files, got {len(live_locales)}")
        if (full & live_locales):
            errors.append("G11 addon-full ownership overlaps live JEI upstream locale files")
        if not (complete | incomplete) <= live_locales:
            errors.append("G11 selected upstream ownership contains locale absent from live pinned JEI")
        for locale in sorted(complete):
            upstream = g11.fetch_upstream_lang(g11.G11_COMMIT, locale)
            missing = normal - set(upstream)
            if missing:
                errors.append(f"{locale}: frozen complete upstream locale is missing {len(missing)} normal keys")
        for locale in sorted(incomplete):
            upstream = g11.fetch_upstream_lang(g11.G11_COMMIT, locale)
            missing = normal - set(upstream)
            if not missing:
                errors.append(f"{locale}: frozen supplement locale is now complete upstream")
    except Exception as exc:
        errors.append(f"failed live G11 pinned-upstream ownership verification: {exc}")

    if audit["minecraft_asset_index"]["sha1"] != "a21e1ded1a24ea1548dd8db0cf30b6acb02655a9":
        errors.append("G11 frozen Minecraft asset-index SHA changed")
    if audit["scope_review"]["minecraft_unselected_code_count"] != 27:
        errors.append("G11 frozen unselected Minecraft code count changed")
    if policy["reviewed_normal_added_or_changed_key_count"] != 71:
        errors.append("G11 policy reviewed-normal-key count changed")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.12.2 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.12.2 / JEI 4.16.5 G11 source, scope and ownership QA")
    print("English: 115 keys / 112 normal / 3 debug")
    print("G10 -> G11: 41 unchanged, 33 added, 11 removed, 41 changed")
    print("Reviewed normal added/changed meanings: 71")
    print("Minecraft raw/selected: 107 / 80; exact 1.12 asset index retained")
    print("Selected upstream: 25 (1 complete + 24 supplements)")
    print("Addon-owned full locales: 55")
    print("kk_kz is JEI-only at this endpoint and remains outside Minecraft-facing scope")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

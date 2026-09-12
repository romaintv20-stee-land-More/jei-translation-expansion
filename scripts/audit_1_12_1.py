#!/usr/bin/env python3
"""Audit pinned Minecraft 1.12.1 / JEI 4.7.8 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.12" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.12.1" / "en_us.lang"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.12-language-scope.json"
BASE_AUDIT = ROOT / "upstream" / "minecraft-1.12-language-audit.json"
PINNED_COMMIT = "7f4160ed969fad85e8c4a14809c66402c51592b2"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + PINNED_COMMIT
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G10-audit"})
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


def parse_lang(path: Path) -> dict[str, str]:
    return parse_lang_text(path.read_text(encoding="utf-8"))


def language_codes(asset_index: dict) -> set[str]:
    return {
        Path(name).stem.lower()
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/") and name.endswith(".lang")
    } | {"en_us"}


def main() -> int:
    errors: list[str] = []
    base = parse_lang(BASE_SOURCE)
    target = parse_lang(TARGET_SOURCE)
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    if base != target:
        errors.append("G10 English source differs from G9 despite pinned upstream identity")

    remote_english = parse_lang_text(fetch_bytes(f"{RAW_BASE}/en_us.lang").decode("utf-8"))
    if remote_english != target:
        errors.append("stored 1.12.1 English source differs from pinned JEI 4.7.8 upstream")

    listing = fetch_json(CONTENTS_URL)
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in listing
        if item.get("type") == "file" and item.get("name", "").endswith(".lang")
    )
    completeness: dict[str, dict] = {}
    for locale in upstream_locales:
        values = parse_lang_text(fetch_bytes(f"{RAW_BASE}/{locale}.lang").decode("utf-8"))
        missing = sorted(target_normal - set(values))
        completeness[locale] = {"present": len(target_normal & set(values)), "missing": missing}

    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(base_scope["addon_full_locales"]) | set(base_scope["selected_upstream_complete_locales"]) | set(base_scope["selected_upstream_incomplete_locales"])
    if len(selected) != 80:
        errors.append(f"expected inherited G9 selected scope of 80, got {len(selected)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.12"), None)
    target_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.12.1"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.12/1.12.1 missing from Mojang version manifest")
        base_meta = target_meta = {}
        base_asset = target_asset = {}
    else:
        base_meta = fetch_json(base_entry["url"])
        target_meta = fetch_json(target_entry["url"])
        base_asset = fetch_json(base_meta["assetIndex"]["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])

    base_codes = language_codes(base_asset) if base_asset else set()
    target_codes = language_codes(target_asset) if target_asset else set()
    added_mc = sorted(target_codes - base_codes)
    removed_mc = sorted(base_codes - target_codes)
    if selected - target_codes:
        errors.append("selected G9 languages absent from Minecraft 1.12.1: " + ", ".join(sorted(selected - target_codes)))

    selected_upstream = sorted(selected & set(upstream_locales))
    selected_complete = sorted(locale for locale in selected_upstream if not completeness[locale]["missing"])
    selected_incomplete = sorted(locale for locale in selected_upstream if completeness[locale]["missing"])
    addon_full = sorted(selected - set(upstream_locales))

    print("Minecraft 1.12.1 / JEI 4.7.8 localization audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print(f"English keys: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print("G9 -> G10: unchanged=93 added=0 removed=0 changed=0")
    if base_meta and target_meta:
        ba = base_meta.get("assetIndex", {})
        ta = target_meta.get("assetIndex", {})
        print(f"Minecraft 1.12 asset index: id={ba.get('id')} sha1={ba.get('sha1')} url={ba.get('url')}")
        print(f"Minecraft 1.12.1 asset index: id={ta.get('id')} sha1={ta.get('sha1')} url={ta.get('url')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1') and ba.get('url') == ta.get('url')}")
    print(f"Minecraft language codes: 1.12={len(base_codes)} 1.12.1={len(target_codes)}")
    print(f"Added codes since 1.12: {', '.join(added_mc) or '(none)'}")
    print(f"Removed codes since 1.12: {', '.join(removed_mc) or '(none)'}")
    print(f"Inherited selected scope: {len(selected)}")
    print(f"Selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete)}")
    print(f"Selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete)}")
    print(f"Addon-owned full locales ({len(addon_full)}): {', '.join(addon_full)}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned Minecraft 1.12.1 / JEI 4.7.8 audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

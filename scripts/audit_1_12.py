#!/usr/bin/env python3
"""Audit pinned Minecraft 1.12 / JEI 4.7.5 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.11.2" / "en_us.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.12" / "en_us.lang"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.11.2-language-scope.json"
PINNED_COMMIT = "6bce08ef068fc0d7ce80ef07512caf85ccd4cab4"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
MC_1_11_ASSET_INDEX = "https://piston-meta.mojang.com/v1/packages/c64959fe73672e9b053b157f57b6aba318d0b3b5/1.11.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G9-audit"})
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
    codes = {
        Path(name).stem.lower()
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/") and name.endswith(".lang")
    }
    codes.add("en_us")
    return codes


def main() -> int:
    errors: list[str] = []
    base = parse_lang(BASE_SOURCE)
    target = parse_lang(TARGET_SOURCE)
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    remote_english = parse_lang_text(fetch_bytes(f"{RAW_BASE}/en_us.lang").decode("utf-8"))
    if remote_english != target:
        errors.append("stored 1.12 English source differs from pinned JEI 4.7.5 upstream")

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])
    if (len(unchanged), len(added), len(removed), len(changed)) != (93, 0, 0, 0):
        errors.append(
            "unexpected G8 -> G9 English diff: "
            f"unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}"
        )

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
        extra = sorted(set(values) - set(target))
        completeness[locale] = {
            "present": len(target_normal & set(values)),
            "target": len(target_normal),
            "missing": missing,
            "extra": extra,
        }

    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(base_scope["addon_full_locales"])
    selected.update(base_scope["selected_upstream_complete_locales"])
    selected.update(base_scope["selected_upstream_incomplete_locales"])
    if len(selected) != 72:
        errors.append(f"expected inherited G8 selected scope of 72, got {len(selected)}")

    manifest = fetch_json(VERSION_MANIFEST)
    version_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.12"), None)
    if not version_entry:
        errors.append("Minecraft 1.12 missing from Mojang version manifest")
        target_meta = {}
        target_asset = {}
    else:
        target_meta = fetch_json(version_entry["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])

    base_asset = fetch_json(MC_1_11_ASSET_INDEX)
    base_codes = language_codes(base_asset)
    target_codes = language_codes(target_asset) if target_asset else set()
    added_mc = sorted(target_codes - base_codes)
    removed_mc = sorted(base_codes - target_codes)
    inherited_missing_from_mc = sorted(selected - target_codes)
    if inherited_missing_from_mc:
        errors.append(
            "inherited selected G8 languages absent from Minecraft 1.12: "
            + ", ".join(inherited_missing_from_mc)
        )

    selected_upstream = sorted(selected & set(upstream_locales))
    selected_complete = sorted(locale for locale in selected_upstream if not completeness[locale]["missing"])
    selected_incomplete = sorted(locale for locale in selected_upstream if completeness[locale]["missing"])
    addon_full_inherited = sorted(selected - set(upstream_locales))

    print("Minecraft 1.12 / JEI 4.7.5 localization audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print(f"English keys: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G8 -> G9: unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}")
    print(f"JEI upstream locales ({len(upstream_locales)}): {', '.join(upstream_locales)}")
    print("Upstream completeness against normal target keys:")
    for locale in upstream_locales:
        item = completeness[locale]
        print(
            f"  {locale}: {item['present']}/{item['target']} missing={len(item['missing'])} "
            f"[{', '.join(item['missing'])}] extra={len(item['extra'])}"
        )
    if target_meta:
        asset = target_meta.get("assetIndex", {})
        print(
            "Minecraft 1.12 asset index: "
            f"id={asset.get('id')} sha1={asset.get('sha1')} url={asset.get('url')}"
        )
    print(f"Minecraft 1.11 language codes: {len(base_codes)}")
    print(f"Minecraft 1.12 language codes: {len(target_codes)}")
    print(f"Minecraft language codes added since 1.11: {', '.join(added_mc) or '(none)'}")
    print(f"Minecraft language codes removed since 1.11: {', '.join(removed_mc) or '(none)'}")
    print(f"Inherited selected scope: {len(selected)}")
    print(f"Selected upstream locales ({len(selected_upstream)}): {', '.join(selected_upstream)}")
    print(f"Selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete)}")
    print(f"Selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete)}")
    print(f"Inherited addon-owned full locales ({len(addon_full_inherited)}): {', '.join(addon_full_inherited)}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned Minecraft 1.12 / JEI 4.7.5 audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

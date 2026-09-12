#!/usr/bin/env python3
"""Audit final Minecraft 1.12.2 / JEI 4.16.5 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.12.1" / "en_us.lang"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.12.1-language-scope.json"
PINNED_COMMIT = "f98331af6b1f7d59da01beecacd681c16dd548b9"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + PINNED_COMMIT
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G11-audit"})
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


def language_metadata(asset_index: dict) -> dict[str, dict]:
    obj = asset_index.get("objects", {}).get("minecraft/lang/languages.json")
    if not obj or "hash" not in obj:
        return {}
    sha1 = obj["hash"]
    url = f"https://resources.download.minecraft.net/{sha1[:2]}/{sha1}"
    raw = fetch_json(url)
    return {str(code).lower(): info for code, info in raw.items()}


def main() -> int:
    errors: list[str] = []
    base = parse_lang(BASE_SOURCE)
    target = parse_lang_text(fetch_bytes(f"{RAW_BASE}/en_us.lang").decode("utf-8"))
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])

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
    inherited = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if len(inherited) != 80:
        errors.append(f"expected inherited G10 selected scope of 80, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.12.1"), None)
    target_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.12.2"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.12.1/1.12.2 missing from Mojang version manifest")
        base_meta = target_meta = {}
        base_asset = target_asset = {}
    else:
        base_meta = fetch_json(base_entry["url"])
        target_meta = fetch_json(target_entry["url"])
        base_asset = fetch_json(base_meta["assetIndex"]["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])

    base_codes = language_codes(base_asset) if base_asset else set()
    target_codes = language_codes(target_asset) if target_asset else set()
    target_language_metadata = language_metadata(target_asset) if target_asset else {}
    added_mc = sorted(target_codes - base_codes)
    removed_mc = sorted(base_codes - target_codes)
    missing_inherited = sorted(inherited - target_codes)
    if missing_inherited:
        errors.append("inherited selected G10 languages absent from Minecraft 1.12.2: " + ", ".join(missing_inherited))

    inherited_upstream = sorted(inherited & set(upstream_locales))
    inherited_complete = sorted(locale for locale in inherited_upstream if not completeness[locale]["missing"])
    inherited_incomplete = sorted(locale for locale in inherited_upstream if completeness[locale]["missing"])
    inherited_full = sorted(inherited - set(upstream_locales))
    unselected_minecraft = sorted(target_codes - inherited)

    print("Minecraft 1.12.2 / JEI 4.16.5 final localization audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print(f"English keys: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G10 -> G11 unchanged: {len(unchanged)}")
    print(f"G10 -> G11 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G10 -> G11 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G10 -> G11 changed ({len(changed)}):")
    for key in changed:
        print(f"  {key}: {base[key]!r} -> {target[key]!r}")

    print(f"JEI upstream locales ({len(upstream_locales)}): {', '.join(upstream_locales)}")
    print("Upstream completeness against normal target keys:")
    for locale in upstream_locales:
        info = completeness[locale]
        print(
            f"  {locale}: {info['present']}/{info['target']} "
            f"missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}"
        )

    if base_meta and target_meta:
        ba = base_meta.get("assetIndex", {})
        ta = target_meta.get("assetIndex", {})
        print(f"Minecraft 1.12.1 asset index: id={ba.get('id')} sha1={ba.get('sha1')} url={ba.get('url')}")
        print(f"Minecraft 1.12.2 asset index: id={ta.get('id')} sha1={ta.get('sha1')} url={ta.get('url')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1') and ba.get('url') == ta.get('url')}")
    print(f"Minecraft language codes: 1.12.1={len(base_codes)} 1.12.2={len(target_codes)}")
    print(f"Added codes since 1.12.1: {', '.join(added_mc) or '(none)'}")
    print(f"Removed codes since 1.12.1: {', '.join(removed_mc) or '(none)'}")
    print(f"Inherited selected scope: {len(inherited)}")
    print(f"Unselected Minecraft codes ({len(unselected_minecraft)}):")
    for code in unselected_minecraft:
        info = target_language_metadata.get(code, {})
        name = info.get("name", "?")
        region = info.get("region", "?")
        bidirectional = info.get("bidirectional", False)
        print(f"  {code}: name={name!r} region={region!r} bidirectional={bidirectional}")
    print(f"Inherited selected upstream complete ({len(inherited_complete)}): {', '.join(inherited_complete)}")
    print(f"Inherited selected upstream incomplete ({len(inherited_incomplete)}): {', '.join(inherited_incomplete)}")
    print(f"Inherited addon-owned full locales ({len(inherited_full)}): {', '.join(inherited_full)}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned final Minecraft 1.12.2 / JEI 4.16.5 audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

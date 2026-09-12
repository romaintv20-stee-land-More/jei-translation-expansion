#!/usr/bin/env python3
"""Audit pinned Minecraft 1.13 / JEI 4.14.4 localization endpoint.

This generation is the legacy .lang -> JSON resource-format transition.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.12.2" / "en_us.lang"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.12.2-language-scope.json"
PINNED_COMMIT = "380bc11efb548abd804c65b763c911ebf9d06e2c"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang?ref=" + PINNED_COMMIT
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G12-audit"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch_bytes(url).decode("utf-8"))


def parse_lang(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value
    return values


def parse_jei_json_bytes(data: bytes) -> dict[str, str]:
    raw = json.loads(data.decode("utf-8"))
    return {
        str(key): str(value)
        for key, value in raw.items()
        if not str(key).startswith("_")
    }


def language_codes(asset_index: dict) -> set[str]:
    codes: set[str] = set()
    for name in asset_index.get("objects", {}):
        if not name.startswith("minecraft/lang/"):
            continue
        path = Path(name)
        if path.name == "languages.json":
            continue
        if path.suffix in {".lang", ".json"}:
            codes.add(path.stem.lower())
    codes.add("en_us")
    return codes


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
    target = parse_jei_json_bytes(fetch_bytes(f"{RAW_BASE}/en_us.json"))
    base_normal = {key for key in base if not key.startswith(DEBUG_PREFIX)}
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])

    listing = fetch_json(CONTENTS_URL)
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in listing
        if item.get("type") == "file" and item.get("name", "").endswith(".json")
    )
    completeness: dict[str, dict] = {}
    for locale in upstream_locales:
        values = parse_jei_json_bytes(fetch_bytes(f"{RAW_BASE}/{locale}.json"))
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
        errors.append(f"expected G11 selected scope of 80, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.12.2"), None)
    target_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.13"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.12.2/1.13 missing from Mojang version manifest")
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
    inherited_missing = sorted(inherited - target_codes)
    inherited_present = inherited & target_codes
    new_candidates = sorted(target_codes - inherited)

    selected_upstream = sorted(inherited_present & set(upstream_locales))
    selected_complete = sorted(locale for locale in selected_upstream if not completeness[locale]["missing"])
    selected_incomplete = sorted(locale for locale in selected_upstream if completeness[locale]["missing"])
    inherited_full = sorted(inherited_present - set(upstream_locales))

    print("Minecraft 1.13 / JEI 4.14.4 localization audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print("Resource format transition: .lang -> .json")
    print(f"G11 English: {len(base)} total / {len(base_normal)} normal")
    print(f"G12 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G11 -> G12 unchanged: {len(unchanged)}")
    print(f"G11 -> G12 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G11 -> G12 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G11 -> G12 changed ({len(changed)}):")
    for key in changed:
        print(f"  {key}: {base[key]!r} -> {target[key]!r}")

    print(f"JEI upstream JSON locales ({len(upstream_locales)}): {', '.join(upstream_locales)}")
    print("Upstream completeness against normal G12 target keys:")
    for locale in upstream_locales:
        info = completeness[locale]
        print(
            f"  {locale}: {info['present']}/{info['target']} "
            f"missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}"
        )

    if base_meta and target_meta:
        ba = base_meta.get("assetIndex", {})
        ta = target_meta.get("assetIndex", {})
        print(f"Minecraft 1.12.2 asset index: id={ba.get('id')} sha1={ba.get('sha1')} url={ba.get('url')}")
        print(f"Minecraft 1.13 asset index: id={ta.get('id')} sha1={ta.get('sha1')} url={ta.get('url')}")
    print(f"Minecraft language codes: 1.12.2={len(base_codes)} 1.13={len(target_codes)}")
    print(f"Added codes since 1.12.2 ({len(added_mc)}): {', '.join(added_mc) or '(none)'}")
    print(f"Removed codes since 1.12.2 ({len(removed_mc)}): {', '.join(removed_mc) or '(none)'}")
    print(f"Inherited selected codes absent from 1.13 ({len(inherited_missing)}): {', '.join(inherited_missing) or '(none)'}")
    print(f"Inherited selected codes still present: {len(inherited_present)}")
    print(f"Minecraft 1.13 codes outside inherited scope ({len(new_candidates)}):")
    for code in new_candidates:
        info = target_language_metadata.get(code, {})
        print(
            f"  {code}: name={info.get('name', '?')!r} "
            f"region={info.get('region', '?')!r} bidirectional={info.get('bidirectional', False)}"
        )
    print(f"Inherited selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete)}")
    print(f"Inherited selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete)}")
    print(f"Inherited addon-owned full locales still present ({len(inherited_full)}): {', '.join(inherited_full)}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned Minecraft 1.13 / JEI 4.14.4 audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

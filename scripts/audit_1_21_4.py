#!/usr/bin/env python3
"""Exploratory audit for final Minecraft 1.21.4 / JEI 20.0.0 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
PINNED_COMMIT = "26845e0d2a248b0084481b4a433ef7b32152d4c6"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_CONTENTS_API = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G40-audit"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def parse_json_bytes(data: bytes) -> dict[str, str]:
    raw = json.loads(data.decode("utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_json(path: Path) -> dict[str, str]:
    return parse_json_bytes(path.read_bytes())


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


def upstream_locales() -> list[str]:
    contents = fetch_json(LANG_CONTENTS_API)
    locales = sorted(
        Path(item["name"]).stem.lower()
        for item in contents
        if item.get("type") == "file" and str(item.get("name", "")).endswith(".json")
    )
    if "en_us" not in locales:
        raise ValueError("Pinned G40 JEI language directory has no en_us.json")
    return locales


def main() -> int:
    errors: list[str] = []
    base = parse_json(BASE_SOURCE)
    target = parse_json_bytes(fetch_bytes(f"{RAW_LANG}/en_us.json"))
    base_normal = {k for k in base if not k.startswith(DEBUG_PREFIX)}
    target_normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.4",
        "minecraftVersionRange=[1.21.4, 1.21.5)",
        "neoforgeVersion=21.4.136",
        "neoforgeVersionRange=[21.4.121,)",
        "specificationVersion=20.0.0",
    ):
        if token not in props:
            errors.append(f"pinned G40 gradle.properties missing {token}")

    locales = upstream_locales()
    completeness: dict[str, dict] = {}
    for locale in locales:
        values = parse_json_bytes(fetch_bytes(f"{RAW_LANG}/{locale}.json"))
        missing = sorted(target_normal - set(values))
        completeness[locale] = {
            "present": len(target_normal & set(values)),
            "target": len(target_normal),
            "missing": missing,
            "extra": sorted(set(values) - set(target)),
        }

    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    inherited = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if len(inherited) != 90:
        errors.append(f"expected G39 selected scope 90, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.21.1"), None)
    target_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.21.4"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.21.1/1.21.4 missing from Mojang version manifest")
        base_meta = target_meta = base_asset = target_asset = {}
    else:
        base_meta = fetch_json(base_entry["url"])
        target_meta = fetch_json(target_entry["url"])
        base_asset = fetch_json(base_meta["assetIndex"]["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])

    base_codes = language_codes(base_asset) if base_asset else set()
    target_codes = language_codes(target_asset) if target_asset else set()
    live_added = target_codes - base_codes
    live_removed = base_codes - target_codes
    if inherited - target_codes:
        errors.append(f"selected G39 language codes absent from 1.21.4 asset pool: {sorted(inherited-target_codes)}")

    upstream_set = set(locales)
    base_upstream = (
        set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    selected_upstream = sorted(inherited & upstream_set)
    selected_complete = sorted(x for x in selected_upstream if not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if completeness[x]["missing"])
    selected_full = sorted(inherited - upstream_set)
    base_full = set(base_scope["addon_full_locales"])
    newly_upstream = sorted(base_full & upstream_set)
    no_longer_upstream = sorted(base_upstream - upstream_set)

    print("Minecraft 1.21.4 / JEI 20.0.0 final localization exploratory audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print("Endpoint: final pinned JEI 1.21.4 state before the Minecraft 1.21.5 port.")
    print("Build: Minecraft 1.21.4 / NeoForge 21.4.136 / Java 21")
    print(f"G39 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G40 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G39 -> G40 unchanged: {len(unchanged)}")
    print(f"G39 -> G40 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G39 -> G40 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G39 -> G40 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    for key in changed:
        print(f"  changed {key}: {base[key]!r} -> {target[key]!r}")

    if base_meta and target_meta:
        ba, ta = base_meta["assetIndex"], target_meta["assetIndex"]
        print(f"Minecraft 1.21.1 asset index: id={ba.get('id')} sha1={ba.get('sha1')}")
        print(f"Minecraft 1.21.4 asset index: id={ta.get('id')} sha1={ta.get('sha1')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1')}")
    print(f"Minecraft live language asset-file codes: 1.21.1={len(base_codes)} 1.21.4={len(target_codes)}")
    print(f"Live asset additions ({len(live_added)}): {', '.join(sorted(live_added)) or '(none)'}")
    print(f"Live asset removals ({len(live_removed)}): {', '.join(sorted(live_removed)) or '(none)'}")
    print(f"Historical selected language scope inherited: {len(inherited)}")
    print(f"Pinned JEI upstream locale files: {len(locales)}")
    print(f"Newly JEI-upstream selected locales from G39 addon-full ({len(newly_upstream)}): {', '.join(newly_upstream) or '(none)'}")
    print(f"No-longer-upstream selected locales from G39 ({len(no_longer_upstream)}): {', '.join(no_longer_upstream) or '(none)'}")
    print("Upstream completeness against normal G40 target keys:")
    for locale in locales:
        info = completeness[locale]
        print(
            f"  {locale}: {info['present']}/{info['target']} "
            f"missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}"
        )
    print(f"Selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete) or '(none)'}")
    print(f"Selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete) or '(none)'}")
    print(f"Selected addon-owned full locales ({len(selected_full)}): {', '.join(selected_full) or '(none)'}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned final Minecraft 1.21.4 / JEI 20.0.0 exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

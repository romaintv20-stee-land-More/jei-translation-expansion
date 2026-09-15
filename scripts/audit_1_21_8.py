#!/usr/bin/env python3
"""Audit the final Minecraft 1.21.8 / JEI endpoint before freezing G44 manifests."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.7" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.7-language-scope.json"
PINNED_COMMIT = "2f8e4ec2c1e607218eae9b1d9272b87a4dcdb1c8"
NEXT_PORT_COMMIT = "1f0f90ee84bb771c25e8118b4cf25aeaf9d26726"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
NEXT_COMMIT_API = f"https://api.github.com/repos/mezz/JustEnoughItems/commits/{NEXT_PORT_COMMIT}"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G44-audit"}
    token = os.getenv("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def clean(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_locale(locale: str) -> tuple[dict[str, str], bool]:
    text = fetch_text(f"{RAW_LANG}/{locale}.json")
    try:
        return clean(json.loads(text)), False
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        repaired, count = re.subn(
            r'("jei\.alias\.villager\.spawn\.egg"\s*:\s*"HMMM")\s*(\n\s*"modmenu\.descriptionTranslation\.jei")',
            r"\1,\2", text, count=1,
        )
        if count != 1:
            raise ValueError("uk_ua repair point changed")
        repaired, count = re.subn(r",\s*}\s*$", "\n}\n", repaired, count=1)
        if count != 1:
            raise ValueError("uk_ua trailing comma repair point changed")
        return clean(json.loads(repaired)), True


def language_codes(asset_index: dict) -> set[str]:
    codes = {
        Path(name).stem.lower()
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/") and Path(name).name != "languages.json" and Path(name).suffix in {".lang", ".json"}
    }
    codes.add("en_us")
    return codes


def main() -> int:
    base = clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(scope["addon_full_locales"]) | set(scope["selected_upstream_complete_locales"]) | set(scope["selected_upstream_incomplete_locales"])
    if len(selected) != 90:
        raise ValueError(f"G43 selected scope changed: {len(selected)}")

    next_commit = fetch_json(NEXT_COMMIT_API)
    parents = [item["sha"] for item in next_commit.get("parents", [])]
    if parents != [PINNED_COMMIT]:
        raise ValueError(f"1.21.9 port is not directly parented by G44 endpoint: {parents}")
    if "1.21.9" not in next_commit.get("commit", {}).get("message", ""):
        raise ValueError("next port commit no longer identifies Minecraft 1.21.9")

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    required = (
        "modJavaVersion=21",
        "minecraftVersion=1.21.8",
        "minecraftVersionRange=[1.21.8, 1.21.9)",
        "neoforgeVersion=21.8.47",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.8.9,)",
        "specificationVersion=24.2.0",
    )
    for token in required:
        if token not in props:
            raise ValueError(f"pinned G44 gradle.properties missing {token}")

    target = clean(json.loads(fetch_text(f"{RAW_LANG}/en_us.json")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])

    contents = fetch_json(LANG_API)
    upstream_locales = sorted(Path(x["name"]).stem.lower() for x in contents if x.get("type") == "file" and str(x.get("name", "")).endswith(".json"))
    upstream_set = set(upstream_locales)
    malformed: set[str] = set()
    complete: list[str] = []
    incomplete: list[str] = []
    missing_counts: dict[str, int] = {}
    for locale in sorted(selected & upstream_set):
        values, repaired = parse_locale(locale)
        if repaired:
            malformed.add(locale)
            continue
        missing = normal - set(values)
        missing_counts[locale] = len(missing)
        (complete if not missing else incomplete).append(locale)
    if malformed != {"uk_ua"}:
        raise ValueError(f"malformed selected upstream set changed: {sorted(malformed)}")
    addon_full = sorted(selected - ((selected & upstream_set) - malformed))

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.7")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.8")
    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_codes = language_codes(fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = language_codes(fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if selected - target_codes:
        raise ValueError(f"selected locales absent from Minecraft 1.21.8: {sorted(selected-target_codes)}")

    print("PASS: exploratory G44 Minecraft 1.21.8 / JEI 24.2.0 audit")
    print(f"Endpoint: {PINNED_COMMIT}")
    print(f"Next port: {NEXT_PORT_COMMIT} (Minecraft 1.21.9, direct child)")
    print(f"English: base={len(base)} target={len(target)} normal={len(normal)} debug={len(target)-len(normal)}")
    print(f"Semantic delta: unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}")
    print("Added keys: " + json.dumps(added, ensure_ascii=False))
    print("Removed keys: " + json.dumps(removed, ensure_ascii=False))
    print("Changed keys: " + json.dumps(changed, ensure_ascii=False))
    print(f"Scope: selected={len(selected)} upstream_files={len(upstream_locales)} full={len(addon_full)} supplements={len(incomplete)} complete={len(complete)} malformed={sorted(malformed)}")
    print("Complete upstream: " + json.dumps(complete))
    print("Incomplete upstream missing counts: " + json.dumps(missing_counts, sort_keys=True))
    print(f"Minecraft language assets: {len(base_codes)} -> {len(target_codes)} added={live_added} removed={live_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

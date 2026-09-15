#!/usr/bin/env python3
"""Exploratory audit for Minecraft 1.21.7 / JEI 23.1.0."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.6" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.6-language-scope.json"
PINNED_COMMIT = "ee33b5d69f6cf9167c32c2e84fdc69fa1b008440"
NEXT_PORT_COMMIT = "f61efdf5f6604d0d3a55a67cc5d28ec340f189aa"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_CONTENTS_API = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G43-audit"}
    token = os.getenv("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def clean_mapping(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_json_bytes(data: bytes) -> dict[str, str]:
    return clean_mapping(json.loads(data.decode("utf-8")))


def repair_uk_ua_text(text: str) -> str:
    repaired, count = re.subn(
        r'("jei\.alias\.villager\.spawn\.egg"\s*:\s*"HMMM")\s*(\n\s*"modmenu\.descriptionTranslation\.jei")',
        r"\1,\2",
        text,
        count=1,
    )
    if count != 1:
        raise ValueError("uk_ua expected missing-comma repair point not found")
    repaired, count = re.subn(r",\s*}\s*$", "\n}\n", repaired, count=1)
    if count != 1:
        raise ValueError("uk_ua expected trailing-comma repair point not found")
    return repaired


def parse_upstream_locale(locale: str, data: bytes) -> tuple[dict[str, str], bool]:
    text = data.decode("utf-8")
    try:
        return clean_mapping(json.loads(text)), False
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        return clean_mapping(json.loads(repair_uk_ua_text(text))), True


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


def main() -> int:
    errors: list[str] = []
    base = parse_json_bytes(BASE_SOURCE.read_bytes())
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
        "minecraftVersion=1.21.7",
        "minecraftVersionRange=[1.21.7, 1.21.8)",
        "neoforgeVersion=21.7.15-beta",
        "neoforgeVersionRange=[21.7.15-beta,)",
        "specificationVersion=23.1.0",
    ):
        if token not in props:
            errors.append(f"pinned G43 gradle.properties missing {token}")

    scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        errors.append(f"expected inherited selected scope 90, got {len(selected)}")

    contents = fetch_json(LANG_CONTENTS_API)
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in contents
        if item.get("type") == "file" and str(item.get("name", "")).endswith(".json")
    )
    completeness: dict[str, dict] = {}
    malformed: set[str] = set()
    for locale in sorted(selected & set(upstream_locales)):
        try:
            values, repaired = parse_upstream_locale(locale, fetch_bytes(f"{RAW_LANG}/{locale}.json"))
        except Exception as exc:
            errors.append(f"{locale}: upstream parse failed: {exc}")
            continue
        if repaired:
            malformed.add(locale)
        missing = sorted(target_normal - set(values))
        completeness[locale] = {
            "present": len(target_normal & set(values)),
            "target": len(target_normal),
            "missing": missing,
            "extra": sorted(set(values) - set(target)),
            "malformed": repaired,
        }

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.21.6"), None)
    target_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.21.7"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.21.6/1.21.7 missing from Mojang manifest")
        base_meta = target_meta = base_asset = target_asset = {}
    else:
        base_meta = fetch_json(base_entry["url"])
        target_meta = fetch_json(target_entry["url"])
        base_asset = fetch_json(base_meta["assetIndex"]["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])
    base_codes = language_codes(base_asset) if base_asset else set()
    target_codes = language_codes(target_asset) if target_asset else set()
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    absent = sorted(selected - target_codes)
    if absent:
        errors.append(f"selected inherited locales absent from Minecraft 1.21.7 assets: {absent}")

    usable_upstream = (selected & set(upstream_locales)) - malformed
    complete = sorted(x for x in usable_upstream if x in completeness and not completeness[x]["missing"])
    incomplete = sorted(x for x in usable_upstream if x in completeness and completeness[x]["missing"])
    full = sorted(selected - usable_upstream)

    print("Minecraft 1.21.7 / JEI 23.1.0 exploratory audit")
    print(f"Pinned endpoint: {PINNED_COMMIT}")
    print(f"Next Minecraft port: 1.21.8 at {NEXT_PORT_COMMIT}")
    print("Endpoint is final because the 1.21.8 port directly follows this commit on mainline.")
    print("Build: Minecraft 1.21.7 / NeoForge 21.7.15-beta / Java 21 / JEI specification 23.1.0")
    print(f"G42 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G43 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G42 -> G43 unchanged: {len(unchanged)}")
    print(f"G42 -> G43 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G42 -> G43 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G42 -> G43 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    for key in changed:
        print(f"  changed {key}: {base[key]!r} -> {target[key]!r}")
    if base_meta and target_meta:
        ba, ta = base_meta["assetIndex"], target_meta["assetIndex"]
        print(f"Minecraft 1.21.6 asset index: id={ba.get('id')} sha1={ba.get('sha1')}")
        print(f"Minecraft 1.21.7 asset index: id={ta.get('id')} sha1={ta.get('sha1')}")
    print(f"Minecraft live language codes: 1.21.6={len(base_codes)} 1.21.7={len(target_codes)}")
    print(f"Live additions ({len(live_added)}): {', '.join(live_added) or '(none)'}")
    print(f"Live removals ({len(live_removed)}): {', '.join(live_removed) or '(none)'}")
    print(f"Pinned JEI upstream locale files: {len(upstream_locales)}")
    print(f"Malformed selected upstream locales ({len(malformed)}): {', '.join(sorted(malformed)) or '(none)'}")
    print("Selected upstream completeness:")
    for locale in sorted(selected & set(upstream_locales)):
        info = completeness.get(locale)
        if info is None:
            continue
        suffix = " MALFORMED->FULL-OVERRIDE" if info["malformed"] else ""
        print(f"  {locale}: {info['present']}/{info['target']} missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}{suffix}")
    print(f"Usable complete upstream ({len(complete)}): {', '.join(complete) or '(none)'}")
    print(f"Usable incomplete upstream ({len(incomplete)}): {', '.join(incomplete) or '(none)'}")
    print(f"Addon/full-override locales ({len(full)}): {', '.join(full) or '(none)'}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.21.7 / JEI 23.1.0 exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

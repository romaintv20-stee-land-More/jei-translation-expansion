#!/usr/bin/env python3
"""Exploratory audit for the final maintained Minecraft 1.21.5 JEI localization endpoint."""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.4" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.4-language-scope.json"
PINNED_COMMIT = "0772287a157beb93f438ee10f88afe402e262856"
FIRST_PORT_COMMIT = "2cc5d1e8b7fb4f79c917804d7582bb7c48374499"
MAINLINE_NEXT_PORT_COMMIT = "2a57409c2af0ce9716749a0329166a41cbcf453f"
MAINLINE_PRE_NEXT_PORT_COMMIT = "e34c5c1221ca81fbf1ca4ca4433f3332208f49d9"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_CONTENTS_API = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
EXPECTED_MALFORMED_SELECTED = {"uk_ua"}


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G41-audit"}
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


def parse_json(path: Path) -> dict[str, str]:
    return parse_json_bytes(path.read_bytes())


def parse_pinned_upstream_locale(locale: str, data: bytes) -> tuple[dict[str, str], bool]:
    """Parse a pinned upstream locale, repairing only the frozen known uk_ua syntax defect."""
    text = data.decode("utf-8")
    try:
        return clean_mapping(json.loads(text)), False
    except json.JSONDecodeError:
        if locale != "uk_ua":
            raise
        repaired = text.replace(
            '  "jei.alias.villager.spawn.egg": "HMMM"\n  \n  "modmenu.descriptionTranslation.jei"',
            '  "jei.alias.villager.spawn.egg": "HMMM",\n  \n  "modmenu.descriptionTranslation.jei"',
        )
        repaired = re.sub(r",\s*}\s*$", "\n}\n", repaired)
        if repaired == text:
            raise ValueError("uk_ua: expected frozen malformed-JSON repair pattern was not found")
        return clean_mapping(json.loads(repaired)), True


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
        raise ValueError("Pinned G41 JEI language directory has no en_us.json")
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
        "minecraftVersion=1.21.5",
        "minecraftVersionRange=[1.21.5, 1.21.6)",
        "neoforgeVersion=21.5.75",
        "neoforgeVersionRange=[21.5.74,)",
        "specificationVersion=21.4.0",
    ):
        if token not in props:
            errors.append(f"pinned G41 gradle.properties missing {token}")

    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    inherited = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if len(inherited) != 90:
        errors.append(f"expected G40 selected scope 90, got {len(inherited)}")

    locales = upstream_locales()
    selected_upstream_candidates = sorted(set(locales) & inherited)
    completeness: dict[str, dict] = {}
    malformed_selected: set[str] = set()
    for locale in selected_upstream_candidates:
        values, repaired = parse_pinned_upstream_locale(locale, fetch_bytes(f"{RAW_LANG}/{locale}.json"))
        if repaired:
            malformed_selected.add(locale)
        missing = sorted(target_normal - set(values))
        completeness[locale] = {
            "present": len(target_normal & set(values)),
            "target": len(target_normal),
            "missing": missing,
            "extra": sorted(set(values) - set(target)),
            "malformed_upstream_json": repaired,
        }
    if malformed_selected != EXPECTED_MALFORMED_SELECTED:
        errors.append(
            f"expected malformed selected upstream locales {sorted(EXPECTED_MALFORMED_SELECTED)}, "
            f"got {sorted(malformed_selected)}"
        )

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.21.4"), None)
    target_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.21.5"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.21.4/1.21.5 missing from Mojang version manifest")
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
    absent = inherited - target_codes
    if absent:
        errors.append(f"selected G40 language codes absent from 1.21.5 asset pool: {sorted(absent)}")

    upstream_set = set(locales)
    usable_selected_upstream_set = (inherited & upstream_set) - malformed_selected
    base_upstream = (
        set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    base_full = set(base_scope["addon_full_locales"])
    selected_upstream = sorted(usable_selected_upstream_set)
    selected_complete = sorted(x for x in selected_upstream if not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if completeness[x]["missing"])
    selected_full = sorted(inherited - usable_selected_upstream_set)
    newly_upstream = sorted(base_full & usable_selected_upstream_set)
    no_longer_usable_upstream = sorted(base_upstream - usable_selected_upstream_set)

    print("Minecraft 1.21.5 final maintained JEI localization exploratory audit")
    print(f"Pinned dedicated-branch head: {PINNED_COMMIT}")
    print(f"First Minecraft 1.21.5 port: {FIRST_PORT_COMMIT}")
    print(f"Mainline pre-1.21.6 boundary: {MAINLINE_PRE_NEXT_PORT_COMMIT}")
    print(f"Mainline Minecraft 1.21.6 port: {MAINLINE_NEXT_PORT_COMMIT}")
    print("The dedicated 1.21.5 branch continued after the mainline 1.21.6 split, so its later branch head is used as the final 1.21.5 endpoint.")
    print("Build: Minecraft 1.21.5 / NeoForge 21.5.75 / Java 21 / JEI specification 21.4.0")
    print(f"G40 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G41 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G40 -> G41 unchanged: {len(unchanged)}")
    print(f"G40 -> G41 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G40 -> G41 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G40 -> G41 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    for key in changed:
        print(f"  changed {key}: {base[key]!r} -> {target[key]!r}")

    if base_meta and target_meta:
        ba, ta = base_meta["assetIndex"], target_meta["assetIndex"]
        print(f"Minecraft 1.21.4 asset index: id={ba.get('id')} sha1={ba.get('sha1')}")
        print(f"Minecraft 1.21.5 asset index: id={ta.get('id')} sha1={ta.get('sha1')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1')}")
    print(f"Minecraft live language asset-file codes: 1.21.4={len(base_codes)} 1.21.5={len(target_codes)}")
    print(f"Live asset additions ({len(live_added)}): {', '.join(sorted(live_added)) or '(none)'}")
    print(f"Live asset removals ({len(live_removed)}): {', '.join(sorted(live_removed)) or '(none)'}")
    print(f"Historical selected language scope inherited: {len(inherited)}")
    print(f"Pinned JEI upstream locale files: {len(locales)}")
    print(f"Malformed selected upstream locale files ({len(malformed_selected)}): {', '.join(sorted(malformed_selected)) or '(none)'}")
    print(f"Forced full overrides due to malformed upstream JSON: {', '.join(sorted(malformed_selected)) or '(none)'}")
    print(f"Newly usable JEI-upstream selected locales from G40 addon-full ({len(newly_upstream)}): {', '.join(newly_upstream) or '(none)'}")
    print(f"No-longer-usable upstream selected locales from G40 ({len(no_longer_usable_upstream)}): {', '.join(no_longer_usable_upstream) or '(none)'}")
    print("Selected upstream completeness against normal G41 target keys:")
    for locale in selected_upstream_candidates:
        info = completeness[locale]
        suffix = " MALFORMED->FORCED-FULL" if info["malformed_upstream_json"] else ""
        print(
            f"  {locale}: {info['present']}/{info['target']} "
            f"missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}{suffix}"
        )
    print(f"Selected usable upstream complete ({len(selected_complete)}): {', '.join(selected_complete) or '(none)'}")
    print(f"Selected usable upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete) or '(none)'}")
    print(f"Selected addon-owned/full-override locales ({len(selected_full)}): {', '.join(selected_full) or '(none)'}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned final maintained Minecraft 1.21.5 JEI exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

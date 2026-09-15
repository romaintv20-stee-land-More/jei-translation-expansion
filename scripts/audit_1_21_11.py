#!/usr/bin/env python3
"""Audit the maintained Minecraft 1.21.11 JEI endpoint before freezing G47 manifests."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.10" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.10-language-scope.json"
BASE_ENDPOINT = "621ddf003a8eceffcba0fd808a955e280f87a4c0"
FIRST_PORT_COMMIT = "6b615d15ef776abf139339779985a91c59c9c324"
MAINLINE_1_21_11_ENDPOINT = "1d37cb1a1cf7139170d214adef128f405b865312"
MAINLINE_NEXT_PORT_COMMIT = "d395fda29b10f09b860d5a6221b459050f5071d3"
# The dedicated 1.21.11 branch continued to receive maintenance after mainline moved to 26.1.
# Follow the same endpoint policy used for other maintained version branches (for example G41).
PINNED_COMMIT = "4b6e47334ac4aaeae51d15facbb38c42cb511321"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
COMMIT_API = "https://api.github.com/repos/mezz/JustEnoughItems/commits/{commit}"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G47-audit"}
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


def parse_locale(locale: str) -> tuple[dict[str, str] | None, str | None]:
    text = fetch_text(f"{RAW_LANG}/{locale}.json")
    try:
        return clean(json.loads(text)), None
    except json.JSONDecodeError as exc:
        return None, f"{exc.msg} at line {exc.lineno} column {exc.colno}"


def language_codes(asset_index: dict) -> set[str]:
    codes = {
        Path(name).stem.lower()
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/")
        and Path(name).name != "languages.json"
        and Path(name).suffix in {".lang", ".json"}
    }
    codes.add("en_us")
    return codes


def assert_single_parent(commit: dict, expected: str, label: str) -> None:
    parents = [item["sha"] for item in commit.get("parents", [])]
    if parents != [expected]:
        raise ValueError(f"{label} is not directly parented by {expected}: {parents}")


def main() -> int:
    base = clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        raise ValueError(f"G46 selected scope changed: {len(selected)}")

    first_port = fetch_json(COMMIT_API.format(commit=FIRST_PORT_COMMIT))
    assert_single_parent(first_port, BASE_ENDPOINT, "1.21.11 port")
    first_message = first_port.get("commit", {}).get("message", "")
    if "Minecraft 1.21.11" not in first_message:
        raise ValueError("first G47 port commit no longer identifies Minecraft 1.21.11")

    # Record the historical mainline handoff, but do not mistake it for the end of the maintained
    # 1.21.11 branch. The dedicated branch is hundreds of commits ahead of this point.
    mainline_next = fetch_json(COMMIT_API.format(commit=MAINLINE_NEXT_PORT_COMMIT))
    assert_single_parent(mainline_next, MAINLINE_1_21_11_ENDPOINT, "26.1-snapshot-1 mainline port")
    if "26.1-snapshot-1" not in mainline_next.get("commit", {}).get("message", ""):
        raise ValueError("mainline next port no longer identifies 26.1-snapshot-1")

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    required = (
        "modJavaVersion=21",
        "minecraftVersion=1.21.11",
        "minecraftVersionRange=[1.21.11]",
        "neoforgeVersion=21.11.45",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.11.44,)",
        "curseProjectId=238222",
        "modrinthId=u6dRKJwZ",
        "specificationVersion=27.38.0",
    )
    for token in required:
        if token not in props:
            raise ValueError(f"maintained G47 gradle.properties missing {token}")

    target = clean(json.loads(fetch_text(f"{RAW_LANG}/en_us.json")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if len(unchanged) + len(added) + len(changed) != len(target):
        raise ValueError("G47 semantic partition does not cover target keys")

    contents = fetch_json(LANG_API)
    upstream_locales = sorted(
        Path(x["name"]).stem.lower()
        for x in contents
        if x.get("type") == "file" and str(x.get("name", "")).endswith(".json")
    )
    upstream_set = set(upstream_locales)
    malformed: dict[str, str] = {}
    complete: list[str] = []
    incomplete: list[str] = []
    missing_counts: dict[str, int] = {}
    for locale in sorted(selected & upstream_set):
        values, error = parse_locale(locale)
        if error is not None or values is None:
            malformed[locale] = error or "unknown JSON parse failure"
            continue
        missing = normal - set(values)
        missing_counts[locale] = len(missing)
        (complete if not missing else incomplete).append(locale)
    usable = (selected & upstream_set) - set(malformed)
    addon_full = sorted(selected - usable)

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.10")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.11")
    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_codes = language_codes(fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = language_codes(fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if selected - target_codes:
        raise ValueError(f"selected locales absent from Minecraft 1.21.11: {sorted(selected-target_codes)}")

    print("PASS: exploratory G47 maintained Minecraft 1.21.11 audit")
    print(f"First port: {FIRST_PORT_COMMIT} (direct child of G46)")
    print(f"Historical mainline endpoint: {MAINLINE_1_21_11_ENDPOINT}")
    print(f"Maintained branch endpoint: {PINNED_COMMIT}")
    print(f"Mainline next port: {MAINLINE_NEXT_PORT_COMMIT} (26.1-snapshot-1)")
    print("Publication metadata: CurseForge and Modrinth publishing are configured on the maintained branch")
    print(f"English: base={len(base)} target={len(target)} normal={len(normal)} debug={len(target)-len(normal)}")
    print(f"Semantic delta: unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}")
    print("Added keys: " + json.dumps(added, ensure_ascii=False))
    print("Removed keys: " + json.dumps(removed, ensure_ascii=False))
    print("Changed keys: " + json.dumps({k: {"old": base[k], "new": target[k]} for k in changed}, ensure_ascii=False))
    print(
        f"Scope: selected={len(selected)} upstream_files={len(upstream_locales)} "
        f"full={len(addon_full)} supplements={len(incomplete)} complete={len(complete)} malformed={malformed}"
    )
    print("Complete upstream: " + json.dumps(complete))
    print("Incomplete upstream missing counts: " + json.dumps(missing_counts, sort_keys=True))
    print(f"Minecraft language assets: {len(base_codes)} -> {len(target_codes)} added={live_added} removed={live_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

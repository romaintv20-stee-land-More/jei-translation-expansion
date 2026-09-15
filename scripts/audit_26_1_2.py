#!/usr/bin/env python3
"""Audit the maintained Minecraft 26.1.2 / JEI 29.37.0 snapshot for G50."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.1.1" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-26.1.1-language-scope.json"
BASE_ENDPOINT = "5a2ecc40c438e9137a8b64b2d9b48c095fc24c23"
FIRST_PATCH_COMMIT = "481a64808dab4ea205772a7289cc766804f5f5d7"
PINNED_COMMIT = "d7c73ed63a7a25a9ad416428eafef3a3dcf0f1c8"
MAINTAINED_BRANCH = "26.1"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
COMMIT_API = "https://api.github.com/repos/mezz/JustEnoughItems/commits/{commit}"
BRANCH_API = f"https://api.github.com/repos/mezz/JustEnoughItems/branches/{MAINTAINED_BRANCH}"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G50-audit"}
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
        raise ValueError(f"G49 selected scope changed: {len(selected)}")

    first_patch = fetch_json(COMMIT_API.format(commit=FIRST_PATCH_COMMIT))
    assert_single_parent(first_patch, BASE_ENDPOINT, "26.1.2 support commit")
    if "26.1.2" not in first_patch.get("commit", {}).get("message", ""):
        raise ValueError("first G50 commit no longer identifies Minecraft 26.1.2")

    branch = fetch_json(BRANCH_API)
    branch_head = branch.get("commit", {}).get("sha")
    if branch_head != PINNED_COMMIT:
        raise ValueError(
            f"Pinned G50 snapshot is stale: branch {MAINTAINED_BRANCH} now points to {branch_head}, "
            f"expected {PINNED_COMMIT}. Re-audit before freezing."
        )

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    required = (
        "modJavaVersion=25",
        "minecraftVersion=26.1.2",
        "minecraftVersionRange=[26.1, 26.1.2]",
        "neoforgeVersion=26.1.2.99",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[26.1.2.99,)",
        "curseProjectId=238222",
        "modrinthId=u6dRKJwZ",
        "specificationVersion=29.37.0",
    )
    for token in required:
        if token not in props:
            raise ValueError(f"G50 gradle.properties missing {token}")

    target = clean(json.loads(fetch_text(f"{RAW_LANG}/en_us.json")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])

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
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "26.1.1")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "26.1.2")
    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_codes = language_codes(fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = language_codes(fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if selected - target_codes:
        raise ValueError(f"selected locales absent from Minecraft 26.1.2: {sorted(selected-target_codes)}")

    print("PASS: exploratory G50 Minecraft 26.1.2 audit")
    print(f"Base G49 endpoint: {BASE_ENDPOINT}")
    print(f"First 26.1.2 commit: {FIRST_PATCH_COMMIT}")
    print(f"Pinned maintained 26.1 branch snapshot: {PINNED_COMMIT}")
    print("Build: JEI 29.37.0 / NeoForge 26.1.2.99 / Java 25")
    print(f"English: base={len(base)} target={len(target)} normal={len(normal)} debug={len(target)-len(normal)}")
    print(f"Semantic delta: unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed={len(changed)}")
    print("Added keys: " + json.dumps({k: target[k] for k in added}, ensure_ascii=False, sort_keys=True))
    print("Removed keys: " + json.dumps(removed, ensure_ascii=False))
    print("Changed English: " + json.dumps({k: {"from": base[k], "to": target[k]} for k in changed}, ensure_ascii=False, sort_keys=True))
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

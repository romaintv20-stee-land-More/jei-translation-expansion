#!/usr/bin/env python3
"""Audit the current JEI Fabric 26.3 RC2 branch as a provisional G52 target.

This does not register G52 as a completed release generation. It freezes enough facts to
prepare translations while Minecraft 26.3 is still an RC and JEI currently exposes only a
Fabric 26.3 branch.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.2" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-26.2-language-scope.json"
BASE_PIN = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
PINNED_COMMIT = "58362ffb5baa95580549d6825811e7363964a271"
MAINTAINED_BRANCH = "fabric-26.3-snapshot-7"
TARGET_MC = "26.3-rc-2"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
BRANCH_API = f"https://api.github.com/repos/mezz/JustEnoughItems/branches/{MAINTAINED_BRANCH}"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G52-pre-audit"}
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


def main() -> int:
    base = clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        raise ValueError(f"G51 selected scope changed: {len(selected)}")

    branch = fetch_json(BRANCH_API)
    branch_head = branch.get("commit", {}).get("sha")
    if branch_head != PINNED_COMMIT:
        raise ValueError(
            f"Provisional 26.3 branch moved to {branch_head}; expected {PINNED_COMMIT}. "
            "Re-audit the new RC/snapshot instead of freezing stale data."
        )

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    required = (
        "modJavaVersion=25",
        "minecraftVersion=26.3-rc-2",
        "minecraftVersionRange=[26.3-rc-2]",
        "fabricLoaderVersion=0.19.5",
        "fabricApiVersion=0.160.4+26.3",
        "fabricLoaderVersionRange=>=0.19.0",
        "specificationVersion=30.32.0",
    )
    for token in required:
        if token not in props:
            raise ValueError(f"26.3 RC2 gradle.properties missing {token}")
    if "neoforgeVersion=" in props:
        raise ValueError("Provisional 26.3 branch unexpectedly contains NeoForge metadata; re-audit loader support")

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
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "26.2")
    target_entry = next((x for x in manifest["versions"] if x.get("id") == TARGET_MC), None)
    base_meta = fetch_json(base_entry["url"])
    base_codes = language_codes(fetch_json(base_meta["assetIndex"]["url"]))
    target_codes: set[str] | None = None
    target_asset = None
    if target_entry is not None:
        target_meta = fetch_json(target_entry["url"])
        target_asset = target_meta["assetIndex"]
        target_codes = language_codes(fetch_json(target_asset["url"]))
        if selected - target_codes:
            raise ValueError(f"selected locales absent from Minecraft {TARGET_MC}: {sorted(selected-target_codes)}")

    report = {
        "status": "provisional-rc-audit-only",
        "not_a_completed_generation": True,
        "base": {"minecraft": "26.2", "jei_commit": BASE_PIN},
        "target": {
            "minecraft": TARGET_MC,
            "jei_specification_version": "30.32.0",
            "jei_commit": PINNED_COMMIT,
            "upstream_branch": MAINTAINED_BRANCH,
            "loader": "fabric",
            "java": 25,
            "fabric_loader": "0.19.5",
            "fabric_api": "0.160.4+26.3",
        },
        "english": {
            "base_keys": len(base),
            "target_keys": len(target),
            "target_normal_keys": len(normal),
            "target_debug_keys": len(target) - len(normal),
            "unchanged": len(unchanged),
            "added": {k: target[k] for k in added},
            "removed": removed,
            "changed": {k: {"from": base[k], "to": target[k]} for k in changed},
        },
        "scope": {
            "selected": len(selected),
            "upstream_json_files": len(upstream_locales),
            "addon_full": len(addon_full),
            "supplements": len(incomplete),
            "complete_upstream": complete,
            "malformed": malformed,
            "missing_counts": missing_counts,
        },
        "minecraft_assets": {
            "base_language_count": len(base_codes),
            "target_metadata_available": target_codes is not None,
            "target_asset_index": target_asset,
            "target_language_count": None if target_codes is None else len(target_codes),
            "added": None if target_codes is None else sorted(target_codes - base_codes),
            "removed": None if target_codes is None else sorted(base_codes - target_codes),
        },
    }

    print("PASS: provisional Minecraft 26.3 RC2 / JEI Fabric translation audit")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print("NOTE: do not register G52 packaging until a publishable Minecraft 26.3 target/loader is selected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

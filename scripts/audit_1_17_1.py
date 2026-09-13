#!/usr/bin/env python3
"""Exploratory audit for final Minecraft 1.17.1 / JEI 8.3.0 localization endpoint."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.16.5" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.17.1" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.16.5-language-scope.json"
PINNED_COMMIT = "ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/src/main/resources/assets/jei/lang"
GITHUB_LANG_API = "https://api.github.com/repos/mezz/JustEnoughItems/contents/src/main/resources/assets/jei/lang"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JEI-Translation-Expansion-G24-audit",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def parse_jei_json_bytes(data: bytes) -> dict[str, str]:
    raw = json.loads(data.decode("utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_jei_json(path: Path) -> dict[str, str]:
    return parse_jei_json_bytes(path.read_bytes())


def discover_upstream_locales() -> tuple[str, ...]:
    query = urllib.parse.urlencode({"ref": PINNED_COMMIT})
    entries = fetch_json(f"{GITHUB_LANG_API}?{query}")
    if not isinstance(entries, list):
        raise ValueError("GitHub language directory response is not a list")
    return tuple(sorted(
        str(entry.get("name", ""))[:-5].lower()
        for entry in entries
        if entry.get("type") == "file" and str(entry.get("name", "")).lower().endswith(".json")
    ))


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
    base = parse_jei_json(BASE_SOURCE)
    stored_target = parse_jei_json(TARGET_SOURCE)
    remote_target = parse_jei_json_bytes(fetch_bytes(f"{RAW_LANG}/en_us.json"))
    if stored_target != remote_target:
        errors.append("stored G24 English source differs from pinned JEI 8.3.0 endpoint")
    target = remote_target
    base_normal = {k for k in base if not k.startswith(DEBUG_PREFIX)}
    target_normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    changed_values = {k: {"from": base[k], "to": target[k]} for k in changed}
    normal_added_or_changed = sorted(
        k for k in set(added) | set(changed) if not k.startswith(DEBUG_PREFIX)
    )
    changed_debug = sorted(k for k in changed if k.startswith(DEBUG_PREFIX))

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    build = fetch_text(f"{RAW_ROOT}/build.gradle")
    for token in (
        "minecraft_version=1.17.1",
        "forge_version=37.0.104",
        "version_major=8",
        "version_minor=3",
        "version_patch=0",
    ):
        if token not in props:
            errors.append(f"pinned G24 gradle.properties missing {token}")
    if "java.toolchain.languageVersion = JavaLanguageVersion.of(16)" not in build:
        errors.append("pinned G24 build metadata no longer confirms Java 16")
    if "mappings channel: 'official', version: project.minecraft_version" not in build and 'mappings channel: "official", version: project.minecraft_version' not in build:
        errors.append("pinned G24 build metadata no longer confirms official 1.17.1 mappings")

    try:
        upstream_locales = discover_upstream_locales()
    except Exception as exc:
        errors.append(f"failed to discover pinned G24 upstream locale inventory: {exc}")
        upstream_locales = ()

    completeness: dict[str, dict] = {}
    for locale in upstream_locales:
        values = parse_jei_json_bytes(fetch_bytes(f"{RAW_LANG}/{locale}.json"))
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
    if len(inherited) != 88:
        errors.append(f"expected G23 selected scope 88, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.16.5"), None)
    target_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.17.1"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.16.5/1.17.1 missing from Mojang version manifest")
        base_meta = target_meta = base_asset = target_asset = {}
    else:
        base_meta = fetch_json(base_entry["url"])
        target_meta = fetch_json(target_entry["url"])
        base_asset = fetch_json(base_meta["assetIndex"]["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])

    base_codes = language_codes(base_asset) if base_asset else set()
    target_codes = language_codes(target_asset) if target_asset else set()
    added_mc = sorted(target_codes - base_codes)
    removed_mc = sorted(base_codes - target_codes)
    inherited_missing = sorted(inherited - target_codes)
    inherited_present = inherited & target_codes
    new_candidates = sorted(target_codes - inherited)
    upstream_set = set(upstream_locales)
    selected_upstream = sorted(inherited_present & upstream_set)
    selected_complete = sorted(x for x in selected_upstream if x in completeness and not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if x in completeness and completeness[x]["missing"])
    selected_full = sorted(inherited_present - upstream_set)

    print("Minecraft 1.17.1 / JEI 8.3.0 final localization exploratory audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print("Build: Minecraft 1.17.1 / Forge 37.0.104 / mappings official 1.17.1 / Java 16")
    print(f"G23 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G24 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G23 -> G24 unchanged: {len(unchanged)}")
    print(f"G23 -> G24 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G23 -> G24 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G23 -> G24 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    print(f"G23 -> G24 changed debug-only ({len(changed_debug)}): {', '.join(changed_debug) or '(none)'}")
    print(f"Normal added-or-changed meanings requiring review ({len(normal_added_or_changed)}): {', '.join(normal_added_or_changed) or '(none)'}")
    print("Changed English values JSON:")
    print(json.dumps(changed_values, ensure_ascii=False, sort_keys=True))
    print(f"JEI upstream JSON locales ({len(upstream_locales)}): {', '.join(upstream_locales)}")
    print("Upstream completeness against normal G24 target keys:")
    for locale in upstream_locales:
        info = completeness[locale]
        print(f"  {locale}: {info['present']}/{info['target']} missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}")
    if base_meta and target_meta:
        ba, ta = base_meta["assetIndex"], target_meta["assetIndex"]
        print(f"Minecraft 1.16.5 asset index: id={ba.get('id')} sha1={ba.get('sha1')} url={ba.get('url')}")
        print(f"Minecraft 1.17.1 asset index: id={ta.get('id')} sha1={ta.get('sha1')} url={ta.get('url')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1')}")
    print(f"Minecraft language codes: 1.16.5={len(base_codes)} 1.17.1={len(target_codes)}")
    print(f"Added codes since 1.16.5 ({len(added_mc)}): {', '.join(added_mc) or '(none)'}")
    print(f"Removed codes since 1.16.5 ({len(removed_mc)}): {', '.join(removed_mc) or '(none)'}")
    print(f"Inherited selected codes absent from 1.17.1 ({len(inherited_missing)}): {', '.join(inherited_missing) or '(none)'}")
    print(f"Inherited selected codes still present: {len(inherited_present)}")
    print(f"New Minecraft codes outside inherited selected scope ({len(new_candidates)}): {', '.join(new_candidates) or '(none)'}")
    print(f"Inherited selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete)}")
    print(f"Inherited selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete)}")
    print(f"Inherited addon-owned full locales still present ({len(selected_full)}): {', '.join(selected_full)}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned final Minecraft 1.17.1 / JEI 8.3.0 exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Exploratory audit for final Minecraft 1.20.4 / JEI 17.3.0 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.20.2" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.20.2-language-scope.json"
PINNED_COMMIT = "282f6faecfd71545243be0a94703bdde90eac4e7"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
EXPECTED_ADDED = {"jei.tooltip.error.render.crash"}
EXPECTED_CHANGED = {"jei.tooltip.error.crash"}
UPSTREAM_LOCALES = (
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "en_au", "en_us", "es_es",
    "fi_fi", "fr_fr", "he_il", "hu_hu", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt",
    "nb_no", "pl_pl", "pt_br", "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn", "zh_tw",
)


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G36-audit"})
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

    if (len(base), len(target), len(target_normal)) != (156, 157, 151):
        errors.append(f"unexpected English counts base={len(base)} target={len(target)} normal={len(target_normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (155, 1, 0, 1):
        errors.append("expected 155 unchanged + 1 added + 0 removed + 1 changed")
    if set(added) != EXPECTED_ADDED:
        errors.append(f"unexpected added keys: {added}")
    if set(changed) != EXPECTED_CHANGED:
        errors.append(f"unexpected changed-English keys: {changed}")

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    forge_build = fetch_text(f"{RAW_ROOT}/Forge/build.gradle.kts")
    for token in (
        "modJavaVersion=17", "minecraftVersion=1.20.4", "forgeVersion=49.0.19",
        "parchmentVersionForge=1.20.3-2023.12.31-1.20.3", "specificationVersion=17.3.0",
    ):
        if token not in props:
            errors.append(f"pinned G36 gradle.properties missing {token}")
    if 'languageVersion.set(JavaLanguageVersion.of(modJavaVersion))' not in forge_build:
        errors.append("pinned G36 Forge build metadata no longer confirms Java toolchain")
    if 'mappings("parchment", parchmentVersionForge)' not in forge_build:
        errors.append("pinned G36 Forge build metadata no longer confirms Parchment mappings")

    completeness: dict[str, dict] = {}
    for locale in UPSTREAM_LOCALES:
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
        errors.append(f"expected G35 selected scope 90, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.20.2"), None)
    target_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.20.4"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.20.2/1.20.4 missing from Mojang version manifest")
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
        errors.append(f"selected G35 language codes absent from 1.20.4 asset pool: {sorted(inherited-target_codes)}")

    upstream_set = set(UPSTREAM_LOCALES)
    selected_upstream = sorted(inherited & upstream_set)
    selected_complete = sorted(x for x in selected_upstream if not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if completeness[x]["missing"])
    selected_full = sorted(inherited - upstream_set)

    print("Minecraft 1.20.4 / JEI 17.3.0 final localization exploratory audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print("Build: Minecraft 1.20.4 / Forge 49.0.19 / Parchment 1.20.3-2023.12.31-1.20.3 / Java 17")
    print(f"G35 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G36 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G35 -> G36 unchanged: {len(unchanged)}")
    print(f"G35 -> G36 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G35 -> G36 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G35 -> G36 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    if base_meta and target_meta:
        ba, ta = base_meta["assetIndex"], target_meta["assetIndex"]
        print(f"Minecraft 1.20.2 asset index: id={ba.get('id')} sha1={ba.get('sha1')}")
        print(f"Minecraft 1.20.4 asset index: id={ta.get('id')} sha1={ta.get('sha1')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1')}")
    print(f"Minecraft live language asset-file codes: 1.20.2={len(base_codes)} 1.20.4={len(target_codes)}")
    print(f"Live asset additions ({len(live_added)}): {', '.join(sorted(live_added)) or '(none)'}")
    print(f"Live asset removals ({len(live_removed)}): {', '.join(sorted(live_removed)) or '(none)'}")
    print(f"Historical selected language scope inherited unchanged: {len(inherited)}")
    print("Upstream completeness against normal G36 target keys:")
    for locale in UPSTREAM_LOCALES:
        info = completeness[locale]
        print(f"  {locale}: {info['present']}/{info['target']} missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}")
    print(f"Selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete)}")
    print(f"Selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete)}")
    print(f"Selected addon-owned full locales ({len(selected_full)}): {', '.join(selected_full)}")
    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned final Minecraft 1.20.4 / JEI 17.3.0 exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

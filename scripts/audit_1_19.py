#!/usr/bin/env python3
"""Exploratory audit for final Minecraft 1.19 / JEI 11.1.1 localization endpoint."""
from __future__ import annotations

import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.18.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.19" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.18.2-language-scope.json"
PINNED_COMMIT = "91527b7d5fae747455ed7630915c088e3fe0f602"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
UPSTREAM_LOCALES = (
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "en_au", "en_us", "es_es",
    "fi_fi", "fr_fr", "he_il", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt",
    "nb_no", "pl_pl", "pt_br", "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn", "zh_tw",
)


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G28-audit"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
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


def client_language_registry(version_meta: dict) -> tuple[set[str], tuple[str, ...]]:
    client_url = version_meta.get("downloads", {}).get("client", {}).get("url")
    if not client_url:
        raise ValueError("version metadata has no client download URL")
    jar = fetch_bytes(client_url, timeout=90)
    with zipfile.ZipFile(io.BytesIO(jar)) as archive:
        candidates = tuple(sorted(
            name for name in archive.namelist()
            if name.lower().endswith("languages.json") or name.lower().endswith("language.json")
        ))
        if not candidates:
            return set(), ()
        for name in candidates:
            try:
                raw = json.loads(archive.read(name).decode("utf-8"))
            except Exception:
                continue
            if isinstance(raw, dict) and raw:
                codes = {str(code).lower() for code in raw}
                if any("_" in code for code in codes):
                    codes.add("en_us")
                    return codes, candidates
        return set(), candidates


def main() -> int:
    errors: list[str] = []
    base = parse_jei_json(BASE_SOURCE)
    stored_target = parse_jei_json(TARGET_SOURCE)
    remote_target = parse_jei_json_bytes(fetch_bytes(f"{RAW_LANG}/en_us.json"))
    if stored_target != remote_target:
        errors.append("stored G28 English source differs from pinned JEI 11.1.1 endpoint")
    target = remote_target
    base_normal = {k for k in base if not k.startswith(DEBUG_PREFIX)}
    target_normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    changed_debug = sorted(k for k in changed if k.startswith(DEBUG_PREFIX))
    reviewed_normal = sorted(k for k in set(added) | set(changed) if not k.startswith(DEBUG_PREFIX))

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    forge_build = fetch_text(f"{RAW_ROOT}/Forge/build.gradle.kts")
    for token in (
        "modJavaVersion=17",
        "minecraftVersion=1.19",
        "forgeVersion=41.1.0",
        "parchmentVersionForge=1.18.2-2022.07.10-1.19",
        "specificationVersion=11.1.1",
    ):
        if token not in props:
            errors.append(f"pinned G28 gradle.properties missing {token}")
    if 'languageVersion.set(JavaLanguageVersion.of(modJavaVersion))' not in forge_build:
        errors.append("pinned G28 Forge build metadata no longer confirms Java toolchain")
    if 'mappings("parchment", parchmentVersionForge)' not in forge_build:
        errors.append("pinned G28 Forge build metadata no longer confirms Parchment mappings")

    upstream_locales = UPSTREAM_LOCALES
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
    if len(inherited) != 86:
        errors.append(f"expected G27 selected scope 86, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.18.2"), None)
    target_entry = next((x for x in manifest.get("versions", []) if x.get("id") == "1.19"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.18.2/1.19 missing from Mojang version manifest")
        base_meta = target_meta = base_asset = target_asset = {}
    else:
        base_meta = fetch_json(base_entry["url"])
        target_meta = fetch_json(target_entry["url"])
        base_asset = fetch_json(base_meta["assetIndex"]["url"])
        target_asset = fetch_json(target_meta["assetIndex"]["url"])

    base_codes = language_codes(base_asset) if base_asset else set()
    target_codes = language_codes(target_asset) if target_asset else set()
    try:
        client_registry, registry_candidates = client_language_registry(target_meta) if target_meta else (set(), ())
    except Exception as exc:
        client_registry, registry_candidates = set(), ()
        print(f"Client language registry inspection warning: {exc}")

    added_mc = sorted(target_codes - base_codes)
    removed_mc = sorted(base_codes - target_codes)
    inherited_missing = sorted(inherited - target_codes)
    inherited_present = inherited & target_codes
    outside_inherited = sorted(target_codes - inherited)
    upstream_set = set(upstream_locales)
    selected_upstream = sorted(inherited_present & upstream_set)
    selected_complete = sorted(x for x in selected_upstream if not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if completeness[x]["missing"])
    selected_full = sorted(inherited_present - upstream_set)
    newly_upstream_from_full = sorted(set(base_scope["addon_full_locales"]) & upstream_set)
    old_upstream = set(base_scope["selected_upstream_complete_locales"]) | set(base_scope["selected_upstream_incomplete_locales"])
    no_longer_upstream = sorted(old_upstream - upstream_set)

    print("Minecraft 1.19 / JEI 11.1.1 final localization exploratory audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print("Build: Minecraft 1.19 / Forge 41.1.0 / Parchment 1.18.2-2022.07.10-1.19 / Java 17")
    print(f"G27 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G28 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G27 -> G28 unchanged: {len(unchanged)}")
    print(f"G27 -> G28 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G27 -> G28 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G27 -> G28 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    print(f"Changed debug-only ({len(changed_debug)}): {', '.join(changed_debug) or '(none)'}")
    print(f"Reviewed normal added-or-changed ({len(reviewed_normal)}): {', '.join(reviewed_normal) or '(none)'}")
    print(f"JEI upstream JSON locales ({len(upstream_locales)}): {', '.join(upstream_locales)}")
    print("Upstream completeness against normal G28 target keys:")
    for locale in upstream_locales:
        info = completeness[locale]
        print(f"  {locale}: {info['present']}/{info['target']} missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}")
    if base_meta and target_meta:
        ba, ta = base_meta["assetIndex"], target_meta["assetIndex"]
        print(f"Minecraft 1.18.2 asset index: id={ba.get('id')} sha1={ba.get('sha1')} url={ba.get('url')}")
        print(f"Minecraft 1.19 asset index: id={ta.get('id')} sha1={ta.get('sha1')} url={ta.get('url')}")
        print(f"Asset index identical: {ba.get('sha1') == ta.get('sha1')}")
    print(f"Minecraft language asset-file codes: 1.18.2={len(base_codes)} 1.19={len(target_codes)}")
    print(f"Added asset-file codes since 1.18.2 ({len(added_mc)}): {', '.join(added_mc) or '(none)'}")
    print(f"Removed asset-file codes since 1.18.2 ({len(removed_mc)}): {', '.join(removed_mc) or '(none)'}")
    print(f"Client JAR language registry candidates: {', '.join(registry_candidates) or '(none)'}")
    print(f"Client JAR declared language codes ({len(client_registry)}): {', '.join(sorted(client_registry)) or '(none)'}")
    print(f"ry_ua present in client JAR registry: {'ry_ua' in client_registry}")
    print(f"Inherited selected codes absent from 1.19 ({len(inherited_missing)}): {', '.join(inherited_missing) or '(none)'}")
    print(f"Inherited selected codes still present: {len(inherited_present)}")
    print(f"Minecraft codes outside inherited selected scope ({len(outside_inherited)}): {', '.join(outside_inherited) or '(none)'}")
    print(f"Selected upstream complete ({len(selected_complete)}): {', '.join(selected_complete)}")
    print(f"Selected upstream incomplete ({len(selected_incomplete)}): {', '.join(selected_incomplete)}")
    print(f"Selected addon-owned full locales ({len(selected_full)}): {', '.join(selected_full)}")
    print(f"Addon-full locales newly shipped by JEI upstream ({len(newly_upstream_from_full)}): {', '.join(newly_upstream_from_full) or '(none)'}")
    print(f"Previously selected upstream locales no longer shipped ({len(no_longer_upstream)}): {', '.join(no_longer_upstream) or '(none)'}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned final Minecraft 1.19 / JEI 11.1.1 exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

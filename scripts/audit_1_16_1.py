#!/usr/bin/env python3
"""Audit final Minecraft 1.16.1 / JEI 7.0.1 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.15.2" / "en_us.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.16.1" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.15.2-language-scope.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.15.2-to-1.16.1.json"
PINNED_COMMIT = "0a0dbfac9c53124d82a602301d466dbf2c5e3e97"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
DEBUG_PREFIX = "description.jei."
UPSTREAM_LOCALES = (
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "en_au", "en_us", "es_es",
    "fi_fi", "fr_fr", "he_il", "it_it", "ja_jp", "ko_kr", "lt_lt", "nb_no",
    "pl_pl", "pt_br", "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn", "zh_tw",
)


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G19-audit"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch_bytes(url).decode("utf-8"))


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


def main() -> int:
    errors: list[str] = []
    base = parse_jei_json(BASE_SOURCE)
    stored_target = parse_jei_json(TARGET_SOURCE)
    remote_target = parse_jei_json_bytes(fetch_bytes(f"{RAW_BASE}/en_us.json"))
    if stored_target != remote_target:
        errors.append("stored G19 English source differs from pinned JEI 7.0.1 endpoint")
    target = remote_target
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])

    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    actual_counts = (len(unchanged), len(added), len(removed), len(changed))
    frozen_counts = (
        diff["unchanged_key_and_value_count"], diff["added_key_count"],
        diff["removed_key_count"], diff["changed_english_value_count"],
    )
    if actual_counts != frozen_counts:
        errors.append(f"frozen G18->G19 diff counts {frozen_counts} differ from live endpoint {actual_counts}")
    if added != diff["added_keys"] or removed != diff["removed_keys"]:
        errors.append("frozen G19 added/removed key sets differ from live endpoint")
    frozen_changed = sorted(diff["changed_english_values"])
    if changed != frozen_changed:
        errors.append(f"frozen changed keys {frozen_changed} differ from live endpoint {changed}")
    for key in changed:
        entry = diff["changed_english_values"][key]
        if entry.get("from") != base[key] or entry.get("to") != target[key]:
            errors.append(f"frozen changed values for {key} differ from live endpoint")

    completeness: dict[str, dict] = {}
    for locale in UPSTREAM_LOCALES:
        values = parse_jei_json_bytes(fetch_bytes(f"{RAW_BASE}/{locale}.json"))
        missing = sorted(target_normal - set(values))
        extra = sorted(set(values) - set(target))
        completeness[locale] = {
            "present": len(target_normal & set(values)), "target": len(target_normal),
            "missing": missing, "extra": extra,
        }

    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    inherited = (
        set(base_scope["addon_full_locales"])
        | set(base_scope["selected_upstream_complete_locales"])
        | set(base_scope["selected_upstream_incomplete_locales"])
    )
    if len(inherited) != 87:
        errors.append(f"expected G18 selected scope of 87, got {len(inherited)}")

    manifest = fetch_json(VERSION_MANIFEST)
    base_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.15.2"), None)
    target_entry = next((item for item in manifest.get("versions", []) if item.get("id") == "1.16.1"), None)
    if not base_entry or not target_entry:
        errors.append("Minecraft 1.15.2/1.16.1 missing from Mojang version manifest")
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
    selected_upstream = sorted(inherited_present & set(UPSTREAM_LOCALES))
    selected_complete = sorted(x for x in selected_upstream if not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if completeness[x]["missing"])
    selected_full = sorted(inherited_present - set(UPSTREAM_LOCALES))

    print("Minecraft 1.16.1 / JEI 7.0.1 final localization audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print(f"G18 English: {len(base)} total")
    print(f"G19 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G18 -> G19 unchanged: {len(unchanged)}")
    print(f"G18 -> G19 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G18 -> G19 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G18 -> G19 changed ({len(changed)}):")
    for key in changed:
        print(f"  {key}: {base[key]!r} -> {target[key]!r}")
    print(f"JEI upstream JSON locales ({len(UPSTREAM_LOCALES)}): {', '.join(UPSTREAM_LOCALES)}")
    print("Upstream completeness against normal G19 target keys:")
    for locale in UPSTREAM_LOCALES:
        info = completeness[locale]
        print(f"  {locale}: {info['present']}/{info['target']} missing={len(info['missing'])} [{', '.join(info['missing'])}] extra={len(info['extra'])}")
    if base_meta and target_meta:
        ba, ta = base_meta.get("assetIndex", {}), target_meta.get("assetIndex", {})
        print(f"Minecraft 1.15.2 asset index: id={ba.get('id')} sha1={ba.get('sha1')} url={ba.get('url')}")
        print(f"Minecraft 1.16.1 asset index: id={ta.get('id')} sha1={ta.get('sha1')} url={ta.get('url')}")
    print(f"Minecraft language codes: 1.15.2={len(base_codes)} 1.16.1={len(target_codes)}")
    print(f"Added codes since 1.15.2 ({len(added_mc)}): {', '.join(added_mc) or '(none)'}")
    print(f"Removed codes since 1.15.2 ({len(removed_mc)}): {', '.join(removed_mc) or '(none)'}")
    print(f"Inherited selected codes absent from 1.16.1 ({len(inherited_missing)}): {', '.join(inherited_missing) or '(none)'}")
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
    print("PASS: pinned final Minecraft 1.16.1 / JEI 7.0.1 audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

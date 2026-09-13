#!/usr/bin/env python3
"""Exploratory audit for final Minecraft 1.19.4 / JEI 13.1.0 localization endpoint."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.19.3" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.19.3-language-scope.json"
PINNED_COMMIT = "b5b00557f5df18c35e545e3cc8cd65ca4b975ba1"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
DEBUG_PREFIX = "description.jei."
UPSTREAM_LOCALES = (
    "ar_sa", "bg_bg", "cs_cz", "de_de", "el_gr", "en_au", "en_us", "es_es",
    "fi_fi", "fr_fr", "he_il", "id_id", "it_it", "ja_jp", "ko_kr", "lt_lt",
    "nb_no", "pl_pl", "pt_br", "ru_ru", "sv_se", "tr_tr", "uk_ua", "zh_cn", "zh_tw",
)


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G32-audit"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def parse_json_bytes(data: bytes) -> dict[str, str]:
    raw = json.loads(data.decode("utf-8"))
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_json(path: Path) -> dict[str, str]:
    return parse_json_bytes(path.read_bytes())


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

    if (len(base), len(target), len(target_normal)) != (156, 156, 150):
        errors.append(f"unexpected English counts base={len(base)} target={len(target)} normal={len(target_normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (156, 0, 0, 0):
        errors.append("expected 156 unchanged + 0 added + 0 removed + 0 changed")

    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    forge_build = fetch_text(f"{RAW_ROOT}/Forge/build.gradle.kts")
    for token in (
        "modJavaVersion=17", "minecraftVersion=1.19.4", "forgeVersion=45.0.40",
        "parchmentVersionForge=1.19.3-2023.03.12-1.19.4", "specificationVersion=13.1.0",
    ):
        if token not in props:
            errors.append(f"pinned G32 gradle.properties missing {token}")
    if 'languageVersion.set(JavaLanguageVersion.of(modJavaVersion))' not in forge_build:
        errors.append("pinned G32 Forge build metadata no longer confirms Java toolchain")
    if 'mappings("parchment", parchmentVersionForge)' not in forge_build:
        errors.append("pinned G32 Forge build metadata no longer confirms Parchment mappings")

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
    if len(inherited) != 88:
        errors.append(f"expected G31 selected scope 88, got {len(inherited)}")

    upstream_set = set(UPSTREAM_LOCALES)
    selected_upstream = sorted(inherited & upstream_set)
    selected_complete = sorted(x for x in selected_upstream if not completeness[x]["missing"])
    selected_incomplete = sorted(x for x in selected_upstream if completeness[x]["missing"])
    selected_full = sorted(inherited - upstream_set)

    print("Minecraft 1.19.4 / JEI 13.1.0 final localization exploratory audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print("Build: Minecraft 1.19.4 / Forge 45.0.40 / Parchment 1.19.3-2023.03.12-1.19.4 / Java 17")
    print(f"G31 English: {len(base)} total / {len(base_normal)} normal / {len(base)-len(base_normal)} debug")
    print(f"G32 English: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G31 -> G32 unchanged: {len(unchanged)}")
    print(f"G31 -> G32 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G31 -> G32 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G31 -> G32 changed ({len(changed)}): {', '.join(changed) or '(none)'}")
    print("Historical selected language scope: unchanged at 88 for Minecraft 1.19.4")
    print("Minecraft 1.19.4 language-file change: en_us ordering changed in 23w07a; selected language membership unchanged")
    print("Upstream completeness against normal G32 target keys:")
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
    print("PASS: pinned final Minecraft 1.19.4 / JEI 13.1.0 exploratory audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

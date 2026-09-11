#!/usr/bin/env python3
"""Audit the pinned Minecraft 1.10.2 / JEI 3.14.8 localization endpoint.

This script is intentionally read-only. It verifies the pinned English source,
computes the exact G5 -> G6 English diff, checks the Minecraft asset inventory,
and measures ownership/completeness of every JEI 3.14.8 upstream locale.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.10" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.10.2" / "en_US.lang"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.10-language-scope.json"
PINNED_COMMIT = "446af20eaa73d260517f0adc737232437363f78d"
RAW_BASE = (
    "https://raw.githubusercontent.com/mezz/JustEnoughItems/"
    f"{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
)
CONTENTS_URL = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
MC_1_10_ASSET_INDEX = (
    "https://piston-meta.mojang.com/v1/packages/"
    "7c2800b458376b8fc0b738382fb7784328fddda9/1.10.json"
)
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G6-audit"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_json(url: str):
    return json.loads(fetch_bytes(url).decode("utf-8"))


def parse_lang_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value
    return values


def parse_lang(path: Path) -> dict[str, str]:
    return parse_lang_text(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    base = parse_lang(BASE_SOURCE)
    target = parse_lang(TARGET_SOURCE)
    target_normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    remote_english = fetch_bytes(f"{RAW_BASE}/en_US.lang").decode("utf-8")
    if parse_lang_text(remote_english) != target:
        errors.append("stored 1.10.2 English source differs from pinned JEI upstream")

    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(key for key in set(base) & set(target) if base[key] != target[key])
    unchanged = sorted(key for key in set(base) & set(target) if base[key] == target[key])

    listing = fetch_json(CONTENTS_URL)
    upstream_locales = sorted(
        Path(item["name"]).stem
        for item in listing
        if item.get("type") == "file" and item.get("name", "").endswith(".lang")
    )

    completeness: dict[str, dict] = {}
    for locale in upstream_locales:
        values = parse_lang_text(fetch_bytes(f"{RAW_BASE}/{locale}.lang").decode("utf-8"))
        missing = sorted(target_normal - set(values))
        extra = sorted(set(values) - set(target))
        completeness[locale] = {
            "present": len(target_normal & set(values)),
            "target": len(target_normal),
            "missing": missing,
            "extra": extra,
        }

    base_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    g3_scope = json.loads((ROOT / "upstream" / "minecraft-1.9-language-scope.json").read_text(encoding="utf-8"))
    selected = set(g3_scope["retained_primary_languages"]) | set(base_scope["new_selected_primary_languages"])
    selected_upstream = sorted(selected & set(upstream_locales))
    selected_upstream_complete = sorted(
        locale for locale in selected_upstream if not completeness[locale]["missing"]
    )
    selected_upstream_incomplete = sorted(
        locale for locale in selected_upstream if completeness[locale]["missing"]
    )
    addon_full = sorted(selected - set(upstream_locales))

    # Minecraft 1.10.2 reuses the same asset index as 1.10. Verify its 94-code set.
    asset_index = fetch_json(MC_1_10_ASSET_INDEX)
    mc_codes = {
        Path(name).stem
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/") and name.endswith(".lang")
    } | {"en_US"}
    if len(mc_codes) != 94:
        errors.append(f"expected 94 Minecraft 1.10.2 language codes, got {len(mc_codes)}")
    if selected - mc_codes:
        errors.append(f"selected scope contains codes absent from Minecraft asset index: {sorted(selected - mc_codes)}")

    print("Minecraft 1.10.2 / JEI 3.14.8 localization audit")
    print(f"Pinned commit: {PINNED_COMMIT}")
    print(f"English keys: {len(target)} total / {len(target_normal)} normal / {len(target)-len(target_normal)} debug")
    print(f"G5 -> G6 unchanged: {len(unchanged)}")
    print(f"G5 -> G6 added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"G5 -> G6 removed ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"G5 -> G6 changed ({len(changed)}):")
    for key in changed:
        print(f"  {key}: {base[key]!r} -> {target[key]!r}")
    print(f"JEI upstream locales ({len(upstream_locales)}): {', '.join(upstream_locales)}")
    print("Upstream completeness against normal target keys:")
    for locale in upstream_locales:
        item = completeness[locale]
        print(
            f"  {locale}: {item['present']}/{item['target']} missing={len(item['missing'])} "
            f"[{', '.join(item['missing'])}] extra={len(item['extra'])}"
        )
    print(f"Minecraft raw language codes: {len(mc_codes)}")
    print(f"Selected project scope: {len(selected)}")
    print(f"Selected upstream locales ({len(selected_upstream)}): {', '.join(selected_upstream)}")
    print(f"Selected upstream complete ({len(selected_upstream_complete)}): {', '.join(selected_upstream_complete)}")
    print(f"Selected upstream incomplete ({len(selected_upstream_incomplete)}): {', '.join(selected_upstream_incomplete)}")
    print(f"Addon-owned full locales ({len(addon_full)}): {', '.join(addon_full)}")

    if errors:
        print(f"FAIL: {len(errors)} audit error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: pinned Minecraft 1.10.2 / JEI 3.14.8 audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

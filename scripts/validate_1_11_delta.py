#!/usr/bin/env python3
"""Validate G7 Minecraft 1.11 / JEI 4.1.1 source, scope and ownership."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import reconstruct_1_11 as g7

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.11-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.11-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g7-mc1.11" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.10.2-to-1.11.json"
G6_AUDIT_PATH = ROOT / "upstream" / "minecraft-1.10.2-language-audit.json"
PINNED_COMMIT = "c9fcc36ff0effec2b5239eebd2c9133da04df4bb"
G6_PINNED_COMMIT = "446af20eaa73d260517f0adc737232437363f78d"
RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
G6_RAW_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{G6_PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
MC_ASSET_INDEX = "https://piston-meta.mojang.com/v1/packages/c64959fe73672e9b053b157f57b6aba318d0b3b5/1.11.json"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G7-QA"})
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


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
    g6_audit = json.loads(G6_AUDIT_PATH.read_text(encoding="utf-8"))
    base = g7.parse_lang(g7.BASE_SOURCE)
    target = g7.parse_lang(g7.TARGET_SOURCE)
    normal = {key for key in target if not key.startswith(DEBUG_PREFIX)}

    if base != target:
        errors.append("G7 English source is no longer identical to G6")
    if len(target) != 87 or len(normal) != 84:
        errors.append(f"target key counts changed: total={len(target)}, normal={len(normal)}")
    if (
        diff["unchanged_key_and_value_count"] != 87
        or diff["added_key_count"] != 0
        or diff["removed_key_count"] != 0
        or diff["changed_english_value_count"] != 0
    ):
        errors.append("static G6->G7 diff manifest no longer describes an all-identical 87-key source")
    if not policy["reuse_all_87_base_key_values"] or policy["new_translation_entries_required"] != 0:
        errors.append("G7 policy must reuse all 87 G6 key/value pairs with zero new translations")

    # Verify exact pinned English source and lowercase upstream locale filenames.
    try:
        english_data = fetch_bytes(f"{RAW_BASE}/en_us.lang")
        if git_blob_sha(english_data) != audit["jei_english"]["git_blob_sha"]:
            errors.append("pinned JEI 4.1.1 English blob SHA differs from audit")
        if parse_lang_text(english_data.decode("utf-8")) != target:
            errors.append("stored G7 English source differs from pinned JEI 4.1.1")

        listing = fetch_json(CONTENTS_URL)
        live_locales = sorted(
            Path(item["name"]).stem
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".lang")
        )
        if live_locales != sorted(audit["jei_upstream_locales"]):
            errors.append("pinned JEI 4.1.1 locale list differs from audit")
        if any(locale != locale.lower() for locale in live_locales):
            errors.append("JEI 4.1.1 locale filenames are not all lowercase")

        selected_complete = set(scope["selected_upstream_complete_locales"])
        selected_incomplete = set(scope["selected_upstream_incomplete_locales"])
        if selected_complete != {"en_us", "ru_ru", "sv_se", "uk_ua"}:
            errors.append("G7 complete upstream selected locale set changed")
        if len(selected_incomplete) != 16:
            errors.append("G7 selected incomplete upstream count must be 16")

        g6_comp_lower = {
            locale.lower(): item
            for locale, item in g6_audit["selected_upstream_locale_completeness"].items()
        }
        persistent = set(audit["persistent_incomplete_locales_from_g6"])
        de_expected = set(
            audit["ownership_changes_from_g6"]["became_incomplete"]["de_de"]["missing_normal_keys"]
        )

        for locale in sorted(selected_complete | selected_incomplete):
            data = fetch_bytes(f"{RAW_BASE}/{locale}.lang")
            values = parse_lang_text(data.decode("utf-8"))
            missing = normal - set(values)
            if locale in selected_complete and missing:
                errors.append(f"{locale}: marked complete upstream but live file is missing {len(missing)} keys")
            if locale in selected_incomplete and not missing:
                errors.append(f"{locale}: marked incomplete upstream but live file is complete")
            if locale in persistent:
                expected = set(g6_comp_lower[locale]["missing_normal_keys"])
                if missing != expected:
                    errors.append(f"{locale}: persistent missing-key set changed from G6")
            elif locale == "de_de":
                if missing != de_expected:
                    errors.append(
                        f"de_de: live missing set differs from frozen 16-key ownership change: {sorted(missing)}"
                    )
            elif locale == "sv_se" and missing:
                errors.append("sv_se must be complete in G7")

        # Verify the preserved de_de values are exact translations from pinned G6 upstream de_DE.
        g6_de = parse_lang_text(fetch_bytes(f"{G6_RAW_BASE}/de_DE.lang").decode("utf-8"))
        de_reuse = g7.parse_lang(g7.DE_REUSE_PATH)
        if set(de_reuse) != de_expected:
            errors.append("de_de reuse file key set differs from exact G7 missing set")
        for key in sorted(de_expected):
            if de_reuse.get(key) != g6_de.get(key):
                errors.append(f"de_de: preserved value is not exact pinned G6 upstream translation: {key}")
    except Exception as exc:
        errors.append(f"failed to verify pinned JEI upstream ownership: {exc}")

    # Verify exact Minecraft 1.11 language inventory and scope decision.
    try:
        asset_index = fetch_json(MC_ASSET_INDEX)
        mc_codes = {
            Path(name).stem.lower()
            for name in asset_index.get("objects", {})
            if name.startswith("minecraft/lang/") and name.endswith(".lang")
        } | {"en_us"}
        if len(mc_codes) != 95:
            errors.append(f"expected 95 Minecraft 1.11 language codes, got {len(mc_codes)}")
        if "io_ido" not in mc_codes:
            errors.append("Minecraft 1.11 expected new code io_ido is absent")
        if scope["raw_language_count"] != 95 or scope["selected_scope_count"] != 72:
            errors.append("G7 raw/selected language counts mismatch")
        if scope["new_minecraft_language_codes"] != ["io_ido"]:
            errors.append("G7 new Minecraft language-code list must contain only io_ido")
        if scope["new_deferred_constructed_languages"] != ["io_ido"]:
            errors.append("G7 must explicitly defer io_ido as constructed language")
    except Exception as exc:
        errors.append(f"failed to verify Minecraft 1.11 asset index: {exc}")

    full_locales = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    if len(full_locales) != 52 or len(complete) != 4 or len(incomplete) != 16:
        errors.append("G7 ownership partition counts must be 52 + 4 + 16")
    if full_locales & complete or full_locales & incomplete or complete & incomplete:
        errors.append("G7 ownership partitions overlap")
    if len(full_locales | complete | incomplete) != 72:
        errors.append("G7 ownership partition does not cover exactly 72 selected languages")
    if any(locale != locale.lower() for locale in full_locales | complete | incomplete):
        errors.append("G7 scope contains non-lowercase runtime locale identifiers")
    if len(set(scope["documented_full_english_fallback_locales"])) != 12:
        errors.append("G7 documented full-English fallback count must remain 12")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.11 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.11 / JEI 4.1.1 G7 source, scope and ownership QA")
    print("English: 87 keys / 84 normal / 3 debug; all 87 unchanged from G6")
    print("Minecraft raw/selected: 95 / 72; io_ido deferred as constructed language")
    print("Selected upstream: 20 (4 complete + 16 supplements)")
    print("Ownership change: de_de becomes incomplete; sv_se becomes complete")
    print("Addon-owned full locales: 52")
    print("Resource filenames: lowercase")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

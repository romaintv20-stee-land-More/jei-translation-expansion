#!/usr/bin/env python3
"""Validate the G5 Minecraft 1.10 / JEI 3.7.1 source, scope and reuse rules."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

import reconstruct_1_9_4 as g4
import reconstruct_1_10 as g5

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.10-language-audit.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.10-language-scope.json"
POLICY_PATH = ROOT / "translations" / "g5-mc1.10" / "policy.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.9.4-to-1.10.json"

MC_1_9_ASSET_INDEX = "https://piston-meta.mojang.com/v1/packages/d7aae43ea69d80cc3441bee4179abd791f6534cd/1.9.json"
MC_1_10_ASSET_INDEX = "https://piston-meta.mojang.com/v1/packages/7c2800b458376b8fc0b738382fb7784328fddda9/1.10.json"
PINNED_COMMIT = "7f4e95d5b7620a0d304aa73243cd9b3f9737e247"
RAW_LANG_BASE = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PINNED_COMMIT}/src/main/resources/assets/jei/lang"
CONTENTS_URL = (
    "https://api.github.com/repos/mezz/JustEnoughItems/contents/"
    f"src/main/resources/assets/jei/lang?ref={PINNED_COMMIT}"
)
DEBUG_PREFIX = "description.jei."
EXPECTED_MC_ADDED = {"de_AT", "haw_US", "mn_MN", "swg_de"}
EXPECTED_NEW_SELECTED = {"haw_US", "mn_MN"}
EXPECTED_NEW_DEFERRED = {"de_AT", "swg_de"}


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-G5-QA"})
    with urllib.request.urlopen(request, timeout=30) as response:
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


def minecraft_language_codes(asset_index_url: str) -> set[str]:
    asset_index = fetch_json(asset_index_url)
    external = {
        Path(name).stem
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/") and name.endswith(".lang")
    }
    return external | {"en_US"}


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    errors: list[str] = []
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    diff_manifest = json.loads(DIFF_PATH.read_text(encoding="utf-8"))

    base = g5.parse_lang(g5.BASE_SOURCE)
    target = g5.parse_lang(g5.TARGET_SOURCE)
    added, removed, changed = g5.source_delta_keys(base, target)

    if added:
        errors.append(f"unexpected 1.10 JEI added keys: {sorted(added)}")
    if removed != g5.REMOVED_KEYS:
        errors.append(f"unexpected 1.10 JEI removed keys: {sorted(removed)}")
    if changed != g5.CHANGED_KEYS:
        errors.append(f"unexpected 1.10 JEI changed-value keys: {sorted(changed)}")
    unchanged = {key for key in set(base) & set(target) if base[key] == target[key]}
    if len(unchanged) != 77:
        errors.append(f"expected 77 unchanged key/value pairs, got {len(unchanged)}")
    if len(target) != 78:
        errors.append(f"expected 78 target keys, got {len(target)}")
    normal_keys = {key for key in target if not key.startswith(DEBUG_PREFIX)}
    if len(normal_keys) != 75:
        errors.append(f"expected 75 normal target keys, got {len(normal_keys)}")

    if diff_manifest["unchanged_key_and_value_count"] != len(unchanged):
        errors.append("diff manifest unchanged count mismatch")
    if set(diff_manifest["removed_keys"]) != removed:
        errors.append("diff manifest removed-key set mismatch")
    if set(diff_manifest["changed_english_values"]) != changed:
        errors.append("diff manifest changed-value key set mismatch")

    # Verify the exact Minecraft-facing language expansion from official asset indexes.
    try:
        mc19 = minecraft_language_codes(MC_1_9_ASSET_INDEX)
        mc110 = minecraft_language_codes(MC_1_10_ASSET_INDEX)
        mc_added = mc110 - mc19
        mc_removed = mc19 - mc110
        if mc_added != EXPECTED_MC_ADDED or mc_removed:
            errors.append(
                "unexpected Minecraft 1.10 language delta: "
                f"added={sorted(mc_added)}, removed={sorted(mc_removed)}"
            )
        if len(mc110) != 94:
            errors.append(f"expected 94 Minecraft 1.10 language codes, got {len(mc110)}")
        audited_index = audit["minecraft_asset_index"]
        if len(mc110) != audited_index["raw_language_count_including_en_us"]:
            errors.append(
                f"Minecraft 1.10 raw language count {len(mc110)} differs from audited "
                f"{audited_index['raw_language_count_including_en_us']}"
            )
        if set(audited_index["added_since_1_9"]) != EXPECTED_MC_ADDED:
            errors.append("audit manifest Minecraft-added code set mismatch")
        if audited_index["removed_since_1_9"]:
            errors.append("audit manifest unexpectedly records removed Minecraft language codes")
        if "no_NO" not in mc110 or "nb_NO" in mc110:
            errors.append("Minecraft 1.10 Norwegian locale-code assumptions changed")
    except Exception as exc:  # network evidence should fail closed in CI
        errors.append(f"failed to verify Minecraft asset indexes: {exc}")

    base_scope = json.loads(g4.G3_SCOPE_PATH.read_text(encoding="utf-8"))
    inherited_selected = set(base_scope["retained_primary_languages"])
    inherited_full = set(base_scope["addon_full_locales"])
    new_selected = set(scope["new_selected_primary_languages"])
    new_deferred = set(scope["new_deferred_regional_or_dialect_variants"])
    if new_selected != EXPECTED_NEW_SELECTED:
        errors.append(f"G5 new selected languages mismatch: {sorted(new_selected)}")
    if new_deferred != EXPECTED_NEW_DEFERRED:
        errors.append(f"G5 new deferred variants mismatch: {sorted(new_deferred)}")
    if new_selected | new_deferred != EXPECTED_MC_ADDED:
        errors.append("G5 policy classification does not cover all four new Minecraft codes")
    if new_selected & new_deferred:
        errors.append("G5 new-language selected and deferred sets overlap")
    if scope["selected_scope_count"] != len(inherited_selected | new_selected) or scope["selected_scope_count"] != 72:
        errors.append("G5 selected scope count must be exactly 72")
    if scope["inherited_selected_scope_count"] != len(inherited_selected):
        errors.append("G5 inherited selected scope count mismatch")
    if set(scope["new_addon_full_locales"]) != EXPECTED_NEW_SELECTED:
        errors.append("G5 new addon full locale set must be haw_US and mn_MN")
    if scope["addon_full_locale_count"] != len(inherited_full | EXPECTED_NEW_SELECTED) or scope["addon_full_locale_count"] != 65:
        errors.append("G5 full addon locale count must be exactly 65")
    if scope["scope_changed_from_minecraft_1_9"] is not True:
        errors.append("G5 scope must explicitly record the Minecraft 1.10 inventory change")

    fallback_locales = set(scope["documented_full_english_fallback_locales"])
    expected_fallbacks = set(g4.G3_SCOPE_PATH.read_text(encoding="utf-8") and base_scope["new_full_documented_english_fallback_locales"])
    # Three inherited G1 fallbacks (gv/kw/se) are not in G3's new-full field.
    expected_fallbacks.update({"gv_IM", "kw_GB", "se_NO"})
    expected_fallbacks.update(EXPECTED_NEW_SELECTED)
    if fallback_locales != expected_fallbacks or len(fallback_locales) != 12:
        errors.append(
            f"G5 fallback set mismatch: expected={sorted(expected_fallbacks)}, actual={sorted(fallback_locales)}"
        )
    if set(scope["new_documented_full_english_fallback_locales"]) != EXPECTED_NEW_SELECTED:
        errors.append("G5 new fallback locale set mismatch")

    # Verify exact JEI upstream locale ownership and completeness at the pinned commit.
    upstream_values: dict[str, dict[str, str]] = {}
    try:
        listing = fetch_json(CONTENTS_URL)
        actual_locales = sorted(
            Path(item["name"]).stem
            for item in listing
            if item.get("type") == "file" and item.get("name", "").endswith(".lang")
        )
        if actual_locales != sorted(audit["jei_upstream_locales"]):
            errors.append(
                f"JEI upstream locale list mismatch: expected={sorted(audit['jei_upstream_locales'])}, "
                f"actual={actual_locales}"
            )

        for locale in audit["jei_upstream_locales"]:
            data = fetch_bytes(f"{RAW_LANG_BASE}/{locale}.lang")
            blob_sha = git_blob_sha(data)
            expected_sha = audit["jei_upstream_blob_shas"][locale]
            if blob_sha != expected_sha:
                errors.append(f"{locale}: upstream blob SHA changed: {blob_sha} != {expected_sha}")
            values = parse_lang_text(data.decode("utf-8"))
            upstream_values[locale] = values
            present = set(values) & normal_keys
            missing = normal_keys - set(values)
            audited = audit["jei_upstream_locale_completeness"][locale]
            if len(present) != audited["normal_present"]:
                errors.append(f"{locale}: normal-present count {len(present)} != {audited['normal_present']}")
            if len(missing) != audited["missing_normal"]:
                errors.append(f"{locale}: missing count {len(missing)} != {audited['missing_normal']}")
            explicit = audited.get("missing_normal_keys")
            if explicit is not None and missing != set(explicit):
                errors.append(
                    f"{locale}: explicit missing set mismatch: expected={sorted(explicit)}, actual={sorted(missing)}"
                )
    except Exception as exc:
        errors.append(f"failed to verify pinned JEI upstream locales: {exc}")

    # Reconstructed supplements must be exactly the keys still missing upstream.
    try:
        supplements = g5.reconstruct_supplements(target, scope, audit)
        for locale in scope["upstream_missing_key_supplement_locales"]:
            if locale not in upstream_values:
                continue
            missing = normal_keys - set(upstream_values[locale])
            if set(supplements[locale]) != missing:
                errors.append(
                    f"{locale}: reconstructed supplement is not exact upstream missing set: "
                    f"expected={sorted(missing)}, actual={sorted(supplements[locale])}"
                )
    except Exception as exc:
        errors.append(f"failed to validate G5 supplement reconstruction: {exc}")

    g3_source = g5.parse_lang(g4.BASE_SOURCE)
    if target[g5.CRAFTING_KEY] != g3_source[g5.CRAFTING_KEY]:
        errors.append("G5 craftingTable English value is not an exact G3 semantic reversion")
    if policy["new_non_english_translation_entries_required"] != 0:
        errors.append("G5 policy unexpectedly requests new non-English translations")
    if set(policy["new_documented_english_fallback_locales"]) != EXPECTED_NEW_SELECTED:
        errors.append("G5 policy new fallback locales mismatch")
    if set(policy["removed_keys"]) != g5.REMOVED_KEYS:
        errors.append("G5 policy removed-key set mismatch")
    if set(policy["semantic_reversion_keys"]) != g5.CHANGED_KEYS:
        errors.append("G5 policy semantic-reversion key set mismatch")
    if policy["full_addon_locale_count"] != 65 or policy["full_english_fallback_locale_count"] != 12:
        errors.append("G5 policy full/fallback locale counts mismatch")

    if errors:
        print(f"FAIL: {len(errors)} Minecraft 1.10 G5 source/scope validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: Minecraft 1.10 / JEI 3.7.1 G5 source, scope and upstream QA")
    print("Minecraft language inventory: 94 codes (4 added since 1.9)")
    print("New selected primary languages: haw_US, mn_MN")
    print("New deferred regional variants: de_AT, swg_de")
    print("Selected project scope: 72 languages")
    print("Full addon locales: 65")
    print("Documented full English fallbacks: 12")
    print("New non-English translation entries required: 0")
    print("Upstream missing-key supplements: 6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

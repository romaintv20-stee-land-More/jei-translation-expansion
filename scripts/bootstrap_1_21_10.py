#!/usr/bin/env python3
"""Freeze deterministic G46 / Minecraft 1.21.10 source, ownership, diff, and reuse policy."""
from __future__ import annotations

import json
from pathlib import Path

import audit_1_21_10 as audit
import reconstruct_1_21_9 as g45

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.21.9" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-1.21.9-language-scope.json"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.21.10" / "en_us.json"
DIFF_PATH = ROOT / "upstream" / "diffs" / "1.21.9-to-1.21.10.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.10-language-scope.json"
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.10-language-audit.json"
POLICY_PATH = ROOT / "translations" / "g46-mc1.21.10" / "policy.json"
PINNED_COMMIT = audit.PINNED_COMMIT
NEXT_PORT_COMMIT = audit.NEXT_PORT_COMMIT
DONOR_COMMIT = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
DONOR_LANG = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{DONOR_COMMIT}/Common/src/main/resources/assets/jei/lang"
DONOR_LANG_API = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={DONOR_COMMIT}"
DEBUG_PREFIX = audit.DEBUG_PREFIX
EXPECTED_ADDED = {
    "jei.config.client.tooltips.enableRecipesGuiIngredientsSummary",
    "jei.config.client.tooltips.enableRecipesGuiIngredientsSummary.description",
    "jei.tooltip.recipe.tooltips.craft.ingredients",
}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_donor_locale(locale: str) -> dict[str, str]:
    text = audit.fetch_text(f"{DONOR_LANG}/{locale}.json")
    return audit.clean(json.loads(text))


def main() -> int:
    base = audit.clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    previous_scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(previous_scope["addon_full_locales"]) | set(previous_scope["selected_upstream_complete_locales"]) | set(previous_scope["selected_upstream_incomplete_locales"])
    if len(selected) != 90:
        raise ValueError(f"G45 selected scope changed: {len(selected)}")

    target_raw = audit.fetch_bytes(f"{audit.RAW_LANG}/en_us.json")
    target = audit.clean(json.loads(target_raw.decode("utf-8")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])
    if (len(base), len(target), len(normal)) != (305, 308, 302):
        raise ValueError(f"unexpected G46 source counts: {len(base)}/{len(target)}/{len(normal)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (305, 3, 0, 0):
        raise ValueError("unexpected G45 -> G46 semantic partition")
    if set(added) != EXPECTED_ADDED:
        raise ValueError(f"G46 added-key set changed: {added}")

    next_commit = audit.fetch_json(audit.NEXT_COMMIT_API)
    if [p["sha"] for p in next_commit.get("parents", [])] != [PINNED_COMMIT]:
        raise ValueError("G46 endpoint is no longer the direct parent of the 1.21.11 port")

    props = audit.fetch_text(f"{audit.RAW_ROOT}/gradle.properties")
    for token in (
        "modJavaVersion=21",
        "minecraftVersion=1.21.10",
        "minecraftVersionRange=[1.21.10, 1.21.11)",
        "neoforgeVersion=21.10.64",
        "neoforgeLoaderVersionRange=[4,)",
        "neoforgeVersionRange=[21.9.2-beta,)",
        "specificationVersion=26.2.0",
    ):
        if token not in props:
            raise ValueError(f"pinned G46 metadata missing {token}")

    contents = audit.fetch_json(audit.LANG_API)
    upstream_locales = sorted(Path(x["name"]).stem.lower() for x in contents if x.get("type") == "file" and str(x.get("name", "")).endswith(".json"))
    upstream_set = set(upstream_locales)
    completeness: dict[str, dict] = {}
    malformed: set[str] = set()
    parsed: dict[str, dict[str, str]] = {}
    for locale in sorted(selected & upstream_set):
        values, repaired = audit.parse_locale(locale)
        parsed[locale] = values
        if repaired:
            malformed.add(locale)
        missing = sorted(normal - set(values))
        completeness[locale] = {
            "present_normal_key_count": len(normal & set(values)),
            "target_normal_key_count": len(normal),
            "missing_normal_key_count": len(missing),
            "missing_normal_keys": missing,
            "extra_key_count": len(set(values) - set(target)),
            "extra_keys": sorted(set(values) - set(target)),
            "malformed_upstream_json": repaired,
        }
    if malformed:
        raise ValueError(f"G46 selected upstream JSON must all be valid, got malformed={sorted(malformed)}")
    usable = selected & upstream_set
    complete = sorted(x for x in usable if not completeness[x]["missing_normal_keys"])
    incomplete = sorted(x for x in usable if completeness[x]["missing_normal_keys"])
    addon_full = sorted(selected - usable)
    if (len(addon_full), len(incomplete), len(complete)) != (64, 25, 1) or complete != ["en_us"]:
        raise ValueError(f"unexpected G46 ownership: {len(addon_full)}/{len(incomplete)}/{len(complete)} {complete}")
    if "uk_ua" not in incomplete or "kk_kz" not in incomplete:
        raise ValueError("G46 expected uk_ua and kk_kz to be valid incomplete upstream locales")
    if completeness["uk_ua"]["missing_normal_keys"] != sorted(EXPECTED_ADDED):
        raise ValueError("G46 uk_ua missing-key set changed")
    if completeness["kk_kz"]["missing_normal_keys"] != sorted(EXPECTED_ADDED):
        raise ValueError("G46 kk_kz missing-key set changed")

    manifest = audit.fetch_json(audit.VERSION_MANIFEST)
    base_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.9")
    target_entry = next(x for x in manifest["versions"] if x.get("id") == "1.21.10")
    base_meta = audit.fetch_json(base_entry["url"])
    target_meta = audit.fetch_json(target_entry["url"])
    base_codes = audit.language_codes(audit.fetch_json(base_meta["assetIndex"]["url"]))
    target_codes = audit.language_codes(audit.fetch_json(target_meta["assetIndex"]["url"]))
    live_added = sorted(target_codes - base_codes)
    live_removed = sorted(base_codes - target_codes)
    if live_added or live_removed or selected - target_codes:
        raise ValueError(f"G46 Minecraft language membership changed: added={live_added} removed={live_removed} absent={sorted(selected-target_codes)}")

    donor_en = audit.clean(json.loads(audit.fetch_text(f"{DONOR_LANG}/en_us.json")))
    donor_exact_added = sorted(key for key in added if donor_en.get(key) == target[key])
    if set(donor_exact_added) != EXPECTED_ADDED:
        raise ValueError(f"donor snapshot does not preserve all G46 added English semantics exactly: {donor_exact_added}")
    donor_contents = audit.fetch_json(DONOR_LANG_API)
    donor_locales = {Path(x["name"]).stem.lower() for x in donor_contents if x.get("type") == "file" and str(x.get("name", "")).endswith(".json")}
    donor_coverage: dict[str, list[str]] = {}
    for locale in sorted(selected & donor_locales):
        try:
            values = parse_donor_locale(locale)
        except Exception:
            continue
        keys = sorted(key for key in donor_exact_added if key in values and g45.preserves_runtime_literals(target[key], values[key]))
        if keys:
            donor_coverage[locale] = keys

    fallback_locales = list(previous_scope["documented_full_english_fallback_locales"])
    if len(fallback_locales) != 30 or "uk_ua" in fallback_locales or not set(fallback_locales) <= set(addon_full):
        raise ValueError("G46 documented fallback ownership changed")

    upstream_literal_safety_overrides: dict[str, list[str]] = {}
    for locale in incomplete:
        values = parsed[locale]
        unsafe = [
            key for key in sorted(normal & set(values))
            if not g45.preserves_runtime_literals(target[key], values[key])
        ]
        if unsafe:
            upstream_literal_safety_overrides[locale] = unsafe
    upstream_literal_safety_override_count = sum(len(keys) for keys in upstream_literal_safety_overrides.values())

    TARGET_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    TARGET_SOURCE.write_bytes(target_raw)
    write_json(DIFF_PATH, {
        "schema_version": 1,
        "base_minecraft": "1.21.9", "base_jei": "25.0.1",
        "target_minecraft": "1.21.10", "target_jei": "26.2.0",
        "base_key_count": len(base), "target_key_count": len(target),
        "target_normal_key_count": len(normal), "target_debug_only_key_count": len(target)-len(normal),
        "unchanged_key_and_value_count": len(unchanged), "added_key_count": len(added),
        "removed_key_count": len(removed), "changed_english_value_count": len(changed),
        "unchanged_keys": unchanged, "added_keys": added, "removed_keys": removed,
        "changed_english_values": {},
        "note": "G46 preserves all 305 G45 key/value semantics and adds three recipe-ingredient-summary UI meanings.",
    })

    scope = {
        "minecraft_version": "1.21.10", "jei_version": "26.2.0", "upstream_commit": PINNED_COMMIT,
        "base_scope_manifest": "upstream/minecraft-1.21.9-language-scope.json",
        "raw_language_count": len(target_codes), "selected_scope_count": 90,
        "selected_scope_changed_from_1.21.9": False, "runtime_locale_filename_case": "lowercase", "resource_format": "json",
        "selected_upstream_complete_locales": complete, "selected_upstream_complete_locale_count": len(complete),
        "selected_upstream_incomplete_locales": incomplete, "selected_upstream_incomplete_locale_count": len(incomplete),
        "malformed_upstream_full_override_locales": [], "malformed_upstream_full_override_locale_count": 0,
        "jei_upstream_unselected_or_nonmatching_locales": sorted(upstream_set-selected),
        "addon_full_locale_count": len(addon_full), "addon_full_locales": addon_full,
        "new_selected_primary_languages": [], "removed_selected_languages": [],
        "downloaded": {
            "base_asset_index_id": str(base_meta["assetIndex"].get("id")), "base_asset_index_sha1": base_meta["assetIndex"].get("sha1"),
            "asset_index_id": str(target_meta["assetIndex"].get("id")), "asset_index_sha1": target_meta["assetIndex"].get("sha1"),
            "language_asset_file_count": len(target_codes), "live_language_asset_additions_from_1.21.9": live_added, "live_language_asset_removals_from_1.21.9": live_removed,
        },
        "documented_full_english_fallback_locales": fallback_locales, "documented_full_english_fallback_count": len(fallback_locales),
        "translated_or_ai_assisted_full_locale_count": len(addon_full)-len(fallback_locales),
        "translation_delta": {
            "base_generation": "g45-mc1.21.9", "unchanged_key_and_english_value_count": len(unchanged),
            "added_key_count": 3, "removed_key_count": 0, "changed_english_value_count": 0,
            "reuse_exact_g45_for_unchanged_meanings": True,
        },
        "exact_future_donor": {"commit": DONOR_COMMIT, "exact_same_key_same_english_added_keys": donor_exact_added, "locale_coverage": donor_coverage},
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "upstream_literal_safety_override_count": upstream_literal_safety_override_count,
        "upstream_literal_safety_override_reason": "Pinned upstream values that fail exact placeholder/technical-literal preservation are overridden only for those exact keys with safe same-key reconstruction or exact target English.",
        "upstream_supplement_policy": {
            "preserve_existing_safe_upstream_keys": True,
            "supplement_missing_keys_plus_explicit_safety_overrides": True,
            "explicit_upstream_owned_override_keys": upstream_literal_safety_overrides,
            "reuse_exact_g45_combined_value_only_for_unchanged_key_and_english": True,
            "future_donor_same_key_same_english_reuse_allowed": True,
            "cross_key_reuse_allowed": False,
            "never_emit_other_upstream_owned_keys": True,
            "runtime_merge_requires_validation_before_jar_promotion": True,
        },
        "upstream_validity_transition": {
            "uk_ua_was_malformed_in_g45": True,
            "uk_ua_is_valid_in_g46": True,
            "uk_ua_g46_ownership": "missing-key-only supplement",
            "uk_ua_missing_keys": sorted(completeness["uk_ua"]["missing_normal_keys"]),
        },
        "source_audit": "upstream/minecraft-1.21.10-language-audit.json", "english_diff": "upstream/diffs/1.21.9-to-1.21.10.json",
    }
    write_json(SCOPE_PATH, scope)

    audit_manifest = {
        "schema_version": 1, "audit_date": "2026-09-15", "status": "verified-source-scope-upstream-ownership-and-validity-transition",
        "minecraft": "1.21.10", "jei": "26.2.0", "jei_upstream_commit": PINNED_COMMIT,
        "endpoint_resolution": {"final_1_21_10_commit": PINNED_COMMIT, "next_minecraft_port_commit": NEXT_PORT_COMMIT, "next_minecraft_version": "1.21.11", "note": "The 1.21.11 port is directly parented by this endpoint; upstream notes that 1.21.11 itself was Maven-only."},
        "build_metadata": {"neoforge": "21.10.64", "neoforge_loader_version_range": "[4,)", "neoforge_version_range": "[21.9.2-beta,)", "java_toolchain": "21", "language_format": "json", "locale_filename_case": "lowercase", "english_source_path": "Common/src/main/resources/assets/jei/lang/en_us.json", "specification_version": "26.2.0"},
        "language_scope": {"selected_scope_count": 90, "changed_from_1.21.9": False, "new_selected_primary_languages": [], "removed_selected_languages": [], "decoupled_assets": True},
        "minecraft_asset_indexes": {"minecraft_1.21.9": {"id": str(base_meta["assetIndex"].get("id")), "sha1": base_meta["assetIndex"].get("sha1"), "language_file_count": len(base_codes)}, "minecraft_1.21.10": {"id": str(target_meta["assetIndex"].get("id")), "sha1": target_meta["assetIndex"].get("sha1"), "language_file_count": len(target_codes)}, "live_language_file_additions": live_added, "live_language_file_removals": live_removed},
        "english_source": {"base_key_count": len(base), "target_key_count": len(target), "target_normal_key_count": len(normal), "target_debug_only_key_count": len(target)-len(normal), "unchanged_key_and_value_count": len(unchanged), "added_keys": added, "removed_keys": removed, "changed_english_values": {}},
        "upstream_locale_file_count": len(upstream_locales), "upstream_locales": upstream_locales,
        "selected_upstream_completeness": completeness,
        "ownership": {"addon_full_locale_count": len(addon_full), "supplement_locale_count": len(incomplete), "complete_upstream_locale_count": len(complete), "complete_upstream_locales": complete, "malformed_override_locale_count": 0},
        "upstream_literal_safety_override_count": upstream_literal_safety_override_count,
        "upstream_literal_safety_overrides": upstream_literal_safety_overrides,
        "exact_future_donor": {"commit": DONOR_COMMIT, "exact_added_keys": donor_exact_added, "locale_coverage": donor_coverage},
        "uk_ua_transition": {"g45_malformed": True, "g46_valid": True, "g46_missing_normal_keys": completeness["uk_ua"]["missing_normal_keys"]},
    }
    write_json(AUDIT_PATH, audit_manifest)

    policy = {
        "schema_version": 1, "generation": "g46-mc1.21.10", "minecraft": "1.21.10", "jei": "26.2.0",
        "selected_scope_count": 90, "target_key_count": 308, "target_normal_key_count": 302,
        "translation_reuse": {
            "reuse_exact_unchanged_g45_semantics": True,
            "unchanged_key_count": 305,
            "new_key_count": 3,
            "future_donor_commit": DONOR_COMMIT,
            "future_donor_allowed_only_for_exact_same_key_same_english": True,
            "cross_key_reuse_allowed": False,
            "fallback_when_no_safe_translation": "exact-target-English",
        },
        "ownership": {"full": len(addon_full), "supplements": len(incomplete), "complete_upstream": len(complete), "malformed_full_overrides": 0},
        "upstream_literal_safety_override_count": upstream_literal_safety_override_count,
        "uk_ua_policy": "valid upstream locale in G46; preserve safe upstream values and emit only missing/safety-override keys",
        "runtime_gate": "JSON supplements remain resource-stack merge-test gated before release promotion",
    }
    write_json(POLICY_PATH, policy)

    print("PASS: froze G46 Minecraft 1.21.10 manifests")
    print(f"English: {len(target)} total / {len(normal)} normal / {len(target)-len(normal)} debug")
    print(f"Ownership: {len(addon_full)} full + {len(incomplete)} supplements + {len(complete)} complete = 90")
    print(f"Literal-safety override keys: {upstream_literal_safety_override_count}")
    print(f"Exact future donor coverage locales: {len(donor_coverage)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

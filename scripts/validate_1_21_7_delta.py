#!/usr/bin/env python3
"""Validate frozen G43 / Minecraft 1.21.7 source delta and locale ownership."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import reconstruct_1_21_7 as g43

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "upstream" / "minecraft-1.21.7-language-audit.json"


def main() -> int:
    errors: list[str] = []
    base = g43.parse_json(g43.BASE_SOURCE)
    target = g43.parse_json(g43.TARGET_SOURCE)
    scope = json.loads(g43.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g43.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g43.POLICY_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    previous_scope = json.loads(g43.g42.SCOPE_PATH.read_text(encoding="utf-8"))

    unchanged, added, removed, changed = g43.semantic_sets(base, target)
    normal_keys = {k for k in target if not k.startswith(g43.DEBUG_PREFIX)}
    if (len(base), len(target), len(normal_keys)) != (289, 291, 285):
        errors.append(f"source counts changed: base={len(base)} target={len(target)} normal={len(normal_keys)}")
    if (len(unchanged), len(added), len(removed), len(changed)) != (289, 2, 0, 0):
        errors.append("semantic partition differs from frozen 289/2/0/0")
    if added != g43.ADDED_G43_KEYS:
        errors.append(f"added key set changed: {sorted(added)}")
    if removed or changed:
        errors.append("G43 must have no removed or changed-English keys")

    expected_diff = {
        "base_key_count":289,"target_key_count":291,"target_normal_key_count":285,
        "target_debug_only_key_count":6,"unchanged_key_and_value_count":289,
        "added_key_count":2,"removed_key_count":0,"changed_english_value_count":0,
    }
    for key, expected in expected_diff.items():
        if diff.get(key) != expected:
            errors.append(f"diff {key}: expected {expected!r}, got {diff.get(key)!r}")
    if set(diff.get("added_keys", [])) != g43.ADDED_G43_KEYS or diff.get("removed_keys") != []:
        errors.append("G43 diff key sets differ from frozen two-addition delta")
    if diff.get("changed_english_values") != {}:
        errors.append("G43 diff must have no changed-English entries")

    full = set(scope["addon_full_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    incomplete = set(scope["selected_upstream_incomplete_locales"])
    selected = full | complete | incomplete
    if len(selected) != 90:
        errors.append(f"selected ownership must total 90 locales, got {len(selected)}")
    if full & complete or full & incomplete or complete & incomplete:
        errors.append("G43 locale ownership sets overlap")
    if "en_us" not in complete:
        errors.append("en_us must remain complete upstream")
    if "uk_ua" not in full or "uk_ua" in complete or "uk_ua" in incomplete:
        errors.append("uk_ua must remain exclusively a full repair override while its pinned JSON is malformed")

    previous_selected = (
        set(previous_scope["addon_full_locales"])
        | set(previous_scope["selected_upstream_complete_locales"])
        | set(previous_scope["selected_upstream_incomplete_locales"])
    )
    if selected != previous_selected:
        errors.append("G43 selected 90-language scope differs from G42")
    if set(scope["documented_full_english_fallback_locales"]) != set(previous_scope["documented_full_english_fallback_locales"]):
        errors.append("G43 documented full-English fallback set differs from G42")
    if scope.get("malformed_upstream_full_override_locales") != ["uk_ua"]:
        errors.append("G43 scope must record uk_ua as the sole malformed upstream full override")

    if policy.get("pinned_commit") != g43.G43_COMMIT:
        errors.append("G43 policy pinned commit differs from reconstruction")
    reuse = policy.get("translation_reuse", {})
    if not reuse.get("reuse_exact_unchanged_g42_semantics"):
        errors.append("G43 policy must allow exact unchanged G42 semantic reuse")
    if reuse.get("cross_key_reuse_allowed") is not False:
        errors.append("G43 policy must forbid cross-key reuse")
    if not reuse.get("historical_same_key_same_english_reuse_allowed"):
        errors.append("G43 policy must explicitly permit exact historical same-key/same-English reuse")
    added_policy = policy.get("added_semantics", {})
    if added_policy.get("count") != 2 or set(added_policy.get("keys", [])) != g43.ADDED_G43_KEYS:
        errors.append("G43 policy does not freeze the two added grindstone semantics")
    if added_policy.get("exact_historical_same_key_reuse_permitted") != [g43.REINTRODUCED_EXPERIENCE_KEY]:
        errors.append("G43 policy must identify only grindstone.experience for historical same-key reuse")
    override = policy.get("malformed_upstream_override", {})
    if override.get("locales") != ["uk_ua"] or not override.get("full_override_required"):
        errors.append("G43 policy must require a full uk_ua repair override")

    g41_source = g43.parse_json(g43.g42.g41.TARGET_SOURCE)
    if g41_source.get(g43.REINTRODUCED_EXPERIENCE_KEY) != target.get(g43.REINTRODUCED_EXPERIENCE_KEY):
        errors.append("reintroduced grindstone.experience is not exact same-key/same-English G41 semantics")

    if audit.get("jei_upstream_commit") != g43.G43_COMMIT:
        errors.append("G43 audit pinned commit differs from reconstruction")
    endpoint = audit.get("endpoint_resolution", {})
    if endpoint.get("final_1_21_7_commit") != g43.G43_COMMIT:
        errors.append("G43 final endpoint changed")
    if endpoint.get("next_minecraft_port_commit") != "f61efdf5f6604d0d3a55a67cc5d28ec340f189aa":
        errors.append("G43 next 1.21.8 port commit changed")
    build = audit.get("build_metadata", {})
    if build.get("neoforge") != "21.7.15-beta" or build.get("neoforge_version_range") != "[21.7.15-beta,)" or build.get("java_toolchain") != "21":
        errors.append("G43 frozen build metadata changed")
    if audit.get("malformed_selected_upstream_locales") != ["uk_ua"]:
        errors.append("G43 audit must freeze uk_ua as the sole malformed selected upstream locale")

    try:
        if g43.fetch_g43_upstream("en_us") != target:
            errors.append("frozen G43 en_us differs from pinned JEI endpoint")
    except Exception as exc:
        errors.append(f"could not verify frozen G43 en_us: {exc}")

    for locale in sorted(complete | incomplete):
        try:
            upstream = g43.fetch_g43_upstream(locale)
        except Exception as exc:
            errors.append(f"{locale}: failed to fetch pinned upstream locale: {exc}")
            continue
        missing = normal_keys - set(upstream)
        if locale in complete and missing:
            errors.append(f"{locale}: marked complete but missing {len(missing)} normal keys")
        if locale in incomplete and not missing:
            errors.append(f"{locale}: marked incomplete but has no missing normal keys")

    try:
        url = g43.RAW_JSON_TEMPLATE.format(commit=g43.G43_COMMIT, locale="uk_ua")
        request = urllib.request.Request(url, headers={"User-Agent":"JEI-Translation-Expansion-G43-validate"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_uk = response.read().decode("utf-8")
        try:
            json.loads(raw_uk)
            errors.append("pinned uk_ua unexpectedly became valid JSON; full-override assumption requires review")
        except json.JSONDecodeError:
            repaired = {
                str(k):str(v)
                for k,v in json.loads(g43.g42.g41.repair_uk_ua_text(raw_uk)).items()
                if not str(k).startswith("_")
            }
            unknown = set(repaired) - set(target)
            if unknown:
                # Extra upstream keys are allowed, but their presence is explicitly tracked by the audit.
                audited = set(audit.get("selected_upstream_completeness", {}).get("uk_ua", {}).get("extra_keys", []))
                if unknown != audited:
                    errors.append("uk_ua repaired extra-key set differs from frozen audit")
    except Exception as exc:
        errors.append(f"uk_ua malformed-source verification failed: {exc}")

    if errors:
        print(f"FAIL: {len(errors)} G43 delta/source ownership error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Minecraft 1.21.7 / JEI 23.1.0 frozen source delta and locale ownership")
    print("English delta: 289 unchanged / 2 added / 0 removed / 0 changed")
    print(f"Ownership: {len(full)} full/override / {len(incomplete)} supplements / {len(complete)} complete upstream = 90 selected locales")
    print("Historical reuse is restricted to exact same-key/same-English grindstone.experience semantics from G41")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

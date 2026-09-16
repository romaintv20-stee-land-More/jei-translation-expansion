#!/usr/bin/env python3
"""Audit stable Minecraft 26.3 readiness without prematurely completing G52.

Minecraft 26.3 can be final while JEI still has only a preview/RC branch. This audit
freezes the final Minecraft language-asset state and current JEI branch state, while
leaving G52 unregistered until an exact publishable JEI 26.3 target exists.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SCOPE = ROOT / "upstream" / "minecraft-26.2-language-scope.json"
OUT = ROOT / "upstream" / "provisional" / "minecraft-26.3-release-readiness.json"
VERSION_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
GITHUB_API = "https://api.github.com/repos/mezz/JustEnoughItems"
BASE_PIN = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
PREVIEW_BRANCH = "fabric-26.3-snapshot-7"
PREVIEW_PIN = "58362ffb5baa95580549d6825811e7363964a271"


def request(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-G52-readiness"}
    token = os.getenv("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return request(url).decode("utf-8")


def fetch_json(url: str):
    return json.loads(fetch_text(url))


def fetch_optional_json(url: str):
    try:
        return fetch_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def language_codes(asset_index: dict) -> set[str]:
    codes = {
        Path(name).stem.lower()
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/")
        and Path(name).name != "languages.json"
        and Path(name).suffix in {".lang", ".json"}
    }
    codes.add("en_us")
    return codes


def selected_scope() -> set[str]:
    scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        raise ValueError(f"G51 selected scope changed unexpectedly: {len(selected)}")
    return selected


def parse_properties(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def main() -> int:
    selected = selected_scope()
    manifest = fetch_json(VERSION_MANIFEST)
    by_id = {entry.get("id"): entry for entry in manifest.get("versions", [])}
    base_entry = by_id.get("26.2")
    target_entry = by_id.get("26.3")
    if base_entry is None:
        raise ValueError("Minecraft 26.2 missing from Mojang version manifest")
    if target_entry is None:
        raise ValueError("Minecraft 26.3 is not present in Mojang version manifest yet")
    if target_entry.get("type") != "release":
        raise ValueError(f"Minecraft 26.3 exists but is not a final release: {target_entry.get('type')}")

    base_meta = fetch_json(base_entry["url"])
    target_meta = fetch_json(target_entry["url"])
    base_asset = base_meta["assetIndex"]
    target_asset = target_meta["assetIndex"]
    base_codes = language_codes(fetch_json(base_asset["url"]))
    target_codes = language_codes(fetch_json(target_asset["url"]))
    missing_selected = sorted(selected - target_codes)
    if missing_selected:
        raise ValueError(f"Selected locales missing from final Minecraft 26.3 assets: {missing_selected}")

    base_branch = fetch_json(f"{GITHUB_API}/branches/26.2")
    exact_branch = fetch_optional_json(f"{GITHUB_API}/branches/26.3")
    preview_branch = fetch_optional_json(f"{GITHUB_API}/branches/{PREVIEW_BRANCH}")
    branches = fetch_json(f"{GITHUB_API}/branches?per_page=100")
    matching_branches = sorted(
        item["name"] for item in branches
        if "26.3" in str(item.get("name", ""))
    )

    preview_head = None
    preview_props: dict[str, str] = {}
    if preview_branch is not None:
        preview_head = preview_branch.get("commit", {}).get("sha")
        preview_props = parse_properties(
            fetch_text(
                "https://raw.githubusercontent.com/mezz/JustEnoughItems/"
                f"{preview_head}/gradle.properties"
            )
        )

    exact_head = None if exact_branch is None else exact_branch.get("commit", {}).get("sha")
    exact_props: dict[str, str] = {}
    if exact_head:
        exact_props = parse_properties(
            fetch_text(
                "https://raw.githubusercontent.com/mezz/JustEnoughItems/"
                f"{exact_head}/gradle.properties"
            )
        )

    exact_target_available = bool(
        exact_head and exact_props.get("minecraftVersion") == "26.3"
    )
    preview_promoted_to_final = bool(
        preview_head and preview_props.get("minecraftVersion") == "26.3"
    )
    jei_exact_target_available = exact_target_available or preview_promoted_to_final

    report = {
        "schema_version": 1,
        "audit_date": "2026-09-16",
        "status": (
            "minecraft-26.3-final-jei-exact-target-available"
            if jei_exact_target_available
            else "minecraft-26.3-final-jei-exact-target-pending"
        ),
        "not_a_completed_generation": True,
        "g52_registration_allowed": False,
        "minecraft": {
            "version": "26.3",
            "manifest_type": target_entry.get("type"),
            "release_time": target_entry.get("releaseTime"),
            "asset_index_id": target_asset.get("id"),
            "asset_index_sha1": target_asset.get("sha1"),
            "language_asset_file_count": len(target_codes),
            "language_additions_from_26_2": sorted(target_codes - base_codes),
            "language_removals_from_26_2": sorted(base_codes - target_codes),
            "selected_scope_count": len(selected),
            "selected_scope_still_present": True,
        },
        "base_g51": {
            "minecraft": "26.2",
            "pinned_jei_commit": BASE_PIN,
            "current_26_2_branch_head": base_branch.get("commit", {}).get("sha"),
            "branch_moved_since_g51_pin": base_branch.get("commit", {}).get("sha") != BASE_PIN,
            "asset_index_id": base_asset.get("id"),
            "asset_index_sha1": base_asset.get("sha1"),
            "language_asset_file_count": len(base_codes),
        },
        "jei": {
            "exact_26_3_branch_present": exact_branch is not None,
            "exact_26_3_branch_head": exact_head,
            "exact_26_3_minecraft_version": exact_props.get("minecraftVersion"),
            "preview_branch": PREVIEW_BRANCH,
            "preview_expected_pin": PREVIEW_PIN,
            "preview_current_head": preview_head,
            "preview_branch_moved": bool(preview_head and preview_head != PREVIEW_PIN),
            "preview_minecraft_version": preview_props.get("minecraftVersion"),
            "preview_specification_version": preview_props.get("specificationVersion"),
            "preview_fabric_loader": preview_props.get("fabricLoaderVersion"),
            "preview_fabric_api": preview_props.get("fabricApiVersion"),
            "matching_26_3_branches": matching_branches,
            "exact_publishable_target_available": jei_exact_target_available,
        },
        "decision": {
            "minecraft_side_ready": True,
            "translation_groundwork_ready": True,
            "complete_g52_now": False,
            "reason": (
                "An exact JEI Minecraft 26.3 target is now visible; run a fresh exact G52 endpoint/loader audit before registration."
                if jei_exact_target_available
                else "Minecraft 26.3 is final, but JEI still has no exact final 26.3 target. Keep the RC2/Fabric work provisional and do not publish or register G52 yet."
            ),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("PASS: Minecraft 26.3 final release readiness audited")
    print(f"Final language assets: {len(target_codes)}")
    print(f"Language additions from 26.2: {sorted(target_codes - base_codes)}")
    print(f"Language removals from 26.2: {sorted(base_codes - target_codes)}")
    print(f"JEI matching 26.3 branches: {matching_branches}")
    print(f"JEI exact final 26.3 target available: {jei_exact_target_available}")
    if jei_exact_target_available:
        print("NEXT: start an exact G52 audit; this readiness report alone does not complete G52")
    else:
        print("WAIT: keep G52 provisional until JEI exposes an exact final 26.3 target")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

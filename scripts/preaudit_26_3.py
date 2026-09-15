#!/usr/bin/env python3
"""Pre-audit JEI's current Minecraft 26.3 preview without creating a final generation.

This intentionally does not register packaging metadata. The observed upstream target is an RC
on a Fabric preview branch, so it is only groundwork for the next stable Minecraft generation.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream" / "sources" / "26.2" / "en_us.json"
BASE_SCOPE = ROOT / "upstream" / "minecraft-26.2-language-scope.json"
OUTPUT = ROOT / "upstream" / "previews" / "minecraft-26.3-rc2-preaudit.json"

BASE_BRANCH = "26.2"
BASE_PIN = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
PREVIEW_BRANCH = "fabric-26.3-snapshot-7"
PREVIEW_PIN = "58362ffb5baa95580549d6825811e7363964a271"
PREVIEW_MC = "26.3-rc-2"
DEBUG_PREFIX = "description.jei."

API_ROOT = "https://api.github.com/repos/mezz/JustEnoughItems"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PREVIEW_PIN}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"


def request(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-26.3-preaudit"}
    token = os.getenv("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def text(url: str) -> str:
    return request(url).decode("utf-8")


def remote_json(url: str):
    return json.loads(text(url))


def clean(raw: dict) -> dict[str, str]:
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def branch_head(name: str) -> str | None:
    try:
        data = remote_json(f"{API_ROOT}/branches/{name}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    return data.get("commit", {}).get("sha")


def parse_locale(locale: str) -> tuple[dict[str, str] | None, str | None]:
    try:
        raw = json.loads(text(f"{RAW_LANG}/{locale}.json"))
        return clean(raw), None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "missing"
        raise
    except json.JSONDecodeError as exc:
        return None, f"{exc.msg} at line {exc.lineno} column {exc.colno}"


def main() -> int:
    current_base_head = branch_head(BASE_BRANCH)
    if current_base_head != BASE_PIN:
        raise ValueError(
            f"G51 base became stale: upstream {BASE_BRANCH} is {current_base_head}, expected {BASE_PIN}"
        )

    preview_head = branch_head(PREVIEW_BRANCH)
    if preview_head != PREVIEW_PIN:
        raise ValueError(
            f"26.3 preview moved: {PREVIEW_BRANCH} is {preview_head}, expected {PREVIEW_PIN}; re-audit first"
        )

    stable_26_3_head = branch_head("26.3")

    props = text(f"{RAW_ROOT}/gradle.properties")
    required = (
        "modJavaVersion=25",
        "minecraftVersion=26.3-rc-2",
        "minecraftVersionRange=[26.3-rc-2]",
        "fabricLoaderVersion=0.19.5",
        "fabricApiVersion=0.160.4+26.3",
        "curseProjectId=238222",
        "modrinthId=u6dRKJwZ",
        "specificationVersion=30.32.0",
        "apiCompatibilityMinecraftVersion=26.2",
    )
    for token in required:
        if token not in props:
            raise ValueError(f"26.3 preview gradle.properties missing {token}")

    base = clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    target = clean(json.loads(text(f"{RAW_LANG}/en_us.json")))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}

    unchanged = sorted(k for k in set(base) & set(target) if base[k] == target[k])
    added = sorted(set(target) - set(base))
    removed = sorted(set(base) - set(target))
    changed = sorted(k for k in set(base) & set(target) if base[k] != target[k])

    scope = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        raise ValueError(f"G51 selected scope changed unexpectedly: {len(selected)}")

    contents = remote_json(
        f"{API_ROOT}/contents/Common/src/main/resources/assets/jei/lang?ref={PREVIEW_PIN}"
    )
    upstream_locales = sorted(
        Path(item["name"]).stem.lower()
        for item in contents
        if item.get("type") == "file" and str(item.get("name", "")).endswith(".json")
    )
    upstream_set = set(upstream_locales)
    complete: list[str] = []
    incomplete: list[str] = []
    malformed: dict[str, str] = {}
    missing_counts: dict[str, int] = {}
    for locale in sorted(selected & upstream_set):
        values, error = parse_locale(locale)
        if error is not None or values is None:
            malformed[locale] = error or "unknown parse failure"
            continue
        missing = normal - set(values)
        missing_counts[locale] = len(missing)
        (complete if not missing else incomplete).append(locale)

    usable_upstream = (selected & upstream_set) - set(malformed)
    addon_full = sorted(selected - usable_upstream)

    manifest = {
        "schema_version": 1,
        "audit_date": "2026-09-15",
        "status": "preliminary-preview-not-final-generation",
        "base": {
            "minecraft": "26.2",
            "generation": "G51",
            "jei_branch": BASE_BRANCH,
            "verified_branch_head": BASE_PIN,
            "english_key_count": len(base),
        },
        "preview": {
            "branch": PREVIEW_BRANCH,
            "commit": PREVIEW_PIN,
            "minecraft": PREVIEW_MC,
            "loader": "fabric",
            "fabric_loader": "0.19.5",
            "fabric_api": "0.160.4+26.3",
            "java": 25,
            "jei_specification_version": "30.32.0",
            "api_compatibility_minecraft": "26.2",
            "stable_26_3_branch_present": stable_26_3_head is not None,
            "stable_26_3_branch_head": stable_26_3_head,
        },
        "english": {
            "target_key_count": len(target),
            "target_normal_key_count": len(normal),
            "target_debug_key_count": len(target) - len(normal),
            "unchanged_same_key_same_english_count": len(unchanged),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "changed_english_value_count": len(changed),
            "added_keys": {k: target[k] for k in added},
            "removed_keys": removed,
            "changed_english_values": {
                k: {"from": base[k], "to": target[k]} for k in changed
            },
        },
        "scope_preview": {
            "selected_scope_count": len(selected),
            "upstream_locale_file_count": len(upstream_locales),
            "addon_full_if_frozen_now": len(addon_full),
            "supplements_if_frozen_now": len(incomplete),
            "complete_upstream_if_frozen_now": len(complete),
            "complete_upstream_locales": complete,
            "malformed_selected_upstream_locales": malformed,
            "incomplete_upstream_missing_counts": missing_counts,
        },
        "policy": {
            "register_as_G52_now": False,
            "package_candidate_now": False,
            "reason": "Upstream currently targets Minecraft 26.3-rc-2 on a Fabric preview branch, not a stable 26.3 release target.",
            "next_action": "Re-audit when upstream publishes or moves to a stable Minecraft 26.3 target; only then freeze G52 and decide final loader packaging.",
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("PASS: preliminary Minecraft 26.3 RC audit")
    print(f"G51 maintained 26.2 branch still pinned at {BASE_PIN}")
    print(f"Preview: {PREVIEW_BRANCH} @ {PREVIEW_PIN} -> Minecraft {PREVIEW_MC} / Fabric / Java 25")
    print(
        f"English delta vs G51: unchanged={len(unchanged)} added={len(added)} "
        f"removed={len(removed)} changed={len(changed)} total={len(target)}"
    )
    print(
        f"Preview ownership if frozen now: full={len(addon_full)} supplements={len(incomplete)} "
        f"complete={len(complete)} malformed={malformed}"
    )
    print(f"Stable 26.3 branch present: {stable_26_3_head is not None}")
    print("PREVIEW ONLY: G52 packaging remains blocked until a stable 26.3 target exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

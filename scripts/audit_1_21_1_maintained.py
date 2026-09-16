#!/usr/bin/env python3
"""Audit the maintained JEI 1.21.1 branch against the historical G39 snapshot.

This does not mutate G39. It quantifies the maintained endpoint delta, current upstream
ownership, and exact same-key/same-English donor coverage available from later completed
project generations before any maintenance refresh is attempted.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_SOURCE = ROOT / "upstream" / "sources" / "1.21.1" / "en_us.json"
SCOPE_PATH = ROOT / "upstream" / "minecraft-1.21.1-language-scope.json"
PACKAGING = ROOT / "packaging" / "completed-versions.json"
HEAD = "bf7b64d24f18b957ffdb806227b6077a2088eaff"
RAW_ROOT = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{HEAD}"
RAW_LANG = f"{RAW_ROOT}/Common/src/main/resources/assets/jei/lang"
API_LANG = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/Common/src/main/resources/assets/jei/lang?ref={HEAD}"
DEBUG_PREFIX = "description.jei."


def fetch_bytes(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-maintained-1.21.1-audit"}
    token = os.getenv("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def parse_text(text: str) -> dict[str, str]:
    raw = json.loads(text)
    return {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}


def parse_file(path: Path) -> dict[str, str]:
    return parse_text(path.read_text(encoding="utf-8"))


def source_for(mc: str) -> Path:
    return ROOT / "upstream" / "sources" / mc / "en_us.json"


def main() -> int:
    old = parse_file(OLD_SOURCE)
    target = parse_text(fetch_text(f"{RAW_LANG}/en_us.json"))
    props = fetch_text(f"{RAW_ROOT}/gradle.properties")
    expected_tokens = (
        "minecraftVersion=1.21.1",
        "modJavaVersion=21",
        "neoforgeVersion=21.1.248",
        "specificationVersion=19.56.0",
    )
    errors = [f"gradle.properties missing {token}" for token in expected_tokens if token not in props]

    old_keys = set(old)
    target_keys = set(target)
    added = sorted(target_keys - old_keys)
    removed = sorted(old_keys - target_keys)
    changed = sorted(k for k in old_keys & target_keys if old[k] != target[k])
    unchanged = sorted(k for k in old_keys & target_keys if old[k] == target[k])

    packaging = json.loads(PACKAGING.read_text(encoding="utf-8"))
    donors: dict[str, list[str]] = {}
    after_g39 = False
    for cfg in packaging["versions"]:
        if cfg["generation"] == "G39":
            after_g39 = True
            continue
        if not after_g39 or cfg.get("format") != "json":
            continue
        path = source_for(cfg["minecraft"])
        if not path.is_file():
            continue
        values = parse_file(path)
        for key in set(added) | set(changed):
            if values.get(key) == target.get(key):
                donors.setdefault(key, []).append(cfg["generation"])

    lang_listing = json.loads(fetch_text(API_LANG))
    upstream_locales = sorted(
        item["name"][:-5]
        for item in lang_listing
        if item.get("type") == "file" and item.get("name", "").endswith(".json")
    )

    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    selected = (
        set(scope["addon_full_locales"])
        | set(scope["selected_upstream_complete_locales"])
        | set(scope["selected_upstream_incomplete_locales"])
    )
    if len(selected) != 90:
        errors.append(f"historical G39 selected scope expected 90, got {len(selected)}")

    normal_keys = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    completeness: dict[str, dict] = {}
    malformed: list[str] = []
    for locale in upstream_locales:
        try:
            values = parse_text(fetch_text(f"{RAW_LANG}/{locale}.json"))
        except (json.JSONDecodeError, urllib.error.URLError) as exc:
            malformed.append(locale)
            completeness[locale] = {"malformed": True, "error": str(exc)}
            continue
        missing = sorted(normal_keys - set(values))
        completeness[locale] = {
            "malformed": False,
            "present": len(normal_keys & set(values)),
            "target": len(normal_keys),
            "missing_count": len(missing),
            "missing": missing,
            "extra_count": len(set(values) - target_keys),
        }

    selected_upstream = sorted(selected & set(upstream_locales))
    selected_complete = sorted(
        loc for loc in selected_upstream
        if not completeness[loc].get("malformed") and completeness[loc]["missing_count"] == 0
    )
    selected_incomplete = sorted(loc for loc in selected_upstream if loc not in selected_complete)
    selected_full = sorted(selected - set(upstream_locales))

    delta_keys = added + changed
    donor_covered = sorted(k for k in delta_keys if k in donors)
    no_donor = sorted(k for k in delta_keys if k not in donors)

    report = {
        "maintained_commit": HEAD,
        "minecraft": "1.21.1",
        "jei": "19.56.0",
        "historical_g39_keys": len(old),
        "maintained_keys": len(target),
        "maintained_normal_keys": len(normal_keys),
        "unchanged_count": len(unchanged),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_english_count": len(changed),
        "added_keys": added,
        "removed_keys": removed,
        "changed_english": {k: {"old": old[k], "new": target[k]} for k in changed},
        "exact_later_generation_donor_coverage_count": len(donor_covered),
        "exact_later_generation_donor_coverage": {k: donors[k] for k in donor_covered},
        "delta_keys_without_exact_later_donor": no_donor,
        "upstream_locale_count": len(upstream_locales),
        "malformed_upstream_locales": malformed,
        "selected_scope_count": len(selected),
        "selected_upstream_complete": selected_complete,
        "selected_upstream_incomplete": selected_incomplete,
        "selected_addon_full": selected_full,
        "selected_upstream_completeness": {loc: completeness[loc] for loc in selected_upstream},
    }
    out = ROOT / "build" / "maintained-1.21.1-audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Maintained JEI 1.21.1 branch audit")
    print(f"Commit: {HEAD}")
    print("Build: Minecraft 1.21.1 / JEI 19.56.0 / NeoForge 21.1.248 / Java 21")
    print(f"Historical G39 keys: {len(old)}")
    print(f"Maintained keys: {len(target)} total / {len(normal_keys)} normal / {len(target)-len(normal_keys)} debug")
    print(f"Delta: unchanged={len(unchanged)} added={len(added)} removed={len(removed)} changed-English={len(changed)}")
    print(f"Added keys ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"Removed keys ({len(removed)}): {', '.join(removed) or '(none)'}")
    print(f"Changed English ({len(changed)}):")
    for key in changed:
        print(f"  {key}: {old[key]!r} -> {target[key]!r}")
    print(f"Exact later-generation donor coverage for added/changed meanings: {len(donor_covered)}/{len(delta_keys)}")
    print(f"No exact later donor ({len(no_donor)}): {', '.join(no_donor) or '(none)'}")
    print(f"Upstream locales: {len(upstream_locales)}; malformed: {', '.join(malformed) or '(none)'}")
    print(f"Selected scope: {len(selected)} = full {len(selected_full)} + incomplete {len(selected_incomplete)} + complete {len(selected_complete)}")
    print(f"Selected complete upstream: {', '.join(selected_complete) or '(none)'}")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS: report written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

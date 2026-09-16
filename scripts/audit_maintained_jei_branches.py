#!/usr/bin/env python3
"""Scan maintained upstream JEI branches for localization drift vs completed project targets."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "completed-versions.json"
API = "https://api.github.com/repos/mezz/JustEnoughItems"
DEBUG_PREFIX = "description.jei."

# Branches that upstream still visibly maintains and that can correspond to a completed target.
BRANCHES = (
    "1.20.1", "1.20.2", "1.20.4", "1.21.1", "1.21.5",
    "1.21.10", "1.21.11", "26.1", "26.2", "fabric-26.3-snapshot-7",
)
LANG_PATHS = (
    "Common/src/main/resources/assets/jei/lang/en_us.json",
    "src/main/resources/assets/jei/lang/en_us.json",
)


def request(url: str) -> bytes:
    headers = {"User-Agent": "JEI-Translation-Expansion-maintained-branch-scan"}
    token = os.getenv("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def text(url: str) -> str:
    return request(url).decode("utf-8")


def api_json(url: str):
    return json.loads(text(url))


def parse_lang(raw: str) -> dict[str, str]:
    obj = json.loads(raw)
    return {str(k): str(v) for k, v in obj.items() if not str(k).startswith("_")}


def parse_props(raw: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def local_source(mc: str) -> Path | None:
    base = ROOT / "upstream" / "sources" / mc
    for name in ("en_us.json", "en_US.json"):
        p = base / name
        if p.is_file():
            return p
    return None


def fetch_upstream_lang(ref: str) -> tuple[str, dict[str, str]] | tuple[None, None]:
    for path in LANG_PATHS:
        url = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{ref}/{path}"
        try:
            return path, parse_lang(text(url))
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
            continue
    return None, None


def main() -> int:
    packaging = json.loads(PACKAGING.read_text(encoding="utf-8"))
    completed = {item["minecraft"]: item for item in packaging["versions"]}
    branch_listing = api_json(f"{API}/branches?per_page=100")
    branch_heads = {item["name"]: item["commit"]["sha"] for item in branch_listing}
    rows = []

    for branch in BRANCHES:
        head = branch_heads.get(branch)
        if not head:
            rows.append({"branch": branch, "status": "missing-upstream-branch"})
            continue
        try:
            props = parse_props(text(f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{head}/gradle.properties"))
        except urllib.error.URLError as exc:
            rows.append({"branch": branch, "head": head, "status": f"gradle-fetch-failed: {exc}"})
            continue
        mc = props.get("minecraftVersion")
        spec = props.get("specificationVersion")
        # RC/snapshot branches are reported but not matched to a completed target.
        cfg = completed.get(mc)
        if cfg is None:
            rows.append({
                "branch": branch, "head": head, "minecraft": mc, "jei": spec,
                "status": "not-a-completed-target",
            })
            continue
        src = local_source(mc)
        if src is None:
            rows.append({
                "branch": branch, "head": head, "minecraft": mc, "jei": spec,
                "status": "missing-local-frozen-source",
            })
            continue
        lang_path, current = fetch_upstream_lang(head)
        if current is None:
            rows.append({
                "branch": branch, "head": head, "minecraft": mc, "jei": spec,
                "status": "upstream-en-us-not-found",
            })
            continue
        frozen = parse_lang(src.read_text(encoding="utf-8"))
        a, b = set(frozen), set(current)
        added = sorted(b - a)
        removed = sorted(a - b)
        changed = sorted(k for k in a & b if frozen[k] != current[k])
        unchanged = sorted(k for k in a & b if frozen[k] == current[k])
        rows.append({
            "branch": branch,
            "head": head,
            "minecraft": mc,
            "canonical_jei": cfg["jei"],
            "maintained_jei": spec,
            "language_path": lang_path,
            "frozen_key_count": len(frozen),
            "maintained_key_count": len(current),
            "unchanged": len(unchanged),
            "added": len(added),
            "removed": len(removed),
            "changed_english": len(changed),
            "added_keys": added,
            "removed_keys": removed,
            "changed_english_keys": changed,
            "needs_localization_refresh": bool(added or changed),
            "status": "audited",
        })

    out = ROOT / "build" / "maintained-jei-branch-scan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("Maintained JEI branch localization scan")
    for row in rows:
        if row.get("status") != "audited":
            print(f"- {row['branch']}: {row.get('minecraft')} / JEI {row.get('jei')} — {row['status']}")
            continue
        flag = "REFRESH" if row["needs_localization_refresh"] else "no localization delta"
        print(
            f"- {row['branch']}: MC {row['minecraft']} JEI {row['canonical_jei']} -> {row['maintained_jei']} | "
            f"keys {row['frozen_key_count']} -> {row['maintained_key_count']} | "
            f"+{row['added']} -{row['removed']} changed={row['changed_english']} | {flag}"
        )
    print(f"Report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

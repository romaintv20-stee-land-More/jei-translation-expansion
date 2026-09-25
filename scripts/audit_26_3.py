#!/usr/bin/env python3
"""Audit a pinned, exact JEI Minecraft 26.3 NeoForge target for G52."""
from __future__ import annotations
import concurrent.futures
import json
import os
import subprocess
import urllib.request
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_SOURCE = ROOT / "upstream/sources/26.2/en_us.json"
BASE_SCOPE = ROOT / "upstream/minecraft-26.2-language-scope.json"
READINESS = ROOT / "upstream/provisional/minecraft-26.3-release-readiness.json"
PIN = "0aed0ce0d09b56923469d1074100f02ed0a45b13"
BRANCH = "26.3"
JEI_VERSION = "31.7.0"
NEOFORGE_VERSION = "26.3.0.7-beta"
NEOFORGE_MIN = "[26.3.0.1-beta,)"
BASE_PIN = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
RAW = f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{PIN}"
LANG_REL = "Common/src/main/resources/assets/jei/lang"
DEBUG_PREFIX = "description.jei."

@lru_cache(maxsize=1)
def local_checkout() -> Path | None:
    supplied = os.environ.get("JEI_26_3_SOURCE_DIR")
    target = Path(supplied) if supplied else Path.home() / "AppData/Local/Temp/jei-upstream-26.3-g52"
    if not target.is_dir():
        return None
    result = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True)
    return target if result.stdout.strip() == PIN else None

def request(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"JEI-Translation-Expansion-G52"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def pinned_bytes(relative: str) -> bytes:
    checkout = local_checkout()
    if checkout and (checkout / relative).is_file():
        return (checkout / relative).read_bytes()
    return request(f"{RAW}/{relative}")

def clean(raw: dict) -> dict[str, str]:
    return {str(k):str(v) for k,v in raw.items() if not str(k).startswith("_")}

def pinned_locale(locale: str) -> dict[str, str]:
    data = json.loads(pinned_bytes(f"{LANG_REL}/{locale}.json").decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{locale}: upstream language root is not an object")
    return clean(data)

def upstream_locale_names() -> set[str]:
    checkout = local_checkout()
    if checkout:
        return {p.stem for p in (checkout / LANG_REL).glob("*.json")}
    api = f"https://api.github.com/repos/mezz/JustEnoughItems/contents/{LANG_REL}?ref={PIN}"
    contents = json.loads(request(api))
    return {Path(x["name"]).stem for x in contents if x.get("type") == "file" and x["name"].endswith(".json")}

def properties() -> dict[str, str]:
    lines = pinned_bytes("gradle.properties").decode("utf-8").splitlines()
    return {a.strip():b.strip() for line in lines if "=" in line and not line.lstrip().startswith("#")
            for a,b in [line.split("=",1)]}

def audit() -> dict:
    base = clean(json.loads(BASE_SOURCE.read_text(encoding="utf-8")))
    target = pinned_locale("en_us")
    props = properties()
    required = {"minecraftVersion":"26.3", "specificationVersion":JEI_VERSION,
                "neoforgeVersion":NEOFORGE_VERSION, "neoforgeVersionRange":NEOFORGE_MIN,
                "neoforgeLoaderVersionRange":"[4,)", "modJavaVersion":"25"}
    for key,expected in required.items():
        if props.get(key) != expected:
            raise ValueError(f"Pinned JEI {key} mismatch: {props.get(key)!r} != {expected!r}")
    if props.get("minecraftVersionRange") != "[26.3]":
        raise ValueError("Pinned JEI does not target Minecraft 26.3 exactly")
    previous = json.loads(BASE_SCOPE.read_text(encoding="utf-8"))
    selected = set(previous["addon_full_locales"]) | set(previous["selected_upstream_incomplete_locales"]) | set(previous["selected_upstream_complete_locales"])
    if len(selected) != 90 or len(base) != 334:
        raise ValueError("G51 selected language set or English source changed")
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    if readiness.get("minecraft",{}).get("version") != "26.3" or readiness["minecraft"]["selected_scope_count"] != 90 or not readiness["minecraft"]["selected_scope_still_present"]:
        raise ValueError("Minecraft 26.3 final language assets have not been verified")
    available = upstream_locale_names()
    wanted = sorted(selected & available)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        mapped = dict(zip(wanted, pool.map(pinned_locale, wanted)))
    normal = {k for k in target if not k.startswith(DEBUG_PREFIX)}
    complete = sorted(l for l in wanted if normal <= mapped[l].keys())
    incomplete = sorted(set(wanted) - set(complete))
    full = sorted(selected - set(wanted))
    unchanged = sorted(k for k in set(base)&set(target) if base[k] == target[k])
    added = sorted(set(target)-set(base))
    removed = sorted(set(base)-set(target))
    changed = sorted(k for k in set(base)&set(target) if base[k] != target[k])
    if (len(target),len(normal),len(target)-len(normal)) != (584,578,6):
        raise ValueError("Unexpected pinned G52 key counts")
    if (len(unchanged),len(added),len(removed),len(changed)) != (193,304,54,87):
        raise ValueError("Unexpected G51 -> G52 key/value delta")
    if (len(full),len(incomplete),len(complete)) != (63,26,1) or complete != ["en_us"]:
        raise ValueError(f"Unexpected G52 ownership: {len(full)}, {len(incomplete)}, {complete}")
    return dict(base=base,target=target,normal=normal,props=props,previous=previous,
                selected=selected,upstream=mapped,upstream_names=available,complete=complete,
                incomplete=incomplete,full=full,unchanged=unchanged,added=added,
                removed=removed,changed=changed,readiness=readiness)

def main() -> int:
    x = audit()
    print("PASS: exact pinned JEI Minecraft 26.3 source and language audit")
    print(f"Source: {PIN}; JEI {JEI_VERSION}; NeoForge {NEOFORGE_VERSION}; Java 25")
    print(f"English: {len(x['base'])} -> {len(x['target'])}; normal={len(x['normal'])}; debug=6")
    print(f"Delta: unchanged={len(x['unchanged'])} added={len(x['added'])} removed={len(x['removed'])} changed={len(x['changed'])}")
    print(f"Selected: {len(x['selected'])}; full={len(x['full'])}; supplements={len(x['incomplete'])}; upstream complete={len(x['complete'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

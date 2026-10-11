#!/usr/bin/env python3
"""Source-only report: compare each pinned JEI generation to its current branch.
DOES NOT build a JAR, change translations, or claim published file compatibility.
"""
from __future__ import annotations
import concurrent.futures as cf
import json
import re
import urllib.error
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/"packaging/completed-versions.json").read_text(encoding="utf-8"))
OUT=ROOT/"upstream/current-branch-audits"
HEADERS={"User-Agent":"JEI-Translation-Expansion-Source-Audit/1.0"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=24) as h:
        return h.read()
def normal(m):
    return {k:v for k,v in m.items() if not k.startswith("_")}
def parse_lang(source):
    out={}
    for l in source.splitlines():
        if not l.strip() or l.lstrip().startswith("#") or "=" not in l:continue
        k,v=l.split("=",1)
        out[k]=v
    return out
def current(branch,version):
    possible=[
        "Common/src/main/resources/assets/jei/lang/en_us.json",
        "src/main/resources/assets/jei/lang/en_us.json",
        "src/main/resources/assets/jei/lang/en_us.lang",
        "src/main/resources/assets/jei/lang/en_US.lang",
        "src/main/resources/assets/jei/lang/en_us.lang",
        "src/main/resources/assets/jei/lang/en_US.lang"
    ]
    for path in possible:
        u=f"https://raw.githubusercontent.com/mezz/JustEnoughItems/{branch}/{path}"
        try:
            content=get(u).decode("utf-8-sig")
            if path.endswith(".json"):
                data=normal(json.loads(content))
                if data and isinstance(data,dict):return data,path
            elif content.strip():
                data=parse_lang(content)
                if data:return data,path
        except (urllib.error.HTTPError,urllib.error.URLError,ValueError,UnicodeDecodeError,TimeoutError):
            continue
    raise RuntimeError("No matching English language source at source branch")
def pinned(mc):
    src=ROOT/"upstream/sources"/mc/"en_us.json"
    if src.exists():
        return normal(json.loads(src.read_text(encoding="utf-8"))),"json"
    lang=ROOT/"upstream/sources"/mc/"en_us.lang"
    if lang.exists():
        return parse_lang(lang.read_text(encoding="utf-8")),"lang"
    return None,None
def check(cfg):
    mc=cfg["minecraft"]
    baseline,fmt=pinned(mc)
    if baseline is None:
        return {"minecraft":mc,"generation":cfg["generation"],"status":"no_pinned_english"}
    try:
        up,path=current(mc,mc)
    except Exception as e:
        return {"minecraft":mc,"generation":cfg["generation"],"status":"not_confirmed","error":str(e)}
    added={k:up[k] for k in sorted(up.keys()-baseline.keys())}
    removed={k:baseline[k] for k in sorted(baseline.keys()-up.keys())}
    changed={k:{"previous":baseline[k],"current":up[k]} for k in sorted(baseline.keys()&up.keys()) if baseline[k]!=up[k]}
    return {
        "minecraft":mc,"generation":cfg["generation"],"status":"compared_branch_head",
        "source":path,"baseline_keys":len(baseline),"current_keys":len(up),
        "added":added,"removed":removed,"changed_english_values":changed,
        "needs_translation_review":bool(added or removed or changed),
        "warning":"Source branch head is not necessarily a published JEI JAR or the endpoint of a maintained branch."
    }
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    versions=CONFIG["versions"]
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for r in pool.map(check,versions):
            path=OUT/(r["minecraft"]+".json")
            path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            print(r["minecraft"],r["status"],"delta",*[len(r.get(k,{})) for k in ("added","removed","changed_english_values")],flush=True)
    files=[json.loads(p.read_text(encoding="utf-8")) for p in OUT.glob("*.json") if p.name!="SUMMARY.json"]
    files.sort(key=lambda r:next((i for i,cfg in enumerate(versions) if cfg["minecraft"]==r["minecraft"]),999))
    summary={
       "generated_utc":datetime.now(timezone.utc).isoformat(),
       "scope":"All 52 pinned Minecraft targets; live GitHub branch-head vs canonical English source (not CurseForge publication)",
       "targets_total":len(versions),"compared":sum(x["status"]=="compared_branch_head" for x in files),
       "changed":sum(x.get("needs_translation_review",False) for x in files),
       "report":[{k:x.get(k) for k in ("minecraft","generation","status","baseline_keys","current_keys","source")}
        | {"added":len(x.get("added",{})),"removed":len(x.get("removed",{})),"changed_values":len(x.get("changed_english_values",{}))}
        for x in files]
    }
    (OUT/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SUMMARY",summary["compared"],"compared,",summary["changed"],"changed",flush=True)
if __name__=="__main__":main()

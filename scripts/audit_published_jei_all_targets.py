#!/usr/bin/env python3
"""Audit *published* JEI JARs per Minecraft target without building any JAR.
Uses verified Modrinth upstream project u6dRKJwZ. Absence is unknown, not unchanged.
"""
from __future__ import annotations
import concurrent.futures as futures,hashlib,json,urllib.parse,urllib.request,zipfile,io
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"packaging/completed-versions.json").read_text(encoding="utf-8"))["versions"]
TMP=Path.home()/"AppData/Local/Temp/jei-published-audit-20261011"
OUT=ROOT/"upstream/published-audits-20261011"
HEADERS={"User-Agent":"JEI-Translation-Expansion-Upstream-Audit/1.2 (research)"}
def fetch(url):
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=42) as response:return response.read()
def load_json(path):return json.loads(path.read_text(encoding="utf-8"))
def clean(d):return {k:v for k,v in d.items() if not k.startswith("_")}
def parse_lang(data):
 items={}
 for line in data.splitlines():
  if not line or line.startswith("#") or "=" not in line:continue
  k,v=line.split("=",1);items[k.strip()]=v.strip()
 return items
def get_newest(cfg):
 mc=cfg["minecraft"]
 loaders=["neoforge"] if cfg.get("loader")=="neoforge" else ["forge","neoforge"]
 for ld in loaders:
  q=urllib.parse.urlencode({"game_versions":json.dumps([mc]),"loaders":json.dumps([ld])})
  data=json.loads(fetch("https://api.modrinth.com/v2/project/u6dRKJwZ/version?"+q))
  if not data:continue
  data.sort(key=lambda v:v["date_published"],reverse=True)
  for v in data:
   files=[x for x in v["files"] if x.get("primary")] or v["files"]
   for f in files:
    if str(f.get("filename","")).endswith(".jar") and mc in v.get("game_versions",[]):
     return v, f,ld
 return None
def audit(cfg):
 mc=cfg["minecraft"]
 out={"minecraft":mc,"generation":cfg["generation"],"previous_jei":cfg["jei"],"status":"unknown"}
 try:
  item=get_newest(cfg)
  if not item:
   out["status"]="no_modrinth_release_matched";return out
  ver,file,loader=item
  out.update(published_jei=ver["version_number"],published_date=ver["date_published"],published_loader=loader,
             version_id=ver["id"],download_url=file["url"],upstream_sha512=file.get("hashes",{}).get("sha512"))
  p=TMP/(mc+"-"+file["filename"])
  if not p.exists():p.write_bytes(fetch(file["url"]))
  out["jar_sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
  with zipfile.ZipFile(p) as z:
   names=z.namelist()
   en=[n for n in names if n.lower().startswith("assets/jei/lang/") and
       n.lower().endswith(("/en_us.json","/en_us.lang"))]
   if not en:
    out["status"]="no_en_us_in_published_jar";return out
   en.sort(key=lambda n:(not n.endswith(".json"),len(n)))
   raw=z.read(en[0]).decode("utf-8-sig")
   lang=clean(json.loads(raw)) if en[0].endswith(".json") else parse_lang(raw)
   out["english_path"]=en[0]
  prev=ROOT/"upstream/sources"/mc/"en_us.json"
  if prev.is_file():
   base=clean(load_json(prev))
  else:
   possibilities=[
    ROOT/"upstream/sources"/mc/"en_us.lang",
    ROOT/"upstream/sources"/mc/"en_US.lang",
   ]
   previous=next((p for p in possibilities if p.is_file()),None)
   if previous is None:
    out["status"]="no_pinned_source";return out
   base=parse_lang(previous.read_text(encoding="utf-8-sig"))
  added={k:lang[k] for k in sorted(lang.keys()-base.keys())}
  removed={k:base[k] for k in sorted(base.keys()-lang.keys())}
  changed={k:{"from":base[k],"to":lang[k]} for k in sorted(base.keys()&lang.keys()) if base[k]!=lang[k]}
  out.update(status="verified_published_jar",previous_keys=len(base),current_keys=len(lang),
             added=added,removed=removed,changed_english_values=changed,
             needs_update=bool(added or removed or changed))
 except Exception as exc:
  out.update(status="error",error=repr(exc))
 return out
def main():
 TMP.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 with futures.ThreadPoolExecutor(max_workers=6) as pool:
  for r in pool.map(audit,CFG):
   (OUT/(r["minecraft"]+".json")).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
   print(r["minecraft"],r["status"],r.get("published_jei","--"),*[len(r.get(k,{})) for k in ("added","removed","changed_english_values")],flush=True)
 results=[json.loads((OUT/(cfg["minecraft"]+".json")).read_text(encoding="utf-8")) for cfg in CFG]
 summary={"generated":datetime.now(timezone.utc).isoformat(),"project":"JEI","target_count":len(CFG),
   "published_verified":sum(r["status"]=="verified_published_jar" for r in results),
   "translations_changed":sum(r.get("needs_update",False) for r in results),
   "unverified":sum(r["status"]!="verified_published_jar" for r in results),
   "versions":[{k:r.get(k) for k in ("minecraft","generation","status","previous_jei","published_jei","previous_keys","current_keys","published_date")}
    |{"added":len(r.get("added",{})),"removed":len(r.get("removed",{})),"changed":len(r.get("changed_english_values",{}))}
    for r in results]}
 (OUT/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("FINAL",summary["published_verified"],"verified,",summary["translations_changed"],"changed",flush=True)
if __name__=="__main__":main()

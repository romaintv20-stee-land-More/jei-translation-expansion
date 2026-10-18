#!/usr/bin/env python3
"""Stage changed LEGACY .lang generations; source-only, never generates JARs."""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import json,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from reconstruct_26_2 import preserves_runtime_literals as safe
AUDITS=ROOT/"upstream/published-audits-20261011"
TMP=Path.home()/"AppData/Local/Temp/jei-published-audit-20261011"
OUT=ROOT/"translations/staged-published-2026-10-11"
CONFIG=json.loads((ROOT/"packaging/completed-versions.json").read_text(encoding="utf-8"))["versions"]
def load_lang(data):
 records={}
 for line in data.decode("utf-8-sig").splitlines():
  s=line.strip()
  if not s or s.startswith("#") or "=" not in s:continue
  key,val=line.split("=",1)
  records[key.strip()]=val
 return records
def save_lang(path,m):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text("# Generated staged fallback; awaiting runtime validation.\n"
  + "".join(k+"="+v+"\n" for k,v in sorted(m.items())),encoding="utf-8")
def save_json(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def lang_members(z):
 return {Path(n).stem.lower():n for n in z.namelist()
         if n.startswith("assets/jei/lang/") and n.lower().endswith(".lang")}
def main():
 results=[]
 for cfg in CONFIG:
  if cfg["format"]!="lang":continue
  mc=cfg["minecraft"]; report=json.loads((AUDITS/(mc+".json")).read_text(encoding="utf-8"))
  if report["status"]!="verified_published_jar" or not report.get("needs_update"):continue
  files=list((ROOT/"candidate-jars"/mc).glob("*.jar"))
  assert len(files)==1,mc
  published=TMP/(mc+"-"+report["download_url"].rsplit("/",1)[-1])
  assert published.is_file(),mc
  oldfile=ROOT/"upstream/sources"/mc/"en_us.lang"
  if not oldfile.is_file():oldfile=ROOT/"upstream/sources"/mc/"en_US.lang"
  assert oldfile.is_file(),mc
  baseline=load_lang(oldfile.read_bytes())
  with zipfile.ZipFile(files[0]) as candidate,zipfile.ZipFile(published) as official:
   cand=lang_members(candidate); orig=lang_members(official)
   official_en=next((n for c,n in orig.items() if c in ("en_us","en_us")),None)
   assert official_en
   en=load_lang(official.read(official_en))
   assert len(en)==report["current_keys"],(mc,len(en),report["current_keys"])
   unchanged={k for k in baseline.keys()&en.keys() if baseline[k]==en[k]}
   dest=OUT/mc
   save_lang(dest/"source/en_us.lang",en)
   stats=Counter(); locales={}
   for code,path in sorted(cand.items()):
    old=load_lang(candidate.read(path))
    curr=load_lang(official.read(orig[code])) if code in orig else {}
    if code=="en_us":continue
    official_keys={k for k,v in curr.items() if k in en and safe(en[k],v)}
    proposed={}
    count=Counter()
    for key,value in sorted(en.items()):
     if key in official_keys:
      count["upstream_owned"]+=1
     elif key in unchanged and key in old and safe(value,old[key]):
      proposed[key]=old[key];count["reused"]+=1
     else:
      proposed[key]=value;count["english_fallback"]+=1
      if key not in baseline:count["added_english_fallback"]+=1
      elif baseline[key]!=value:count["changed_english_fallback"]+=1
    assert len(proposed)+len(official_keys)==len(en),(mc,code)
    assert all(safe(en[k],v) for k,v in proposed.items()),(mc,code)
    target_name=Path(path).name
    if proposed:
     save_lang(dest/("supplements" if official_keys else "full")/"assets/jei/lang"/target_name,proposed)
    count["ownership"]="upstream-complete" if not proposed else ("supplement" if official_keys else "full")
    locales[code]=dict(count)
    stats.update({k:v for k,v in count.items() if isinstance(v,int)})
   save_json(dest/"semantic-diff.json",{
     "minecraft":mc,"old_jei":cfg["jei"],"current_jei":report["published_jei"],
     "added":report["added"],"removed":report["removed"],
     "changed_english_values":report["changed_english_values"],
     "upstream_jar_sha256":report["jar_sha256"],"source_only":True,
     "policy":"Only exact same English text is reused. Official keys never overridden. English fallback for changed/new keys.",
     "locale_counts":locales,"totals":dict(stats)})
   results.append({"minecraft":mc,"updated":report["published_jei"],"locales":len(locales),
      "added":len(report["added"]),"removed":len(report["removed"]),"changed":len(report["changed_english_values"])})
   print("LEGACY STAGED",mc,"locales",len(locales),"added",len(report["added"]),"changed",len(report["changed_english_values"]),flush=True)
 (OUT/"legacy-SUMMARY.json").write_text(json.dumps({"no_jars":True,"versions":results},indent=2)+"\n",encoding="utf-8")
 print("LEGACY COMPLETE",len(results),"generations; no JAR",flush=True)
if __name__=="__main__":main()

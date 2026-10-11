#!/usr/bin/env python3
"""Stage translated sources across changed verified official JEI JARs.
No JAR compilation or packaging. Upstream-owned keys are always excluded.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from reconstruct_26_2 import preserves_runtime_literals as safe
PUBLISHED=ROOT/"upstream/published-audits-20261011"
CACHE=Path.home()/"AppData/Local/Temp/jei-published-audit-20261011"
OUTPUT=ROOT/"translations/staged-published-2026-10-11"
CONFIG=json.loads((ROOT/"packaging/completed-versions.json").read_text(encoding="utf-8"))["versions"]
def save(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
def clean(data):
 return {k:v for k,v in data.items() if not k.startswith("_")}
def jlocale(z,locale):
 name=f"assets/jei/lang/{locale}.json"
 return clean(json.loads(z.read(name))) if name in z.namelist() else {}
def main():
 records=[]
 for cfg in CONFIG:
  mc=cfg["minecraft"]
  audit=json.loads((PUBLISHED/(mc+".json")).read_text(encoding="utf-8"))
  if audit.get("status")!="verified_published_jar" or not audit.get("needs_update"):
   continue
  upstream_jar=CACHE/(mc+"-"+audit["download_url"].rsplit("/",1)[-1])
  assert upstream_jar.is_file(),(mc,upstream_jar)
  old_jar=list((ROOT/"candidate-jars"/mc).glob("*.jar"))
  assert len(old_jar)==1,(mc,old_jar)
  baseline=ROOT/"upstream/sources"/mc/"en_us.json"
  prev=clean(json.loads(baseline.read_text(encoding="utf-8")))
  stats=Counter()
  locales={}
  with zipfile.ZipFile(upstream_jar) as official,zipfile.ZipFile(old_jar[0]) as candidate:
   current=jlocale(official,"en_us")
   assert current and len(current)==audit["current_keys"],mc
   assert len(prev)==audit["previous_keys"],mc
   assert len(set(current)-set(prev))==len(audit["added"]),mc
   assert len(set(prev)-set(current))==len(audit["removed"]),mc
   unchanged={k for k in set(prev)&set(current) if prev[k]==current[k]}
   output=OUTPUT/mc
   save(output/"source/en_us.json",current)
   previous_names={Path(x).stem for x in candidate.namelist() if x.startswith("assets/jei/lang/") and x.endswith(".json")}
   official_names={Path(x).stem for x in official.namelist() if x.startswith("assets/jei/lang/") and x.endswith(".json")}
   # Include upstream-owned locales ONLY if previously selected, and preserve optional main English.
   selected=(previous_names|{"en_us"})-{"en_us"}
   for loc in sorted(selected):
    old=jlocale(candidate,loc)
    upstream=jlocale(official,loc)
    safe_upstream={k for k,v in upstream.items() if k in current and safe(current[k],v)}
    entries={}
    local=Counter()
    for key,english in sorted(current.items()):
     if key in safe_upstream:
      local["upstream_owned"]+=1
      continue
     if key in unchanged and key in old and safe(english,old[key]):
      entries[key]=old[key]
      local["reused_unchanged"]+=1
     else:
      entries[key]=english
      local["english_fallback"]+=1
      if key not in prev:local["new_key_english_fallback"]+=1
      elif prev[key]!=english:local["changed_meaning_english_fallback"]+=1
    assert len(entries)+len(safe_upstream)==len(current),(mc,loc)
    assert set(entries).isdisjoint(safe_upstream),(mc,loc)
    assert all(safe(current[k],v) for k,v in entries.items()),(mc,loc)
    if entries:
     dest=output/("supplements" if safe_upstream else "full")/"assets/jei/lang"/(loc+".json")
     save(dest,entries)
    local["ownership"]="upstream-complete" if not entries else ("supplement" if safe_upstream else "full")
    locales[loc]=dict(local)
    stats.update({k:v for k,v in local.items() if isinstance(v,int)})
   save(output/"semantic-diff.json",{
     "minecraft":mc,"generation":cfg["generation"],
     "old_jei":cfg["jei"],"new_jei":audit["published_jei"],
     "added":audit["added"],"removed":audit["removed"],
     "changed_english_values":audit["changed_english_values"],
     "upstream_jar_sha256":audit["jar_sha256"],
     "policy":"Reuse only unchanged key+English meaning; upstream translations first; otherwise exact new English fallback pending review.",
     "note":"Staged sources ONLY. No JAR created, no runtime-tested claim. Old supplement-only translated keys absent from candidate files are not inferred.",
     "locale_counts":locales,"totals":dict(stats)
   })
  records.append({
   "minecraft":mc,"old_jei":cfg["jei"],"current_jei":audit["published_jei"],
   "selected_locales":len(locales),"added":len(audit["added"]),"removed":len(audit["removed"]),
   "changed":len(audit["changed_english_values"]),"current_keys":audit["current_keys"],
   "upstream_only_locale_count":len(official_names-previous_names),
   "fallback_total":stats["english_fallback"]
  })
  print("STAGED",mc,"locales",len(locales),"new",len(audit["added"]),
        "removed",len(audit["removed"]),"changed",len(audit["changed_english_values"]),flush=True)
 save(OUTPUT/"SUMMARY.json",{"sources_only":True,"never_build_jar":True,"generation_count":len(records),"versions":records})
 print("ALL STAGED",len(records),"versions, NO JAR",flush=True)
if __name__=="__main__":main()

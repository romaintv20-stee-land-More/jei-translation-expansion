#!/usr/bin/env python3
"""Stage (never package) JEI 26.3 translations for latest published upstream.
Preserves translations ONLY when same key and identical English meaning.
Requires a locally downloaded authentic official JEI JAR; no output JAR created.
"""
from __future__ import annotations
import argparse,json,zipfile,sys,hashlib,urllib.request
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from reconstruct_26_2 import preserves_runtime_literals
def pinned_locale(locale):
    url=("https://raw.githubusercontent.com/mezz/JustEnoughItems/"
         "0aed0ce0d09b56923469d1074100f02ed0a45b13/"
         "Common/src/main/resources/assets/jei/lang/"+locale+".json")
    req=urllib.request.Request(url,headers={"User-Agent":"JEI-Translation-G53"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        return norm(json.loads(resp.read()))

PINNED=ROOT/"upstream/sources/26.3/en_us.json"
SCOPE=ROOT/"upstream/minecraft-26.3-language-scope.json"
DONOR=ROOT/"candidate-jars/26.3/jei-translation-expansion-1.0.0-mc26.3-neoforge.jar"
OUT=ROOT/"translations/g53-mc26.3-31.10.0.63"
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def norm(d):return {k:v for k,v in d.items() if not k.startswith("_")}
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def jar_locale(z,locale):
 path=f"assets/jei/lang/{locale}.json"
 return norm(json.loads(z.read(path))) if path in z.namelist() else {}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--official-jar",type=Path,required=True)
 ap.add_argument("--output",type=Path,default=OUT)
 args=ap.parse_args()
 assert args.official_jar.is_file()
 pinned=norm(load(PINNED))
 scope=load(SCOPE)
 full=set(scope["addon_full_locales"])
 supp=set(scope["selected_upstream_incomplete_locales"])
 complete=set(scope["selected_upstream_complete_locales"])
 assert complete=={"en_us"} and len(full)==63 and len(supp)==26
 assert len(full|supp|complete)==90
 report={"target":"Minecraft 26.3","jei_version":"31.10.0.63","source_jar_sha256":hashlib.sha256(args.official_jar.read_bytes()).hexdigest(),
         "policy":"Same key and identical source English value only; upstream official translation first; English fallback on unsafe/unknown translation; no cross-key reuse",
         "files":{},"locales":{},"status":"source-only proposal; NOT a tested release"}
 with zipfile.ZipFile(args.official_jar) as latest,zipfile.ZipFile(DONOR) as donor:
  current=jar_locale(latest,"en_us")
  assert len(current)>600 and len(pinned)==584,(len(current),len(pinned))
  newset=set(current)-set(pinned);remove=set(pinned)-set(current)
  modified={k for k in set(pinned)&set(current) if pinned[k]!=current[k]}
  unchanged={k for k in set(pinned)&set(current) if pinned[k]==current[k]}
  report.update(keys_old=len(pinned),keys_new=len(current),
                keys_added=len(newset),keys_removed=len(remove),english_values_changed=len(modified),
                added_keys={k:current[k] for k in sorted(newset)},
                removed_keys={k:pinned[k] for k in sorted(remove)},
                changed_values={k:{"old":pinned[k],"new":current[k]} for k in sorted(modified)})
  sourcepath=args.output/"upstream/en_us.json"
  save(sourcepath,current)
  totals=Counter()
  for locale in sorted(full|supp):
   old_addon=jar_locale(donor,locale)
   old_official=pinned_locale(locale) if locale in supp else {}
   old_combined=dict(old_official)
   old_combined.update(old_addon)
   official=jar_locale(latest,locale)
   official_keys={k for k in official if k in current and preserves_runtime_literals(current[k],official[k])}
   new_values={}
   counts=Counter()
   for k in sorted(current):
    if k in official_keys:
     counts["upstream_owned"]+=1
     continue
    if k in unchanged and k in old_combined and preserves_runtime_literals(current[k],old_combined[k]):
     new_values[k]=old_combined[k]
     counts["safe_reused"]+=1
    else:
     new_values[k]=current[k]
     counts["english_fallback"]+=1
     if k in newset: counts["fallback_new_key"]+=1
     if k in modified: counts["fallback_modified_english"]+=1
   if locale in full:
    # If official acquired a locale, emit only missing keys and record ownership migration.
    if not official_keys:
     assert len(new_values)==len(current)
     target=args.output/"full/assets/jei/lang"/(locale+".json")
     counts["ownership"]="full"
    else:
     target=args.output/"supplements/assets/jei/lang"/(locale+".json")
     counts["ownership"]="upstream-partial"
   else:
    assert official_keys
    target=args.output/"supplements/assets/jei/lang"/(locale+".json")
    counts["ownership"]="supplement"
   assert new_values and set(new_values).isdisjoint(official_keys)
   assert all(preserves_runtime_literals(current[k],v) for k,v in new_values.items()),locale
   save(target,new_values)
   report["locales"][locale]=dict(counts)
   report["files"][locale]=str(target.relative_to(ROOT)).replace("\\","/")
   totals.update({k:v for k,v in counts.items() if isinstance(v,int)})
  report["totals"]=dict(totals)
  assert set(report["locales"])==full|supp
  save(args.output/"audit.json",report)
  print("STAGED",len(report["locales"]),"locales, English",len(pinned),"->",len(current),
        "added",len(newset),"removed",len(remove),"changed values",len(modified))
  print("Coverage ownership counts",Counter(q["ownership"] for q in report["locales"].values()))
  print("Fallbacks from new keys",totals["fallback_new_key"],"changed meanings",totals["fallback_modified_english"])
  print("No JAR created. Human translation and in-game validation still required.")
if __name__=="__main__":main()

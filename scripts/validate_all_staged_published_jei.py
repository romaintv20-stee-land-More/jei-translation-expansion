#!/usr/bin/env python3
"""Verify all newly staged published-JEI locales without building any JAR."""
from __future__ import annotations
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
STAGED=ROOT/"translations/staged-published-2026-10-11"
AUDITS=ROOT/"upstream/published-audits-20261011"
PLACEHOLDER=re.compile(r"%(?:\d+\$)?[sdf]")
def parse_lang(path):
 values={}
 for line in path.read_text(encoding="utf-8-sig").splitlines():
  if line.startswith("#") or not line.strip():continue
  assert "=" in line,(path,line)
  k,v=line.split("=",1)
  assert k not in values,(path,k)
  values[k]=v
 return values
def read(path):
 return parse_lang(path) if path.suffix==".lang" else {
  k:v for k,v in json.loads(path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
def main():
 versions=[]; files_count=0
 for path in sorted(STAGED.iterdir()):
  if not path.is_dir() or not (path/"semantic-diff.json").exists():continue
  mc=path.name
  report=json.loads((path/"semantic-diff.json").read_text(encoding="utf-8"))
  upstream=json.loads((AUDITS/(mc+".json")).read_text(encoding="utf-8"))
  assert report["minecraft"]==mc
  english=list((path/"source").glob("en_us.*"))
  assert len(english)==1,(mc,english)
  source=read(english[0])
  assert len(source)==upstream["current_keys"],(mc,len(source),upstream["current_keys"])
  assert len(report["added"])==len(upstream["added"])
  assert len(report["removed"])==len(upstream["removed"])
  assert len(report["changed_english_values"])==len(upstream["changed_english_values"])
  fs=list(path.glob("*/assets/jei/lang/*"))
  locales=set()
  for p in fs:
   assert p.suffix in (".json",".lang")
   locale=p.stem.lower()
   assert locale not in locales,(mc,locale)
   locales.add(locale)
   content=read(p)
   assert content
   assert not set(content)-set(source),(mc,locale,set(content)-set(source))
   expected_upstream=int(report["locale_counts"][locale].get("upstream_owned",0))
   assert len(content)+expected_upstream==len(source),(mc,locale,len(content),expected_upstream,len(source))
   for k,v in content.items():
    assert isinstance(v,str) and v.strip(),(mc,locale,k)
    assert sorted(PLACEHOLDER.findall(v))==sorted(PLACEHOLDER.findall(source[k])),(mc,locale,k)
   files_count+=1
  expected_files=sum(1 for loc,v in report["locale_counts"].items() if v["ownership"]!="upstream-complete")
  assert len(fs)==expected_files,(mc,len(fs),expected_files)
  versions.append(mc)
  print("PASS",mc,"files",len(fs),"keys",len(source),flush=True)
 assert len(versions)==20,(len(versions),versions)
 print("ALL STATIC SOURCE AUDITS PASS",len(versions),"versions,",files_count,"translation files. No JAR built.")
if __name__=="__main__":main()

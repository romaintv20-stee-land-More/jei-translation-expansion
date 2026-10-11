#!/usr/bin/env python3
"""Prepare, verify and (optionally) write JEI 1.8.8 source translations.

Sources:
- Official JEI 2.12.0.49 English (56 keys), audited SHA-256
- Previously approved JEI 1.8 English (58 keys) and 54 language files

Only exact English key+text matches are reused. New or modified English
meanings are deliberately left as review-required English fallbacks.
Original JEI 1.8.8 locales are *never* copied or overridden.

This generates .lang TEXT only. No ZIP/JAR/class is ever made.
"""
from __future__ import annotations
import argparse
import json
import re
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"translations/g1-mc1.8"
OLD=ROOT/"upstream/sources/1.8/en_US.lang"
CURRENT=ROOT/"upstream/sources/1.8.8/en_us.lang"
UPSTREAM=ROOT/"upstream/sources/1.8.8/provenance.json"
DEST=ROOT/"translations/staged-mc1.8.8"
PLACEHOLDERS=re.compile(r"%(?:MODNAME|(?:\d+\$)?[,]?[a-zA-Z])")


def parse(path):
    values={}
    for index,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{index}: no equals separator")
        key,value=line.split("=",1)
        key=key.strip()
        if key in values:
            raise ValueError(f"{path}:{index}: duplicate key {key}")
        values[key]=value
    return values


def generate(dest):
    older=parse(OLD)
    newest=parse(CURRENT)
    provenance=json.loads(UPSTREAM.read_text(encoding="utf-8"))
    assert len(older)==58 and len(newest)==provenance["source_keys"]==56
    assert len(provenance["upstream_languages"])==6
    files=sorted(BASE.glob("*.lang"))
    assert len(files)==54,len(files)
    assert not any(f.stem.lower() in provenance["upstream_languages"] for f in files)
    unchanged={k for k in older.keys() & newest.keys() if older[k]==newest[k]}
    needs_translation=set(newest)-unchanged
    stats={}
    for source in files:
        oldlocale=parse(source)
        assert set(oldlocale)==set(older),(source,len(oldlocale))
        newlocale={}
        reused=0
        for key,new_en in sorted(newest.items()):
            if key in unchanged and oldlocale.get(key):
                val=oldlocale[key]
                reused+=1
            else:
                val=new_en
            assert val
            assert sorted(PLACEHOLDERS.findall(val))==sorted(PLACEHOLDERS.findall(new_en)),(source,key)
            assert "\n" not in val and "\r" not in val
            newlocale[key]=val
        file=dest/"assets/jei/lang"/source.name
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(
            "# JEI 1.8.8 / 2.12.0.49 -- SOURCE-ONLY DRAFT, human review pending\n"
            "# Reused only byte-identical English meanings from approved JEI 1.8 locales.\n"
            "# Other keys retain official English until safely translated.\n"
            + "".join(k+"="+v+"\n" for k,v in sorted(newlocale.items())),
            encoding="utf-8"
        )
        assert parse(file)==newlocale
        stats[source.stem]={
            "unchanged_english_key_reuse":reused,
            "needs_translation_english_fallback":len(newest)-reused,
        }
    manifest={
        "minecraft":"1.8.8","upstream_jei":"2.12.0.49",
        "status":"source_only_unreviewed_not_packaged",
        "addon_locale_count":len(files),
        "full_english_key_count":len(newest),
        "reusable_semantically_unchanged_source_keys":len(unchanged),
        "source_keys_requiring_new_translation":len(needs_translation),
        "changed_or_new_english_keys":sorted(needs_translation),
        "official_upstream_languages":provenance["upstream_languages"],
        "policy":"No source-meaning changed translation reuse; original upstream locale keys remain first priority.",
        "locale_stats":stats,
        "no_jar_generated":True,
    }
    (dest/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true",help="write .lang drafts into translations/staged-mc1.8.8")
    parser.add_argument("--check",action="store_true",help="assert that committed stage files are identical")
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="jei188-text-stage-") as folder:
        draft=Path(folder)
        report=generate(draft)
        if args.write:
            import shutil
            for f in sorted(draft.rglob("*")):
                if f.is_file():
                    target=DEST/f.relative_to(draft)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(f,target)
        if args.check:
            assert DEST.is_dir(),"1.8.8 translation texts have not been staged yet"
            expected={p.relative_to(draft) for p in draft.rglob("*") if p.is_file()}
            committed={p.relative_to(DEST) for p in DEST.rglob("*") if p.is_file()}
            assert expected==committed,(len(expected),len(committed))
            for rel in expected:
                assert (draft/rel).read_bytes()==(DEST/rel).read_bytes(),rel
        print("JEI 1.8.8 text stage PASS:",report["addon_locale_count"],
              "languages,",report["full_english_key_count"],"keys,",
              report["source_keys_requiring_new_translation"],
              "source meanings needing fresh translations; no JAR made")


if __name__=="__main__":
    main()

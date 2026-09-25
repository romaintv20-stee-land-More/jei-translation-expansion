#!/usr/bin/env python3
"""Deterministically reconstruct G52 using exact-semantic G51 donors and pinned JEI 26.3."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import audit_26_3 as audit
import reconstruct_26_2 as g51

ROOT = audit.ROOT
BASE = audit.BASE_SOURCE
TARGET = ROOT / "upstream/sources/26.3/en_us.json"
SCOPE = ROOT / "upstream/minecraft-26.3-language-scope.json"
DIFF = ROOT / "upstream/diffs/26.2-to-26.3.json"
POLICY = ROOT / "translations/g52-mc26.3/policy.json"
DEFAULT_OUTPUT = ROOT / "build/reconstructed/26.3"
G51_JAR = ROOT / "candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar"
G51_JAR_SHA256 = "b3d3a30c23b4a9c3080ed49781fa51df17c024fdf67bdde6c2d467649230824f"
DEBUG_PREFIX = audit.DEBUG_PREFIX
write_json = g51.write_json
preserves_runtime_literals = g51.preserves_runtime_literals

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def verify_semantics() -> tuple[dict[str,str],dict[str,str]]:
    base = audit.clean(load(BASE))
    target = audit.clean(load(TARGET))
    unchanged = {k for k in set(base)&set(target) if base[k] == target[k]}
    changed = {k for k in set(base)&set(target) if base[k] != target[k]}
    diff = load(DIFF)
    policy = load(POLICY)
    if (len(base),len(target),len(unchanged),len(changed)) != (334,584,193,87):
        raise ValueError("G52 English source semantic counts changed")
    if set(diff["unchanged_keys"]) != unchanged or set(diff["added_keys"]) != set(target)-set(base):
        raise ValueError("Frozen G52 semantic diff does not match source")
    if set(diff["removed_keys"]) != set(base)-set(target) or set(diff["changed_english_values"]) != changed:
        raise ValueError("Frozen G52 removals/changed meanings are stale")
    if not policy["translation_reuse"]["reuse_only_exact_same_key_same_english"] or policy["translation_reuse"]["cross_key_reuse_allowed"] is not False:
        raise ValueError("G52 semantic reuse policy is unsafe")
    return base,target

def candidate_sha256() -> str:
    return hashlib.sha256(G51_JAR.read_bytes()).hexdigest()

def previous_combined(zf: zipfile.ZipFile, previous_scope: dict, locale: str,
                      pinned_previous_upstream: dict[str,dict[str,str]]) -> dict[str,str]:
    p = f"assets/jei/lang/{locale}.json"
    if locale in set(previous_scope["addon_full_locales"]):
        return json.loads(zf.read(p))
    if locale in set(previous_scope["selected_upstream_incomplete_locales"]):
        combined = dict(pinned_previous_upstream[locale])
        combined.update(json.loads(zf.read(p)))
        return combined
    if locale in set(previous_scope["selected_upstream_complete_locales"]):
        if locale == "en_us":
            return audit.clean(load(BASE))
        return dict(pinned_previous_upstream[locale])
    raise ValueError(f"{locale}: outside selected G51 scope")

def reconstruct_all(output: Path, clean: bool=True) -> tuple[int,int,int,dict]:
    base,target=verify_semantics()
    scope=load(SCOPE)
    previous_scope=load(audit.BASE_SCOPE)
    if scope["upstream_commit"] != audit.PIN or scope["jei_version"] != audit.JEI_VERSION:
        raise ValueError("G52 frozen source metadata mismatch")
    full=set(scope["addon_full_locales"])
    supp=set(scope["selected_upstream_incomplete_locales"])
    complete=set(scope["selected_upstream_complete_locales"])
    fallback=set(scope["documented_full_english_fallback_locales"])
    if (len(full),len(supp),complete,len(fallback)) != (63,26,{"en_us"},30):
        raise ValueError("G52 full/supplement/complete language ownership changed")
    if full&supp or full&complete or supp&complete or len(full|supp|complete)!=90:
        raise ValueError("G52 language sets are not disjoint")
    if candidate_sha256()!=G51_JAR_SHA256:
        raise ValueError("Pinned G51 donor JAR SHA-256 mismatch")
    normal={k for k in target if not k.startswith(DEBUG_PREFIX)}
    if len(normal)!=578:
        raise ValueError("G52 normal key count changed")
    unchanged={k for k in set(base)&set(target) if base[k]==target[k]}
    all_old=sorted(supp | (complete-{"en_us"}))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        old_upstream=dict(zip(all_old,pool.map(g51.fetch_g51_upstream,all_old)))
        upstream=dict(zip(sorted(supp|complete),pool.map(audit.pinned_locale,sorted(supp|complete))))
    for key in normal:
        if upstream["en_us"][key] != target[key]:
            raise ValueError(f"Upstream English no longer agrees with frozen target: {key}")
    overrides={k:set(v) for k,v in scope["upstream_literal_safety_overrides"].items()}
    result_full={};result_supp={};stats_full={};stats_supp={}
    totals={"exact_g51_semantic":0,"target_english_fallback":0,
            "missing_new_or_changed_english":0,"upstream_safety_overrides":0,
            "upstream_owned_safe":0}
    def donor_or_english(previous:dict[str,str],key:str) -> tuple[str,bool]:
        if key in unchanged and key in previous:
            value=previous[key]
            if preserves_runtime_literals(target[key],value):
                return value,True
        return target[key],False
    with zipfile.ZipFile(G51_JAR) as zf:
        for locale in sorted(full):
            previous=previous_combined(zf,previous_scope,locale,old_upstream)
            values={}
            reused=0; english=0; new_changed=0
            for key in target:
                value,was_reused=donor_or_english(previous,key)
                values[key]=value
                reused+=int(was_reused)
                english+=int(not was_reused)
                new_changed+=int(key not in unchanged and not was_reused)
            if locale in fallback and values!=target:
                raise ValueError(f"{locale}: documented English fallback changed")
            result_full[locale]=values
            stats_full[locale]={"exact_g51_semantic":reused,"target_english_fallback":english,
                                "new_or_changed_english":new_changed}
            totals["exact_g51_semantic"]+=reused
            totals["target_english_fallback"]+=english
            totals["missing_new_or_changed_english"]+=new_changed
        for locale in sorted(supp):
            previous=previous_combined(zf,previous_scope,locale,old_upstream)
            current=upstream[locale]
            missing=normal-set(current)
            unsafe={k for k in normal&set(current)
                    if not preserves_runtime_literals(target[k],current[k])}
            if unsafe != overrides.get(locale,set()):
                raise ValueError(f"{locale}: frozen upstream safety overrides changed")
            emitted={}
            reused=0; english=0; new_changed=0
            for key in sorted(missing|unsafe):
                value,was_reused=donor_or_english(previous,key)
                emitted[key]=value
                reused+=int(was_reused)
                english+=int(not was_reused)
                new_changed+=int(key not in unchanged and not was_reused)
            if not emitted or set(emitted)&set(current)!=unsafe or not set(emitted)<=normal:
                raise ValueError(f"{locale}: invalid supplement ownership")
            combined=dict(current);combined.update(emitted)
            for key in normal:
                if key not in combined or not preserves_runtime_literals(target[key],combined[key]):
                    raise ValueError(f"{locale}: missing or unsafe combined translation {key}")
            result_supp[locale]=emitted
            stats_supp[locale]={"exact_g51_semantic":reused,"target_english_fallback":english,
                                "new_or_changed_english":new_changed,
                                "upstream_owned_safe":len(normal&set(current))-len(unsafe),
                                "upstream_safety_overrides":len(unsafe)}
            totals["exact_g51_semantic"]+=reused
            totals["target_english_fallback"]+=english
            totals["missing_new_or_changed_english"]+=new_changed
            totals["upstream_safety_overrides"]+=len(unsafe)
            totals["upstream_owned_safe"]+=len(normal&set(current))-len(unsafe)
    if totals["upstream_safety_overrides"]!=scope["upstream_literal_safety_override_count"]:
        raise ValueError("G52 safety override count changed")
    if clean and output.exists():
        shutil.rmtree(output)
    fdir=output/"full/assets/jei/lang"
    sdir=output/"supplements/assets/jei/lang"
    fdir.mkdir(parents=True,exist_ok=True)
    sdir.mkdir(parents=True,exist_ok=True)
    for locale,values in sorted(result_full.items()):
        write_json(fdir/f"{locale}.json",values)
    for locale,values in sorted(result_supp.items()):
        write_json(sdir/f"{locale}.json",values)
    provenance={
        "schema_version":1,"generation":"g52-mc26.3",
        "upstream_commit":audit.PIN,"g51_donor_jar_sha256":G51_JAR_SHA256,
        "cross_key_reuse_allowed":False,
        "translation_quality":"new or changed English meanings use explicit English fallback unless translated upstream",
        "full_locales":stats_full,"supplement_locales":stats_supp,"totals":totals,
    }
    write_json(output/"provenance.json",provenance)
    return len(result_full),len(result_supp),len(target),provenance

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument("--no-clean",action="store_true")
    args=parser.parse_args()
    full,supp,keys,provenance=reconstruct_all(args.output,not args.no_clean)
    print(f"PASS: G52 deterministic reconstruction: {full} full + {supp} supplements; {keys} keys")
    print("Donor exact same-key+English reuses:",provenance["totals"]["exact_g51_semantic"])
    print("Explicit English fallback values:",provenance["totals"]["target_english_fallback"])
    print("Upstream safety overrides:",provenance["totals"]["upstream_safety_overrides"])
    print("Runtime resource-stack merge validation remains separate")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

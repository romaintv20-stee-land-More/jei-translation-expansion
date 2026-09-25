#!/usr/bin/env python3
"""Validate frozen G52 delta, language coverage and deterministic reconstruction."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
import audit_26_3 as audit
import reconstruct_26_3 as g52

def load(p:Path)->dict:
    return json.loads(p.read_text(encoding="utf-8"))

def main()->int:
    base,target=g52.verify_semantics()
    scope=load(g52.SCOPE)
    diff=load(g52.DIFF)
    policy=load(g52.POLICY)
    normal={k for k in target if not k.startswith(g52.DEBUG_PREFIX)}
    full=set(scope["addon_full_locales"])
    supp=set(scope["selected_upstream_incomplete_locales"])
    upstream_complete=set(scope["selected_upstream_complete_locales"])
    fallback=set(scope["documented_full_english_fallback_locales"])
    overrides={k:set(v) for k,v in scope["upstream_literal_safety_overrides"].items()}
    if (len(base),len(target),len(normal))!=(334,584,578):
        raise ValueError("Frozen G52 source counts mismatch")
    if (len(full),len(supp),upstream_complete,len(fallback))!=(63,26,{"en_us"},30):
        raise ValueError("Frozen G52 locale ownership mismatch")
    if len(full|supp|upstream_complete)!=90 or full&supp or full&upstream_complete or supp&upstream_complete:
        raise ValueError("Selected G52 locale ownership overlaps or omits a language")
    if (diff["unchanged_key_and_value_count"],diff["added_key_count"],
        diff["removed_key_count"],diff["changed_english_value_count"])!=(193,304,54,87):
        raise ValueError("Frozen G52 semantic delta count mismatch")
    if policy["source_commit"]!=audit.PIN or policy["runtime_promotion_allowed"] is not False:
        raise ValueError("G52 policy pin or runtime release gate mismatch")
    pinned= audit.pinned_locale("en_us")
    if pinned!=target:
        raise ValueError("Frozen G52 English differs from pinned upstream commit")
    with tempfile.TemporaryDirectory(prefix="jei-g52-verify-") as tmp:
        directory=Path(tmp)
        nfull,nsupp,nkeys,provenance=g52.reconstruct_all(directory)
        if (nfull,nsupp,nkeys)!=(63,26,584):
            raise ValueError("G52 reconstruction count mismatch")
        full_dir=directory/"full/assets/jei/lang"
        supp_dir=directory/"supplements/assets/jei/lang"
        if {p.stem for p in full_dir.glob("*.json")}!=full:
            raise ValueError("G52 full language file inventory mismatch")
        if {p.stem for p in supp_dir.glob("*.json")}!=supp:
            raise ValueError("G52 supplement file inventory mismatch")
        changed_or_added=(set(diff["added_keys"])|set(diff["changed_english_values"]))
        for locale in sorted(full):
            values=load(full_dir/f"{locale}.json")
            if set(values)!=set(target):
                raise ValueError(f"{locale}: incomplete full translation file")
            if locale in fallback and values!=target:
                raise ValueError(f"{locale}: documented English fallback diverged")
            for key,value in values.items():
                if not g52.preserves_runtime_literals(target[key],value):
                    raise ValueError(f"{locale}: invalid runtime literals: {key}")
            for key in changed_or_added:
                if values[key]!=target[key]:
                    raise ValueError(f"{locale}: unsanctioned reuse of new/changed English meaning: {key}")
        for locale in sorted(supp):
            official=audit.pinned_locale(locale)
            emitted=load(supp_dir/f"{locale}.json")
            unsafe={k for k in set(official)&normal
                    if not g52.preserves_runtime_literals(target[k],official[k])}
            missing=normal-set(official)
            if unsafe!=overrides.get(locale,set()) or set(emitted)!=missing|unsafe:
                raise ValueError(f"{locale}: supplement includes unexpected upstream-owned keys")
            if any(k.startswith(g52.DEBUG_PREFIX) for k in emitted):
                raise ValueError(f"{locale}: debug-only keys leaked into supplement")
            combined=dict(official);combined.update(emitted)
            for key in normal:
                if key not in combined or not g52.preserves_runtime_literals(target[key],combined[key]):
                    raise ValueError(f"{locale}: combined translation incomplete or unsafe: {key}")
            for key in changed_or_added&set(emitted):
                if emitted[key]!=target[key]:
                    raise ValueError(f"{locale}: unsanctioned donor reuse for changed/new key: {key}")
        if provenance["upstream_commit"]!=audit.PIN:
            raise ValueError("G52 reconstruction provenance pin mismatch")
        if provenance["totals"]["upstream_safety_overrides"]!=scope["upstream_literal_safety_override_count"]:
            raise ValueError("G52 safety override provenance mismatch")
        if provenance["cross_key_reuse_allowed"] is not False:
            raise ValueError("G52 provenance unexpectedly permits cross-key reuse")
    print("PASS: G52 frozen delta, 90-language ownership, semantics and runtime-literal checks")
    print("PASS: 63 full JSON files, 26 exact missing-key/safety supplements, 1 upstream-complete locale")
    print("PASS: 584 English keys (578 normal, 6 debug), 304 added, 54 removed, 87 changed")
    print("PASS: deterministic G51 reuse only for 193 unchanged English key/value meanings")
    print("PASS: upstream safety overrides =",scope["upstream_literal_safety_override_count"])
    print("NOTE: new/changed text uses English fallbacks; in-game merge test still required")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Register the frozen, statically validated G52 target without runtime promotion."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"packaging/completed-versions.json"
G52={
    "generation":"G52","minecraft":"26.3","jei":"31.7.0","era":"modern",
    "loader":"neoforge","neoforge":"26.3.0.7-beta",
    "loader_version_range":"[4,)","neoforge_version_range":"[26.3.0.1-beta,)",
    "jei_version_range":"[31.7.0,31.8.0)","jei_modid":"jei","java_target":25,
    "format":"json","full":63,"supplements":26,"keys":584,
    "reconstruct_script":"scripts/reconstruct_26_3.py"}
def main()->int:
    policy=json.loads((ROOT/"translations/g52-mc26.3/policy.json").read_text(encoding="utf-8"))
    if policy["source_commit"]!="0aed0ce0d09b56923469d1074100f02ed0a45b13":
        raise ValueError("G52 source has not been frozen against exact verified endpoint")
    if policy["runtime_promotion_allowed"] is not False:
        raise ValueError("G52 runtime promotion gate must remain closed")
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches=[v for v in data["versions"] if v["generation"]=="G52" or v["minecraft"]=="26.3"]
    if matches and matches!=[G52]:
        raise ValueError(f"Existing G52 registration conflicts with frozen target: {matches}")
    if not matches:
        if (data["versions"][-1]["generation"],data["versions"][-1]["minecraft"])!=("G51","26.2"):
            raise ValueError("Cannot append G52: latest registered target is not G51")
        data["versions"].append(G52)
    data["note"]="G1-G52 are translation/reconstruction complete. These static-validated candidates are not runtime-promoted finals; G52 uses explicit English fallback for new/changed meanings pending translation review."
    encoded=json.dumps(data,ensure_ascii=False,indent=2)+"\n"
    if REGISTRY.read_text(encoding="utf-8")!=encoded:
        REGISTRY.write_text(encoded,encoding="utf-8")
    subprocess.run([sys.executable,str(ROOT/"scripts/sync_upstream_registries.py"),"--date","2026-09-25"],
                   check=True,cwd=ROOT)
    print("PASS: G52 Minecraft 26.3 registered; 52 chronological generations")
    print("PASS: upstream versions/generations registries synchronized")
    print("NOTE: candidate JAR must pass Java25 static packaging and runtime gates remain open")
    return 0
if __name__=="__main__":
    raise SystemExit(main())

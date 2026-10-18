#!/usr/bin/env python3
"""Validate the exact 53-target search scope and source-only safety contract.

No JAR compilation, no Minecraft runtime, no mutation of release packaging.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "features/language-search"
MATRIX = json.loads((FEATURE / "target-matrix.json").read_text(encoding="utf-8"))
COMPLETED = json.loads((ROOT / "packaging/completed-versions.json").read_text(encoding="utf-8"))
TARGETS = MATRIX["minecraft_targets"]
BUILT = COMPLETED["versions"]

assert len(BUILT) == 52
assert len(TARGETS) == 53
assert COMPLETED["project_version"] == "1.0.0"
assert len({target["minecraft"] for target in TARGETS}) == 53
assert [target["minecraft"] for target in TARGETS if target["minecraft"] != "1.8.8"] == [
    record["minecraft"] for record in BUILT
]
missing = next(t for t in TARGETS if t["minecraft"] == "1.8.8")
assert missing["upstream_jei"] == "2.12.0.49"
source_188 = ROOT / "upstream/sources/1.8.8/en_us.lang"
provenance_188 = json.loads((ROOT/"upstream/sources/1.8.8/provenance.json").read_text(encoding="utf-8"))
english_188 = dict(
    line.split("=",1) for line in source_188.read_text(encoding="utf-8").splitlines()
    if line and not line.startswith("#") and "=" in line
)
assert len(english_188)==56
assert provenance_188["source_keys"]==56
assert provenance_188["official_sha256"]=="ae95a7a3d02a16b5e1144cdc833d0b25c551053738d5ac36a667c04ad2cb4d96"
assert sum(provenance_188["upstream_languages"].values())>56
assert set(provenance_188["upstream_languages"])=={"de_de","en_us","fi_fi","ko_kr","ru_ru","zh_cn"}
assert missing["upstream_language_source"]=="upstream/sources/1.8.8/en_us.lang"

assert "pending" in missing["status"]
assert all(t["status"] == "native" for t in TARGETS if t["minecraft"].startswith("26."))
assert MATRIX["completed_translation_generations"] == 52
assert MATRIX["sources_only"] is True

legacy = next((FEATURE / "legacy_1_8_to_1_12").rglob("LanguageSearchLegacyForge.java"))
forge = next((FEATURE / "forge_1_16_5").rglob("LanguageSearchForge1165.java"))
modern = next((FEATURE / "mc1_21_1").rglob("LanguageSearch1211.java"))
matcher = next((FEATURE / "common").rglob("LanguageSearchMatcher.java"))
assert all(path.is_file() for path in (legacy, forge, modern, matcher))
for path in (legacy, forge, modern):
    body = path.read_text(encoding="utf-8")
    assert "LanguageSearchMatcher.matches(" in body or "LanguageSearchMatcher" not in body
assert "LanguageSearchMatcher.matches(" in legacy.read_text(encoding="utf-8")
assert "LanguageSearchMatcher.matches(" in forge.read_text(encoding="utf-8")

native = sum(t["status"] == "native" for t in TARGETS)
staged = sum("source_prepared" in t["status"] for t in TARGETS)
pending = sum("pending_versioned_gui_adapter" == t["status"] for t in TARGETS)
assert (native, staged, pending) == (5, 48, 0), (native, staged, pending)
assert len(MATRIX["search_adapters"])==38
assert MATRIX["search_source_targets_total"]==48
assert MATRIX["native_search_targets_total"]==5
assert MATRIX["runtime_verified_search_targets_total"]==0
for target in TARGETS:
    if target["status"]=="native":
        continue
    if "adapter_source_path" in target:
        source=ROOT/target["adapter_source_path"]
        assert source.is_file(),(target["minecraft"],source)
        java=source.read_text(encoding="utf-8")
        assert "class LanguageSearch" in java
        assert "draft" in target["source_note"].lower() or "draft" in java.lower(),(target["minecraft"],source)
print(f"PASS 53 target records: {staged} source-only adapters, {native} native search, {pending} missing source drafts; 0 runtime-verified adapters")
print("PASS release freeze: 52 already-completed translations; 1.8.8 pending; no JARs created")

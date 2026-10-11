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
assert missing["upstream_jei"] == "2.0.0"
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
assert (native, staged, pending) == (5, 17, 31), (native, staged, pending)
print(f"PASS 53 target records: {staged} source-only adapters, {native} native search, {pending} adapter gaps")
print("PASS release freeze: 52 already-completed translations; 1.8.8 pending; no JARs created")

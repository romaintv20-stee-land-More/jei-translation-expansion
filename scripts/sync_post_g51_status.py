#!/usr/bin/env python3
"""Synchronize public project status through completed G51 and stable-26.3 readiness."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

G51_SHA = "b3d3a30c23b4a9c3080ed49781fa51df17c024fdf67bdde6c2d467649230824f"
G51_PIN = "f93563ca4965d511bd07d4f041b3a6ddd1158ef0"
PREVIEW_PIN = "58362ffb5baa95580549d6825811e7363964a271"


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sync_project_status() -> None:
    path = ROOT / "PROJECT_STATUS.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Candidate packaging state\n"
    if marker not in text:
        raise ValueError("PROJECT_STATUS.md candidate packaging marker not found")
    prefix = text.split(marker, 1)[0].rstrip()
    tail = f"""

### G52 readiness — Minecraft 26.3 final / exact JEI target pending

- Minecraft Java 26.3 is a final release in Mojang's version manifest, released 2026-09-15.
- Final 26.3 language assets remain at 143 locale files with no additions/removals relative to Minecraft 26.2; all 90 selected project locales remain present.
- The maintained JEI `26.2` branch still points to the frozen G51 pin `{G51_PIN}`.
- JEI currently exposes no exact `26.3` branch. The only matching branch remains `fabric-26.3-snapshot-7` at `{PREVIEW_PIN}` and still targets `minecraftVersion=26.3-rc-2` with Fabric loader `0.19.5` / Fabric API `0.160.4+26.3`.
- Existing provisional 26.3 RC2 translation groundwork remains valid preparation only: 334 exact unchanged English semantics, selected scope 90, provisional ownership 63 full + 26 supplements + 1 complete upstream, and deterministic reconstruction already validated.
- **Do not register G52 or persist a 26.3 candidate JAR until JEI exposes an exact final Minecraft 26.3 target and its loader/publication state is re-audited.**
- Stable-release readiness audit run `35064326868` is green; frozen report: `upstream/provisional/minecraft-26.3-release-readiness.json`.

## Candidate packaging state

- The canonical candidate inventory on `main` contains **51 version-specific 1.0.0 candidates through Minecraft 26.2**.
- G51 / Minecraft 26.2 is canonically persisted at `candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar`.
- G51 persisted SHA-256: `{G51_SHA}`.
- G52 is deliberately not registered and has no candidate JAR while exact final JEI 26.3 support is unavailable.
- Candidate JARs are not runtime-promoted finals.

## Current next target

- Keep G51 frozen at JEI `30.32.0` / `{G51_PIN}` unless the maintained 26.2 branch moves and a later 26.2 snapshot is deliberately re-audited.
- Minecraft 26.3 itself is now final, so the next chronological generation remains **G52 = Minecraft 26.3**, but completion is blocked on an exact final JEI 26.3 target.
- Re-run `scripts/audit_26_3_release_readiness.py` when JEI branch state changes. As soon as an exact 26.3 target appears, perform a fresh endpoint/loader/upstream-ownership audit before translating, packaging, or registering G52.
- Keep the existing RC2/Fabric artifact QA-only and outside `candidate-jars/`.
- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.

## Documentation synchronization debt

- `PROJECT_STATUS.md`, `README.md`, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` are synchronized through completed G51 plus the stable-Minecraft-26.3 / JEI-target-pending readiness state.
- `packaging/completed-versions.json`, `upstream/versions.json`, and `upstream/generations.json` remain canonical only through completed G51; provisional G52 data stays under `upstream/provisional/` and is intentionally excluded from completed registries.

## Release gates still open

- Minecraft 1.8.9 prototype/runtime lineage still requires a real client runtime validation before final release promotion.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.
- NeoForge candidates G39–G51 remain static candidates until their version-specific runtime checks are complete.
- Provisional 26.3 RC2/Fabric work is QA-only and is not a release candidate.
"""
    write(path, prefix + tail)


def sync_readme() -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("## Current status\n")
    end = text.index("## Repository layout\n")
    replacement = f"""## Current status

The selected translation/reconstruction scopes are complete and CI-validated from **Minecraft 1.8 through Minecraft 26.2** (**G1-G51**).

Each completed Minecraft target receives its own **JEI Translation Expansion 1.0.0 static-validated JAR candidate**. Forge is used for historical Forge targets, NeoForge for the completed modern NeoForge targets, and the 26.x line uses Java 25 where required. Static candidates live under `candidate-jars/<minecraft-version>/` after canonical packaging persistence.

**G51 / Minecraft 26.2 / JEI 30.32.0** is frozen at maintained JEI branch commit `{G51_PIN}`. It contains 334 keys (328 normal + 6 debug), keeps the 90-language selected scope, and reconstructs 63 addon-full locales plus 26 missing-key/safety-override supplements; `en_us` is the single complete selected upstream locale. All 334 English semantics are unchanged from G50. Its canonical NeoForge candidate is `candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar` with SHA-256 `{G51_SHA}`.

Minecraft **26.3 is now a final release**, but JEI has not yet exposed an exact final 26.3 target. The only matching JEI branch remains the provisional Fabric branch `fabric-26.3-snapshot-7`, pinned at `{PREVIEW_PIN}`, and still targets `26.3-rc-2`. Translation groundwork is prepared and validated, but **G52 is intentionally not registered and no 26.3 candidate is published** until an exact final JEI 26.3 endpoint and loader state can be audited.

Runtime-tested final JAR promotion is tracked separately from chronological translation auditing. Final artifacts belong under `release-jars/<minecraft-version>/` only after the required runtime validation. Starting with Minecraft 1.13, missing-key-only JSON supplements remain runtime merge-test-gated before final promotion.

The next chronological generation remains **G52 / Minecraft 26.3**, pending exact final JEI 26.3 support.

For the canonical handoff and exact next task, always read [`PROJECT_STATUS.md`](PROJECT_STATUS.md) first.

"""
    write(path, text[:start] + replacement + text[end:])


def sync_version_matrix() -> None:
    path = ROOT / "docs" / "VERSION_MATRIX.md"
    text = path.read_text(encoding="utf-8")
    if "| G51 | 26.2 |" not in text:
        rows = (
            "| G46 | 1.21.10 | 26.2.0 | `621ddf0` | NeoForge | 308 | 90 | 64 | 25 | 1 | complete |\n"
            "| G47 | 1.21.11 | 27.38.0 | `4b6e473` | NeoForge | 334 | 90 | 63 | 26 | 1 | complete |\n"
            "| G48 | 26.1 | 29.2.0 | `16c0e3b` | NeoForge | 309 | 90 | 64 | 25 | 1 | complete |\n"
            "| G49 | 26.1.1 | 29.4.0 | `5a2ecc4` | NeoForge | 309 | 90 | 64 | 25 | 1 | complete |\n"
            "| G50 | 26.1.2 | 29.37.0 | `d7c73ed` | NeoForge | 334 | 90 | 63 | 26 | 1 | complete |\n"
            "| G51 | 26.2 | 30.32.0 | `f93563c` | NeoForge | 334 | 90 | 63 | 26 | 1 | complete |\n"
        )
        match = re.search(r"^\| G45 \|[^\n]+\n", text, flags=re.MULTILINE)
        if not match:
            raise ValueError("VERSION_MATRIX.md G45 row not found")
        text = text[:match.end()] + rows + text[match.end():]

    marker = "## Candidate packaging\n"
    if marker not in text:
        raise ValueError("VERSION_MATRIX.md candidate packaging marker not found")
    prefix = text.split(marker, 1)[0].rstrip()
    tail = f"""

## Candidate packaging

Completed generations are registered in `packaging/completed-versions.json`. Their deterministic static candidates are persisted one Minecraft version at a time under `candidate-jars/<minecraft-version>/`.

G51 / Minecraft 26.2 is the latest completed target. Its Java-25 NeoForge candidate is persisted as `candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar` with SHA-256 `{G51_SHA}`. The canonical inventory contains 51 version-specific candidates.

## Current target

Minecraft 26.3 is a final release, but JEI currently has no exact final 26.3 branch/target. The only matching upstream branch remains `fabric-26.3-snapshot-7` at `{PREVIEW_PIN}`, still targeting Minecraft `26.3-rc-2`. The provisional translation reconstruction is prepared but is not G52 and is not a publishable candidate. The next chronological target is **G52 = Minecraft 26.3** once an exact final JEI 26.3 endpoint and loader state are available for audit.
"""
    write(path, prefix + tail)


def sync_translation_status() -> None:
    path = ROOT / "docs" / "TRANSLATION_STATUS.md"
    text = path.read_text(encoding="utf-8")
    if "| G51 | 26.2 |" not in text:
        rows = (
            "| G48 | 26.1 | 29.2.0 | 309 | 90 | 64 | 25 | 1 | complete |\n"
            "| G49 | 26.1.1 | 29.4.0 | 309 | 90 | 64 | 25 | 1 | complete |\n"
            "| G50 | 26.1.2 | 29.37.0 | 334 | 90 | 63 | 26 | 1 | complete |\n"
            "| G51 | 26.2 | 30.32.0 | 334 | 90 | 63 | 26 | 1 | complete |\n"
        )
        match = re.search(r"^\| G47 \|[^\n]+\n", text, flags=re.MULTILINE)
        if not match:
            raise ValueError("TRANSLATION_STATUS.md G47 row not found")
        text = text[:match.end()] + rows + text[match.end():]

    current = "## Current generation\n"
    release = "## Release limitations\n"
    if current not in text or release not in text:
        raise ValueError("TRANSLATION_STATUS.md current/release markers not found")
    start = text.index(current)
    end = text.index(release)
    replacement = f"""## Current generation

G51 / Minecraft 26.2 / JEI 30.32.0 is complete, statically validated, and canonically packaged. It contains 334 keys, keeps the selected scope at 90, and uses ownership 63 addon-full + 26 missing-key/safety-override supplements + 1 complete upstream locale (`en_us`). Its candidate SHA-256 is `{G51_SHA}`.

Minecraft 26.3 is now final on the Minecraft side, and the 90 selected locales remain present in its final language assets. JEI still has no exact final 26.3 target: `fabric-26.3-snapshot-7` remains pinned at `{PREVIEW_PIN}` and targets `26.3-rc-2`. Existing provisional reconstruction is therefore preparation only; G52 remains unregistered until the exact final JEI endpoint and loader state can be audited.

"""
    write(path, text[:start] + replacement + text[end:])


def main() -> int:
    sync_project_status()
    sync_readme()
    sync_version_matrix()
    sync_translation_status()
    print("PASS: synchronized public status through G51 and stable Minecraft 26.3 readiness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

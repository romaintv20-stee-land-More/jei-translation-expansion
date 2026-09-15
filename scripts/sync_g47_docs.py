#!/usr/bin/env python3
"""Synchronize G47 documentation with the maintained Minecraft 1.21.11 endpoint."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "PROJECT_STATUS.md"
TRANSLATION = ROOT / "docs" / "TRANSLATION_STATUS.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def sync_project_status() -> None:
    text = STATUS.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "| G47 | 1.21.11 | 27.3.0 | `1d37cb1` | 308 | 90 | 64 | 25 | 1 | complete; upstream Maven-only; no public candidate |",
        "| G47 | 1.21.11 | 27.38.0 | `4b6e473` | 334 | 90 | 63 | 26 | 1 | complete; maintained branch validated; packaging pending |",
        "PROJECT_STATUS G47 row",
    )
    start = text.index("### G47 — Minecraft 1.21.11")
    end = text.index("\n## Candidate packaging state", start)
    section = """### G47 — Minecraft 1.21.11 / JEI 27.38.0

- first 1.21.11 port `6b615d15ef776abf139339779985a91c59c9c324` directly follows G46 and historically stated that JEI 1.21.11 would be Maven-only
- historical mainline 1.21.11 endpoint `1d37cb1a1cf7139170d214adef128f405b865312`; mainline then moves to `d395fda29b10f09b860d5a6221b459050f5071d3` (`26.1-snapshot-1`)
- maintained dedicated 1.21.11 branch endpoint `4b6e47334ac4aaeae51d15facbb38c42cb511321` is the canonical G47 source because maintenance continued after mainline moved on
- maintained build: NeoForge `21.11.45`, minimum `[21.11.44,)`, Java 21, JEI specification version `27.38.0`
- 334 keys = 328 normal + 6 debug
- G46→maintained-G47 semantic delta = 291 unchanged + 37 added + 11 removed + 6 changed-English values
- translation inheritance is allowed only for exact same-key/same-English semantics; cross-key reuse remains forbidden
- project-owned added or changed meanings use exact target English unless a safe target-upstream translation already owns that key
- selected scope remains 90; ownership = 63 addon-full locales + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- all selected upstream JSON files are syntactically valid at the maintained endpoint; `fil_ph` and `uk_ua` are valid incomplete upstream supplement locales
- 91 upstream-owned values require frozen literal-safety overrides so placeholders and fixed technical literals remain exact
- the maintained branch has normal CurseForge project `238222` and Modrinth project `u6dRKJwZ` publication configuration, superseding the first-port Maven-only limitation for current maintained releases
- isolated maintained-endpoint reconstruction validation run `35006503247`, green
- public candidate packaging remains a separate project step until the maintained-target metadata is merged and the candidate builder is validated
"""
    text = text[:start] + section + text[end:]
    text = replace_once(
        text,
        "- The canonical candidate inventory on `main` contains **46 version-specific 1.0.0 candidates through Minecraft 1.21.10**.\n- G47 translation/reconstruction is complete, but it is intentionally excluded from normal `candidate-jars/` packaging because upstream JEI 1.21.11 is Maven-only.\n- Candidate JARs are not runtime-promoted finals.",
        "- The canonical candidate inventory on `main` contains **46 version-specific 1.0.0 candidates through Minecraft 1.21.10**.\n- Maintained G47 translation/reconstruction is complete; its 1.21.11 candidate has not yet been added to `candidate-jars/` while packaging metadata is validated separately.\n- Candidate JARs are not runtime-promoted finals.",
        "PROJECT_STATUS candidate state",
    )
    text = replace_once(
        text,
        "- G47 / Minecraft 1.21.11 translation auditing is complete and statically validated.\n- Before assigning G48, identify the next **publicly relevant Minecraft/JEI target** after the Maven-only 1.21.11 line; do not promote `26.1-snapshot-1` merely because it is the next upstream development commit.\n- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.",
        "- Maintained G47 / Minecraft 1.21.11 translation auditing is complete and statically validated at JEI 27.38.0.\n- Validate and persist the dedicated G47 NeoForge candidate now that the maintained upstream branch has normal CurseForge/Modrinth publication configuration.\n- After G47 packaging, audit the Minecraft 26.1/26.1.2 maintained line carefully under the one-Minecraft-version-per-JAR rule before assigning G48/G49.\n- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.",
        "PROJECT_STATUS current target",
    )
    text = replace_once(
        text,
        "- `PROJECT_STATUS.md` and `docs/TRANSLATION_STATUS.md` are synchronized through completed G47 translation/reconstruction.\n- `upstream/versions.json` and `upstream/generations.json` remain packaging-derived and are synchronized through publicly packaged G46; G47 is deliberately not inserted through the packaging registry because its upstream target is Maven-only.\n- `README.md` and `docs/VERSION_MATRIX.md` remain aligned to the normal public candidate line through G46; this is intentional until a subsequent public target is identified.",
        "- `PROJECT_STATUS.md` and `docs/TRANSLATION_STATUS.md` are synchronized through maintained G47 translation/reconstruction.\n- `upstream/versions.json` and `upstream/generations.json` remain packaging-derived and stay synchronized through G46 until G47 is deliberately added to the packaging registry.\n- `README.md` and `docs/VERSION_MATRIX.md` remain aligned to the packaged candidate line through G46 until G47 candidate packaging is completed.",
        "PROJECT_STATUS docs debt",
    )
    text = replace_once(
        text,
        "- G39–G46 NeoForge candidates remain static candidates until their version-specific runtime checks are complete.\n- G47 has no normal public candidate because upstream JEI 1.21.11 is Maven-only.",
        "- G39–G46 NeoForge candidates remain static candidates until their version-specific runtime checks are complete.\n- G47 translation/reconstruction is statically validated; its maintained-branch candidate remains pending separate packaging validation and will remain runtime-gated after creation.",
        "PROJECT_STATUS release gates",
    )
    STATUS.write_text(text, encoding="utf-8")


def sync_translation_status() -> None:
    text = TRANSLATION.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "| G47 | 1.21.11 | 27.3.0 | 308 | 90 | 64 | 25 | 1 | complete; upstream Maven-only |",
        "| G47 | 1.21.11 | 27.38.0 | 334 | 90 | 63 | 26 | 1 | complete; maintained branch validated |",
        "TRANSLATION_STATUS G47 row",
    )
    start = text.index("### G47 — Minecraft 1.21.11")
    end = text.index("\n## Current generation", start)
    section = """### G47 — Minecraft 1.21.11 / JEI 27.38.0

- First 1.21.11 port: `6b615d15ef776abf139339779985a91c59c9c324`; it historically stated that this line would be Maven-only.
- Historical mainline endpoint: `1d37cb1a1cf7139170d214adef128f405b865312`; mainline next moves to `d395fda29b10f09b860d5a6221b459050f5071d3` (`26.1-snapshot-1`).
- Maintained dedicated 1.21.11 endpoint: `4b6e47334ac4aaeae51d15facbb38c42cb511321`.
- Build: NeoForge `21.11.45`, minimum `[21.11.44,)`, Java 21, JEI specification version `27.38.0`.
- 334 keys = 328 normal + 6 debug.
- G46→maintained-G47: 291 unchanged, 37 added, 11 removed, 6 changed-English values.
- Only exact same-key/same-English meanings may inherit G46 translations; cross-key reuse is forbidden. Project-owned added/changed meanings use exact target English when no safe target-upstream value owns the key.
- Selected scope remains 90; ownership is 63 addon-full + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`).
- All selected upstream JSON files are valid at the maintained endpoint; `fil_ph` and `uk_ua` are valid incomplete upstream locales.
- 91 upstream-owned values require frozen literal-safety overrides.
- The maintained branch has normal CurseForge project `238222` and Modrinth project `u6dRKJwZ` publication configuration, so the historical first-port Maven-only note no longer describes the maintained branch's current distribution configuration.
- Complete isolated maintained-endpoint validation run `35006503247` is green.
- Candidate packaging remains separate until the maintained G47 metadata is merged and the NeoForge candidate build is validated.
"""
    text = text[:start] + section + text[end:]
    text = replace_once(
        text,
        "G47 translation/reconstruction is complete and statically validated. Public candidate packaging is intentionally withheld because upstream JEI 1.21.11 is Maven-only. The next chronological work item must first identify the next **publicly relevant Minecraft/JEI target** rather than treating the upstream `26.1-snapshot-1` development transition as an automatic public generation.",
        "Maintained G47 translation/reconstruction is complete and statically validated at JEI 27.38.0. The next step is to validate and persist its dedicated NeoForge candidate, then audit the Minecraft 26.1/26.1.2 maintained line under the one-Minecraft-version-per-JAR rule before assigning the next generation(s).",
        "TRANSLATION_STATUS current generation",
    )
    TRANSLATION.write_text(text, encoding="utf-8")


def main() -> int:
    sync_project_status()
    sync_translation_status()
    print("PASS: synchronized maintained G47 documentation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

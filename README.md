# JEI Translation Expansion

Unofficial localization companion for **Just Enough Items (JEI)**. The project adds missing languages and completes incomplete JEI translations across historical Minecraft versions while preserving translations already shipped by JEI.

> This project is independent and unofficial. It is not affiliated with or endorsed by mezz or the JEI project.

## Upstream

- JEI source: https://github.com/mezz/JustEnoughItems
- JEI CurseForge: https://www.curseforge.com/minecraft/mc-mods/jei
- This project: https://github.com/romaintv20-stee-land-More/jei-translation-expansion

## Fixed project rules

- Audit the real upstream endpoint before translating a Minecraft version.
- Reuse a translation only when both the localization key and English meaning are unchanged.
- Preserve JEI upstream translations; selected upstream locales receive only exact missing-key supplements unless an override is explicitly approved.
- Preserve placeholders and technical literals exactly.
- Prefer a documented English fallback over an unreliable translation.
- Focus initially on real-world primary Minecraft languages; constructed/novelty languages and most regional variants are deferred.
- **One Minecraft version = one final release JAR. Never combine several Minecraft versions in one JAR.**

## AI-assisted translation policy

Translations may be created or assisted with AI, but AI output is not treated as automatically correct. Automated QA checks exact key coverage, resource syntax, placeholders, technical tokens, semantic reuse boundaries, upstream ownership and deterministic reconstruction. Low-confidence language content uses an explicit English fallback instead of an invented translation.

## Current status

The selected translation/reconstruction scopes are complete and CI-validated from **Minecraft 1.8 through Minecraft 26.2** (**G1-G51**).

Each completed Minecraft target receives its own **JEI Translation Expansion 1.0.0 static-validated JAR candidate**. Forge is used for historical Forge targets, NeoForge for the completed modern NeoForge targets, and the 26.x line uses Java 25 where required. Static candidates live under `candidate-jars/<minecraft-version>/` after canonical packaging persistence.

**G51 / Minecraft 26.2 / JEI 30.32.0** is frozen at maintained JEI branch commit `f93563ca4965d511bd07d4f041b3a6ddd1158ef0`. It contains 334 keys (328 normal + 6 debug), keeps the 90-language selected scope, and reconstructs 63 addon-full locales plus 26 missing-key/safety-override supplements; `en_us` is the single complete selected upstream locale. All 334 English semantics are unchanged from G50. Its canonical NeoForge candidate is `candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar` with SHA-256 `b3d3a30c23b4a9c3080ed49781fa51df17c024fdf67bdde6c2d467649230824f`.

Minecraft **26.3 is now a final release**, but JEI has not yet exposed an exact final 26.3 target. The only matching JEI branch remains the provisional Fabric branch `fabric-26.3-snapshot-7`, pinned at `58362ffb5baa95580549d6825811e7363964a271`, and still targets `26.3-rc-2`. Translation groundwork is prepared and validated, but **G52 is intentionally not registered and no 26.3 candidate is published** until an exact final JEI 26.3 endpoint and loader state can be audited.

Runtime-tested final JAR promotion is tracked separately from chronological translation auditing. Final artifacts belong under `release-jars/<minecraft-version>/` only after the required runtime validation. Starting with Minecraft 1.13, missing-key-only JSON supplements remain runtime merge-test-gated before final promotion.

**G52 / Minecraft 26.3** is registered against the exact JEI 26.3 NeoForge branch (Java 25, 584 keys and 90 selected languages). New or changed text uses explicit English fallback pending translation review. Static packaging and in-game release gates remain separate.

For the canonical handoff and exact next task, always read [`PROJECT_STATUS.md`](PROJECT_STATUS.md) first.

## Repository layout

```text
translations/
  g1-.../
  g2-.../
  ...
upstream/
  versions.json
  generations.json
  sources/
  diffs/
overrides/
  approved-overrides.json
scripts/
packaging/
  completed-versions.json
candidate-jars/
  <minecraft-version>/
docs/
  VERSION_MATRIX.md
  TRANSLATION_STATUS.md
  WORKFLOW.md
release-jars/
  <minecraft-version>/
PROJECT_STATUS.md
README.md
LICENSE
NOTICE
```

Localization generations are an internal reuse mechanism only. Final release artifacts remain strictly version-specific.

## Licensing

This project is licensed under the MIT License. JEI is also distributed under the MIT License. Any upstream JEI material redistributed by this project must retain the applicable JEI copyright and MIT notice. See [`NOTICE`](NOTICE) and [`LICENSE`](LICENSE).

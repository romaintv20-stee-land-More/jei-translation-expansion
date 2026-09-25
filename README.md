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

The selected translation/reconstruction scopes are QA-complete from **Minecraft 1.8 through Minecraft 26.3** (**G1–G52**). Each Minecraft target receives its own 1.0.0 static-validated candidate JAR; the modern 26.x NeoForge line uses Java 25.

**G52 / Minecraft 26.3 / JEI 31.7.0 (31.7.x-compatible)** is pinned to JEI commit `0aed0ce0d09b56923469d1074100f02ed0a45b13`. It covers 90 selected languages with 584 keys: 63 add-on-owned complete resource files, 26 JEI missing-key/safety-override supplements, and upstream `en_us`. Only 193 unchanged key+English meanings inherit the G51 translations; new/changed texts receive explicit English fallbacks if JEI lacks a verified translation. These texts still need native-language review.

The Java-25 NeoForge candidate is stored at [`candidate-jars/26.3/jei-translation-expansion-1.0.0-mc26.3-neoforge.jar`](candidate-jars/26.3/jei-translation-expansion-1.0.0-mc26.3-neoforge.jar) (SHA-256 `3cdfd40342ab8e8128f8d940b5eeb5464a36b2d0f3e9596445a2488cd32ca1e9`, 845,501 bytes). Dedicated G52 static tests and canonical packaging CI passed.

Runtime-tested final JAR promotion is tracked separately from chronological translation auditing. Final artifacts belong under `release-jars/<minecraft-version>/` only after the required runtime validation. Starting with Minecraft 1.13, missing-key-only JSON supplements remain runtime merge-test-gated before final promotion.

**G52 has a persisted static candidate and complete source/key-coverage QA**. It is not a runtime-tested final release. In-game merging and native-language review remain open.

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

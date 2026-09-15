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

The selected translation/reconstruction scopes are complete and CI-validated from **Minecraft 1.8 through Minecraft 1.21.6** (**G1-G42**).

Each completed Minecraft target receives its own **JEI Translation Expansion 1.0.0 static-validated JAR candidate**. Forge is used for the historical Forge targets; current 1.21.x targets use their dedicated NeoForge packaging path. Static candidates live under `candidate-jars/<minecraft-version>/` after canonical packaging persistence.

**G42 / Minecraft 1.21.6 / JEI 22.0.0** is pinned to JEI commit `2a57409c2af0ce9716749a0329166a41cbcf453f`, whose direct successor is the Minecraft 1.21.7 port. It contains 289 English keys (283 normal + 6 debug), keeps the 90-language selected scope, and reconstructs 65 addon/full-override locales plus 24 missing-key-only upstream supplements; `en_us` is the single complete selected upstream locale. G41→G42 is a removal-only semantic delta: the surviving 289 key/value meanings are unchanged and `gui.jei.category.grindstone.experience` is removed. The pinned upstream Ukrainian file remains malformed JSON, so `uk_ua` remains an explicit valid full repair override. Full reconstruction QA is green, and the deterministic NeoForge candidate build/inspection produced 89 language resources with SHA-256 `6a1f0262f68189ae064fbc1909792ae41542af8cfdf6c6f5286e5d703c98fdfb`.

Runtime-tested final JAR promotion is tracked separately from chronological translation auditing. Final artifacts belong under `release-jars/<minecraft-version>/` only after the required runtime validation. Starting with Minecraft 1.13, missing-key-only JSON supplements remain runtime merge-test-gated before final promotion.

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

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

The selected translation/reconstruction scopes are complete and CI-validated from **Minecraft 1.8 through Minecraft 1.18.2** (G1-G27). Version-specific **1.0.0 static-validated JAR candidates** are built separately from runtime release promotion.

Minecraft 1.19 / G28 has isolated QA complete but still requires its clean canonical full-history gate before it is treated as completed for packaging.

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
  ...
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

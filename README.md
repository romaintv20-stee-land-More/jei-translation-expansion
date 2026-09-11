# JEI Translation Expansion

Unofficial localization companion for **Just Enough Items (JEI)**. The goal is to add missing languages and complete incomplete JEI translations across supported Minecraft versions and mod loaders without unnecessarily replacing translations already provided by JEI.

> This project is independent and unofficial. It is not affiliated with or endorsed by mezz or the JEI project.

## Upstream

- JEI source: https://github.com/mezz/JustEnoughItems
- JEI CurseForge: https://www.curseforge.com/minecraft/mc-mods/jei
- This project: https://github.com/romaintv20-stee-land-More/jei-translation-expansion

## Project goals

- Audit JEI translation keys across Minecraft versions before translating.
- Group compatible Minecraft/JEI versions into localization generations for internal translation reuse.
- Add missing real-world languages supported by Minecraft.
- Complete missing keys in languages already included by JEI.
- Preserve upstream JEI translations by default; only override an existing upstream key when explicitly reviewed and allowlisted.
- Preserve formatting placeholders such as `%s`, `%d`, indexed placeholders, escaped characters and other formatting tokens.
- Avoid blindly reusing a translation when the same key changes English meaning between JEI generations.
- Exclude novelty/fantasy languages and initially defer most regional/orthographic variants when a primary form is already covered.
- Prefer an English fallback over an unreliable translation for low-confidence languages.
- Produce **one dedicated release JAR per Minecraft version**. Compatible translations may be reused internally, but multiple Minecraft versions are never grouped into the same JAR.

## AI-assisted translation policy

Translations may be created or assisted with artificial intelligence. AI output is not treated as automatically correct. The project uses automated QA and manual/community review where possible to check key coverage, JSON/LANG syntax, placeholders, unchanged technical tokens, consistency and compatibility between JEI generations.

If a language cannot be translated with sufficient confidence, the project keeps a documented English fallback rather than publishing a knowingly unreliable translation.

## Current status

Audit and translation work is progressing chronologically through historical JEI/Minecraft versions. The selected translation/reconstruction scopes are complete and CI-validated for **Minecraft 1.8, 1.8.9, 1.9, 1.9.4 and 1.10**. Minecraft 1.10 / JEI 3.7.1 expands the selected project scope to 72 languages after Minecraft adds Hawaiian and Mongolian; its deterministic pipeline validates 65 complete addon locales plus six exact missing-key-only JEI supplements.

Version-specific runtime/JAR validation may be finalized separately while auditing continues to later Minecraft versions. The next chronological audit target is Minecraft **1.10.2**. The oldest verified JEI branch in the official upstream repository is **Minecraft 1.8**; the modern upstream endpoint is audited separately as the project progresses.

For the canonical handoff and exact next steps, read [`PROJECT_STATUS.md`](PROJECT_STATUS.md) first.

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

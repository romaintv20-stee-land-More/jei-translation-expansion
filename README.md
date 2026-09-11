# JEI Translation Expansion

Unofficial localization companion for **Just Enough Items (JEI)**. The goal is to add missing languages and complete incomplete JEI translations across supported Minecraft versions and mod loaders without unnecessarily replacing translations already provided by JEI.

> This project is independent and unofficial. It is not affiliated with or endorsed by mezz or the JEI project.

## Upstream

- JEI source: https://github.com/mezz/JustEnoughItems
- JEI CurseForge: https://www.curseforge.com/minecraft/mc-mods/jei
- This project: https://github.com/romaintv20-stee-land-More/jei-translation-expansion

## Project goals

- Audit JEI translation keys across Minecraft versions before translating.
- Group compatible Minecraft/JEI versions into localization generations instead of maintaining one translation set per Minecraft version.
- Add missing real-world languages supported by Minecraft.
- Complete missing keys in languages already included by JEI.
- Preserve upstream JEI translations by default; only override an existing upstream key when explicitly reviewed and allowlisted.
- Preserve formatting placeholders such as `%s`, `%d`, indexed placeholders, escaped characters and other formatting tokens.
- Avoid blindly reusing a translation when the same key changes English meaning between JEI generations.
- Exclude novelty/fantasy languages and initially defer most regional/orthographic variants when a primary form is already covered.
- Prefer an English fallback over an unreliable translation for low-confidence languages.
- Produce the smallest practical number of distributable JARs by grouping compatible Minecraft versions and loaders safely.

## AI-assisted translation policy

Translations may be created or assisted with artificial intelligence. AI output is not treated as automatically correct. The project will use automated QA and manual/community review where possible to check key coverage, JSON/LANG syntax, placeholders, unchanged technical tokens, consistency and compatibility between JEI generations.

If a language cannot be translated with sufficient confidence, the project should keep a documented English fallback rather than publish a knowingly unreliable translation.

## Current status

The project is in the **upstream audit / architecture phase**. Translation work should not begin until JEI versions have been grouped into verified localization generations.

The oldest verified JEI branch in the official upstream repository is **Minecraft 1.8**. The current upstream default branch at project initialization is **26.2**.

For the canonical handoff and exact next steps, read [`PROJECT_STATUS.md`](PROJECT_STATUS.md) first.

## Planned repository layout

```text
translations/
  g1-.../
  g2-.../
  ...
upstream/
  versions.json
  generations.json
  official-locales.json
overrides/
  approved-overrides.json
scripts/
  audit_jei.py
  compare_keys.py
  validate_translations.py
  build_release.py
docs/
  VERSION_MATRIX.md
  WORKFLOW.md
PROJECT_STATUS.md
README.md
LICENSE
NOTICE
```

The exact generation names and number of JARs must be determined by the audit rather than guessed in advance.

## Licensing

This project is licensed under the MIT License. JEI is also distributed under the MIT License. Any upstream JEI material redistributed by this project must retain the applicable JEI copyright and MIT notice. See [`NOTICE`](NOTICE) and [`LICENSE`](LICENSE).

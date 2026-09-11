# JEI Translation Expansion — Project Status

> **Start here in a new chat. This file is the canonical handoff for the project and should be enough to resume work without relying on previous conversation history.**

Last synchronized: **2026-09-11**

## Repository

- Project: **JEI Translation Expansion**
- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Default branch: `main`
- Upstream JEI repository: https://github.com/mezz/JustEnoughItems
- Upstream CurseForge: https://www.curseforge.com/minecraft/mc-mods/jei
- Upstream default branch when the project was initialized: `26.2`
- License: MIT

## Purpose

Create an **unofficial localization companion for Just Enough Items (JEI)** that adds missing languages and fills missing translation keys across JEI/Minecraft generations and loaders while preserving JEI's own translations whenever possible.

The addon adds no gameplay content. It should contain localization resources plus only the minimal loader metadata/stub code required to load those resources.

## Current phase

**Phase 1 — upstream version/generation audit, with the Minecraft 1.8 language-file stage completed.**

Do not publish a release until version-generation boundaries, loader metadata, Java/runtime requirements and packaging compatibility have been audited.

## Verified oldest starting point

The official JEI repository has an upstream branch named `1.8`. No older official JEI branch was found during the initial branch audit.

For branch `1.8`:

- Minecraft: **1.8**
- JEI: **2.15.0**
- Forge: **11.14.4.1577**
- Translation format: legacy `.lang`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- Local source snapshot: `upstream/sources/1.8/en_US.lang`
- 58 localization keys total
- 55 normal translatable keys
- 3 debug-only description keys explicitly marked upstream as not requiring translation
- JEI upstream locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- JEI's build uses Java source/target compatibility 1.7; final runtime/release Java metadata must still be verified separately

Therefore the oldest Minecraft version currently planned for support is **Minecraft 1.8**.

## Minecraft 1.8 language scope — COMPLETE

The audited Minecraft 1.8 language set contains 75 language codes when `en_US` is included.

Project scope for this generation:

- excluded novelty/fantasy: `en_PT`, `qya_AA`, `tlh_AA`
- 12 regional/orthographic variants deferred for now
- 60 primary languages retained
- 6 of those already supplied by JEI upstream
- addon target: **54 locale files**

Current result under `translations/g1-mc1.8/`:

- **54/54 addon locale files present**
- **51 translated / AI-assisted locales**
- **3 documented English fallbacks** because translation confidence was too low:
  - `gv_IM` — Manx
  - `kw_GB` — Cornish
  - `se_NO` — Northern Sami
- the 3 upstream debug-only strings remain English in every addon locale by design

The exact scope is recorded in `upstream/minecraft-1.8-language-scope.json` and the human-readable status is in `docs/TRANSLATION_STATUS.md`.

## Translation benchmark

A five-language pilot (`fr_FR`, `es_ES`, `it_IT`, `pt_BR`, `nl_NL`) was used to measure translation-stage speed for the small 1.8 schema.

- 55 normal translatable keys per locale
- 275 translated entries in the pilot
- translation + initial QA measured at **1 minute 36 seconds** for the five pilot locales
- about **19 seconds per locale** for this small legacy schema

This timing is documented in `docs/TRANSLATION_BENCHMARK.md` and must not be extrapolated directly to modern JEI, whose English localization contains several hundred entries.

## QA now in repository

`scripts/validate_translations.py` validates the Minecraft 1.8 generation for:

- all 54 expected addon locale files;
- exact key-set parity with the audited English source;
- duplicate keys;
- placeholder parity including `%,d`, `%s`, `%MODNAME`;
- technical-token preservation including `/give`, `@ModName`, `modId:name[:meta]`, `NBT`, `ItemStack`, `JEI`, `Minecraft`, `mB`, `Ctrl`;
- debug-only strings staying in English;
- English fallback being limited to the three documented low-confidence locales.

`.github/workflows/validate.yml` runs the validator on push and pull requests.

## Modern endpoint already inspected

On upstream branch `26.2`:

- language files are JSON under `Common/src/main/resources/assets/jei/lang/`;
- `en_us.json` contains several hundred UI/config/tooltips/messages entries;
- existing translations are uneven in completeness;
- for example, `fr_fr.json` is missing newer English keys and contains older translation structure in places.

This makes JEI suitable for both adding absent languages and filling missing keys in languages already shipped upstream.

## Translation policy

1. Protect existing JEI translations by default.
2. For locales already shipped by JEI, add only missing keys unless an override has been explicitly reviewed and allowlisted.
3. For absent locales, provide the full generation translation set.
4. Reuse translations across generations only when both key and English meaning are unchanged.
5. Preserve placeholders and technical literals exactly.
6. Do not migrate renamed keys blindly.
7. Prefer a documented English fallback over a low-confidence invented translation.
8. AI-assisted translations are allowed but must undergo automated QA and remain open to community/native-speaker correction.
9. Focus on real-world primary languages; exclude novelty/fantasy languages and initially defer most regional/orthographic variants.
10. Copy no unnecessary JEI gameplay/source code; preserve MIT attribution where upstream material is redistributed.

## Architecture

Keep **localization generations** separate from **distribution JAR groups**.

`translations/g1-mc1.8/` currently names the first audited translation set. The final boundary of generation G1 is not yet known: adjacent JEI versions must be compared before deciding whether they can reuse the same translation schema.

Distribution artifacts should be grouped across Minecraft versions only when loader/resource compatibility is demonstrably safe. Avoid one JAR per Minecraft version where possible.

## Important files

- `README.md` — public project overview
- `PROJECT_STATUS.md` — canonical handoff
- `docs/VERSION_MATRIX.md` — audited version facts
- `docs/WORKFLOW.md` — project workflow
- `docs/TRANSLATION_BENCHMARK.md` — translation timing pilot
- `docs/TRANSLATION_STATUS.md` — current language coverage
- `upstream/versions.json` — machine-readable partial version audit
- `upstream/generations.json` — generation definitions; still incomplete
- `upstream/official-locales.json` — partial upstream locale inventory
- `upstream/minecraft-1.8-language-scope.json` — exact 1.8 language scope/status
- `upstream/sources/1.8/en_US.lang` — audited English source snapshot
- `translations/g1-mc1.8/` — 54 addon locale files
- `scripts/validate_translations.py` — current translation QA
- `.github/workflows/validate.yml` — CI validation
- `overrides/approved-overrides.json` — reviewed override allowlist
- `LICENSE`, `NOTICE` — licensing/attribution

## Still to build

- `scripts/audit_jei.py`
- `scripts/compare_keys.py`
- `scripts/build_release.py`
- verified translation directories for later generations
- final release packaging/build workflow

## Immediate next steps

1. Continue the upstream audit from **Minecraft 1.8.9** and then forward through JEI's historical branches/releases toward `26.2`.
2. For each relevant branch/version, record Minecraft version, JEI version, loader(s), Java requirement/source compatibility, English localization path/format/key count, and upstream locales.
3. Compare each adjacent English localization source to determine exact generation boundaries.
4. Determine whether the completed `g1-mc1.8` translations can be reused partially or fully for 1.8.9 and later versions.
5. Define verified localization generations in `upstream/generations.json`.
6. Determine safe grouped distribution JARs.
7. Only after those audits, build release packaging and runtime-test representative endpoints.
8. Keep this file updated after every significant change.

## Resume prompt for a future ChatGPT conversation

> Reprends le projet JEI Translation Expansion depuis https://github.com/romaintv20-stee-land-More/jei-translation-expansion. Lis d'abord `PROJECT_STATUS.md`, puis `docs/TRANSLATION_STATUS.md`, `docs/VERSION_MATRIX.md`, `docs/WORKFLOW.md` et `docs/TRANSLATION_BENCHMARK.md`. Vérifie l'état actuel de l'upstream `mezz/JustEnoughItems` avant toute modification. Continue à partir des étapes restantes indiquées dans `PROJECT_STATUS.md` et mets ce fichier à jour après chaque changement important.

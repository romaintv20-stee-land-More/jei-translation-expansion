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

**Phase 1 — upstream version/generation audit and translation expansion.**

The selected translation scope is now complete for **Minecraft 1.8** and **Minecraft 1.8.9**. Continue auditing forward through official JEI branches before building final release JARs.

The user does not plan to publish immediately. It is acceptable and preferred to continue auditing/translating versions first, while recording enough metadata for a later reproducible multi-version JAR build phase.

Do not publish a release until version-generation boundaries, loader metadata, Java/runtime requirements, dependency metadata, resource packaging and representative runtime compatibility have been audited.

## Translation policy

1. Protect existing JEI translations by default.
2. For locales already shipped by JEI, add only missing keys unless an override has been explicitly reviewed and allowlisted.
3. For absent locales, provide the complete generation translation set.
4. Reuse translations across generations only when both key and English meaning are unchanged.
5. Preserve placeholders and technical literals exactly.
6. Do not migrate renamed keys blindly.
7. Prefer a documented English fallback over a low-confidence invented translation.
8. AI-assisted translations are allowed but must undergo automated QA and remain open to community/native-speaker correction.
9. Focus on real-world primary languages; exclude novelty/fantasy languages and initially defer most regional/orthographic variants.
10. Copy no unnecessary JEI gameplay/source code; preserve MIT attribution where upstream material is redistributed.

## Minecraft 1.8 / JEI 2.15.0 — translation stage complete

Verified from official upstream branch `1.8`:

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
- Upstream build Java source/target compatibility: `1.7`

No older official JEI branch was found in the initial branch audit, so Minecraft 1.8 remains the oldest current support target.

### 1.8 language scope

The audited Minecraft 1.8 language set contains 75 language codes when `en_US` is included.

Project scope:

- novelty/fantasy excluded: `en_PT`, `qya_AA`, `tlh_AA`
- 12 regional/orthographic variants deferred for now
- 60 primary languages retained
- 6 already supplied by JEI upstream
- addon target: **54 locale files**

Result under `translations/g1-mc1.8/`:

- **54/54 addon locale files present**
- **51 translated / AI-assisted locales**
- **3 documented English fallbacks** because translation confidence was too low:
  - `gv_IM` — Manx
  - `kw_GB` — Cornish
  - `se_NO` — Northern Sami
- the 3 upstream debug-only strings remain English in every addon locale by design

Exact scope: `upstream/minecraft-1.8-language-scope.json`.

### 1.8 benchmark

A five-language pilot (`fr_FR`, `es_ES`, `it_IT`, `pt_BR`, `nl_NL`) measured the small 1.8 translation stage:

- 55 normal translatable keys per locale
- 275 translated entries in the pilot
- translation + initial QA: **1 minute 36 seconds** for five locales
- about **19 seconds per locale** for this small legacy schema

Do not extrapolate this directly to modern JEI, whose English localization contains several hundred entries.

## Minecraft 1.8.9 / JEI 2.28.18 — translation delta complete

Verified from official upstream branch `1.8.9`:

- Minecraft: **1.8.9**
- JEI: **2.28.18**
- Forge: **11.15.1.1855**
- Translation format: legacy `.lang`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- Local source snapshot: `upstream/sources/1.8.9/en_US.lang`
- 75 localization keys total
- JEI upstream locales remain: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- Upstream build Java source/target compatibility: `1.7`

### Exact 1.8 -> 1.8.9 localization diff

Compared with the verified 1.8 English source:

- **46 keys** keep both the same identifier and the same English meaning and are safe to reuse;
- **19 keys added**;
- **2 keys removed**;
- **10 existing keys changed English text/meaning**;
- therefore **29 entries per locale** require a new or explicitly reviewed 1.8.9 translation.

Machine-readable diff: `upstream/diffs/1.8-to-1.8.9.json`.

Because the schema and meanings changed, 1.8.9 is stored as a distinct translation generation rather than being treated as identical to 1.8.

### G2 delta storage

The project intentionally avoids duplicating all 75 strings for every locale.

`translations/g2-mc1.8.9/` contains six TSV batches covering **54/54 addon locale deltas**. Each locale contains exactly the 29 new/changed entries. The 46 proven unchanged translations are inherited from G1 at build time.

At build time, a complete 1.8.9 locale must be reconstructed by:

1. loading the corresponding G1 1.8 locale;
2. removing the two keys removed upstream;
3. applying the locale's 29-entry G2 delta;
4. ordering/validating against `upstream/sources/1.8.9/en_US.lang`;
5. packaging the resulting complete `.lang` resource.

Current G2 result:

- **54/54 locale deltas present**
- **51 translated / AI-assisted locale deltas**
- **3 documented English fallback deltas**: `gv_IM`, `kw_GB`, `se_NO`

The current 1.8.9 translation work deliberately reuses the same 54 primary addon locales selected for 1.8. The exact Mojang 1.8.9 language-asset inventory still needs an independent release-metadata audit before publication; this does not invalidate the verified JEI source/diff or completed translation delta.

## Current localization generations

Generation definitions are machine-readable in `upstream/generations.json`.

### G1 — `g1-mc1.8`

- Minecraft 1.8
- JEI 2.15.0
- 58-key source schema
- full locale files stored under `translations/g1-mc1.8/`

### G2 — `g2-mc1.8.9`

- Minecraft 1.8.9
- JEI 2.28.18
- 75-key source schema
- base generation: G1
- 46 unchanged translations reusable
- +19 keys, -2 keys, 10 changed meanings
- 29-entry locale deltas stored under `translations/g2-mc1.8.9/`

Localization generations are separate from distribution JAR groups. G1 and G2 being distinct does **not** automatically mean two final downloadable JARs are required; that depends on Forge/resource/dependency compatibility and must be decided during packaging audit.

## QA in the repository

### Minecraft 1.8

`scripts/validate_translations.py` validates:

- all 54 expected addon locale files;
- exact key-set parity with the audited English source;
- duplicate keys;
- placeholder parity including `%,d`, `%s`, `%MODNAME`;
- technical-token preservation;
- debug-only strings staying in English;
- English fallback being limited to the three documented low-confidence locales.

### Minecraft 1.8.9

`scripts/validate_1_8_9_delta.py` validates:

- verified 58 -> 75 English-source transition;
- exact diff shape: +19 added, -2 removed, 10 changed meanings, 46 reusable;
- all six delta TSV batches;
- exactly 54 addon locale deltas;
- exactly 29 delta keys per locale;
- placeholder parity;
- important technical literals and search-prefix symbols;
- the three documented fallback locales;
- that the target 1.8.9 key set can be reconstructed from G1 plus the verified delta.

`.github/workflows/validate.yml` runs both validators on pushes and pull requests.

## Modern endpoint already inspected

On upstream branch `26.2`:

- language files are JSON under `Common/src/main/resources/assets/jei/lang/`;
- `en_us.json` is about 28.7 KB and contains several hundred UI/config/tooltips/messages entries;
- existing translations are uneven in completeness;
- for example, some existing languages lag behind newer English keys.

Modern JEI is therefore substantially larger than the 1.8-era translation set and will require more translation/QA time.

## JAR / release strategy

The user intends to keep translating versions now and publish later. That workflow is supported.

Do **not** stop after every Minecraft version to create a final CurseForge-ready JAR. Instead:

1. audit the exact upstream JEI branch/version;
2. snapshot and compare its English localization source;
3. define or extend a verified localization generation;
4. translate only new/changed material when safe reuse is proven;
5. run QA and record loader/Java/dependency metadata;
6. continue to the next version.

Later, once the CurseForge/Modrinth project is ready, implement/use a generic reproducible build pipeline that reconstructs complete locale resources and produces all required Forge/Fabric/NeoForge JARs in one build phase.

Before any publication, still verify:

- loader metadata and minimal entrypoint/stub requirements;
- JEI required dependency ranges;
- whether a resource-only JAR is sufficient for each loader era;
- Minecraft/resource compatibility ranges;
- Java/runtime requirements;
- complete-locale reconstruction from deltas;
- reproducible JAR contents and hashes;
- representative in-game tests, especially oldest/newest endpoints of any grouped artifact.

A prototype old-Forge JAR should eventually be tested before release, but this does not block continuing translation work now.

## Important files

- `README.md` — public project overview
- `PROJECT_STATUS.md` — canonical handoff
- `docs/VERSION_MATRIX.md` — audited version facts
- `docs/WORKFLOW.md` — project workflow
- `docs/TRANSLATION_BENCHMARK.md` — 1.8 translation timing pilot
- `docs/TRANSLATION_STATUS.md` — current language coverage
- `upstream/versions.json` — machine-readable verified/partial version audit
- `upstream/generations.json` — current generation definitions
- `upstream/official-locales.json` — partial upstream locale inventory
- `upstream/minecraft-1.8-language-scope.json` — exact 1.8 language scope/status
- `upstream/sources/1.8/en_US.lang` — audited 1.8 English source
- `upstream/sources/1.8.9/en_US.lang` — audited 1.8.9 English source
- `upstream/diffs/1.8-to-1.8.9.json` — exact localization diff
- `translations/g1-mc1.8/` — 54 full G1 addon locale files
- `translations/g2-mc1.8.9/` — six G2 delta TSV batches covering 54 locales
- `scripts/validate_translations.py` — G1 QA
- `scripts/validate_1_8_9_delta.py` — G2/diff QA
- `.github/workflows/validate.yml` — CI validation for G1 and G2
- `overrides/approved-overrides.json` — reviewed override allowlist
- `LICENSE`, `NOTICE` — licensing/attribution

## Still to build / audit

- `scripts/audit_jei.py`
- `scripts/compare_keys.py`
- generic delta reconstruction/build tooling
- `scripts/build_release.py`
- final loader-specific release packaging/build workflow
- verified translation generations after 1.8.9
- exact Mojang language inventories for release metadata where required
- final runtime compatibility tests

## Immediate next steps

1. Identify and verify the **next official JEI/Minecraft branch after 1.8.9** rather than assuming its target from memory.
2. Record its exact Minecraft version, JEI version, loader, Forge/other loader version, Java compatibility, English source path/key count and official locales.
3. Compare its English key/value set with 1.8.9.
4. Reuse translations only where both key and English meaning remain unchanged.
5. Translate and QA only the new/changed delta where possible.
6. Define the next verified generation only if the source comparison requires one.
7. Continue forward systematically toward modern JEI/26.2.
8. Keep this file updated after every significant audit, translation generation or release/build decision.

## Resume prompt for a future ChatGPT conversation

> Reprends le projet JEI Translation Expansion depuis https://github.com/romaintv20-stee-land-More/jei-translation-expansion. Lis d'abord `PROJECT_STATUS.md`, puis `docs/TRANSLATION_STATUS.md`, `docs/VERSION_MATRIX.md`, `docs/WORKFLOW.md` et `docs/TRANSLATION_BENCHMARK.md`. Vérifie l'état actuel de l'upstream `mezz/JustEnoughItems` avant toute modification. Continue à partir des étapes restantes indiquées dans `PROJECT_STATUS.md`, réutilise les traductions entre générations seulement quand la clé et le sens anglais sont identiques, et mets `PROJECT_STATUS.md` à jour après chaque changement important.

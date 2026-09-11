# JEI Translation Expansion — Project Status

> **Canonical handoff file. Start here in a new chat.**

Last synchronized: **2026-09-11**

## Repository

- Project: **JEI Translation Expansion**
- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Default branch: `main`
- Upstream JEI: https://github.com/mezz/JustEnoughItems
- Upstream CurseForge: https://www.curseforge.com/minecraft/mc-mods/jei
- License: MIT

## Purpose

Create an unofficial localization companion for Just Enough Items (JEI) that adds missing languages and fills missing translation keys across JEI/Minecraft versions while preserving JEI's own translations whenever possible.

The addon adds no gameplay content. It should contain localization resources plus only the minimal loader metadata/stub code required to load those resources.

## Current phase

**Upstream audit + translation expansion.**

Translation work is complete for the selected scope on:

- Minecraft **1.8** / JEI **2.15.0**
- Minecraft **1.8.9** / JEI **2.28.18**

Continue auditing and translating forward through official JEI versions before the final release-build phase. The user does not plan to publish immediately, so it is preferred to keep advancing translations now and generate release JARs later from the audited repository data.

## Fixed release/JAR policy

**One Minecraft version per release JAR.**

Do not group several Minecraft versions into one downloadable JAR, even when their translation schemas are compatible.

Examples of the intended release model:

- one JAR targeting Minecraft 1.8;
- one JAR targeting Minecraft 1.8.9;
- one JAR targeting each later audited Minecraft version.

Translation reuse between versions is still allowed internally. For example, a later generation may inherit unchanged strings from an earlier generation, but the final complete resources must be reconstructed and packaged into that Minecraft version's own JAR.

Loader support must still be audited per Minecraft version. If one physical JAR can safely support all required loaders for the same Minecraft version, that is acceptable; otherwise loader-specific artifacts may be necessary. In every case, a JAR must not claim multiple Minecraft versions.

This decision supersedes earlier ideas about grouped multi-version JARs.

## Translation policy

1. Protect existing JEI translations by default.
2. For locales already shipped by JEI, add only missing keys unless an override has been explicitly reviewed and allowlisted.
3. For absent locales, provide the complete generation translation set.
4. Reuse translations only when both key and English meaning are unchanged.
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
- translation format: legacy `.lang`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- local snapshot: `upstream/sources/1.8/en_US.lang`
- **58** localization keys total
- **55** normal translatable keys
- **3** debug-only description keys intentionally left in English
- JEI upstream locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- upstream Java source/target compatibility: **1.7**

No older official JEI branch was found in the initial audit, so Minecraft 1.8 is the oldest current support target.

### 1.8 language scope

- audited Minecraft language codes including `en_US`: **75**
- novelty/fantasy excluded: `en_PT`, `qya_AA`, `tlh_AA`
- 12 regional/orthographic variants deferred
- retained primary languages: **60**
- already supplied by JEI upstream: **6**
- addon target locale files: **54**

Result under `translations/g1-mc1.8/`:

- **54/54** addon locale files present
- **51** translated / AI-assisted locales
- **3** documented English fallbacks: `gv_IM`, `kw_GB`, `se_NO`

Exact scope: `upstream/minecraft-1.8-language-scope.json`.

## Minecraft 1.8.9 / JEI 2.28.18 — translation delta complete

Verified from official upstream branch `1.8.9`:

- Minecraft: **1.8.9**
- JEI: **2.28.18**
- Forge: **11.15.1.1855**
- translation format: legacy `.lang`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- local snapshot: `upstream/sources/1.8.9/en_US.lang`
- **75** localization keys total
- JEI upstream locales remain: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- upstream Java source/target compatibility: **1.7**

### Exact 1.8 -> 1.8.9 diff

Compared with the verified 1.8 English source:

- **46** keys keep both the same identifier and the same English meaning and are safe to reuse;
- **19** keys added;
- **2** keys removed;
- **10** existing keys changed English text/meaning;
- therefore **29 entries per locale** require a new or reviewed 1.8.9 translation.

Machine-readable diff: `upstream/diffs/1.8-to-1.8.9.json`.

### G2 storage

`translations/g2-mc1.8.9/` stores the verified 29-entry delta for all **54** addon locales instead of duplicating all 75 strings.

At build time, a complete 1.8.9 locale is reconstructed by:

1. loading the matching G1 1.8 locale;
2. removing the two keys removed upstream;
3. applying the 29-entry G2 delta;
4. ordering/validating against the 1.8.9 English source;
5. packaging the resulting complete `.lang` file into the dedicated Minecraft 1.8.9 JAR.

Current G2 result:

- **54/54** locale deltas present
- **51** translated / AI-assisted locale deltas
- **3** documented English fallback deltas: `gv_IM`, `kw_GB`, `se_NO`

## Current localization generations

Generation definitions are stored in `upstream/generations.json`.

### G1 — `g1-mc1.8`

- Minecraft 1.8
- JEI 2.15.0
- 58-key source schema
- full locale files under `translations/g1-mc1.8/`

### G2 — `g2-mc1.8.9`

- Minecraft 1.8.9
- JEI 2.28.18
- 75-key source schema
- base generation: G1
- 46 unchanged translations reusable
- +19 keys, -2 keys, 10 changed meanings
- 29-entry locale deltas under `translations/g2-mc1.8.9/`

Generations are only an internal translation/reuse mechanism. **Final distribution remains one Minecraft version per JAR.**

## QA in repository

### Minecraft 1.8

`scripts/validate_translations.py` validates:

- all 54 expected locale files;
- exact key-set parity;
- duplicate keys;
- placeholder parity including `%,d`, `%s`, `%MODNAME`;
- technical-token preservation;
- debug-only strings staying in English;
- English fallback limited to the three documented low-confidence locales.

### Minecraft 1.8.9

`scripts/validate_1_8_9_delta.py` validates:

- exact 58 -> 75 English-source transition;
- +19 / -2 / 10 changed / 46 reusable diff shape;
- all 54 locale deltas;
- exactly 29 delta keys per locale;
- placeholder and technical-token preservation;
- documented fallback locales;
- successful reconstruction of the target 1.8.9 key set from G1 + G2 delta.

`.github/workflows/validate.yml` runs both validators. The latest validation after completing 1.8.9 passed successfully.

## Modern endpoint already inspected

Upstream branch `26.2` uses JSON language files under `Common/src/main/resources/assets/jei/lang/`.

Its `en_us.json` is about **28.7 KB** and contains several hundred UI/config/tooltips/messages entries, making modern JEI substantially larger than the 1.8-era schemas. Existing upstream translations are uneven in completeness, which makes the project useful both for absent locales and missing keys.

## Release-build workflow

Do not stop translation work after each Minecraft version just to publish a JAR.

For each version now:

1. audit exact JEI/Minecraft/loader/Java metadata;
2. snapshot the real English localization source;
3. compare it with the previous audited version;
4. reuse only proven unchanged translations;
5. translate new/changed material;
6. validate and store the version/generation data;
7. continue to the next Minecraft version.

Later, when the CurseForge/Modrinth project is ready, implement/use `scripts/build_release.py` to reconstruct complete locale resources and generate **one release JAR per Minecraft version**.

Before publication, each version-specific JAR still needs:

- loader metadata verification;
- JEI dependency metadata/range;
- resource-only vs minimal entrypoint/stub decision;
- Java/runtime requirement verification;
- complete locale reconstruction from deltas;
- reproducible contents/hashes;
- representative in-game test for that exact Minecraft version.

## Important files

- `README.md` — public project overview
- `PROJECT_STATUS.md` — canonical handoff
- `docs/VERSION_MATRIX.md` — audited version facts
- `docs/WORKFLOW.md` — workflow and one-version-per-JAR policy
- `docs/TRANSLATION_BENCHMARK.md` — 1.8 timing pilot
- `docs/TRANSLATION_STATUS.md` — language coverage
- `upstream/versions.json` — version audit
- `upstream/generations.json` — generation definitions + JAR policy
- `upstream/official-locales.json` — partial upstream locale inventory
- `upstream/minecraft-1.8-language-scope.json` — exact 1.8 scope
- `upstream/sources/1.8/en_US.lang` — audited 1.8 English source
- `upstream/sources/1.8.9/en_US.lang` — audited 1.8.9 English source
- `upstream/diffs/1.8-to-1.8.9.json` — exact diff
- `translations/g1-mc1.8/` — 54 full G1 locale files
- `translations/g2-mc1.8.9/` — G2 deltas for 54 locales
- `scripts/validate_translations.py` — G1 QA
- `scripts/validate_1_8_9_delta.py` — G2 QA
- `.github/workflows/validate.yml` — CI
- `overrides/approved-overrides.json` — reviewed override allowlist
- `LICENSE`, `NOTICE` — licensing/attribution

## Still to build / audit

- identify and audit the next official JEI/Minecraft version after 1.8.9;
- `scripts/audit_jei.py`;
- `scripts/compare_keys.py`;
- generic delta reconstruction tooling;
- `scripts/build_release.py`;
- version-specific release packaging metadata;
- final runtime compatibility tests.

## Immediate next steps

1. Identify and verify the next official JEI/Minecraft branch after **1.8.9**.
2. Record exact Minecraft version, JEI version, loader, loader version, Java compatibility, English source path/key count and official locales.
3. Compare its English key/value set with 1.8.9.
4. Reuse translations only where both key and English meaning remain unchanged.
5. Translate and QA only the new/changed material where possible.
6. Continue forward systematically toward modern JEI/26.2.
7. Keep this file updated after every significant audit, translation or build-policy decision.

## Resume prompt for a future ChatGPT conversation

> Reprends le projet JEI Translation Expansion depuis https://github.com/romaintv20-stee-land-More/jei-translation-expansion. Lis d'abord `PROJECT_STATUS.md`, puis `docs/TRANSLATION_STATUS.md`, `docs/VERSION_MATRIX.md` et `docs/WORKFLOW.md`. Continue l'audit à partir de la prochaine version après 1.8.9. Réutilise les traductions uniquement quand la clé et le sens anglais sont identiques. Politique de distribution fixe : **un JAR par version Minecraft, jamais un JAR multi-version**. Mets `PROJECT_STATUS.md` à jour après chaque changement important.

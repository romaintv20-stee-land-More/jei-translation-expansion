# JEI Version Matrix

This document tracks verified JEI/Minecraft translation endpoints. It is intentionally incomplete until the full upstream audit is finished.

## Verified endpoints

| Upstream branch | Minecraft | JEI | Loader(s) | Translation format | English keys | Project status |
|---|---:|---:|---|---|---:|---|
| `1.8` | 1.8 | 2.15.0 | Forge | legacy `.lang` | 58 | translation scope complete |
| `1.8.9` | 1.8.9 | 2.28.18 | Forge | legacy `.lang` | 75 | selected scope complete + reproducible prototype JAR builds |
| `1.9` pinned at `b2ffe6b` | 1.9 | 3.3.3 | Forge | legacy `.lang` | 77 | selected 70-language translation/reconstruction scope complete; CI green |
| `1.9` pinned at `bd9fcad` | 1.9.4 | 3.6.8 | Forge | legacy `.lang` | 80 | selected 70-language translation/reconstruction scope complete; CI green |
| `1.10` pinned at `7f4e95d` | 1.10 | 3.7.1 | Forge | legacy `.lang` | 78 | selected 72-language translation/reconstruction scope complete; CI green |
| `26.2` | 26.2 | audit pending exact JEI release | audit pending | JSON | several hundred | partially verified |

## Minecraft 1.8 details

- `mcversion=1.8`
- Forge `11.14.4.1577`
- JEI `2.15.0`
- Java source/target `1.7`
- 58 English keys
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- selected project scope: 60 languages

No upstream `1.7` branch was found in the initial audit, so Minecraft 1.8 is the current oldest support target.

## Minecraft 1.8.9 details

- `mcversion=1.8.9`
- Forge build `11.15.1.1855`; JEI minimum declared Forge `11.15.1.1808`
- JEI `2.28.18`, mod id `JEI`, accepted Minecraft `[1.8.9]`
- Java source/target `1.7`
- 75 English keys = 72 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

### 1.8 -> 1.8.9 localization transition

- 46 unchanged key/value pairs reusable
- 19 new keys
- 2 removed keys
- 10 existing keys with changed English values
- 29 new/reviewed entries per absent addon locale

Exact comparison: `upstream/diffs/1.8-to-1.8.9.json`.

The 54 complete absent-locale files are reconstructable from G1 + G2 with `scripts/reconstruct_1_8_9.py`.

### Existing JEI locale completeness

| Locale | Upstream normal keys | Addon supplement | Combined normal coverage |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

### 1.8.9 prototype packaging

Latest successful static CI build:

- source commit `ef200a1ac1e03b09fd5c3b950c319e8ebf760647`
- workflow run `34632859235`
- JAR `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`
- SHA-256 `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`
- 59 language resources; 64 total JAR entries
- Actions artifact ID `10277785240`

Runtime validation is still required before final promotion to `release-jars/1.8.9/`.

## Minecraft 1.9 / JEI 3.3.3 details

### Correct historical endpoint

The upstream `1.9` branch later transitioned to Minecraft 1.9.4. The exact Minecraft 1.9 endpoint is pinned to:

`b2ffe6bd7734d093006de99f9dc99b2b77ce780d`

At the pinned commit:

- Minecraft `1.9`
- JEI `3.3.3`
- Forge `12.16.0.1865-1.9`
- MCP mappings `snapshot_20160421`
- Java source/target `1.7`
- legacy `.lang`
- English source `upstream/sources/1.9/en_US.lang`
- 77 keys = 74 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### 1.8.9 -> 1.9 localization transition

- 74 unchanged key/value pairs reusable
- 2 added keys
- 0 removed
- 1 changed English value
- inherited addon locales require only a 3-entry delta

Exact comparison: `upstream/diffs/1.8.9-to-1.9.json`.

### Minecraft 1.9 language inventory and policy

- 90 raw language codes
- selected project scope: **70 languages**
- **63 complete addon locales + 5 selected upstream supplements**
- full addon realization: 53 translated / AI-assisted + 10 documented English fallbacks
- successful complete validation run: **34638556534**

Detailed policy/audit:

- `upstream/minecraft-1.9-language-audit.json`
- `upstream/minecraft-1.9-language-scope.json`
- `translations/g3-mc1.9/`

Minecraft uses `no_NO`; JEI 3.3.3 ships `nb_NO`. The project keeps `no_NO` as the Minecraft-facing addon locale and preserves `nb_NO` untouched.

## Minecraft 1.9.4 / JEI 3.6.8 details

### Pinned endpoint

The historical upstream branch `1.9` ends at:

`bd9fcad11a8b92d181fc8c2ec976e31c7467799a`

Verified build metadata:

- Minecraft `1.9.4`
- JEI `3.6.8`
- Forge `12.17.0.1962`
- MCP mappings `snapshot_20160518`
- Java source/target `1.7`
- legacy `.lang`
- English source `upstream/sources/1.9.4/en_US.lang`
- 80 keys = 77 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### 1.9 -> 1.9.4 localization transition

- **76 unchanged key/value pairs reusable**
- **3 added keys**
- **0 removed**
- **1 changed English value**
- four new/reviewed entries per complete addon locale

Added keys:

- `jei.tooltip.cheat.mode`
- `config.jei.advanced.hideLaggyModelsEnabled`
- `config.jei.advanced.hideLaggyModelsEnabled.comment`

Changed value:

- `gui.jei.category.craftingTable`: `Crafting Table` -> `Crafting`

Exact comparison: `upstream/diffs/1.9-to-1.9.4.json`.

### Minecraft language scope

Minecraft 1.9.4 uses the exact same vanilla asset index as the audited Minecraft 1.9 target:

- asset index id `1.9`
- SHA-1 `d7aae43ea69d80cc3441bee4179abd791f6534cd`

Therefore the raw 90-code inventory and the selected **70-language** project scope carry forward unchanged. The output remains **63 complete addon locales** with the same 53 translated / AI-assisted and 10 documented full-English fallback locales.

### JEI 3.6.8 exact upstream completeness

| Locale | Normal present | Missing normal | Addon handling |
|---|---:|---:|---|
| `de_DE` | 53/77 | 24 | exact missing-key supplement |
| `en_US` | 77/77 | 0 | upstream only |
| `fi_FI` | 58/77 | 19 | exact missing-key supplement |
| `fr_FR` | 74/77 | 3 | exact missing-key supplement |
| `ko_KR` | 5/77 | 72 | exact missing-key supplement |
| `nb_NO` | 74/77 | 3 | preserve upstream; not the selected Minecraft locale code |
| `ru_RU` | 73/77 | 4 | exact missing-key supplement |
| `zh_CN` | 74/77 | 3 | exact missing-key supplement |

Only `en_US`, `ru_RU`, and `zh_CN` changed as JEI language files between the pinned 1.9 and 1.9.4 endpoints. The G4 reconstruction deliberately filters older supplements against the exact JEI 3.6.8 missing sets, so translations newly supplied upstream are never duplicated by the addon.

Special semantic review: `ko_KR` still lacks `gui.jei.category.craftingTable` upstream. Its addon-owned value was revised to `제작` to match the new generic English meaning `Crafting` rather than the previous table-specific `Crafting Table`.

### G4 implementation and validation

- source audit: `upstream/minecraft-1.9.4-language-audit.json`
- scope: `upstream/minecraft-1.9.4-language-scope.json`
- delta: `translations/g4-mc1.9.4/delta.tsv`
- policy: `translations/g4-mc1.9.4/policy.json`
- supplement deltas: `translations/g4-mc1.9.4/upstream-supplement-delta/`
- reconstruction: `scripts/reconstruct_1_9_4.py`
- delta QA: `scripts/validate_1_9_4_delta.py`
- complete QA: `scripts/validate_1_9_4_complete.py`
- successful validation workflow run: **34639831977**

The validated target is exactly **63 complete 80-key addon locales + 6 selected missing-key-only upstream supplements**.

No final 1.9.4 JAR has been promoted yet; the project is intentionally continuing version audits/translations first.

## Minecraft 1.10 / JEI 3.7.1 details

### Pinned endpoint

The historical upstream branch `1.10` later changes to Minecraft 1.10.2 at commit `c88aa6c5c078586fa23abaa83309d293cd72ea61`. The last Minecraft 1.10 endpoint is therefore pinned to its parent:

`7f4e95d5b7620a0d304aa73243cd9b3f9737e247`

Verified build metadata:

- Minecraft `1.10`
- JEI `3.7.1`
- Forge `12.18.0.1999-1.10.0`
- MCP mappings `snapshot_20160518`
- Java source/target `1.7`
- legacy `.lang`
- English source `upstream/sources/1.10/en_US.lang`
- 78 keys = 75 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### 1.9.4 -> 1.10 localization transition

- **77 unchanged key/value pairs reusable**
- **0 added keys**
- **2 removed keys**: the two `hideLaggyModels` config entries
- **1 changed English value**: `gui.jei.category.craftingTable`, `Crafting` -> `Crafting Table`

That changed value is an exact return to the G3 Minecraft 1.9 meaning, so G5 restores the already validated G3 translations instead of retranslating. For example, addon-owned `ko_KR` returns from G4 `제작` to G3 `제작대`.

Exact comparison: `upstream/diffs/1.9.4-to-1.10.json`.

### Minecraft 1.10 language inventory and policy

The live Mojang asset-index audit found **94 raw language codes**, four more than Minecraft 1.9/1.9.4:

- `de_AT` — Austrian German: deferred as a regional German variant;
- `haw_US` — Hawaiian: selected as a new primary language;
- `mn_MN` — Mongolian: selected as a new primary language;
- `swg_de` — Oschtallgaierisch: deferred as a regional German/Swabian variety.

The selected scope therefore grows to **72 languages**. The target contains **65 complete addon locales**: 63 inherited from G4 plus new `haw_US` and `mn_MN`. Because reliable full technical translations were not guaranteed in this pass, those two new locales use explicit English fallbacks rather than invented translations. Total complete-locale realization is therefore **53 translated / AI-assisted + 12 documented English fallbacks**.

### JEI 3.7.1 exact upstream completeness

| Locale | Normal present | Missing normal | Addon handling |
|---|---:|---:|---|
| `de_DE` | 53/75 | 22 | exact missing-key supplement |
| `en_US` | 75/75 | 0 | upstream only |
| `fi_FI` | 58/75 | 17 | exact missing-key supplement |
| `fr_FR` | 74/75 | 1 | only `jei.tooltip.cheat.mode` |
| `ko_KR` | 5/75 | 70 | exact supplement; restore G3 Crafting Table wording |
| `nb_NO` | 74/75 | 1 | preserve upstream; not selected Minecraft code |
| `ru_RU` | 73/75 | 2 | only the color-search key/comment pair |
| `zh_CN` | 74/75 | 1 | only `jei.tooltip.cheat.mode` |

The G5 QA fetches the pinned JEI files, checks their Git blob SHAs and requires every generated supplement to equal the exact set of normal keys still absent upstream.

### G5 implementation and validation

- source audit: `upstream/minecraft-1.10-language-audit.json`
- scope: `upstream/minecraft-1.10-language-scope.json`
- policy: `translations/g5-mc1.10/policy.json`
- deterministic reconstruction: `scripts/reconstruct_1_10.py`
- source/scope/upstream QA: `scripts/validate_1_10_delta.py`
- complete QA: `scripts/validate_1_10_complete.py`
- successful validation workflow run: **34641765047**

The validated target is exactly **65 complete 78-key addon locales + 6 exact missing-key-only upstream supplements**.

No final 1.10 JAR has been promoted yet; translation/version auditing continues first.

## Audit rules

For every upstream branch/version added to this table, record actual values from upstream instead of inferring them from the branch name.

Collect where practical:

- English translation key count and adjacent-version semantic diff
- exact Minecraft language inventory
- JEI official locale list and missing-key coverage
- loader/build metadata and Java target
- resource format and path

## Generation rule

Translation generations may inherit from earlier versions only when the key and English meaning are demonstrably unchanged. Release builds must reconstruct and validate complete resources against the exact target version.

## Distribution rule

Project policy is **one Minecraft version per release JAR**. Final runtime-validated artifacts must also be retained under `release-jars/<minecraft-version>/`.

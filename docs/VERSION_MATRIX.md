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
| `1.10` pinned at `446af20` | 1.10.2 | 3.14.8 | Forge | legacy `.lang` | 87 | selected 72-language translation/reconstruction scope complete; CI green |
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

Exact comparison: `upstream/diffs/1.9-to-1.9.4.json`.

Minecraft 1.9.4 uses the same vanilla asset index as 1.9, so the raw 90-code inventory and selected **70-language** scope carry forward unchanged. The validated target is **63 complete 80-key addon locales + 6 selected missing-key-only upstream supplements**. Successful validation workflow run: **34639831977**.

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

### 1.9.4 -> 1.10 localization transition

- **77 unchanged key/value pairs reusable**
- **0 added keys**
- **2 removed keys**
- **1 changed English value**: `gui.jei.category.craftingTable`, `Crafting` -> `Crafting Table`

That changed value is an exact return to the G3 Minecraft 1.9 meaning, so G5 restores the already validated G3 translations instead of retranslating.

Exact comparison: `upstream/diffs/1.9.4-to-1.10.json`.

### Minecraft 1.10 language inventory and policy

The live Mojang asset-index audit found **94 raw language codes**, four more than Minecraft 1.9/1.9.4:

- `de_AT` — deferred regional German variant;
- `haw_US` — selected;
- `mn_MN` — selected;
- `swg_de` — deferred regional German/Swabian variety.

The selected scope grows to **72 languages**. G5 reconstructs **65 complete addon locales** plus **6 exact upstream supplements**. Successful validation workflow run: **34641765047**.

## Minecraft 1.10.2 / JEI 3.14.8 details

### Pinned endpoint

The final Minecraft 1.10.2 endpoint of the historical upstream branch `1.10` is:

`446af20eaa73d260517f0adc737232437363f78d`

Verified directly from upstream build metadata:

- Minecraft `1.10.2`
- JEI `3.14.8`
- Forge `12.18.3.2254`
- MCP mappings `snapshot_20161111`
- Java source/target `1.6`
- legacy `.lang`
- English source `upstream/sources/1.10.2/en_US.lang`
- 87 keys = 84 normal + 3 debug-only
- 23 upstream locale files

The earlier transition commit `c88aa6c5c078586fa23abaa83309d293cd72ea61` is only the first 1.10.2 commit (JEI 3.7.2); it is not the final endpoint used for G6.

### 1.10 -> 1.10.2 localization transition

- **53 unchanged key/value pairs reusable**
- **25 added keys**
- **16 removed keys**
- **9 changed English values**
- **34 added/changed keys require review**

`gui.jei.category.craftingTable` changes from `Crafting Table` back to `Crafting`, exactly matching G4, so that one semantic reversion reuses G4 translations. The other 33 added/changed entries use documented target-English fallback when no already-validated exact-semantic translation exists.

Exact comparison: `upstream/diffs/1.10-to-1.10.2.json`.

### Scope and upstream ownership

Minecraft 1.10.2 uses the exact same asset index as Minecraft 1.10, so:

- raw inventory remains **94 language codes**;
- selected project scope remains **72 languages**.

JEI 3.14.8 expands to 23 upstream locale files. Within the selected scope:

- **20 selected upstream locales** exist;
- **4 are complete upstream**: `de_DE`, `en_US`, `ru_RU`, `uk_UA`;
- **16 are incomplete** and receive exact missing-key-only supplements;
- **52 locales remain addon-owned full files**;
- `en_AU`, `nb_NO`, `zh_TW` are preserved upstream but are not selected matching project locales.

The 16 exact supplement locales are:

`ar_SA`, `bg_BG`, `cs_CZ`, `el_GR`, `es_ES`, `fi_FI`, `fr_FR`, `he_IL`, `it_IT`, `ja_JP`, `ko_KR`, `lt_LT`, `pl_PL`, `pt_BR`, `sv_SE`, `zh_CN`.

### G6 implementation and validation

- source audit: `upstream/minecraft-1.10.2-language-audit.json`
- scope: `upstream/minecraft-1.10.2-language-scope.json`
- policy: `translations/g6-mc1.10.2/policy.json`
- deterministic reconstruction: `scripts/reconstruct_1_10_2.py`
- source/scope/upstream QA: `scripts/validate_1_10_2_delta.py`
- complete QA: `scripts/validate_1_10_2_complete.py`
- successful validation workflow run: **34642956606**

The validated target is exactly **52 complete 87-key addon locale files + 16 exact missing-key-only upstream supplements**, with no addon resource emitted for the four selected locales already complete upstream.

No final 1.10.2 JAR has been promoted yet; translation/version auditing continues first.

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

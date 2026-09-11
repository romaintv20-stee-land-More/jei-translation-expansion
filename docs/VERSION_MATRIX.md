# JEI Version Matrix

This document tracks verified JEI/Minecraft translation endpoints. It is intentionally incomplete until the full upstream audit is finished.

## Verified endpoints

| Upstream branch | Minecraft | JEI | Loader(s) | Translation format | English keys | Project status |
|---|---:|---:|---|---|---:|---|
| `1.8` | 1.8 | 2.15.0 | Forge | legacy `.lang` | 58 | translation scope complete |
| `1.8.9` | 1.8.9 | 2.28.18 | Forge | legacy `.lang` | 75 | selected scope complete + reproducible prototype JAR builds |
| `1.9` pinned at `b2ffe6b` | 1.9 | 3.3.3 | Forge | legacy `.lang` | 77 | selected 70-language translation/reconstruction scope complete; CI green |
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

Latest successful static CI build after strengthening the Forge annotation inspection:

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

This is immediately before transition commit `d6b11a003a4a10702a36f8a97fa28cae883c9360` (`Minecraft 1.9.4: update Forge and MCP mappings`).

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
- 2 added keys: `jei.tooltip.shapeless.recipe`, `key.jei.focusSearch`
- 0 removed
- 1 changed English value: `key.jei.toggleOverlay`
- inherited addon locales require only a 3-entry delta

Exact comparison: `upstream/diffs/1.8.9-to-1.9.json`.

### Minecraft 1.9 language inventory and policy

Automated raw audit: `scripts/audit_1_9.py`; audit workflow run `34635026243`. Permanent raw summary: `upstream/minecraft-1.9-language-audit.json`.

Verified asset inventory:

- 89 external Minecraft `.lang` files
- plus integrated/base `en_US`
- **90 raw language codes**
- 15 codes added compared with the project's Minecraft 1.8 raw scope
- 0 codes removed

New codes:

`be_BY`, `br_FR`, `en_NZ`, `en_UD`, `fo_FO`, `fy_NL`, `gd_GB`, `jbo_EN`, `ksh_DE`, `li_LI`, `lol_US`, `mk_MK`, `so_SO`, `sq_AL`, `tzl_TZL`.

Final project-policy classification:

- selected primary languages: `be_BY`, `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `mk_MK`, `so_SO`, `sq_AL`
- deferred regional variant: `en_NZ`
- novelty exclusions: `en_UD`, `lol_US`
- constructed languages deferred: `jbo_EN`, `tzl_TZL`

The selected Minecraft 1.9 project scope is therefore frozen at **70 languages** in `upstream/minecraft-1.9-language-scope.json`.

### Norwegian identifier audit

Minecraft 1.9 contains `no_NO` and does not contain `nb_NO`; JEI 3.3.3 contains `nb_NO` and not `no_NO`.

Project handling: `no_NO` remains the Minecraft-facing addon locale. JEI's upstream `nb_NO` is preserved as upstream-owned material and is not treated as a replacement unless runtime evidence later proves an alias.

### JEI 3.3.3 upstream completeness

| Locale | Normal present | Missing normal | Addon handling |
|---|---:|---:|---|
| `de_DE` | 53/74 | 21 | missing-key supplement |
| `en_US` | 74/74 | 0 | upstream only |
| `fi_FI` | 58/74 | 16 | missing-key supplement |
| `fr_FR` | 74/74 | 0 | upstream only |
| `ko_KR` | 5/74 | 69 | missing-key supplement |
| `nb_NO` | 74/74 | 0 | preserve upstream; not a Minecraft 1.9 asset code |
| `ru_RU` | 53/74 | 21 | missing-key supplement |
| `zh_CN` | 21/74 | 53 | missing-key supplement |

The selected scope resolves to **63 complete addon locales + 5 partial upstream supplements**. `en_US` and `fr_FR` remain entirely upstream-owned.

### Translation realization

Of the 63 complete addon locales:

- 53 inherit the 1.8.9 translation base and apply the audited three-entry G3 delta;
- the 10 new selected locales have no earlier project base;
- `be_BY`, `mk_MK`, `sq_AL` have full AI-assisted 1.9 drafts;
- `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `so_SO` use explicit documented English fallbacks because reliable full technical translations could not be guaranteed;
- inherited low-confidence fallbacks `gv_IM`, `kw_GB`, `se_NO` also remain English.

Result: **53 translated/AI-assisted complete addon locales + 10 documented English fallback complete locales**, plus the five upstream missing-key-only supplements.

Relevant files:

- `translations/g3-mc1.9/inherited-delta.tsv`
- `translations/g3-mc1.9/upstream-supplement-delta.tsv`
- `translations/g3-mc1.9/new-full-policy.json`
- `scripts/reconstruct_1_9.py`
- `scripts/validate_1_9_delta.py`
- `scripts/validate_1_9_complete.py`

Complete validation workflow run **34638556534** passed all Minecraft 1.9 delta, reconstruction and output QA steps.

No final 1.9 JAR has been promoted yet; auditing may continue to 1.9.4 before runtime packaging is finalized.

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

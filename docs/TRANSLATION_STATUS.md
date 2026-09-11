# Translation Status

## Minecraft 1.8 / JEI 2.15.0

Status: **language-file stage complete for the selected scope**.

- English source: `upstream/sources/1.8/en_US.lang`
- 58 localization keys total
- 55 normal translatable keys
- 3 debug-only description keys intentionally left in English
- addon target: 54 locale files
- 51 translated / AI-assisted locales
- 3 documented English fallbacks: `gv_IM`, `kw_GB`, `se_NO`

All 54 full locale files are under `translations/g1-mc1.8/`.

`scripts/validate_translations.py` validates exact key parity, placeholders, technical tokens, debug-only text, duplicate keys, expected locale files and documented fallbacks.

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected primary-language translation scope complete and prototype packaging buildable**.

### English source and G2 delta

- English source: `upstream/sources/1.8.9/en_US.lang`
- 75 keys = 72 normal + 3 debug-only
- compared with Minecraft 1.8: 46 unchanged, 19 added, 2 removed, 10 changed English values
- 29 translated/reviewed delta entries per absent addon locale

Exact comparison: `upstream/diffs/1.8-to-1.8.9.json`.

`translations/g2-mc1.8.9/` covers all 54 absent addon-locale deltas. `scripts/reconstruct_1_8_9.py` deterministically reconstructs all 54 complete 75-key files and CI verifies them.

- 51 locale deltas translated / AI-assisted
- 3 documented English fallback locales: `gv_IM`, `kw_GB`, `se_NO`

### Completion of upstream JEI locales

| Locale | Upstream normal keys | Addon supplement | Combined |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

The prototype JAR remains non-final until a real Minecraft 1.8.9 + Forge + JEI runtime test is completed.

## Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction stage complete; CI green; version-specific JAR not finalized yet**.

Pinned upstream commit: `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`.

### English/G3 delta

- source: `upstream/sources/1.9/en_US.lang`
- 77 keys = 74 normal + 3 debug-only
- versus 1.8.9: 74 unchanged, 2 added, 0 removed, 1 changed English value
- inherited addon locales require only a 3-entry delta

Exact diff: `upstream/diffs/1.8.9-to-1.9.json`.

### Scope and realization

The verified Minecraft 1.9 raw inventory contains 90 codes. The selected project scope is frozen at **70 real-world primary-language locales** in `upstream/minecraft-1.9-language-scope.json`.

There are **63 addon-owned full locales**:

- 53 inherited from G2;
- 10 newly selected primary locales;
- 53 complete locales translated / AI-assisted;
- 10 complete locales use documented English fallback: `gv_IM`, `kw_GB`, `se_NO`, `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `so_SO`.

JEI 3.3.3 selected-scope upstream handling:

| Locale | Upstream normal | Addon supplement | Combined |
|---|---:|---:|---:|
| `de_DE` | 53/74 | 21 | 74/74 |
| `fi_FI` | 58/74 | 16 | 74/74 |
| `ko_KR` | 5/74 | 69 | 74/74 |
| `ru_RU` | 53/74 | 21 | 74/74 |
| `zh_CN` | 21/74 | 53 | 74/74 |

`en_US` and `fr_FR` are complete upstream. Minecraft uses `no_NO`; JEI ships `nb_NO`, so the project keeps `no_NO` as a separate full addon locale and preserves `nb_NO` untouched.

### Automation and CI

- delta QA: `scripts/validate_1_9_delta.py`
- deterministic reconstruction: `scripts/reconstruct_1_9.py`
- complete output QA: `scripts/validate_1_9_complete.py`
- successful complete validation run: **34638556534**

## Minecraft 1.9.4 / JEI 3.6.8

Status: **selected 70-language translation/reconstruction stage complete; CI green; version-specific JAR not finalized yet**.

Pinned upstream commit: `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`.

Verified build metadata:

- Forge `12.17.0.1962`
- MCP mappings `snapshot_20160518`
- Java source/target `1.7`
- legacy `.lang`

### English/G4 delta

- source: `upstream/sources/1.9.4/en_US.lang`
- 80 keys = 77 normal + 3 debug-only
- versus 1.9: **76 unchanged**, **3 added**, **0 removed**, **1 changed English value**
- four entries require translation/review per complete addon locale

Added keys:

- `jei.tooltip.cheat.mode`
- `config.jei.advanced.hideLaggyModelsEnabled`
- `config.jei.advanced.hideLaggyModelsEnabled.comment`

Changed English meaning:

- `gui.jei.category.craftingTable`: `Crafting Table` -> `Crafting`

Exact diff: `upstream/diffs/1.9-to-1.9.4.json`.

### Scope

Minecraft 1.9.4 points to the exact same asset-index SHA-1 as the audited Minecraft 1.9 target: `d7aae43ea69d80cc3441bee4179abd791f6534cd`.

Therefore:

- raw inventory remains 90 language codes;
- selected project scope remains **70 languages**;
- complete addon target remains **63 locales**;
- the same 53 translated / AI-assisted and 10 documented full-English fallback locales carry forward.

Scope: `upstream/minecraft-1.9.4-language-scope.json`.

### Exact upstream supplement handling

JEI 3.6.8 added many Russian and Simplified Chinese translations upstream. G4 does **not** blindly inherit the old supplement: it rebuilds each supplement from the exact keys still absent in the pinned JEI 3.6.8 files.

| Locale | Upstream normal | Addon supplement | Combined |
|---|---:|---:|---:|
| `de_DE` | 53/77 | 24 | 77/77 |
| `fi_FI` | 58/77 | 19 | 77/77 |
| `fr_FR` | 74/77 | 3 | 77/77 |
| `ko_KR` | 5/77 | 72 | 77/77 |
| `ru_RU` | 73/77 | 4 | 77/77 |
| `zh_CN` | 74/77 | 3 | 77/77 |

`en_US` is complete upstream. `nb_NO` remains upstream-owned and is not treated as a replacement for Minecraft's `no_NO`.

Special checks:

- `fr_FR` receives only the three G4-added keys;
- `ko_KR` still lacks `gui.jei.category.craftingTable` upstream, so its addon translation was revised from the old table-specific wording to `제작` for the new generic `Crafting` meaning;
- `ru_RU` outputs only its four still-missing keys;
- `zh_CN` outputs only its three still-missing keys;
- any obsolete G3 supplement key that JEI 3.6.8 now owns causes G4 QA to fail.

### Automation and CI

- translation delta: `translations/g4-mc1.9.4/delta.tsv`
- policy: `translations/g4-mc1.9.4/policy.json`
- upstream supplement deltas: `translations/g4-mc1.9.4/upstream-supplement-delta/`
- deterministic reconstruction: `scripts/reconstruct_1_9_4.py`
- delta QA: `scripts/validate_1_9_4_delta.py`
- complete QA: `scripts/validate_1_9_4_complete.py`
- successful complete validation run: **34639831977**

The successful run reconstructed and validated exactly **63 complete 80-key addon locale files + 6 missing-key-only upstream supplements**.

## Next version

The next task is to audit the next chronological JEI/Minecraft target after Minecraft 1.9.4. The exact upstream endpoint must be pinned from actual build metadata before any translation inheritance is assumed.

## Release limitation

Minecraft 1.8.9 still requires real runtime validation before final publication. Minecraft 1.9 and 1.9.4 have complete translation/reconstruction data but do not yet have finalized runtime-tested release JARs. Audit/translation work may continue to later Minecraft versions before those JARs are finalized.

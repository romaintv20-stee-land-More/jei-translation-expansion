# Translation Status

## Minecraft 1.8 / JEI 2.15.0

Status: **language-file stage complete for the selected scope**.

- English source: `upstream/sources/1.8/en_US.lang`
- 58 localization keys total
- 55 normal translatable keys
- 3 debug-only description keys intentionally left in English
- Addon target: 54 locale files
- 51 translated / AI-assisted locales
- 3 documented English fallbacks: `gv_IM`, `kw_GB`, `se_NO`

All 54 full locale files are under `translations/g1-mc1.8/`.

`scripts/validate_translations.py` validates exact key parity, placeholders, important technical tokens, debug-only text, duplicate keys, expected locale files and documented fallbacks.

## Minecraft 1.8.9 / JEI 2.28.18

Status: **translation-delta stage complete for the current selected language scope**.

### Source and diff

- Upstream JEI branch: `1.8.9`
- English source snapshot: `upstream/sources/1.8.9/en_US.lang`
- 75 localization keys total
- Compared with Minecraft 1.8:
  - 46 unchanged keys safely reusable from G1
  - 19 new keys
  - 2 removed keys
  - 10 existing keys with changed English text/meaning
  - 29 translated/reviewed delta entries required per addon locale

The exact comparison is stored in `upstream/diffs/1.8-to-1.8.9.json`.

### Translation storage

`translations/g2-mc1.8.9/` contains **6 TSV batches covering 54/54 locale deltas**.

Each locale row contains exactly the 29 keys that are new or semantically changed relative to Minecraft 1.8. At build time the complete 1.8.9 locale is reconstructed by:

1. taking the corresponding G1 locale;
2. removing the 2 keys removed by JEI 1.8.9;
3. applying the 29-entry G2 delta;
4. ordering and validating the result against the 1.8.9 English source.

- **51 locale deltas** are translated / AI-assisted.
- **3 locale deltas** intentionally remain English fallbacks: `gv_IM`, `kw_GB`, `se_NO`.

This avoids duplicating 46 unchanged translations per locale while preserving explicit semantic review where JEI changed the English text.

### QA

`scripts/validate_1_8_9_delta.py` validates:

- the 58 -> 75 English-source transition;
- the exact `+19 / -2 / 10 changed / 46 reusable` diff shape;
- all 6 TSV batches;
- exactly 54 addon locale deltas;
- exactly 29 delta keys per locale;
- formatting placeholder parity;
- important technical literals and search-prefix symbols;
- the three documented English fallback locales;
- that the target 1.8.9 key set can be reconstructed from G1 plus the verified delta.

### Language-scope note

The current 1.8.9 translation work deliberately reuses the same 54 primary addon locales selected for Minecraft 1.8. The exact Mojang Minecraft 1.8.9 language-asset inventory still needs an independent release-metadata audit before publication. This does not change the verified JEI source/diff audit or the completed 54-locale delta work.

## Release limitation

Completing translation files/deltas does **not** mean a release JAR is ready. Before publication the project still needs loader/dependency packaging, full-locale reconstruction, reproducible builds, metadata validation and representative in-game runtime tests.

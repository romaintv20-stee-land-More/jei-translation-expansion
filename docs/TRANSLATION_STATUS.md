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

- Upstream JEI branch: `1.8.9`
- English source snapshot: `upstream/sources/1.8.9/en_US.lang`
- 75 localization keys total
- 72 normal keys + 3 debug-only description keys
- Compared with Minecraft 1.8:
  - 46 unchanged keys safely reusable from G1
  - 19 new keys
  - 2 removed keys
  - 10 existing keys with changed English text/meaning
  - 29 translated/reviewed delta entries required per absent addon locale

The exact comparison is stored in `upstream/diffs/1.8-to-1.8.9.json`.

### 54 locales absent from JEI upstream

`translations/g2-mc1.8.9/` contains 6 TSV batches covering **54/54 locale deltas**.

At build time each complete 1.8.9 locale is reconstructed by `scripts/reconstruct_1_8_9.py` from G1 + G2. CI proves all 54 complete files reconstruct to the exact 75-key target schema.

- **51 locale deltas** are translated / AI-assisted.
- **3 locale deltas** intentionally remain English fallbacks: `gv_IM`, `kw_GB`, `se_NO`.

### Completion of the 5 non-English locales already shipped by JEI

JEI 1.8.9 itself ships `de_DE`, `fi_FI`, `ko_KR`, `ru_RU` and `zh_CN`, but these files do not all contain the full normal 1.8.9 English key set. Their upstream snapshots are stored under:

`upstream/sources/1.8.9/official/`

The addon therefore contains **partial supplement files only for keys missing upstream** under:

`translations/g2-mc1.8.9/upstream-supplements/`

No existing upstream key is intentionally duplicated or overridden.

Validated normal-key coverage:

| Locale | Keys already in JEI | Addon missing-key supplement | Combined normal-key coverage |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

Together with upstream `en_US`, the 54 absent addon locales and these 5 supplements, the project's selected **60 primary-language scope is covered for JEI 1.8.9**. The 3 documented low-confidence addon locales remain English fallbacks by policy.

### QA

The 1.8.9 CI validates:

- exact `+19 / -2 / 10 changed / 46 reusable` G1 -> G2 diff;
- all 54 absent-locale deltas;
- placeholder and technical-token preservation;
- the three documented English fallback locales;
- deterministic reconstruction of all 54 complete absent-locale files;
- official upstream locale snapshots;
- supplements containing **exactly** the normal keys missing from each upstream locale;
- zero overlap between each supplement and its upstream locale;
- 72/72 merged normal-key coverage for all 5 upstream non-English locales.

Validator: `scripts/validate_1_8_9_upstream_supplements.py`.

### Prototype JAR

`.github/workflows/build-1.8.9.yml` successfully builds and inspects a prototype Forge JAR containing:

- 54 complete absent-locale `.lang` files;
- 5 missing-key supplement `.lang` files;
- 59 language resource files total;
- a minimal client-only Forge `@Mod` entrypoint;
- `mcmod.info`, `LICENSE`, `NOTICE` and a deterministic manifest.

Successful prototype build from commit `8100b0bf500a9a98957a090b3b758f99fe07b576`:

- filename: `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`
- SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`
- build workflow run: `34632271287`
- temporary GitHub Actions artifact: `jei-translation-expansion-mc1.8.9-prototype`

This prototype is **not a final release artifact** and is not copied to `release-jars/1.8.9/` yet. An in-game Minecraft 1.8.9 + Forge + JEI runtime test is still required before final promotion.

### Language-scope note

The project currently carries forward the same selected primary-language scope established for Minecraft 1.8. The exact Mojang Minecraft 1.8.9 language-asset inventory still needs an independent release-metadata audit before publication. This does not change the verified JEI source/diff or the completed selected-scope coverage.

## Release limitation

Translation and deterministic prototype building are complete for the selected 1.8.9 scope, but **publication readiness still requires an in-game runtime test** and final promotion of the validated JAR into `release-jars/1.8.9/`.

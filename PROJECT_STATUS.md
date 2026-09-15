# JEI Translation Expansion — Canonical Project Status

Last synchronized: **2026-09-15**

This file is the canonical handoff for continuing the historical JEI localization audit chronologically.

## Fixed project rules

- **One Minecraft version = one dedicated release JAR.** Never group multiple Minecraft versions in one JAR.
- Reuse translation data only when the **localization key and English source value/meaning are identical**.
- Preserve JEI upstream locale keys. For incomplete upstream locales, emit only the exact missing normal keys unless a deliberate override is explicitly approved.
- Preserve placeholders and fixed technical literals exactly.
- Prefer exact target-English fallback over uncertain technical translation.
- Constructed/novelty languages, historical/non-primary forms, and most regional/script variants remain outside the selected primary-language scope unless explicitly reviewed otherwise.
- Runtime-tested final artifacts go only to `release-jars/<minecraft-version>/`.
- Translation/reconstruction QA does **not** imply runtime validation or release promotion.
- Minecraft 1.13+ missing-key-only JSON supplements remain runtime merge-test-gated before release promotion.
- Static-validated candidates are stored in `candidate-jars/<minecraft-version>/`.
- Update this file after every material generation milestone.

## Translation/reconstruction generations

| G | Minecraft | JEI | Pin | Keys | Selected | Full addon | Supplements | Complete upstream | Status |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| G1 | 1.8 | 2.15.0 | branch | 58 | 60 | 54 | — | audited | complete |
| G2 | 1.8.9 | 2.28.18 | branch | 75 | inherited | 54 | 5 | 1 | complete |
| G3 | 1.9 | 3.3.3 | `b2ffe6b` | 77 | 70 | 63 | 5 | 1 | complete |
| G4 | 1.9.4 | 3.6.8 | `bd9fcad` | 80 | 70 | 63 | 6 | 1 | complete |
| G5 | 1.10 | 3.7.1 | `7f4e95d` | 78 | 72 | 65 | 6 | 1 | complete |
| G6 | 1.10.2 | 3.14.8 | `446af20` | 87 | 72 | 52 | 16 | 4 | complete |
| G7 | 1.11 | 4.1.1 | `c9fcc36` | 87 | 72 | 52 | 16 | 4 | complete |
| G8 | 1.11.2 | 4.5.1 | `11023c1` | 93 | 72 | 52 | 19 | 1 | complete |
| G9 | 1.12 | 4.7.5 | `6bce08e` | 93 | 80 | 60 | 18 | 2 | complete |
| G10 | 1.12.1 | 4.7.8 | `7f4160e` | 93 | 80 | 60 | 18 | 2 | complete |
| G11 | 1.12.2 | 4.16.5 | `f98331a` | 115 | 80 | 55 | 24 | 1 | complete |
| G12 | 1.13 | 4.14.4 | `380bc11` | 105 | 83 | 62 | 12 | 9 | complete; runtime gate open |
| G13 | 1.13.2 | 5.0.0 | `2d16f42` | 106 | 87 | 66 | 19 | 2 | complete; runtime gate open |
| G14 | 1.14.2 | 6.0.0 | `f1fd2f1` | 109 | 91 | 70 | 19 | 2 | complete; runtime gate open |
| G15 | 1.14.3 | 6.0.0 | `9e7de1d` | 109 | 91 | 70 | 18 | 3 | complete; runtime gate open |
| G16 | 1.14.4 | 6.0.1 | `de8b6a1` | 109 | 91 | 70 | 16 | 5 | complete; runtime gate open |
| G17 | 1.15.1 | 6.0.0 | `381a0d7` | 109 | 87 | 66 | 16 | 5 | complete; runtime gate open |
| G18 | 1.15.2 | 6.0.2 | `1ea7720` | 110 | 87 | 66 | 18 | 3 | complete; runtime gate open |
| G19 | 1.16.1 | 7.0.1 | `0a0dbfa` | 110 | 88 | 67 | 18 | 3 | complete; runtime gate open |
| G20 | 1.16.2 | 7.3.2 | `df46cef` | 114 | 88 | 67 | 19 | 2 | complete; runtime gate open |
| G21 | 1.16.3 | 7.6.0 | `130181a` | 114 | 88 | 67 | 18 | 3 | complete; runtime gate open |
| G22 | 1.16.4 | 7.6.1 | `8255a01` | 114 | 88 | 67 | 16 | 5 | complete; runtime gate open |
| G23 | 1.16.5 | 7.7.1 | `f6bd6ea` | 119 | 88 | 66 | 15 | 7 | complete; runtime gate open |
| G24 | 1.17.1 | 8.3.0 | `ff99d00` | 141 | 86 | 64 | 21 | 1 | complete; runtime gate open |
| G25 | 1.18 | 9.0.0 | `2df668b` | 141 | 86 | 64 | 21 | 1 | complete; runtime gate open |
| G26 | 1.18.1 | 9.4.1 | `82a6222` | 149 | 86 | 64 | 21 | 1 | complete; runtime gate open |
| G27 | 1.18.2 | 10.1.0 | `530ef6c` | 154 | 86 | 64 | 21 | 1 | complete; runtime gate open |
| G28 | 1.19 | 11.1.1 | `91527b7` | 154 | 86 | 64 | 19 | 3 | complete; candidate packaged |
| G29 | 1.19.1 | 11.2.0 | `90b37d0` | 153 | 86 | 64 | 19 | 3 | complete; candidate packaged |
| G30 | 1.19.2 | 11.5.0 | `01f6136` | 153 | 86 | 64 | 19 | 3 | complete; candidate packaged |
| G31 | 1.19.3 | 12.3.0 | `739fde7` | 156 | 88 | 66 | 21 | 1 | complete; candidate packaged |
| G32 | 1.19.4 | 13.1.0 | `b5b0055` | 156 | 88 | 66 | 20 | 2 | complete; candidate packaged |
| G33 | 1.20 | 14.0.0 | `aa6e142` | 156 | 90 | 68 | 20 | 2 | complete; candidate packaged |
| G34 | 1.20.1 | 15.2.0 | `eecef8a` | 156 | 90 | 68 | 20 | 2 | complete; candidate packaged |
| G35 | 1.20.2 | 16.0.0 | `e78fd19` | 156 | 90 | 68 | 20 | 2 | complete; candidate packaged |
| G36 | 1.20.4 | 17.3.0 | `282f6fa` | 157 | 90 | 67 | 22 | 1 | complete; candidate packaged |
| G37 | 1.20.6 | 18.0.0 | `7cc7d59` | 157 | 90 | 67 | 22 | 1 | complete; candidate packaged |
| G38 | 1.21 | 19.8.2 | `0237023` | 176 | 90 | 67 | 21 | 2 | complete; candidate packaged |
| G39 | 1.21.1 | 19.21.1 | `28eb51f` | 286 | 90 | 64 | 24 | 2 | complete; NeoForge candidate packaged |
| G40 | 1.21.4 | 20.0.0 | `26845e0` | 288 | 90 | 64 | 25 | 1 | complete; NeoForge candidate packaged |
| G41 | 1.21.5 | 21.4.0 | `0772287` | 290 | 90 | 65 | 24 | 1 | complete; NeoForge candidate packaged |
| G42 | 1.21.6 | 22.0.0 | `2a57409` | 289 | 90 | 65 | 24 | 1 | complete; NeoForge candidate packaged |
| G43 | 1.21.7 | 23.1.0 | `ee33b5d` | 291 | 90 | 65 | 23 | 2 | complete; NeoForge candidate packaged |
| G44 | 1.21.8 | 24.2.0 | `2f8e4ec` | 305 | 90 | 65 | 24 | 1 | complete; NeoForge candidate packaged |
| G45 | 1.21.9 | 25.0.1 | `bdfdb4c` | 305 | 90 | 65 | 24 | 1 | complete; NeoForge candidate packaged |
| G46 | 1.21.10 | 26.2.0 | `621ddf0` | 308 | 90 | 64 | 25 | 1 | complete; NeoForge candidate packaged |
| G47 | 1.21.11 | 27.38.0 | `4b6e473` | 334 | 90 | 63 | 26 | 1 | complete; NeoForge candidate packaged |
| G48 | 26.1 | 29.2.0 | `16c0e3b` | 309 | 90 | 64 | 25 | 1 | complete; NeoForge candidate packaged |
| G49 | 26.1.1 | 29.4.0 | `5a2ecc4` | 309 | 90 | 64 | 25 | 1 | complete; NeoForge candidate validated |
| G50 | 26.1.2 | 29.37.0 | `d7c73ed` | 334 | 90 | 63 | 26 | 1 | complete; NeoForge candidate validated |
| G51 | 26.2 | 30.32.0 | `f93563c` | 334 | 90 | 63 | 26 | 1 | complete; NeoForge candidate validated |

## Recent canonical milestones

### G41 — Minecraft 1.21.5 / JEI 21.4.0

- final maintained endpoint `0772287a157beb93f438ee10f88afe402e262856`; the dedicated 1.21.5 branch continued after mainline had moved to 1.21.6
- Minecraft 1.21.5 / NeoForge `21.5.75` / NeoForge minimum `[21.5.74,)` / Java 21
- 290 keys = 284 normal + 6 debug
- G40→G41 semantic delta = 288 unchanged + 2 added + 0 removed + 0 changed-English values
- added keys: `gui.jei.category.grindstone.experience` and `jei.message.missing.recipes.from.server`
- selected scope remains 90
- ownership = 65 addon/full-override + 24 missing-key-only supplements + 1 complete upstream (`en_us`)
- pinned upstream `uk_ua.json` is syntactically malformed; Ukrainian is deliberately emitted as a valid full repair override
- reproducible full QA run `34930359475`, green
- NeoForge packaging-validation run `34930428119`, green
- validated candidate SHA-256 `d07378fa02b78dd7e55c63144030d737a44f1f1dc575a488d88e36915a816638`
- PR #14 merged to `main` as `a769e41b38ec250625631343d2bff25c81580ae0`
- canonical candidate persistence completed in run `34930590379`, commit `b8d2e402abbdaf9be33ad2ec42816454f42c8629`
- candidate: `candidate-jars/1.21.5/jei-translation-expansion-1.0.0-mc1.21.5-neoforge.jar`

### G42 — Minecraft 1.21.6 / JEI 22.0.0

- final 1.21.6 mainline endpoint `2a57409c2af0ce9716749a0329166a41cbcf453f`
- next Minecraft port `8a22d93e6e903142c9dbcdf699496f435d1c569d` targets 1.21.7 and directly follows the G42 endpoint
- build: NeoForge `21.6.20-beta`, minimum `[21.6.20-beta,)`, Java 21
- 289 keys = 283 normal + 6 debug
- G41→G42 semantic delta = 289 unchanged + 0 added + 1 removed + 0 changed-English values
- removed key: `gui.jei.category.grindstone.experience`; it is not emitted by G42-owned resources
- selected scope remains 90; Minecraft live language membership remains 143 codes with no additions/removals
- ownership = 65 addon/full-override + 24 missing-key-only supplements + 1 complete upstream (`en_us`)
- pinned `uk_ua.json` remains malformed and is handled as a deterministic full repair override
- complete frozen-manifest/reconstruction QA run `34931544591`, green
- deterministic NeoForge build/inspection passed in run `34931774000`
- validated candidate SHA-256 `6a1f0262f68189ae064fbc1909792ae41542af8cfdf6c6f5286e5d703c98fdfb`
- canonical candidate: `candidate-jars/1.21.6/jei-translation-expansion-1.0.0-mc1.21.6-neoforge.jar`

### G43 — Minecraft 1.21.7 / JEI 23.1.0

- final 1.21.7 mainline endpoint `ee33b5d69f6cf9167c32c2e84fdc69fa1b008440`
- next Minecraft port `f61efdf5f6604d0d3a55a67cc5d28ec340f189aa` targets 1.21.8 and directly follows the G43 endpoint
- build: NeoForge `21.7.15-beta`, minimum `[21.7.15-beta,)`, Java 21
- 291 keys = 285 normal + 6 debug
- G42→G43 semantic delta = 289 unchanged + 2 added + 0 removed + 0 changed-English values
- added keys: `gui.jei.category.grindstone` and `gui.jei.category.grindstone.experience`
- the reintroduced grindstone-experience key may reuse G41 only for exact same-key/same-English semantics; cross-key reuse remains forbidden
- selected scope remains 90; ownership = 65 addon/full-override + 23 missing-key-only supplements + 2 complete upstream (`en_us`, `zh_cn`)
- pinned `uk_ua.json` remains malformed and is handled as a deterministic full repair override
- complete isolated validation run `34934366667`, green
- deterministic NeoForge package SHA-256 `d6c24f20e8f650c3ee6e52c0c7d6438f2c3972e2271d077fd93802703de82dbd`
- runtime promotion remains separately gated

### G44 — Minecraft 1.21.8 / JEI 24.2.0

- final 1.21.8 mainline endpoint `2f8e4ec2c1e607218eae9b1d9272b87a4dcdb1c8`
- next Minecraft port `1f0f90ee84bb771c25e8118b4cf25aeaf9d26726` targets 1.21.9, making this the final 1.21.8 endpoint
- build: NeoForge `21.8.47`, minimum `[21.8.9,)`, Java 21
- 305 keys = 299 normal + 6 debug
- G43→G44 semantic delta = 290 unchanged + 15 added + 1 removed + 0 changed-English values
- the 15 additions introduce lookup-history configuration/tooltips and split bookmark show/hide tooltips; the old `jei.tooltip.bookmarks` key is removed
- added-key reuse from future JEI data is allowed only for exact same-key/same-English semantics; cross-key reuse remains forbidden
- selected scope remains 90; ownership = 65 addon/full-override + 24 missing-key-only supplements + 1 complete upstream (`en_us`)
- pinned `uk_ua.json` remains malformed and is handled as a deterministic full repair override
- complete isolated validation run `34937513155`, green
- deterministic NeoForge package SHA-256 `277074fdea18ac52e2f1e13601cd206dde847195c0253be1486afacc66f2f9fc`
- runtime promotion remains separately gated

### G45 — Minecraft 1.21.9 / JEI 25.0.1

- final 1.21.9 mainline endpoint `bdfdb4c09026c4fb488805ff729c66ae48ede875`
- next Minecraft port `0999689eb56a4bb3f7061af263de7aef387f0045` targets 1.21.10 and directly follows the G45 endpoint
- build: NeoForge `21.9.2-beta`, minimum `[21.9.2-beta,)`, Java 21
- 305 keys = 299 normal + 6 debug
- G44→G45 semantic delta = 297 unchanged + 8 added + 8 removed + 0 changed-English values
- eight JEI key-category localization IDs move from `jei.key.category.*` to `key.category.jei.*`; matching English meanings do not permit cross-key translation reuse
- selected scope remains 90; ownership = 65 addon/full-override + 24 supplement locales + 1 complete upstream (`en_us`)
- pinned `uk_ua.json` remains malformed and is handled as a deterministic full repair override
- 89 pinned upstream-owned values across incomplete locales fail exact placeholder/technical-literal preservation; only this frozen key set receives explicit safe same-key/English overrides, while all other upstream-owned keys remain preserved
- exact future-donor reuse for the eight added IDs is allowed only for same key + same English semantics
- complete fixed reconstruction QA run `34959813095`, green
- deterministic NeoForge candidate SHA-256 `2042e85d9781b93f1b5fd730a77ea9c8b670ad823b9ea1472c28e03aa0632d88`
- runtime promotion remains separately gated

### G46 — Minecraft 1.21.10 / JEI 26.2.0

- final 1.21.10 mainline endpoint `621ddf003a8eceffcba0fd808a955e280f87a4c0`
- next Minecraft port `6b615d15ef776abf139339779985a91c59c9c324` targets 1.21.11 and is directly parented by the G46 endpoint; upstream explicitly marks 1.21.11 as Maven-only
- build: NeoForge `21.10.64`, minimum `[21.9.2-beta,)`, Java 21
- 308 keys = 302 normal + 6 debug
- G45→G46 semantic delta = 305 unchanged + 3 added + 0 removed + 0 changed-English values
- added keys: `jei.config.client.tooltips.enableRecipesGuiIngredientsSummary`, `jei.config.client.tooltips.enableRecipesGuiIngredientsSummary.description`, and `jei.tooltip.recipe.tooltips.craft.ingredients`
- selected scope remains 90; ownership = 64 addon-full locales + 25 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- `uk_ua` is valid upstream again in G46 and returns to supplement ownership instead of a full repair override
- 92 frozen upstream-owned values require literal-safety overrides; all emitted/combined values preserve required placeholders and fixed technical literals
- deterministic NeoForge candidate SHA-256 `f0370c0a9bd5bc26d98ae624237a0b39a14c275eeaf54964ffd2c8caef223f8d`
- final packaging-validation run `34964123873`, green
- canonical candidate persistence run `35002178659`, green
- candidate: `candidate-jars/1.21.10/jei-translation-expansion-1.0.0-mc1.21.10-neoforge.jar`
- runtime promotion remains separately gated

### G47 — Minecraft 1.21.11 / JEI 27.38.0

- first 1.21.11 port `6b615d15ef776abf139339779985a91c59c9c324` directly follows G46 and historically stated that JEI 1.21.11 would be Maven-only
- historical mainline 1.21.11 endpoint `1d37cb1a1cf7139170d214adef128f405b865312`; mainline then moves to `d395fda29b10f09b860d5a6221b459050f5071d3` (`26.1-snapshot-1`)
- maintained dedicated 1.21.11 branch endpoint `4b6e47334ac4aaeae51d15facbb38c42cb511321` is the canonical G47 source because maintenance continued after mainline moved on
- maintained build: NeoForge `21.11.45`, minimum `[21.11.44,)`, Java 21, JEI specification version `27.38.0`
- 334 keys = 328 normal + 6 debug
- G46→maintained-G47 semantic delta = 291 unchanged + 37 added + 11 removed + 6 changed-English values
- translation inheritance is allowed only for exact same-key/same-English semantics; cross-key reuse remains forbidden
- project-owned added or changed meanings use exact target English unless a safe target-upstream translation already owns that key
- selected scope remains 90; ownership = 63 addon-full locales + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- all selected upstream JSON files are syntactically valid at the maintained endpoint; `fil_ph` and `uk_ua` are valid incomplete upstream supplement locales
- 91 upstream-owned values require frozen literal-safety overrides so placeholders and fixed technical literals remain exact
- the maintained branch has normal CurseForge project `238222` and Modrinth project `u6dRKJwZ` publication configuration, superseding the first-port Maven-only limitation for current maintained releases
- isolated maintained-endpoint reconstruction validation run `35006503247`, green
- dedicated NeoForge candidate packaging is complete and persisted on `main`
- canonical candidate SHA-256 `9bfb53fd798ed9afc85060072c50bfff980a2ce87cacb6a2aa053cbec833c3d8`
- candidate: `candidate-jars/1.21.11/jei-translation-expansion-1.0.0-mc1.21.11-neoforge.jar`


### G48 — Minecraft 26.1 / JEI 29.2.0

- final exact-26.1 endpoint `16c0e3b3fcb8cd4093617a691de6f3d1c137e1ca`
- first 26.1 release commit `9de18f504f357be537c5de24cac408b51ca9d8b1`; next patch support commit `b1ebe15147adb0bded6f3e5ccf86b35124fa5929` targets 26.1.1 and directly follows the G48 endpoint
- build: NeoForge `26.1.0.8-beta`, minimum `[26.1.0.8-beta,)`, Java 25
- 309 keys = 303 normal + 6 debug
- G47→G48 semantic delta = 294 unchanged + 9 added + 34 removed + 6 changed-English values
- selected scope remains 90; ownership = 64 addon-full locales + 25 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- all selected upstream JSON files are syntactically valid; `uk_ua` is a valid incomplete supplement locale with 4 missing normal keys
- 92 frozen upstream-owned values require literal-safety overrides
- complete finalization/build run `35014496588`, green
- canonical persistence run `35016479980`, green
- candidate SHA-256 `1b99b64f7d1696570ac93cd7f5bc721013b1b300a9c308cc4a08612802b921fd`
- candidate: `candidate-jars/26.1/jei-translation-expansion-1.0.0-mc26.1-neoforge.jar`
- runtime promotion remains separately gated

### G49 — Minecraft 26.1.1 / JEI 29.4.0

- first 26.1.1 commit `b1ebe15147adb0bded6f3e5ccf86b35124fa5929` directly follows G48; final 26.1.1 endpoint `5a2ecc40c438e9137a8b64b2d9b48c095fc24c23`
- next patch commit `481a64808dab4ea205772a7289cc766804f5f5d7` targets Minecraft 26.1.2 and directly follows the G49 endpoint
- build: NeoForge `26.1.1.1-beta`, minimum `[26.1.0.8-beta,)`, Java 25
- 309 keys = 303 normal + 6 debug
- G48→G49 semantic delta = 309 unchanged + 0 added + 0 removed + 0 changed-English values
- selected scope remains 90; ownership = 64 addon-full locales + 25 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- Minecraft language membership remains 143 codes with no additions/removals
- all selected upstream JSON files are syntactically valid; `uk_ua` remains a valid supplement locale with 4 missing normal keys
- 92 frozen upstream-owned values require literal-safety overrides; cross-key reuse remains forbidden
- complete isolated reconstruction validation run `35017320214`, green
- deterministic Java-25 NeoForge finalization/build run `35017623490`, green
- validated candidate SHA-256 `401e6dea929125a537565d6a54e4a805e976217e97dbb9a31b1d5065cfa9e0d8`
- canonical candidate persistence will follow merge to `main`; runtime promotion remains separately gated

### G50 — Minecraft 26.1.2 / JEI 29.37.0

- first 26.1.2 support commit `481a64808dab4ea205772a7289cc766804f5f5d7` directly follows the G49 endpoint
- maintained JEI `26.1` branch snapshot pinned at `d7c73ed63a7a25a9ad416428eafef3a3dcf0f1c8` for reproducibility; this is a maintained snapshot, not claimed as a historical final endpoint
- build: NeoForge `26.1.2.99`, minimum `[26.1.2.99,)`, Java 25
- 334 keys = 328 normal + 6 debug
- G49→G50 semantic delta = 294 unchanged + 34 added + 9 removed + 6 changed-English values
- translation reuse remains limited to exact same-key/same-English meanings; the 40 added/changed meanings fall back to exact target English when not already owned by upstream
- selected scope remains 90; ownership = 63 addon-full locales + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- `fil_ph` moves from add-on full ownership to an incomplete upstream supplement locale
- Minecraft language membership remains 143 codes with no additions/removals
- all selected upstream JSON files are syntactically valid at the pinned snapshot
- 91 upstream-owned values require frozen literal-safety overrides so placeholders and fixed technical literals remain exact
- isolated complete reconstruction validation run `35020580691`, green
- deterministic Java-25 NeoForge candidate SHA-256 `cabbd6dfbb9b45d2be04edcf1116e140ed4b3c088fc9204d0c7a85c47f79ae89`
- runtime promotion remains separately gated

### G51 — Minecraft 26.2 / JEI 30.32.0

- first 26.2 support commit `71d31cea392876a8414426e15f6f31f1b40ca9cc` follows parent `79442458a4bc67ccb7d8925986c2d81e4cd2b7ff`
- maintained JEI `26.2` branch snapshot pinned at `f93563ca4965d511bd07d4f041b3a6ddd1158ef0` for reproducibility; this is an actively maintained snapshot, not claimed as a historical final endpoint
- build: NeoForge `26.2.0.69`, minimum `[26.2.0.67,)`, Java 25
- 334 keys = 328 normal + 6 debug
- G50→G51 semantic delta = 334 unchanged + 0 added + 0 removed + 0 changed-English values
- all translation reuse is exact same-key/same-English reuse from G50; cross-key reuse remains forbidden
- selected scope remains 90; ownership = 63 addon-full locales + 26 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- Minecraft language membership remains 143 codes with no additions/removals
- all selected upstream JSON files are syntactically valid at the pinned snapshot
- frozen literal-safety overrides preserve placeholders and fixed technical literals for unsafe upstream-owned values
- isolated complete reconstruction validation run `35022849550`, green
- deterministic Java-25 NeoForge packaging/finalization run `35023833664`, green
- validated candidate SHA-256 `b3d3a30c23b4a9c3080ed49781fa51df17c024fdf67bdde6c2d467649230824f`
- runtime promotion remains separately gated

## Candidate packaging state

- The canonical candidate inventory on `main` contains **50 version-specific 1.0.0 candidates through Minecraft 26.1.2**.
- G51 / Minecraft 26.2 has passed complete static reconstruction and deterministic Java-25 NeoForge candidate validation; canonical persistence follows its merge to `main`.
- Candidate JARs are not runtime-promoted finals.

## Current next target

- Merge G51 and persist `candidate-jars/26.2/jei-translation-expansion-1.0.0-mc26.2-neoforge.jar` using the validated candidate digest above.
- Because JEI actively maintains Minecraft 26.2 on branch `26.2`, re-audit that branch before declaring a later 26.2 snapshot or selecting the next chronological Minecraft target.
- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.

## Documentation synchronization debt

- `PROJECT_STATUS.md`, `packaging/completed-versions.json`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through validated G51 on the work branch.
- README / version-matrix / translation-status prose may lag the canonical generation line and should be refreshed before a public documentation release.

## Release gates still open

- Minecraft 1.8.9 prototype/runtime lineage still requires a real client runtime validation before final release promotion.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.
- NeoForge candidates G39–G51 remain static candidates until their version-specific runtime checks are complete.

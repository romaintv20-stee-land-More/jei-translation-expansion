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
| G42 | 1.21.6 | 22.0.0 | `2a57409` | 289 | 90 | 65 | 24 | 1 | complete; NeoForge packaging validated |
| G43 | 1.21.7 | 23.1.0 | `ee33b5d` | 291 | 90 | 65 | 23 | 2 | complete; NeoForge packaging validated |
| G44 | 1.21.8 | 24.2.0 | `2f8e4ec` | 305 | 90 | 65 | 24 | 1 | complete; NeoForge packaging validated |

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
- packaging metadata and synchronized upstream registries are being finalized before merge

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

## Candidate packaging state

- The canonical candidate inventory on `main` contains **43 version-specific 1.0.0 candidates through Minecraft 1.21.7**.
- G44 has passed complete translation/reconstruction QA and deterministic NeoForge packaging on the work branch; canonical `candidate-jars/1.21.8/` persistence follows merge to `main`.
- Candidate JARs are not runtime-promoted finals.

## Current next target

- Merge the completed G44 / Minecraft 1.21.8 work and let the main packaging workflow persist its NeoForge candidate.
- The chronological next audit target is **G45 = Minecraft 1.21.9**.
- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.

## Documentation synchronization debt

- `PROJECT_STATUS.md`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through completed G44.
- `README.md`, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` should be synchronized through G44 before final public release preparation.

## Release gates still open

- Minecraft 1.8.9 prototype/runtime lineage still requires a real client runtime validation before final release promotion.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.
- G39–G44 NeoForge candidates remain static candidates until their version-specific runtime checks are complete.

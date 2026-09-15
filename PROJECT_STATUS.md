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
| G41 | 1.21.5 | 21.4.0 | `0772287` | 290 | 90 | 65 | 24 | 1 | complete; NeoForge packaging validated |

## Recent canonical milestones

### G39 — Minecraft 1.21.1 / JEI 19.21.1

- final endpoint `28eb51f58d2798512a2ef75cf8b29189228573ad`
- Minecraft 1.21.1 / NeoForge `21.1.116` / Java 21
- 286 keys = 280 normal + 6 debug
- selected scope remains 90
- ownership = 64 addon-full + 24 missing-key-only supplements + 2 complete upstream (`en_us`, `ja_jp`)
- full clean G1→G39 validation after the G14 technical-token boundary fix: run `34908672666`, green
- G14→G39 candidate refresh/persist: run `34927435585`, all 26 builds plus persistence green
- static candidate: `candidate-jars/1.21.1/jei-translation-expansion-1.0.0-mc1.21.1-neoforge.jar`

### G40 — Minecraft 1.21.4 / JEI 20.0.0

- final endpoint `26845e0d2a248b0084481b4a433ef7b32152d4c6`, immediately before the JEI Minecraft 1.21.5 port `2cc5d1e8b7fb4f79c917804d7582bb7c48374499`
- Minecraft 1.21.4 / NeoForge `21.4.136` / NeoForge minimum `[21.4.121,)` / Java 21
- 288 keys = 282 normal + 6 debug
- G39→G40 semantic delta = 285 unchanged + 3 added + 1 removed + 0 changed-English values
- removed key: `gui.jei.category.fuel`; added keys: `gui.jei.category.smelting_fuel`, `gui.jei.category.smoking_fuel`, `gui.jei.category.blasting_fuel`
- selected scope remains 90; ownership = 64 full + 25 supplements + 1 complete upstream (`en_us`)
- isolated QA run `34928320930`, green; packaging-validation run `34928413594`, green
- canonical static candidate is persisted at `candidate-jars/1.21.4/jei-translation-expansion-1.0.0-mc1.21.4-neoforge.jar`

### G41 — Minecraft 1.21.5 / JEI 21.4.0

- final maintained endpoint `0772287a157beb93f438ee10f88afe402e262856`; the dedicated 1.21.5 branch continued after mainline had moved to 1.21.6
- Minecraft 1.21.5 / NeoForge `21.5.75` / NeoForge minimum `[21.5.74,)` / Java 21
- 290 keys = 284 normal + 6 debug
- G40→G41 semantic delta = 288 unchanged + 2 added + 0 removed + 0 changed-English values
- added keys: `gui.jei.category.grindstone.experience` and `jei.message.missing.recipes.from.server`
- selected scope remains 90
- ownership = 65 addon/full-override + 24 missing-key-only supplements + 1 complete upstream (`en_us`)
- pinned upstream `uk_ua.json` is syntactically malformed; Ukrainian is deliberately emitted as a valid full repair override that preserves repaired upstream target values and safely fills only missing same-key semantics
- reproducible full QA run `34930359475`, green
- NeoForge packaging-validation run `34930428119`, green
- validated candidate SHA-256: `d07378fa02b78dd7e55c63144030d737a44f1f1dc575a488d88e36915a816638`
- PR #14 merged to `main` as `a769e41b38ec250625631343d2bff25c81580ae0`
- canonical `candidate-jars/1.21.5/` persistence is handled by the main packaging workflow and was still queued at the last synchronization point

## Candidate packaging state

- The canonical candidate inventory on `main` currently contains **40 version-specific 1.0.0 candidates through Minecraft 1.21.4**.
- G41 / Minecraft 1.21.5 has a green deterministic NeoForge packaging validation; canonical persistence is pending the queued main packaging workflow.
- Candidate JARs are not runtime-promoted finals.

## Current next target

- **G42 = Minecraft 1.21.6 / JEI 22.0.0**.
- final 1.21.6 mainline endpoint: `2a57409c2af0ce9716749a0329166a41cbcf453f` (`Update to Minecraft 1.21.6`).
- the next Minecraft port is `8a22d93e6e903142c9dbcdf699496f435d1c569d` (`Update to Minecraft 1.21.7`) and its direct parent is the G42 endpoint, so the endpoint boundary is exact.
- build metadata at the endpoint: NeoForge `21.6.20-beta`, Java 21, JEI specification `22.0.0`.
- preliminary English delta from G41: 289 surviving key/value meanings unchanged, 0 added, 1 removed, 0 changed; removed key is `gui.jei.category.grindstone.experience`.
- G42 audit/bootstrap/reconstruction validation is in progress on `work/g42-mc1.21.6-audit`.
- Keep all static candidates outside `release-jars/` until their runtime gates are satisfied.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need broad synchronization through the latest completed generations. `README.md` also needs synchronization through G41/G42 once G42 is finalized.

## Release gates still open

- Minecraft 1.8.9 prototype/runtime lineage still requires a real client runtime validation before final release promotion.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.
- G39, G40 and G41 NeoForge candidates remain static candidates until their version-specific runtime checks are complete.

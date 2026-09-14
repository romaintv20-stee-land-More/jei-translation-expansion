# JEI Translation Expansion — Canonical Project Status

Last synchronized: **2026-09-14**

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

## Recent canonical milestones

### G31 — Minecraft 1.19.3 / JEI 12.3.0

- endpoint `739fde73225d006c83af22db04c5723d9c539dc7`
- 156 keys = 150 normal + 6 debug; G30→G31 adds 3 normal keys
- selected historical scope grows 86→88 with Nahuatl (`nah`) and Rusyn (`ry_ua`)
- ownership = 66 addon-full + 21 supplements + 1 complete upstream

### G32 — Minecraft 1.19.4 / JEI 13.1.0

- endpoint `b5b00557f5df18c35e545e3cc8cd65ca4b975ba1`
- all 156 English semantics unchanged from G31
- selected scope remains 88
- ownership = 66 addon-full + 20 supplements + 2 complete upstream; `uk_ua` becomes complete upstream
- candidate: `candidate-jars/1.19.4/jei-translation-expansion-1.0.0-mc1.19.4-forge.jar`

### G33 — Minecraft 1.20 / JEI 14.0.0

- endpoint `aa6e14229c0c44cd685ac6b4d1d7f513360da18a`
- Forge `46.0.1`, Parchment `1.19.3-2023.03.12-1.19.4`, Java 17
- all 156 English semantics unchanged from G32
- selected historical scope grows 88→90 with Lao (`lo_la`) and Yakut (`sah_sah`)
- ownership = 68 addon-full + 20 supplements + 2 complete upstream
- complete QA run `34812895012`, metadata rerun `34813134898`
- PR #3 merged as `e78dc4de3f028e8ecc97a288369fa2f73c61eee2`
- packaging run `34813374412` green
- candidate: `candidate-jars/1.20/jei-translation-expansion-1.0.0-mc1.20-forge.jar`

### G34 — Minecraft 1.20.1 / JEI 15.2.0

- final endpoint `eecef8ae335701b97a6918e20b4dd87966a46dfa`, immediately before `e78fd195...` (`Update to Minecraft 1.20.2`)
- Forge `47.0.1`, Parchment `1.19.3-2023.03.12-1.20.1`, Java 17
- 156 keys = 150 normal + 6 debug; **all 156 English semantics unchanged from G33**
- Minecraft 1.20 and 1.20.1 use the same asset index `5` (`0dd020f0d45d336531ce00c14065ef6dd01b9bc5`) and 143 language files
- selected scope remains 90; no language additions/removals
- ownership remains 68 addon-full + 20 supplements + 2 complete upstream (`en_us`, `uk_ua`)
- 37 translated/AI-assisted addon-full locales + 31 documented complete-English fallback locales
- isolated complete QA run `34875502127`, job `104081567846`, green
- metadata-recording rerun `34875868343`, job `104082770963`, green
- PR #4 merged as `6269b70a3b607ec589b20509a743e7c21e35ea91`
- packaging run `34876314002` green; build, bundle, and persistence all succeeded
- candidate: `candidate-jars/1.20.1/jei-translation-expansion-1.0.0-mc1.20.1-forge.jar`

## Current next target

- **G35 = Minecraft 1.20.2**.
- first upstream 1.20.2 port commit: `e78fd1951c38770de8462ead2187e565fe2996eb` (`Update to Minecraft 1.20.2`), whose parent is the final G34 endpoint.
- Resolve the **final** JEI 1.20.2 endpoint before the next Minecraft-version port, then repeat source/scope/ownership/reconstruction QA.
- Keep G34 and earlier candidates outside `release-jars/` until their runtime gates are satisfied.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before final release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

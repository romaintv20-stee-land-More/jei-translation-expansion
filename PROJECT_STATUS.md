# JEI Translation Expansion — Canonical Project Status

Last synchronized: **2026-09-13**

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
- Update this file after every material generation milestone.

## Translation/reconstruction generations

| G | Minecraft | JEI | Pin | Keys | Selected | Full addon | Supplements | Complete upstream | CI |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| G1 | 1.8 | 2.15.0 | branch | 58 | 60 | 54 | — | audited | complete |
| G2 | 1.8.9 | 2.28.18 | branch | 75 | inherited | 54 | 5 | 1 | prototype `34632859235` |
| G3 | 1.9 | 3.3.3 | `b2ffe6b` | 77 | 70 | 63 | 5 | 1 | `34638556534` |
| G4 | 1.9.4 | 3.6.8 | `bd9fcad` | 80 | 70 | 63 | 6 | 1 | `34639831977` |
| G5 | 1.10 | 3.7.1 | `7f4e95d` | 78 | 72 | 65 | 6 | 1 | `34641765047` |
| G6 | 1.10.2 | 3.14.8 | `446af20` | 87 | 72 | 52 | 16 | 4 | `34642956606` |
| G7 | 1.11 | 4.1.1 | `c9fcc36` | 87 | 72 | 52 | 16 | 4 | `34644034423` |
| G8 | 1.11.2 | 4.5.1 | `11023c1` | 93 | 72 | 52 | 19 | 1 | `34644712028` |
| G9 | 1.12 | 4.7.5 | `6bce08e` | 93 | 80 | 60 | 18 | 2 | `34668113754` |
| G10 | 1.12.1 | 4.7.8 | `7f4160e` | 93 | 80 | 60 | 18 | 2 | `34668344181` |
| G11 | 1.12.2 | 4.16.5 | `f98331a` | 115 | 80 | 55 | 24 | 1 | `34668803121` |
| G12 | 1.13 | 4.14.4 | `380bc11` | 105 | 83 | 62 | 12 | 9 | `34671542080` |
| G13 | 1.13.2 | 5.0.0 | `2d16f42` | 106 | 87 | 66 | 19 | 2 | `34671958137` |
| G14 | 1.14.2 | 6.0.0 | `f1fd2f1` | 109 | 91 | 70 | 19 | 2 | `34677329178` |
| G15 | 1.14.3 | 6.0.0 | `9e7de1d` | 109 | 91 | 70 | 18 | 3 | `34677627657` |
| G16 | 1.14.4 | 6.0.1 | `de8b6a1` | 109 | 91 | 70 | 16 | 5 | `34678167977` |
| G17 | 1.15.1 | 6.0.0 | `381a0d7` | 109 | 87 | 66 | 16 | 5 | `34709161680` |
| G18 | 1.15.2 | 6.0.2 | `1ea7720` | 110 | 87 | 66 | 18 | 3 | `34709639659` |
| G19 | 1.16.1 | 7.0.1 | `0a0dbfa` | 110 | 88 | 67 | 18 | 3 | `34712320469` |
| G20 | 1.16.2 | 7.3.2 | `df46cef` | 114 | 88 | 67 | 19 | 2 | `34712876829` |
| G21 | 1.16.3 | 7.6.0 | `130181a` | 114 | 88 | 67 | 18 | 3 | `34724333790` |
| G22 | 1.16.4 | 7.6.1 | `8255a01` | 114 | 88 | 67 | 16 | 5 | `34742453589` |
| G23 | 1.16.5 | 7.7.1 | `f6bd6ea` | 119 | 88 | 66 | 15 | 7 | `34743463506` |
| G24 | 1.17.1 | 8.3.0 | `ff99d00` | 141 | 86 | 64 | 21 | 1 | isolated `34744097497`; canonical pending |

## G23 — Minecraft 1.16.5 / JEI 7.7.1 — completed

- final endpoint `f6bd6ea033084f3d18ad256c9921641dcbd0330f`
- Forge `36.2.0`, mappings `official / 1.16.5`, Java 8 via Gradle toolchain
- 119 keys = 113 normal + 6 debug
- G22→G23 = **113 unchanged + 6 added + 1 removed + 0 changed values**
- Minecraft raw/selected = **125 / 88**
- JEI upstream = 25 locales
- ownership = **66 addon-full + 15 supplements + 7 complete upstream**
- complete upstream: `en_us`, `it_it`, `ko_kr`, `ru_ru`, `sv_se`, `tr_tr`, `zh_cn`
- `id_id` moved addon-full → upstream-incomplete; `pl_pl` and `pt_br` each need the two new category-navigation keys
- no cross-key reuse from removed `jei.message.ftbguilib` to new `jei.message.ftblibrary`
- isolated full QA `34743332585` green
- definitive full G1→G23 CI **`34743463506`** green

## G24 — Minecraft 1.17.1 / JEI 8.3.0 — isolated QA complete

Historical endpoint/build:
- commit `75d2fd9ec0d5e911bfdaf8e4be9ac5ff4b860024`, titled `Port to 1.17`, actually jumps directly from Minecraft 1.16.5 to **1.17.1**; there is no separate Minecraft 1.17 generation to invent
- final 1.17.1 endpoint is **`ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7`**, the parent-side endpoint before `2df668b5ac4a8473b9837ad2785d0f5a4fb845a6` ports to Minecraft 1.18
- JEI `8.3.0`, Forge `37.0.104`, mappings `official / 1.17.1`, Java 16
- pinned English blob SHA `abd5d9b6b1e17f61ddcdc0b2a20e7f6d3f604b7e`

English/source delta:
- 141 keys = **135 normal + 6 debug**
- G23→G24 = **87 unchanged + 24 added + 2 removed + 30 changed values**
- one changed value is debug-only, so **53 normal added-or-changed meanings** were reviewed
- only exact unchanged key+English pairs may inherit G23 values
- all added/changed project-owned meanings use exact G24 target English
- removed keys are not emitted and cross-key reuse is forbidden

Minecraft scope:
- asset index changes to id `1.17`, SHA1 `f425401a00adf0112fde624ee80c66333530f8a1`
- raw language inventory **125 → 123**
- added code: `zlm_arab`
- removed codes: `gv_im`, `mi_nz`, `swg`
- `gv_im` and `mi_nz` were selected, so selected scope **88 → 86**
- `zlm_arab` is deferred as a Malay Jawi/Arabic-script variant because primary Malay `ms_my` is already selected

JEI ownership:
- JEI still ships 25 upstream JSON locales
- ownership = **64 addon-full + 21 supplements + 1 complete upstream**
- only selected complete upstream locale: `en_us`
- `it_it`, `ko_kr`, `ru_ru`, `sv_se`, `tr_tr`, `zh_cn` all move from complete to incomplete upstream
- 27 documented complete-English fallback full locales; 37 translated/AI-assisted full locales

Validation/files:
- exploratory endpoint/source/scope audit **`34743938626`** green
- isolated complete audit/scope/reconstruction/QA **`34744097497`** green
- integrated into `.github/workflows/validate.yml`
- temporary `.github/workflows/audit-g24.yml` removed
- definitive clean-head full G1→G24 gate is pending
- files: `upstream/sources/1.17.1/en_us.json`, `upstream/diffs/1.16.5-to-1.17.1.json`, `upstream/minecraft-1.17.1-language-audit.json`, `upstream/minecraft-1.17.1-language-scope.json`, `translations/g24-mc1.17.1/policy.json`, `scripts/audit_1_17_1.py`, `scripts/reconstruct_1_17_1.py`, `scripts/validate_1_17_1_delta.py`, `scripts/validate_1_17_1_complete.py`

## Current next target — G25 Minecraft 1.18

Do not freeze G25 until the clean full G1→G24 gate is green.

Read-only historical research already shows:
- `2df668b5ac4a8473b9837ad2785d0f5a4fb845a6` is `Initial port to Minecraft 1.18`
- `11170466754e1065e25a6769d70bcfbffbb36130` explicitly updates Minecraft 1.18 → 1.18.1 and has parent `2df668b5...`
- therefore the final Minecraft 1.18 endpoint is **`2df668b5ac4a8473b9837ad2785d0f5a4fb845a6`**
- its transition diff identifies Minecraft `1.18`, Forge `38.0.14`, JEI version `9.0.0`
- Minecraft 1.18.1 and 1.18.2 also have distinct later transitions and must remain separate generations

Immediate next steps:
1. require a green canonical full G1→G24 CI from the clean head after this status update;
2. replace the G24 table CI field with that canonical run ID and mark G24 completed;
3. audit exact G25 Minecraft 1.18 build/source/scope/ownership from endpoint `2df668b5...`;
4. continue chronologically through 1.18.1 and 1.18.2 as separate generations if their endpoint audits confirm them.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

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
| G24 | 1.17.1 | 8.3.0 | `ff99d00` | 141 | 86 | 64 | 21 | 1 | `34744321527` |
| G25 | 1.18 | 9.0.0 | `2df668b` | 141 | 86 | 64 | 21 | 1 | `34745954288` |
| G26 | 1.18.1 | 9.4.1 | `82a6222` | 149 | 86 | 64 | 21 | 1 | `34747275451` |

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

## G24 — Minecraft 1.17.1 / JEI 8.3.0 — completed

- final endpoint **`ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7`**; the historical `Port to 1.17` jumps directly to Minecraft **1.17.1**, so there is no separate 1.17 generation
- JEI `8.3.0`, Forge `37.0.104`, mappings `official / 1.17.1`, Java 16
- 141 keys = **135 normal + 6 debug**
- G23→G24 = **87 unchanged + 24 added + 2 removed + 30 changed values**; **53 normal added-or-changed meanings** reviewed
- Minecraft raw/selected = **123 / 86**; `zlm_arab` deferred; `gv_im` and `mi_nz` removed from selected scope
- ownership = **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- isolated complete QA **`34744097497`** green
- definitive clean-head full G1→G24 CI **`34744321527`** green

## G25 — Minecraft 1.18 / JEI 9.0.0 — completed

- final endpoint **`2df668b5ac4a8473b9837ad2785d0f5a4fb845a6`**, `Initial port to Minecraft 1.18`
- Minecraft `1.18`, JEI `9.0.0`, Forge `38.0.14`, mappings `official / 1.18`, Java 17
- 141 keys = **135 normal + 6 debug**; G24→G25 = **141 unchanged + 0 added + 0 removed + 0 changed**
- asset index id `1.18`, SHA1 `d31a2e85ae149dd1b1a7070b22cb8887892fda6c`; raw/selected = **124 / 86**
- `ry_ua` appears as an asset file but no explicit 1.18 client language registry was found, so it remains deferred
- ownership = **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- isolated full QA **`34745793615`** green
- definitive clean-head full G1→G25 CI **`34745954288`** green

## G26 — Minecraft 1.18.1 / JEI 9.4.1 — completed

Endpoint/build:
- final endpoint **`82a622213dbf2a9df65af4e3cebbccc77ec44deb`**, the parent of `e72e49fa7a072755e7f96cad65388205f6a010dc` (`Port to 1.18.2 (#2739)`)
- Minecraft `1.18.1`, JEI `9.4.1`, Forge `39.0.89`, mappings `official / 1.18.1`, Java 17
- pinned English blob SHA `aa3a3da58dff3d623ee553aca40c7b24c80c2d18`

English/source delta:
- 149 keys = **143 normal + 6 debug**
- G25→G26 = **124 unchanged + 11 added + 3 removed + 14 changed values**
- **25 normal added-or-changed meanings** reviewed; zero debug meanings changed
- only the 124 exact unchanged key+English pairs inherit G25 values
- all 25 added/changed project-owned meanings use exact G26 target English unless separately reviewed
- removed keys are never emitted and cross-key reuse remains forbidden

Minecraft scope/ownership:
- Minecraft 1.18.1 uses the same asset index as 1.18: id `1.18`, SHA1 `d31a2e85ae149dd1b1a7070b22cb8887892fda6c`
- raw/selected = **124 / 86**, with no language-code delta from G25
- no client-JAR language registry candidate was found; `ry_ua` remains deferred
- JEI ships the same 25 upstream locale codes
- ownership remains **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- 27 documented complete-English fallback full locales; 37 translated/AI-assisted full locales

Validation/files:
- first pinned endpoint audit **`34746723993`** green
- final optimized isolated audit/scope/reconstruction/complete QA **`34747127823`** green
- the G25 reconstruction inputs are cached once in the G26 reconstructor to avoid repeated historical reconstruction without changing output semantics
- integrated into `.github/workflows/validate.yml`
- temporary `.github/workflows/audit-g26.yml` removed
- definitive clean-head full G1→G26 CI **`34747275451`** green
- files: `upstream/sources/1.18.1/en_us.json`, `upstream/diffs/1.18-to-1.18.1.json`, `upstream/minecraft-1.18.1-language-audit.json`, `upstream/minecraft-1.18.1-language-scope.json`, `translations/g26-mc1.18.1/policy.json`, `scripts/audit_1_18_1.py`, `scripts/reconstruct_1_18_1.py`, `scripts/validate_1_18_1_delta.py`, `scripts/validate_1_18_1_complete.py`

## Current next target — G27 Minecraft 1.18.2

Historical boundary confirmed:
- `e72e49fa7a072755e7f96cad65388205f6a010dc` is `Port to 1.18.2 (#2739)` and has G26 endpoint `82a622213...` as parent
- `5b2e71f...` is the subsequent `Update for Minecraft 1.19`; its parent is therefore the final Minecraft 1.18.2 endpoint **`530ef6c8d604370bef850f3656a28beab56cbfba`**
- direct endpoint metadata confirms Minecraft `1.18.2`, JEI specification version **`10.1.0`**, Forge **`40.0.24`**, and Java **17**
- JEI was refactored to a multi-module layout in this generation; locate and pin the exact `en_us.json` blob from the endpoint tree rather than assuming the former monolithic resource path

Immediate next steps:
1. resolve the exact G27 English resource path/blob at `530ef6c8...` from the Git tree;
2. audit G26→G27 source delta plus Minecraft 1.18.2 language scope and JEI upstream ownership;
3. reconstruct/validate G27 with the fixed key+English reuse rule;
4. integrate G27 into the chronological main workflow and require a clean full G1→G27 gate.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.
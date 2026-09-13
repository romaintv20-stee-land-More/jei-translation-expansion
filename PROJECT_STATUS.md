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
| G27 | 1.18.2 | 10.1.0 | `530ef6c` | 154 | 86 | 64 | 21 | 1 | `34770977507` |
| G28 | 1.19 | 11.1.1 | `91527b7` | 154 | 86 | 64 | 19 | 3 | isolated `34773007144`; canonical pending |

## G23 — Minecraft 1.16.5 / JEI 7.7.1 — completed

- final endpoint `f6bd6ea033084f3d18ad256c9921641dcbd0330f`
- Forge `36.2.0`, mappings `official / 1.16.5`, Java 8 via Gradle toolchain
- 119 keys = 113 normal + 6 debug
- G22→G23 = **113 unchanged + 6 added + 1 removed + 0 changed values**
- Minecraft raw/selected = **125 / 88**
- ownership = **66 addon-full + 15 supplements + 7 complete upstream**
- definitive full G1→G23 CI **`34743463506`** green

## G24 — Minecraft 1.17.1 / JEI 8.3.0 — completed

- final endpoint `ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7`; the historical `Port to 1.17` jumps directly to Minecraft **1.17.1**, so there is no separate 1.17 generation
- Forge `37.0.104`, mappings `official / 1.17.1`, Java 16
- 141 keys = **135 normal + 6 debug**
- G23→G24 = **87 unchanged + 24 added + 2 removed + 30 changed values**
- Minecraft raw/selected = **123 / 86**; `zlm_arab` deferred; `gv_im` and `mi_nz` removed from selected scope
- ownership = **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- definitive clean-head full G1→G24 CI **`34744321527`** green

## G25 — Minecraft 1.18 / JEI 9.0.0 — completed

- final endpoint `2df668b5ac4a8473b9837ad2785d0f5a4fb845a6`
- Forge `38.0.14`, mappings `official / 1.18`, Java 17
- G24→G25 = **141 unchanged + 0 added + 0 removed + 0 changed**
- raw/selected = **124 / 86**; `ry_ua` remains deferred because no explicit user-facing registry was found
- ownership = **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- definitive clean-head full G1→G25 CI **`34745954288`** green

## G26 — Minecraft 1.18.1 / JEI 9.4.1 — completed

- final endpoint `82a622213dbf2a9df65af4e3cebbccc77ec44deb`
- Forge `39.0.89`, mappings `official / 1.18.1`, Java 17
- 149 keys = **143 normal + 6 debug**
- G25→G26 = **124 unchanged + 11 added + 3 removed + 14 changed values**
- raw/selected = **124 / 86**; `ry_ua` remains deferred
- ownership = **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- isolated full QA **`34747127823`** green
- definitive clean-head full G1→G26 CI **`34747275451`** green

## G27 — Minecraft 1.18.2 / JEI 10.1.0 — completed

Endpoint/build:
- final endpoint **`530ef6c8d604370bef850f3656a28beab56cbfba`**, parent of `5b2e71f...` (`Update for Minecraft 1.19`)
- Minecraft `1.18.2`, JEI `10.1.0`, Forge `40.0.24`, Parchment `2022.03.13-1.18.2`, Java 17
- JEI multi-module language path: `Common/src/main/resources/assets/jei/lang/`
- pinned English blob SHA `346c310ab5f7d9a9b44005ca7ecb6041fe1c69a7`

Source/scope:
- 154 keys = **148 normal + 6 debug**
- G26→G27 = **149 unchanged + 5 added + 0 removed + 0 changed values**
- five new normal keys: `key.jei.closeRecipeGui`, `jei.key.combo.shift`, `jei.key.combo.control`, `jei.key.combo.command`, `jei.key.combo.alt`
- Minecraft asset language count / selected scope = **124 / 86**
- `ry_ua` remains deferred; no explicit user-facing client registry was found
- JEI ships 25 upstream locales
- ownership = **64 addon-full + 21 supplements + 1 complete upstream** (`en_us`)
- 27 documented complete-English fallbacks; 37 translated/AI-assisted full locales

Validation:
- pinned exploratory audit **`34770553079`** green
- integrated into `.github/workflows/validate.yml`; temporary G27 workflow removed
- definitive clean-head full G1→G27 CI **`34770977507`** green

## G28 — Minecraft 1.19 / JEI 11.1.1 — isolated QA complete; canonical gate pending

Endpoint/build:
- final endpoint **`91527b7d5fae747455ed7630915c088e3fe0f602`**, parent of `16116299...` (`Update for Minecraft 1.19.1`)
- Minecraft `1.19`, JEI `11.1.1`, Forge `41.1.0`, Parchment `1.18.2-2022.07.10-1.19`, Java 17
- language path remains `Common/src/main/resources/assets/jei/lang/`
- English blob remains exactly `346c310ab5f7d9a9b44005ca7ecb6041fe1c69a7`

Source/scope:
- 154 keys = **148 normal + 6 debug**
- G27→G28 = **154 unchanged + 0 added + 0 removed + 0 changed values**
- Minecraft 1.19 asset index id `1.19`, SHA1 `a9c8b05a8082a65678beda6dfa2b8f21fa627bce`
- raw/selected = **124 / 86**, with no language-code delta from G27
- no client-JAR language registry candidate was found; `ry_ua` remains deferred
- JEI still ships 25 upstream locale codes
- `bg_bg` and `pl_pl` are now complete upstream
- ownership = **64 addon-full + 19 supplements + 3 complete upstream** (`bg_bg`, `en_us`, `pl_pl`)

Validation/files:
- exploratory audit **`34772733476`** green
- full isolated audit/scope/reconstruction/complete QA **`34773007144`** green
- integrated into `.github/workflows/validate.yml`
- temporary `.github/workflows/audit-g28.yml` removed
- canonical full G1→G28 gate: **pending on clean head**
- files: `upstream/sources/1.19/en_us.json`, `upstream/diffs/1.18.2-to-1.19.json`, `upstream/minecraft-1.19-language-audit.json`, `upstream/minecraft-1.19-language-scope.json`, `translations/g28-mc1.19/policy.json`, `scripts/audit_1_19.py`, `scripts/reconstruct_1_19.py`, `scripts/validate_1_19_delta.py`, `scripts/validate_1_19_complete.py`

## Current next target

Immediate gate:
1. require a clean full **G1→G28** `Validate translations` run to finish green;
2. once green, record that run as the canonical G28 CI and mark G28 completed.

Next historical generation after that:
- **G29 = Minecraft 1.19.1**
- first 1.19.1 port commit: `16116299c676183dee0f63380a6a09a64d754359`
- the later `Update dependencies for Minecraft 1.19.2` commit is `c0859d6ac6b798bcc3d96338109f8ab976ea16c5`; its parent must be resolved after G28 becomes canonical to pin the final 1.19.1 endpoint.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

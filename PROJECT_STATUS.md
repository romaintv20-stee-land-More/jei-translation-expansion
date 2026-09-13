# JEI Translation Expansion — Canonical Project Status

Last synchronized: **2026-09-13**

This file is the canonical handoff for continuing the historical JEI localization audit chronologically.

## Fixed project rules

- **One Minecraft version = one dedicated release JAR.** Never group multiple Minecraft versions in one JAR.
- Reuse translation data only when the **localization key and English source value/meaning are identical**.
- Preserve JEI upstream locale keys. For incomplete upstream locales, emit only the exact missing normal keys unless a deliberate override is explicitly approved.
- Preserve placeholders and fixed technical literals exactly.
- Prefer exact target-English fallback over uncertain technical translation.
- Constructed/novelty languages, historical/non-primary forms, and most regional variants remain outside the selected primary-language scope unless explicitly reviewed otherwise.
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

## G22 — Minecraft 1.16.4 / JEI 7.6.1 — completed

- final endpoint `8255a01a6db0980f6e03b2b4d9d5f376bef7fd25`
- Forge `35.0.2`, mappings `snapshot / 20201028-1.16.3`, Java 8
- 114 keys = 111 normal + 3 debug; G21→G22 = **114 unchanged**
- Minecraft raw/selected = **125 / 88**, unchanged from G21
- ownership = **67 addon-full + 16 supplements + 5 complete upstream**
- complete upstream: `en_us`, `pl_pl`, `pt_br`, `ru_ru`, `sv_se`
- isolated endpoint audit `34724798647` green
- isolated complete QA `34724953978` green
- definitive full G1→G22 CI **`34742453589`** green

## G23 — Minecraft 1.16.5 / JEI 7.7.1 — completed

Endpoint/build:
- final endpoint `f6bd6ea033084f3d18ad256c9921641dcbd0330f`
- the next port commit `75d2fd9ec0d5e911bfdaf8e4be9ac5ff4b860024` has this commit as its parent
- Forge `36.2.0`
- mappings `official / 1.16.5`
- Java 8 via Gradle toolchain
- JSON lowercase resources

English/source delta:
- 119 keys = **113 normal + 6 debug**
- G22→G23 = **113 unchanged + 6 added + 1 removed + 0 changed values**
- added: `description.jei.debug.formatting.1`, `.2`, `.3`, `jei.message.ftblibrary`, `key.jei.nextCategory`, `key.jei.previousCategory`
- removed: `jei.message.ftbguilib`
- no cross-key reuse from `ftbguilib` to `ftblibrary`; new project-owned meanings use exact target English

Minecraft scope/ownership:
- Minecraft 1.16.4 and 1.16.5 share asset index id `1.16`, SHA1 `f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2`
- raw/selected = **125 / 88**, unchanged
- JEI ships **25** upstream JSON locales; `id_id` is newly upstream-owned
- ownership = **66 addon-full + 15 supplements + 7 complete upstream**
- complete upstream: `en_us`, `it_it`, `ko_kr`, `ru_ru`, `sv_se`, `tr_tr`, `zh_cn`
- newly complete from G22: `it_it`, `ko_kr`, `tr_tr`, `zh_cn`
- `pl_pl` and `pt_br` become incomplete again because each lacks the two new category-navigation keys
- `id_id` moves from addon-full to upstream-incomplete and needs only `jei.message.ftblibrary`
- `ja_jp` lacks smelting time plus the two new category-navigation keys
- 28 documented full-English fallback locales; 38 translated/AI-assisted full locales

Validation:
- first isolated audit `34743108957` failed only because the Java detector expected the old Java declaration syntax
- corrected isolated endpoint audit **`34743169568`** green
- isolated full audit/scope/reconstruction/complete QA **`34743332585`** green
- definitive full G1→G23 CI **`34743463506`** green

G23 files:
- `upstream/sources/1.16.5/en_us.json`
- `upstream/diffs/1.16.4-to-1.16.5.json`
- `upstream/minecraft-1.16.5-language-audit.json`
- `upstream/minecraft-1.16.5-language-scope.json`
- `translations/g23-mc1.16.5/policy.json`
- `scripts/audit_1_16_5.py`
- `scripts/reconstruct_1_16_5.py`
- `scripts/validate_1_16_5_delta.py`
- `scripts/validate_1_16_5_complete.py`

## Current next target — G24 Minecraft 1.17.1 / JEI 8.3.0

Historical boundary is already pinned in read-only research:
- commit `75d2fd9ec0d5e911bfdaf8e4be9ac5ff4b860024`, titled `Port to 1.17`, actually changes the build directly from **Minecraft 1.16.5 to 1.17.1**; do not invent a distinct Minecraft 1.17 JEI generation
- the later transition commit `2df668b5ac4a8473b9837ad2785d0f5a4fb845a6`, `Initial port to Minecraft 1.18`, has parent **`ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7`**
- therefore the final Minecraft 1.17.1 endpoint is **`ff99d00a9e412e8c29dbbcdf24b437f93f72e4d7`**
- endpoint build: Minecraft `1.17.1`, JEI `8.3.0`, Forge `37.0.104`, mappings `official / 1.17.1`, Java 16
- pinned final English blob SHA: `abd5d9b6b1e17f61ddcdc0b2a20e7f6d3f604b7e`
- English localization changes substantially from G23; G24 must use a fresh audit and semantic delta, not whole-file inheritance

Immediate next steps:
1. store the exact pinned `1.17.1/en_us.json` source;
2. run an isolated G24 endpoint audit that computes the G23→G24 delta directly before freezing a diff manifest;
3. audit Minecraft 1.17.1 language inventory and JEI upstream ownership;
4. freeze G24 diff/scope/policy from the audit output;
5. reconstruct and validate G24, integrate into the main workflow, remove the temporary audit workflow, then require a green full G1→G24 gate.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need a broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

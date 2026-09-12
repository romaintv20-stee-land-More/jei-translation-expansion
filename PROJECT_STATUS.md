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
| G21 | 1.16.3 | 7.6.0 | `130181a` | 114 | 88 | 67 | 18 | 3 | isolated `34724150364`; canonical pending |

## G19 — Minecraft 1.16.1 / JEI 7.0.1

- final endpoint `0a0dbfac9c53124d82a602301d466dbf2c5e3e97`
- Forge `32.0.47`, mappings `snapshot / 20200514-1.16`, Java 8
- 110 keys = 107 normal + 3 debug
- G18→G19 = 108 unchanged + 2 changed placeholder values; old values for those two keys are not reused
- Minecraft raw/selected = 125 / 88; new selected primary language `fur_it`
- ownership = 67 addon-full + 18 supplements + 3 complete upstream (`en_us`, `ja_jp`, `pl_pl`)
- definitive full G1→G19 CI `34712320469` green

## G20 — Minecraft 1.16.2 / JEI 7.3.2 — completed

Endpoint/build:
- final endpoint `df46cefb0ade79851101fd32b065a34115fee70c`
- Forge `33.0.19`
- mappings `snapshot / 20200723-1.16.1`
- Java 8
- JSON lowercase language resources

English/source delta:
- pinned English blob `ec04c5e8545308efdba9f7de6de8ae50e804946b`
- 114 keys = 111 normal + 3 debug
- G19→G20 = **110 unchanged + 4 added**, no removed or changed values
- added keys:
  - `config.jei`
  - `config.jei.search.searchAdvancedTooltips`
  - `gui.jei.category.smelting.time.seconds`
  - `jei.message.ftbguilib`
- unchanged meanings inherit exact G19 values; newly project-owned meanings use exact G20 target English

Minecraft scope/ownership:
- asset index id `1.16`, SHA1 `f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2`
- raw/selected = 125 / 88, unchanged from G19
- ownership = 67 addon-full + 19 supplements + 2 complete upstream (`en_us`, `pt_br`)
- `pt_br` becomes complete upstream; `ja_jp` and `pl_pl` become incomplete and require supplements
- 28 documented complete-English fallback locales; 39 translated/AI-assisted full locales

Validation:
- isolated audit `34712596596` green
- isolated audit/scope/reconstruction/complete QA `34712762163` green
- definitive full G1→G20 CI **`34712876829`** green

G20 files:
- `upstream/sources/1.16.2/en_us.json`
- `upstream/diffs/1.16.1-to-1.16.2.json`
- `upstream/minecraft-1.16.2-language-audit.json`
- `upstream/minecraft-1.16.2-language-scope.json`
- `translations/g20-mc1.16.2/policy.json`
- `scripts/audit_1_16_2.py`
- `scripts/reconstruct_1_16_2.py`
- `scripts/validate_1_16_2_delta.py`
- `scripts/validate_1_16_2_complete.py`

## G21 — Minecraft 1.16.3 / JEI 7.6.0 — isolated QA complete

Endpoint/build:
- final endpoint `130181aa9ee3762c6accd7614a03d932486710f9`
- next transition commit `b2717092173303cd8861c2487a36ecffb0bae5b8` explicitly changes Minecraft 1.16.3 → 1.16.4
- Forge `34.1.0`
- mappings `snapshot / 20200723-1.16.1`
- Java 8
- JSON lowercase resources

English/source delta:
- pinned English blob remains `ec04c5e8545308efdba9f7de6de8ae50e804946b`
- 114 keys = 111 normal + 3 debug
- G20→G21 = **114 unchanged**, no added, removed, or changed values
- all project-owned translation values therefore inherit exact G20 semantics

Minecraft scope/ownership:
- Minecraft 1.16.2 and 1.16.3 share the same `1.16` asset index SHA1 `f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2`
- raw/selected = 125 / 88; no codes added or removed
- JEI still ships 24 upstream locale files
- ownership = 67 addon-full + 18 supplements + 3 complete upstream (`en_us`, `pt_br`, `sv_se`)
- `sv_se` becomes complete upstream, so the G20 Swedish supplement is retired
- `zh_tw` improves to 110/111 normal keys but remains outside selected primary scope
- 28 documented complete-English fallback locales; 39 translated/AI-assisted full locales

Validation:
- isolated endpoint audit `34724024760` green
- isolated full audit/scope/reconstruction/complete QA **`34724150364`** green
- integrated into `.github/workflows/validate.yml`; definitive full G1→G21 CI is the current gate

G21 files:
- `upstream/sources/1.16.3/en_us.json`
- `upstream/diffs/1.16.2-to-1.16.3.json`
- `upstream/minecraft-1.16.3-language-audit.json`
- `upstream/minecraft-1.16.3-language-scope.json`
- `translations/g21-mc1.16.3/policy.json`
- `scripts/audit_1_16_3.py`
- `scripts/reconstruct_1_16_3.py`
- `scripts/validate_1_16_3_delta.py`
- `scripts/validate_1_16_3_complete.py`

## Current next target — G22 Minecraft 1.16.4 / JEI 7.6.1

Read-only lineage already identified; do not freeze G22 until the full G1→G21 gate is green:
- commit `c24d5f203d41ea277418928f74b954ed297b9123` explicitly changes Minecraft 1.16.4 → 1.16.5
- its parent and therefore final Minecraft 1.16.4 endpoint is `8255a01a6db0980f6e03b2b4d9d5f376bef7fd25`
- Minecraft `1.16.4`
- JEI `7.6.1`
- Forge `35.0.2`
- mappings `snapshot / 20201028-1.16.3`
- G22 English is already observed byte-identical to G21, same blob `ec04c5e8545308efdba9f7de6de8ae50e804946b`; full scope/ownership must still be audited before reconstruction

Immediate next steps:
1. require a green canonical full G1→G21 CI from the clean integrated head;
2. update this file with that canonical G21 run ID;
3. open G22 with a pinned endpoint audit before freezing scope/ownership;
4. continue chronologically to Minecraft 1.16.5 after G22 completes.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need a broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

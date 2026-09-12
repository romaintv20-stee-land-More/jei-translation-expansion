# JEI Translation Expansion — Canonical Project Status

Last synchronized: **2026-09-12**

This file is the canonical handoff for continuing the historical JEI localization audit chronologically.

## Fixed project rules

- **One Minecraft version = one dedicated release JAR.** Never group multiple Minecraft versions in one JAR.
- Translation data may be reused between versions only when the **localization key and English source value/meaning are identical**.
- Existing JEI upstream locale keys are preserved. For incomplete upstream locales, emit only the exact missing normal keys unless a deliberate override is explicitly approved.
- Preserve placeholders and fixed technical literals exactly.
- Prefer exact target-English fallback over uncertain technical translation.
- Constructed/novelty languages, historical/non-primary forms, and most regional variants remain outside the selected primary-language scope unless explicitly reviewed otherwise.
- Runtime-tested final artifacts go only to `release-jars/<minecraft-version>/`.
- Translation/reconstruction QA does **not** imply runtime validation or release promotion.
- Minecraft 1.13+ missing-key-only JSON supplements remain runtime merge-test-gated before release promotion.
- Update this file after every material generation milestone.

## Completed translation/reconstruction generations

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

## G17 — Minecraft 1.15.1 / JEI 6.0.0

- final endpoint `381a0d7df6ffd282f9eda4da41a299fdbea02352`
- Forge `30.0.15`, mappings `snapshot / 20191105-1.14.3`, Java 8
- 109 keys = 106 normal + 3 debug; G16→G17 = 109 unchanged
- Minecraft raw/selected = 122 / 87
- new selected primary language: `lmo`; removed selected Minecraft codes: `kab_kab`, `moh_ca`, `nuk`, `oj_ca`, `scn`
- ownership = 66 addon-full + 16 supplements + 5 complete upstream
- exact Swedish G16 upstream values for Smoking/Blasting/Campfire Cooking are preserved after G17 upstream regression
- definitive full CI `34709161680` green

## G18 — Minecraft 1.15.2 / JEI 6.0.2

- final endpoint `1ea77203d8b731c99cea68166b02afeb3d9c6176`
- Forge `31.1.43`, mappings `snapshot / 20200411-1.15.1`, Java 8
- JSON lowercase resources
- 110 keys = 107 normal + 3 debug
- G17→G18 = **109 unchanged + 1 added**, no removed/changed values
- added key: `gui.jei.category.stoneCutter = "Stonecutting"`
- same Minecraft `1.15` asset index as G17: SHA1 `58c12b1e2878e0a78719778acb803746450b3f1c`
- raw/selected = 122 / 87
- ownership = 66 addon-full + 18 supplements + 3 complete upstream (`en_us`, `ja_jp`, `pl_pl`)
- `ja_jp` becomes complete upstream; `de_de`, `pt_br`, `ru_ru` each miss only Stonecutting
- 27 documented full-English fallback locales; 39 translated/AI-assisted full locales
- isolated audit `34709392197` green; isolated full QA `34709532127` green
- definitive full G1→G18 CI **`34709639659`** green

G18 files:
- `upstream/sources/1.15.2/en_us.json`
- `upstream/diffs/1.15.1-to-1.15.2.json`
- `upstream/minecraft-1.15.2-language-audit.json`
- `upstream/minecraft-1.15.2-language-scope.json`
- `translations/g18-mc1.15.2/policy.json`
- `scripts/audit_1_15_2.py`
- `scripts/reconstruct_1_15_2.py`
- `scripts/validate_1_15_2_delta.py`
- `scripts/validate_1_15_2_complete.py`

## Latest completed milestone — G19 Minecraft 1.16.1 / JEI 7.0.1

Endpoint/build:
- final 1.16.1 endpoint `0a0dbfac9c53124d82a602301d466dbf2c5e3e97`
- next commit `10c7fa91843781a90f461a9aa5d08f7bc3dbe114` explicitly transitions to Minecraft 1.16.2
- Forge `32.0.47`
- mappings `snapshot / 20200514-1.16`
- Java 8
- JSON lowercase language resources

English/source delta:
- pinned English blob `a0af1c7ea689ae0d34da4c5680c4109c6911a1a7`
- 110 keys = 107 normal + 3 debug
- G18→G19 = **108 unchanged, 0 added, 0 removed, 2 changed**
- changed placeholders:
  - `jei.tooltip.liquid.amount`: `%,d mB` → `%s mB`
  - `jei.tooltip.liquid.amount.with.capacity`: `%,d / %,d mB` → `%s / %s mB`
- old locale values for these two keys are not reusable; project-owned values use exact G19 target English

Minecraft scope:
- asset index id `1.16`, SHA1 `f3c4aa96e12951cd2781b3e1c0e8ab82bf719cf2`
- raw language inventory = 125
- new codes: `fur_it`, `swg`, `tok`
- selected new primary language: `fur_it` (Friulian)
- deferred: `swg` regional/dialect variant, `tok` constructed Toki Pona
- no removed codes; no inherited selected locale disappears
- selected scope = 88

Ownership/reconstruction:
- 67 addon-full locales = G18's 66 + `fur_it`
- 18 exact missing-key-only supplements
- 3 complete selected upstream locales: `en_us`, `ja_jp`, `pl_pl`
- 28 documented full-English fallbacks; `fur_it` is the new complete-English fallback
- 39 translated/AI-assisted full locales remain intact
- all 108 unchanged G18 semantics are inherited exactly
- the two changed liquid placeholders use exact target-English fallback only where project-owned

Validation:
- isolated audit run `34712048789` green
- isolated audit/scope/reconstruction/complete QA run `34712227590` green
- definitive full G1→G19 CI **`34712320469`** green

G19 files:
- `upstream/sources/1.16.1/en_us.json`
- `upstream/diffs/1.15.2-to-1.16.1.json`
- `upstream/minecraft-1.16.1-language-audit.json`
- `upstream/minecraft-1.16.1-language-scope.json`
- `translations/g19-mc1.16.1/policy.json`
- `scripts/audit_1_16_1.py`
- `scripts/reconstruct_1_16_1.py`
- `scripts/validate_1_16_1_delta.py`
- `scripts/validate_1_16_1_complete.py`

## Current task — G20 Minecraft 1.16.2 / JEI 7.3.2

Historical endpoint identified:
- commit `8b081bb7731dec0f8e5c8f750766ff63ed4a311c` explicitly changes Minecraft `1.16.2` → `1.16.3`
- its parent and therefore final Minecraft 1.16.2 endpoint is `df46cefb0ade79851101fd32b065a34115fee70c`
- Minecraft `1.16.2`
- JEI `7.3.2`
- Forge `33.0.19`
- mappings `snapshot / 20200723-1.16.1`
- Java 8 expected from the same build lineage; audit must verify
- JSON language resources
- upstream English blob SHA observed: `ec04c5e8545308efdba9f7de6de8ae50e804946b`

Pre-audit observation only — not yet frozen:
- the final 1.16.2 English source visibly contains four new normal keys compared with G19:
  - `config.jei = "JEI Config"`
  - `config.jei.search.searchAdvancedTooltips = "Search advanced tooltips"`
  - `gui.jei.category.smelting.time.seconds = "%ss"`
  - `jei.message.ftbguilib = "Install FTB GUI Library to access ingame config"`
- exact source diff, Mojang language inventory, selected scope, and JEI upstream completeness must be verified by the G20 audit before reconstruction

Immediate next steps:
1. pin the final G20 English source and exact G19→G20 diff candidate;
2. implement/run the pinned G20 endpoint audit;
3. freeze Minecraft scope and JEI ownership only from audit output;
4. reconstruct exact reusable G19 semantics and use target-safe fallback for genuinely new/changed meanings;
5. validate G20 in isolation, integrate it into main CI, then require a green full G1→G20 run;
6. continue chronologically to the final Minecraft 1.16.3 endpoint.

## Documentation synchronization debt

`upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` still need a broad synchronization through the latest completed generations. Chronological generation work remains the primary task, but this debt should be cleared before release packaging.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

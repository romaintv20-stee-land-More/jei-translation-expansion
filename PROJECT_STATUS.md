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

## G13 — Minecraft 1.13.2 / JEI 5.0.0

- final branch `1.13` endpoint `2d16f4210cbae340ad76b483b4aa8b461561e86f`
- Forge `25.0.85`, mappings `snapshot / 20180921-1.13`, Java 8
- JSON lowercase language resources
- 106 semantic keys = 103 normal + 3 debug
- G12→G13 = 101 unchanged, 1 added, 0 removed, 4 changed
- Minecraft raw/selected = 118 / 87
- new selected: `bar`, `kk_kz`, `moh_ca`, `tt_ru`; `fra_de` deferred
- ownership = 66 addon-full + 19 supplements + 2 complete upstream (`en_us`, `pl_pl`)
- 27 documented full-English fallback locales; 39 translated/AI-assisted full locales
- `%CTRL` → `%s` runtime placeholder migration is explicitly locked by QA
- full CI run `34671958137` green

## G14 — Minecraft 1.14.2 / JEI 6.0.0

- pin `f1fd2f1d20cf86d9644e907a641f99873b4d8888`
- Forge `26.0.63`, mappings `snapshot / 20190615-1.14.2`, Java 8
- JSON lowercase language resources
- 109 keys = 106 normal + 3 debug
- G13→G14 = 106 unchanged + 3 added cooking-category keys; no removals or changed meanings
- Minecraft raw/selected = 126 / 91
- selected additions: `ba_ru`, `scn`, `tl_ph`, `yi_de`
- deferred: `es_ec`, `esan`, `isv`, `got_de`
- ownership = 70 addon-full + 19 supplements + 2 complete upstream
- 31 documented full-English fallbacks; 39 translated/AI-assisted full locales
- run `34677329178` green

## G15 — Minecraft 1.14.3 / JEI 6.0.0

- pin `9e7de1d9b5115053b85ed59558f841edcb6e5414`
- Forge `27.0.17`, mappings `snapshot / 20190630-1.14.3`, Java 8
- same English blob as G14: `d9b1fa673aaf7ca233650da01d117b8bc9b4a76d`
- 109/109 semantics unchanged from G14
- same Minecraft asset index as G14: id `1.14`, SHA1 `43b2f3021fe9f7d768378de95538e22da3ee8301`
- raw/selected = 126 / 91
- ownership = 70 addon-full + 18 supplements + 3 complete upstream (`en_us`, `pl_pl`, `pt_br`)
- `pt_br` supplement retired because JEI upstream becomes complete
- run `34677627657` green

## G16 — Minecraft 1.14.4 / JEI 6.0.1

- final branch `1.14` endpoint `de8b6a10eba45899be1c62694c9f27a435ae8c2c`
- Forge `28.1.85`, mappings `20191105-1.14.3`, Java 8
- same English blob as G14/G15: `d9b1fa673aaf7ca233650da01d117b8bc9b4a76d`
- 109 keys = 106 normal + 3 debug; G15→G16 = 109 unchanged, 0 added/removed/changed
- same Minecraft asset index as G14/G15: id `1.14`, SHA1 `43b2f3021fe9f7d768378de95538e22da3ee8301`
- raw/selected = 126 / 91
- ownership = 70 addon-full + 16 supplements + 5 complete upstream (`de_de`, `en_us`, `pl_pl`, `pt_br`, `ru_ru`)
- `de_de` and `ru_ru` supplements retired because JEI upstream becomes complete
- 31 documented full-English fallbacks; 39 translated/AI-assisted full locales
- full G1→G16 run `34678167977` green

## Latest completed milestone — G17 Minecraft 1.15.1 / JEI 6.0.0

Endpoint:
- final Minecraft 1.15.1 commit `381a0d7df6ffd282f9eda4da41a299fdbea02352`
- the next commit `b674c7c1d50c4b3726790b1851b40037182067c6` explicitly transitions to Minecraft 1.15.2
- Forge `30.0.15`
- mappings `snapshot / 20191105-1.14.3`
- Java 8
- JSON lowercase language resources

English/source delta:
- pinned source blob remains `d9b1fa673aaf7ca233650da01d117b8bc9b4a76d`
- 109 keys = 106 normal + 3 debug
- G16→G17 = **109 unchanged, 0 added, 0 removed, 0 changed**
- all G16 semantic values are exact-reuse eligible

Minecraft scope:
- asset index id `1.15`, SHA1 `58c12b1e2878e0a78719778acb803746450b3f1c`
- raw language inventory drops from 126 to 122
- added codes: `lmo`, `lzh`, `rpr`, `zh_hk`
- selected new primary language: `lmo` (Lombard)
- deferred: `lzh` (historical/literary), `rpr` (historical orthography), `zh_hk` (regional variant)
- removed codes: `got_de`, `kab_kab`, `moh_ca`, `nuk`, `oj_ca`, `scn`, `swg`, `tzl_tzl`
- previously selected locales removed by Minecraft: `kab_kab`, `moh_ca`, `nuk`, `oj_ca`, `scn`
- selected scope = 87

Ownership/reconstruction:
- 66 addon-full locales = 65 surviving G16 full locales + new `lmo`
- 16 exact missing-key-only supplements
- 5 complete selected upstream locales: `de_de`, `en_us`, `pl_pl`, `pt_br`, `ru_ru`
- 27 documented full-English fallback locales; `lmo` is the new exact-English fallback
- 39 translated/AI-assisted full locales remain intact
- `sv_se` upstream regresses by losing `Smoking`, `Blasting`, and `Campfire Cooking`; those exact Swedish G16 upstream values are preserved in the G17 supplement instead of falling back to English

Validation:
- isolated endpoint audit run `34708848506` green
- isolated full G17 audit/scope/reconstruction/QA run `34709070904` green
- definitive full G1→G17 CI run **`34709161680`** green
- GitHub API directory-listing dependencies were removed from G15/G16/G17 audit scripts after an anonymous API 403; pinned raw locale contents remain checked live

G17 files:
- `upstream/sources/1.15.1/en_us.json`
- `upstream/diffs/1.14.4-to-1.15.1.json`
- `upstream/minecraft-1.15.1-language-audit.json`
- `upstream/minecraft-1.15.1-language-scope.json`
- `translations/g17-mc1.15.1/policy.json`
- `scripts/audit_1_15_1.py`
- `scripts/reconstruct_1_15_1.py`
- `scripts/validate_1_15_1_delta.py`
- `scripts/validate_1_15_1_complete.py`

## Current task — G18 Minecraft 1.15.2 / JEI 6.0.2

Historical endpoint already identified:
- the first Minecraft 1.16 transition commit is `b6c3363868fc6cd39950d980eb5dabb143fdd8bb` (`Update JEI to 1.16 (#1988)`)
- its parent, and therefore the final Minecraft 1.15.2 endpoint, is `1ea77203d8b731c99cea68166b02afeb3d9c6176`
- Minecraft `1.15.2`
- JEI `6.0.2`
- Forge `31.1.43`
- mappings `snapshot / 20200411-1.15.1`
- Java 8
- JSON lowercase language resources
- pinned English blob SHA `1cdebf187dacca64bc4a73c73537d674e2941beb`

Pre-audit observation only — not yet frozen:
- compared with G17, the final 1.15.2 English source visibly adds `gui.jei.category.stoneCutter = "Stonecutting"`
- exact source diff, Mojang language inventory, scope classification, and JEI upstream completeness must be verified by the G18 audit before reconstruction

Immediate next steps:
1. pin `upstream/sources/1.15.2/en_us.json` and exact G17→G18 diff;
2. implement/run the pinned G18 endpoint audit against Mojang and JEI upstream;
3. freeze G18 scope/ownership/policy;
4. reconstruct exact reusable G17 semantics and review only genuinely new/changed meanings;
5. add G18 delta/reconstruction/complete QA to main CI and require a green full run;
6. synchronize `upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` through the latest completed generation.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

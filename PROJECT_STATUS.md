# JEI Translation Expansion — Canonical Project Status

Last synchronized: **2026-09-12**

This file is the canonical handoff for continuing the historical JEI localization audit chronologically.

## Fixed project rules

- **One Minecraft version = one dedicated release JAR.** Never group multiple Minecraft versions in one JAR.
- Translation data may be reused between versions only when the **localization key and English source value/meaning are identical**.
- Existing JEI upstream locale keys are preserved. For incomplete upstream locales, emit only the exact missing normal keys unless a deliberate override is explicitly approved.
- Preserve placeholders and fixed technical literals exactly.
- Prefer exact target-English fallback over uncertain technical translation.
- Constructed/novelty languages and most regional variants remain outside the selected primary-language scope.
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

Endpoint:
- pin `f1fd2f1d20cf86d9644e907a641f99873b4d8888`
- Forge `26.0.63`
- mappings `snapshot / 20190615-1.14.2`
- Java 8
- JSON lowercase language resources

English/source delta:
- 109 semantic keys = 106 normal + 3 debug
- G13→G14 = **106 unchanged, 3 added, 0 removed, 0 changed**
- added categories: `gui.jei.category.blasting`, `gui.jei.category.campfire`, `gui.jei.category.smoking`
- all 106 G13 semantics are exact-reuse eligible; the three new categories use exact target English when project-owned

Minecraft scope:
- asset index id `1.14`, SHA1 `43b2f3021fe9f7d768378de95538e22da3ee8301`
- raw language inventory = 126
- new selected primary languages: `ba_ru`, `scn`, `tl_ph`, `yi_de`
- deferred: regional `es_ec`, `esan`; constructed `isv`; historical/nonprimary `got_de`
- selected scope = 91

Ownership:
- 70 addon-full JSON locales
- 19 exact missing-key-only supplements
- 2 complete selected upstream locales: `en_us`, `pl_pl`
- 31 documented full-English fallback locales
- 39 inherited translated/AI-assisted full locales

G14 files:
- `upstream/sources/1.14.2/en_us.json`
- `upstream/diffs/1.13.2-to-1.14.2.json`
- `upstream/minecraft-1.14.2-language-audit.json`
- `upstream/minecraft-1.14.2-language-scope.json`
- `translations/g14-mc1.14.2/policy.json`
- `scripts/audit_1_14_2.py`
- `scripts/reconstruct_1_14_2.py`
- `scripts/validate_1_14_2_delta.py`
- `scripts/validate_1_14_2_complete.py`

Full G1→G14 CI run **34677329178** is green.

## Latest completed milestone — G15 Minecraft 1.14.3 / JEI 6.0.0

Endpoint:
- pin `9e7de1d9b5115053b85ed59558f841edcb6e5414`
- Forge `27.0.17`
- mappings `snapshot / 20190630-1.14.3`
- Java 8
- JSON lowercase language resources

English/source delta:
- upstream `en_us.json` is byte-identical to G14 (blob `d9b1fa673aaf7ca233650da01d117b8bc9b4a76d`)
- 109 semantic keys = 106 normal + 3 debug
- G14→G15 = **109 unchanged, 0 added, 0 removed, 0 changed**
- no new semantic translation work; all G14 values are exact-reuse eligible

Minecraft scope:
- exact same asset index as G14: id `1.14`, SHA1 `43b2f3021fe9f7d768378de95538e22da3ee8301`
- raw/selected = 126 / 91
- no added or removed Minecraft language codes

Ownership:
- 70 addon-full JSON locales
- 18 exact missing-key-only supplements
- 3 complete selected upstream locales: `en_us`, `pl_pl`, `pt_br`
- `pt_br` becomes complete upstream and its G14 supplement is retired
- 31 documented full-English fallback locales
- 39 translated/AI-assisted full locales

G15 files:
- `upstream/sources/1.14.3/en_us.json`
- `upstream/diffs/1.14.2-to-1.14.3.json`
- `upstream/minecraft-1.14.3-language-audit.json`
- `upstream/minecraft-1.14.3-language-scope.json`
- `translations/g15-mc1.14.3/policy.json`
- `scripts/audit_1_14_3.py`
- `scripts/reconstruct_1_14_3.py`
- `scripts/validate_1_14_3_delta.py`
- `scripts/validate_1_14_3_complete.py`

Full G1→G15 CI run **34677627657** is green.

## Current task — G16 Minecraft 1.14.4 / JEI 6.0.1

Pinned final branch `1.14` endpoint:
- commit `de8b6a10eba45899be1c62694c9f27a435ae8c2c`
- Minecraft `1.14.4`
- JEI `6.0.1`
- Forge `28.1.85`
- mappings `20191105-1.14.3`
- Java 8 expected from unchanged build setup
- JSON languages

Already verified:
- final `en_us.json` uses the same upstream blob `d9b1fa673aaf7ca233650da01d117b8bc9b4a76d` as G14/G15
- G15→G16 English semantics are therefore 109 unchanged, 0 added, 0 removed, 0 changed
- `upstream/sources/1.14.4/en_us.json` and `upstream/diffs/1.14.3-to-1.14.4.json` are pinned
- `scripts/audit_1_14_4.py` is implemented
- audit CI has been wired and is currently running; use its final output before freezing scope/ownership

Immediate next steps:
1. finish the pinned G16 audit and extract Mojang asset/language inventory plus JEI upstream completeness;
2. freeze G16 audit/scope/policy manifests;
3. implement deterministic G15 inheritance with ownership recomputed against JEI 6.0.1;
4. run full G1→G16 CI;
5. synchronize `upstream/versions.json`, `upstream/generations.json`, README, `docs/VERSION_MATRIX.md`, and `docs/TRANSLATION_STATUS.md` through G16;
6. identify the next chronological JEI branch/version after 1.14.4.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

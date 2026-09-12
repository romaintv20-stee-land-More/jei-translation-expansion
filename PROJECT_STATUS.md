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

## Latest completed milestone — G13 Minecraft 1.13.2

Endpoint:
- Minecraft `1.13.2`
- JEI `5.0.0`
- final branch `1.13` HEAD `2d16f4210cbae340ad76b483b4aa8b461561e86f`
- Forge `25.0.85`, group `net.minecraftforge`
- mappings `snapshot` / `20180921-1.13`
- Java 8
- JSON languages, lowercase locale filenames

English source/diff:
- `upstream/sources/1.13.2/en_us.json`
- 106 semantic keys = 103 normal + 3 debug
- G12→G13 = 101 unchanged, 1 added, 0 removed, 4 changed
- 1 changed key is debug-only; 4 normal added/changed meanings are reviewed
- `upstream/diffs/1.13-to-1.13.2.json`

Minecraft scope:
- asset index id `1.13.1`
- asset SHA `a8ef90d58d4a170f85e3439470c99c25aa8e988b`
- raw language inventory = 118
- new selected primary languages: `bar`, `kk_kz`, `moh_ca`, `tt_ru`
- `fra_de` deferred as a regional/dialect German variety
- selected scope = 87

Ownership:
- 66 addon-owned full JSON locales
- 19 exact missing-key-only JSON supplements
- 2 complete selected upstream locales: `en_us`, `pl_pl`
- seven G12-complete upstream locales (`de_de`, `fr_fr`, `ja_jp`, `pt_br`, `ru_ru`, `sv_se`, `zh_cn`) become supplements because JEI 5.0.0 lacks only the re-added `key.jei.toggleEditMode`
- 27 documented complete-English fallback locales
- 39 translated/AI-assisted addon-full locales

Semantic/reconstruction rules:
1. Reuse the 101 G12 values only when key + English value are exactly unchanged.
2. `key.jei.toggleEditMode` uses target English when project-owned; its G13 English does not exactly match the older G11 value.
3. `gui.jei.editMode.description.hide` and `.hide.wild` changed from literal `%CTRL` to runtime placeholder `%s`; no G12 value may be reused.
4. Changed/new project-owned meanings use exact target English fallback.
5. Supplements remain missing-key-only and never override upstream-owned JEI keys.

G13 files:
- `scripts/audit_1_13_2.py`
- `scripts/reconstruct_1_13_2.py`
- `scripts/validate_1_13_2_delta.py`
- `scripts/validate_1_13_2_complete.py`
- `upstream/minecraft-1.13.2-language-audit.json`
- `upstream/minecraft-1.13.2-language-scope.json`
- `translations/g13-mc1.13.2/policy.json`

Full G1→G13 CI run **34671958137** is green.

## Current task — Minecraft 1.14.x

Historical upstream branch `1.14` currently ends at:
- HEAD `de8b6a10eba45899be1c62694c9f27a435ae8c2c`
- Minecraft `1.14.4`
- JEI `6.0.1`
- Forge `28.1.85`
- mappings `20191105-1.14.3`
- JSON languages

Do **not** assume the whole branch is one Minecraft target. Immediate next work:
1. inspect branch history for transitions among 1.14 / 1.14.1 / 1.14.2 / 1.14.3 / 1.14.4;
2. pin the last commit for each actual Minecraft version represented by JEI;
3. start the next chronological generation from the earliest real endpoint after 1.13.2;
4. audit English diff, Mojang language inventory, JEI ownership, reconstruction and CI for each endpoint separately.

## Release gates still open

- Minecraft 1.8.9 prototype JAR still requires a real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

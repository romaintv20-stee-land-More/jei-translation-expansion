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

## Latest completed milestone — G12 Minecraft 1.13

Endpoint:
- Minecraft `1.13`
- JEI `4.14.4`
- commit `380bc11efb548abd804c65b763c911ebf9d06e2c`
- Forge `24.0.181-1.13-pre`, group `net.minecraftforge.test`
- mappings `snapshot` / `20180921-1.13`
- Java 8
- language format **JSON**, lowercase locale filenames

Source/diff:
- `upstream/sources/1.13/en_us.json`
- 105 semantic keys = 102 normal + 3 debug
- G11→G12 = 59 unchanged, 4 added, 14 removed, 42 changed
- 43 normal added/changed meanings reviewed
- `upstream/diffs/1.12.2-to-1.13.json`

Minecraft scope:
- asset SHA `2175b85e150c64f7ed285e7624b87c18cd992497`
- raw language inventory = 113
- runtime locale rename `ksh_de` → `ksh`
- new selected primary languages: `nuk`, `ovd`, `szl`
- selected project scope = 83

Ownership:
- 62 addon-owned full JSON locales
- 12 exact missing-key-only JSON supplements
- 9 selected locales complete upstream
- 23 documented complete-English fallback locales
- 39 translated/AI-assisted addon-full locales

Reconstruction policy:
1. Reuse exact G11 combined value only when key + English value are identical.
2. If G12 differs from G11 but exactly returns to the same key/value found in G10, reuse the exact G10 combined value.
3. Otherwise use exact G12 English for project-owned missing meanings.
4. Never reuse across renamed keys; Tag keys do not inherit Ore Dictionary keys.
5. Reject historical values that lose placeholders or fixed literals such as `JEI`, `Minecraft`, `/give`, `mB`, or required format tokens.

Scripts:
- `scripts/audit_1_13.py`
- `scripts/reconstruct_1_13.py`
- `scripts/validate_1_13_delta.py`
- `scripts/validate_1_13_complete.py`

Full G1→G12 CI run **34671542080** is green.

## Current task — G13 Minecraft 1.13.2

The upstream `1.13` branch jumps directly from 1.13 to 1.13.2 at transition commit `a05771ea4ff870381302afe76d5c2298e0a1efe8`. No distinct 1.13.1 JEI endpoint has been found.

Previously observed final branch HEAD candidate:
`2d16f4210cbae340ad76b483b4aa8b461561e86f`

Previously observed build metadata at that candidate:
- Minecraft `1.13.2`
- JEI `5.0.0`
- Forge `25.0.85`
- Forge group `net.minecraftforge`
- MCP mappings `20180921-1.13`
- JSON languages

### Immediate next actions

1. Re-verify branch `1.13` HEAD and final 1.13.2 build metadata.
2. Pin final `en_us.json` and compute exact G12→G13 semantic diff.
3. Audit Minecraft 1.13.2 asset index and language inventory/scope changes.
4. Audit final JEI JSON locale ownership/completeness.
5. Freeze `upstream/minecraft-1.13.2-language-audit.json`, scope, diff and G13 policy.
6. Add deterministic reconstruction + QA to CI and obtain a green run.
7. Update canonical manifests/docs, then continue chronologically.

## Release gates still open

- Minecraft 1.8.9 prototype JAR has not yet received the required real client runtime validation.
- Minecraft 1.13+ missing-key-only JSON supplements require a real runtime resource-stack merge test before promotion to their version-specific release JAR.

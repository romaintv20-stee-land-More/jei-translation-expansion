# Translation Status

This file summarizes completed localization generations. Exact endpoint metadata lives in `upstream/versions.json`; generation/reuse metadata lives in `upstream/generations.json`. The fixed distribution rule is **one Minecraft version per final JAR**.

## Completed generations

| Generation | Minecraft | JEI | Keys | Selected scope | Addon full locales | Exact upstream supplements | Complete selected upstream | CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G1 | 1.8 | 2.15.0 | 58 | 60 | 54 | — | 6 JEI files audited | validator complete |
| G2 | 1.8.9 | 2.28.18 | 75 | inherited | 54 | 5 | 1 (`en_US`) | prototype `34632859235` |
| G3 | 1.9 | 3.3.3 | 77 | 70 | 63 | 5 | 1 | `34638556534` |
| G4 | 1.9.4 | 3.6.8 | 80 | 70 | 63 | 6 | 1 | `34639831977` |
| G5 | 1.10 | 3.7.1 | 78 | 72 | 65 | 6 | 1 | `34641765047` |
| G6 | 1.10.2 | 3.14.8 | 87 | 72 | 52 | 16 | 4 | `34642956606` |
| G7 | 1.11 | 4.1.1 | 87 | 72 | 52 | 16 | 4 | `34644034423` |
| G8 | 1.11.2 | 4.5.1 | 93 | 72 | 52 | 19 | 1 | `34644712028` |

## G1 — Minecraft 1.8 / JEI 2.15.0

Status: **selected scope complete**.

- 58 keys = 55 normal + 3 debug-only.
- 54 addon-owned full locales.
- 51 translated / AI-assisted + 3 documented English fallbacks (`gv_IM`, `kw_GB`, `se_NO`).

## G2 — Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible prototype JAR builds; real runtime test pending**.

- G1→G2: 46 unchanged, 19 added, 2 removed, 10 changed English values.
- 54 reconstructed addon full locales.
- Exact supplements for `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`.
- Prototype run **34632859235**; JAR SHA-256 `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`.
- Do not promote to `release-jars/1.8.9/` before real client runtime validation.

## G3 — Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language scope complete; CI green**.

Pinned commit `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`.

- 77 keys = 74 normal + 3 debug.
- G2→G3: 74 unchanged, 2 added, 0 removed, 1 changed.
- 63 addon full locales = 53 translated/AI-assisted + 10 documented English fallbacks.
- 5 exact upstream supplements.
- CI **34638556534**.

## G4 — Minecraft 1.9.4 / JEI 3.6.8

Status: **selected 70-language scope complete; CI green**.

Pinned commit `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`.

- 80 keys = 77 normal + 3 debug.
- G3→G4: 76 unchanged, 3 added, 0 removed, 1 changed.
- Minecraft asset index/scope unchanged from 1.9.
- 63 addon full locales + 6 exact supplements.
- G4 rebuilds supplements from exact current upstream missing sets instead of blindly inheriting old supplement files.
- CI **34639831977**.

## G5 — Minecraft 1.10 / JEI 3.7.1

Status: **selected 72-language scope complete; CI green**.

Pinned commit `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`.

- 78 keys = 75 normal + 3 debug.
- G4→G5: 77 unchanged, 0 added, 2 removed, 1 changed.
- `Crafting` → `Crafting Table` is an exact semantic return to G3, so G3 translations are reused.
- Minecraft raw inventory grows from 90 to 94; `haw_US` and `mn_MN` join the selected scope, while `de_AT` and `swg_de` remain deferred variants.
- 65 addon full locales + 6 exact supplements.
- 12 documented full-English fallback locales total.
- CI **34641765047**.

## G6 — Minecraft 1.10.2 / JEI 3.14.8

Status: **selected 72-language scope complete; CI green**.

Pinned final branch endpoint `446af20eaa73d260517f0adc737232437363f78d`.

- Forge `12.18.3.2254`; MCP `snapshot_20161111`; Java source/target `1.6`.
- 87 keys = 84 normal + 3 debug.
- G5→G6: 53 unchanged, 25 added, 16 removed, 9 changed.
- `Crafting Table` → `Crafting` reuses the exact G4 semantic translation; the other newly reviewed meanings use documented target-English fallback when no validated translation exists.
- Minecraft raw/selected = 94 / 72.
- JEI expands to 23 upstream locale files.
- 52 addon full locales + 16 exact supplements; `de_DE`, `en_US`, `ru_RU`, `uk_UA` are complete upstream.
- CI **34642956606**.

## G7 — Minecraft 1.11 / JEI 4.1.1

Status: **selected 72-language scope complete; CI green**.

Pinned endpoint `c9fcc36ff0effec2b5239eebd2c9133da04df4bb`, immediately before the branch transitions to 1.11.2.

- Forge `13.19.1.2188`; MCP `snapshot_20161205`; Java source/target `1.6`.
- JEI resource locale filenames switch to lowercase (`en_us.lang`).
- 87 keys, byte-identical to G6: **87 unchanged, 0 added, 0 removed, 0 changed**.
- Minecraft raw inventory grows to 95 only because of `io_ido`; Ido is deferred as a constructed language, so selected scope remains 72.
- Ownership: 52 addon full locales + 16 supplements + 4 complete upstream (`en_us`, `ru_ru`, `sv_se`, `uk_ua`).
- `de_de` becomes incomplete; its 16 vanished JEI translations are preserved exactly from pinned G6 upstream in `translations/g7-mc1.11/de_de-from-g6-upstream.lang`.
- `sv_se` becomes complete, so its older supplement is retired.
- CI **34644034423**.

## G8 — Minecraft 1.11.2 / JEI 4.5.1

Status: **selected 72-language scope complete; CI green**.

Pinned final branch endpoint `11023c1f4449b82d0b88366001b058e6949b40ab`.

- Forge `13.20.0.2315`; MCP `snapshot_20170425`; Java source/target `1.6`.
- 93 keys = 90 normal + 3 debug.
- G7→G8: **85 unchanged, 7 added, 1 removed, 1 changed**.
- Added keys cover max-subtype configuration, ResourceId search, item information and previous/next-page controls; `key.jei.recipeBack` changes meaning to “Show Previously Viewed Recipe”.
- Minecraft 1.11.2 reuses the exact Minecraft 1.11 asset index: raw/selected remains 95 / 72.
- 52 addon full locales + **19 exact supplements**; `en_us` is the only selected upstream locale complete in JEI 4.5.1.
- The 85 unchanged meanings inherit G7 exactly. The 8 reviewed G8 meanings use documented target-English fallback only when project-owned and not translated upstream.
- QA contains an anti-loss assertion: an unchanged key newly missing upstream may not silently fall back to English if a G7 project translation should exist.
- CI **34644712028**.

Files:

- `upstream/diffs/1.11-to-1.11.2.json`
- `upstream/minecraft-1.11.2-language-audit.json`
- `upstream/minecraft-1.11.2-language-scope.json`
- `translations/g8-mc1.11.2/policy.json`
- `scripts/reconstruct_1_11_2.py`
- `scripts/validate_1_11_2_delta.py`
- `scripts/validate_1_11_2_complete.py`

## Next version

G8 is complete. The next historical upstream family is `1.12`, but upstream contains both `1.12` and `1.12-FG3`. Their actual history/build metadata must be audited before G9 is assigned to a Minecraft version.

## Release limitation

Chronological translation/reconstruction auditing may continue before runtime-tested release JARs are finalized. Final distribution remains strictly **one Minecraft version per JAR**.

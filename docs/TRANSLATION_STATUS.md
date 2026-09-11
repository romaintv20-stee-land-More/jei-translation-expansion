# Translation Status

This file summarizes completed localization generations. Exact endpoint metadata lives in `upstream/versions.json`; generation/reuse metadata lives in `upstream/generations.json`.

## Minecraft 1.8 / JEI 2.15.0

Status: **selected language-file scope complete**.

- 58 keys = 55 normal + 3 debug-only
- selected scope: 60 languages
- 54 addon-owned full locales
- 51 translated / AI-assisted locales
- 3 documented full-English fallbacks: `gv_IM`, `kw_GB`, `se_NO`
- validator: `scripts/validate_translations.py`

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible prototype JAR builds; real runtime test still pending**.

- 75 keys = 72 normal + 3 debug-only
- diff from 1.8: 46 unchanged, 19 added, 2 removed, 10 changed English values
- 54 addon-owned full locales reconstructed from G1 + G2
- exact upstream supplements: `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- prototype build run: **34632859235**
- prototype SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`

Do not promote to `release-jars/1.8.9/` until a real Minecraft/Forge/JEI runtime test succeeds.

## Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction scope complete; CI green**.

Pinned upstream commit: `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`.

- 77 keys = 74 normal + 3 debug-only
- diff from 1.8.9: 74 unchanged, 2 added, 0 removed, 1 changed value
- Minecraft raw inventory: 90 codes
- selected scope: 70 languages
- 63 addon-owned full locales
- 53 translated / AI-assisted full locales
- 10 documented full-English fallback locales
- 5 selected upstream missing-key supplements
- CI run: **34638556534**

Files:

- `upstream/diffs/1.8.9-to-1.9.json`
- `upstream/minecraft-1.9-language-scope.json`
- `translations/g3-mc1.9/`
- `scripts/reconstruct_1_9.py`
- `scripts/validate_1_9_delta.py`
- `scripts/validate_1_9_complete.py`

## Minecraft 1.9.4 / JEI 3.6.8

Status: **selected 70-language translation/reconstruction scope complete; CI green**.

Pinned upstream commit: `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`.

- 80 keys = 77 normal + 3 debug-only
- diff from 1.9: 76 unchanged, 3 added, 0 removed, 1 changed value
- same Minecraft asset index and selected 70-language scope as 1.9
- 63 addon-owned full locales
- 53 translated / AI-assisted + 10 documented full-English fallbacks
- 6 exact selected upstream supplements
- CI run: **34639831977**

G4 rebuilds supplements from the exact keys still missing in JEI 3.6.8 instead of carrying old supplements wholesale. `ko_KR` uses `제작` for the generic `Crafting` meaning.

Files:

- `upstream/diffs/1.9-to-1.9.4.json`
- `upstream/minecraft-1.9.4-language-scope.json`
- `translations/g4-mc1.9.4/`
- `scripts/reconstruct_1_9_4.py`
- `scripts/validate_1_9_4_delta.py`
- `scripts/validate_1_9_4_complete.py`

## Minecraft 1.10 / JEI 3.7.1

Status: **selected 72-language translation/reconstruction scope complete; CI green**.

Pinned upstream commit: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`.

- 78 keys = 75 normal + 3 debug-only
- diff from 1.9.4: 77 unchanged, 0 added, 2 removed, 1 changed value
- `gui.jei.category.craftingTable` returns from `Crafting` to `Crafting Table`, so validated G3 translations are reused
- Minecraft raw inventory grows from 90 to 94 codes
- selected scope grows from 70 to 72 with `haw_US` and `mn_MN`
- `de_AT` and `swg_de` remain deferred regional/dialect variants
- 65 addon-owned full locales
- 53 translated / AI-assisted + 12 documented full-English fallbacks
- 6 exact selected upstream supplements
- CI run: **34641765047**

Files:

- `upstream/diffs/1.9.4-to-1.10.json`
- `upstream/minecraft-1.10-language-scope.json`
- `translations/g5-mc1.10/`
- `scripts/reconstruct_1_10.py`
- `scripts/validate_1_10_delta.py`
- `scripts/validate_1_10_complete.py`

## Minecraft 1.10.2 / JEI 3.14.8

Status: **selected 72-language translation/reconstruction scope complete; CI green**.

Pinned final endpoint of the historical upstream `1.10` branch:

`446af20eaa73d260517f0adc737232437363f78d`

Verified build metadata:

- Forge `12.18.3.2254`
- MCP mappings `snapshot_20161111`
- Java source/target `1.6`
- legacy `.lang`

### English/G6 transition

- source: `upstream/sources/1.10.2/en_US.lang`
- 87 keys = 84 normal + 3 debug-only
- versus 1.10: **53 unchanged**, **25 added**, **16 removed**, **9 changed English values**
- 34 added/changed keys require review
- `gui.jei.category.craftingTable` is an exact semantic return to G4 `Crafting`, so G4 translations are reused for that key
- for the other 33 added/changed entries, target English is used when no validated exact-semantic translation exists rather than inventing low-confidence technical translations

Exact diff: `upstream/diffs/1.10-to-1.10.2.json`.

### Scope and ownership

Minecraft 1.10.2 reuses the exact 1.10 asset index, so the raw inventory remains **94 codes** and the selected project scope remains **72 languages**.

JEI 3.14.8 expands to **23 upstream locale files**. Within the selected scope:

- 20 matching selected upstream locales exist
- 4 are fully complete upstream: `de_DE`, `en_US`, `ru_RU`, `uk_UA`
- 16 are incomplete and receive exact missing-key-only supplements
- 52 locales remain addon-owned full files
- 40 of those retain translated / AI-assisted inherited content
- 12 remain documented full-English fallbacks
- `en_AU`, `nb_NO`, `zh_TW` are preserved upstream but are not matching selected project locale codes

The 16 supplement locales are:

`ar_SA`, `bg_BG`, `cs_CZ`, `el_GR`, `es_ES`, `fi_FI`, `fr_FR`, `he_IL`, `it_IT`, `ja_JP`, `ko_KR`, `lt_LT`, `pl_PL`, `pt_BR`, `sv_SE`, `zh_CN`.

### Automation and CI

- policy: `translations/g6-mc1.10.2/policy.json`
- deterministic reconstruction: `scripts/reconstruct_1_10_2.py`
- source/scope/upstream QA: `scripts/validate_1_10_2_delta.py`
- complete QA: `scripts/validate_1_10_2_complete.py`
- successful workflow run: **34642956606**

The validated G6 result is exactly **52 complete 87-key addon locale files + 16 exact missing-key-only upstream supplements**, with no addon file for selected locales already complete upstream.

## Next version

G6 is complete. The next chronological Minecraft target must be selected from actual JEI upstream branch/history metadata before a G7 generation is created. Do not infer the target solely from branch naming.

## Release limitation

Historical translation/reconstruction work may continue chronologically before runtime-tested release JARs are finalized. The fixed distribution rule remains **one Minecraft version per final JAR**.

# JEI Translation Expansion — Project Status

> **Canonical handoff file. Start here in a new chat.**

Last synchronized: **2026-09-11**

## Project rules

- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Upstream: https://github.com/mezz/JustEnoughItems
- Unofficial MIT localization companion for JEI; no gameplay content.
- **One Minecraft version per final JAR. Never group multiple Minecraft versions in one artifact.**
- Final runtime-validated JARs go in `release-jars/<minecraft-version>/`; prototypes do not.
- Translation reuse between versions is allowed only when both localization key and English meaning are unchanged.
- Preserve upstream JEI translations. For a locale already shipped by JEI, add only missing keys unless an override is explicitly approved.
- Preserve placeholders and technical literals exactly. Prefer a documented English fallback to an uncertain translation.
- Initial scope focuses on real-world primary Minecraft languages; novelty/fantasy entries, constructed non-primary languages and most regional variants are excluded/deferred.

## Minecraft 1.8 / JEI 2.15.0

Status: **selected translation scope complete**.

- 58 keys = 55 normal + 3 debug-only.
- Selected scope: 60 languages.
- 54 addon-owned full locales: 51 translated/AI-assisted + 3 English fallbacks (`gv_IM`, `kw_GB`, `se_NO`).

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible Forge prototype passes static CI; real runtime test still pending**.

- 75 keys = 72 normal + 3 debug-only.
- Exact 1.8 -> 1.8.9 diff: 46 unchanged, 19 added, 2 removed, 10 changed English values.
- 54 absent-locale files reconstruct from G1 + G2.
- Missing-key-only supplements complete `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`.
- Latest successful static prototype build run: `34632859235`.
- JAR SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`.

Do **not** promote to `release-jars/1.8.9/` yet. Remaining blocker: real Minecraft 1.8.9 + compatible Forge + JEI 2.28.18 client test. Details: `packaging/1.8.9/release.json`.

## Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

- pinned commit `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`
- 77 keys = 74 normal + 3 debug-only
- 74 unchanged, 2 added, 0 removed, 1 changed vs 1.8.9
- raw Minecraft inventory 90; selected scope 70
- 63 complete addon locales + 5 exact supplements
- 53 translated/AI-assisted + 10 documented full-English fallbacks
- CI run **34638556534**

## Minecraft 1.9.4 / JEI 3.6.8

Status: **selected 70-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

- pinned commit `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`
- 80 keys = 77 normal + 3 debug-only
- 76 unchanged, 3 added, 0 removed, 1 changed vs 1.9
- raw Minecraft inventory 90; selected scope 70
- 63 complete addon locales + 6 exact supplements
- 53 translated/AI-assisted + 10 documented full-English fallbacks
- CI run **34639831977**

Important G4 rule: JEI 3.6.8 gained many `ru_RU` and `zh_CN` translations upstream, so supplements are rebuilt against exact current missing sets. `ko_KR` uses `제작` for generic `Crafting`.

## Minecraft 1.10 / JEI 3.7.1

Status: **selected 72-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned endpoint: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`, direct parent of the Minecraft 1.10.2 transition commit `c88aa6c5c078586fa23abaa83309d293cd72ea61`.

- Forge `12.18.0.1999-1.10.0`; MCP `snapshot_20160518`; Java 1.7; legacy `.lang`
- 78 keys = 75 normal + 3 debug-only
- 77 unchanged, 0 added, 2 removed, 1 changed vs 1.9.4
- changed `gui.jei.category.craftingTable`: `Crafting` -> `Crafting Table`; exact semantic return to G3, so G3 translations reused
- Minecraft raw inventory 94 after additions `de_AT`, `haw_US`, `mn_MN`, `swg_de`
- selected scope 72: retain `haw_US`, `mn_MN`; defer regional `de_AT`, `swg_de`
- 65 complete addon locales + 6 exact supplements
- 53 translated/AI-assisted + 12 documented full-English fallbacks
- CI run **34641765047**

## Minecraft 1.10.2 / JEI 3.14.8

Status: **endpoint/source/scope/upstream-ownership audit complete; G6 reconstruction and validators implemented; CI validation pending**.

Pinned final endpoint of historical upstream branch `1.10`:

`446af20eaa73d260517f0adc737232437363f78d`

Verified build metadata:

- Minecraft `1.10.2`
- JEI `3.14.8`
- Forge `12.18.3.2511`
- MCP mappings `snapshot_20161111`
- Java source/target **1.8**
- legacy `.lang`
- English source `upstream/sources/1.10.2/en_US.lang`

The earlier commit `c88aa6c5...` is only the first 1.10.2 transition (JEI 3.7.2); branch HEAD remains Minecraft 1.10.2 and is the final JEI 3.14.8 endpoint, so it is the selected 1.10.2 audit target.

### Exact G5 -> G6 English diff

Target: **87 keys = 84 normal + 3 debug-only**.

- **53 unchanged key/value pairs** reusable
- **25 added keys**
- **16 removed keys**
- **9 changed English values**
- total reviewed added/changed keys: **34**

Exact manifest: `upstream/diffs/1.10-to-1.10.2.json`.

One changed key has a safe exact-semantic reuse source:

- `gui.jei.category.craftingTable`: `Crafting Table` -> `Crafting`, exactly matching G4 / Minecraft 1.9.4, so G4 translations can be restored.

The other 33 added/changed entries use the conservative project rule: if no reliable already-validated exact-semantic translation exists, emit target English rather than inventing a low-confidence technical translation. This is especially important for the new `%CTRL` placeholder-bearing edit-mode strings.

### Minecraft language scope

Minecraft 1.10.2 reuses the exact Minecraft 1.10 asset index:

- asset index id `1.10`
- SHA-1 `7c2800b458376b8fc0b738382fb7784328fddda9`
- raw inventory remains **94 codes**
- selected project scope remains **72 languages**

### JEI 3.14.8 ownership expansion

JEI upstream grows from 8 locale files in 3.7.1 to **23 locale files** in 3.14.8:

`ar_SA`, `bg_BG`, `cs_CZ`, `de_DE`, `el_GR`, `en_AU`, `en_US`, `es_ES`, `fi_FI`, `fr_FR`, `he_IL`, `it_IT`, `ja_JP`, `ko_KR`, `lt_LT`, `nb_NO`, `pl_PL`, `pt_BR`, `ru_RU`, `sv_SE`, `uk_UA`, `zh_CN`, `zh_TW`.

Within the selected 72-language project scope:

- selected upstream locales: **20**
- complete upstream selected locales: **4** — `de_DE`, `en_US`, `ru_RU`, `uk_UA`
- incomplete upstream selected locales requiring exact missing-key supplements: **16**
- addon-owned full locales: **52**
- unselected/nonmatching upstream locales preserved untouched: `en_AU`, `nb_NO`, `zh_TW`

The 16 selected supplement locales are:

`ar_SA`, `bg_BG`, `cs_CZ`, `el_GR`, `es_ES`, `fi_FI`, `fr_FR`, `he_IL`, `it_IT`, `ja_JP`, `ko_KR`, `lt_LT`, `pl_PL`, `pt_BR`, `sv_SE`, `zh_CN`.

Important examples:

- `ja_JP`: 82/84 normal keys, only `key.jei.ctrl` and `key.jei.ctrl.mac` missing
- `zh_CN`: 74/84, only the ten new search-mode keys/comments missing
- `de_DE`, `ru_RU`, `uk_UA`: fully complete upstream; addon must emit nothing for them
- `fi_FI`: 50/84, 34 missing

Full exhaustive audit: `upstream/minecraft-1.10.2-language-audit.json`.

### G6 realization policy

- 52 complete addon files
- 16 exact missing-key-only supplements
- 4 complete selected upstream locales receive no addon file
- 12 existing full-English fallback locales remain full fallbacks
- 40 addon-owned locales retain translated/AI-assisted inherited content on safely reusable keys
- 53 unchanged key/value pairs reuse G5 project translations where the addon owns them
- `Crafting` exact semantic reversion reuses G4 where available
- remaining 33 added/changed entries use documented target-English fallback when no validated exact-semantic translation exists
- existing JEI upstream keys are never emitted in supplements

Files already committed:

- `upstream/sources/1.10.2/en_US.lang`
- `upstream/diffs/1.10-to-1.10.2.json`
- `upstream/minecraft-1.10.2-language-audit.json`
- `upstream/minecraft-1.10.2-language-scope.json`
- `translations/g6-mc1.10.2/policy.json`
- `scripts/audit_1_10_2.py`
- `scripts/reconstruct_1_10_2.py`
- `scripts/validate_1_10_2_delta.py`
- `scripts/validate_1_10_2_complete.py`

Initial endpoint audit run: **34642438873**, successful.

## Current task

1. Add the G6 reconstruction/QA steps to `.github/workflows/validate.yml`.
2. Run CI and fix any deterministic reconstruction, placeholder or ownership failures.
3. Once green, mark Minecraft 1.10.2 complete for the selected translation/reconstruction scope.
4. Update `upstream/versions.json`, `upstream/generations.json`, README and docs.
5. Continue chronologically to the next Minecraft version as a separate future JAR target.

## Modern endpoint

Branch `26.2` uses JSON language files at `Common/src/main/resources/assets/jei/lang/`; full audit is still pending.

## Important handoff files

- `PROJECT_STATUS.md` — canonical handoff
- `README.md`
- `docs/WORKFLOW.md`
- `docs/VERSION_MATRIX.md`
- `docs/TRANSLATION_STATUS.md`
- `upstream/versions.json`
- `upstream/generations.json`
- `upstream/minecraft-1.10.2-language-audit.json`
- `upstream/minecraft-1.10.2-language-scope.json`
- `packaging/1.8.9/release.json`

## Resume prompt

> Reprends JEI Translation Expansion depuis `PROJECT_STATUS.md`. Minecraft 1.10 est termine. Minecraft 1.10.2 cible le HEAD final de la branche historique 1.10, commit `446af20eaa73d260517f0adc737232437363f78d`, JEI 3.14.8. Audit: 87 cles (84 normales), diff G5->G6 = 53 inchangees, 25 ajoutees, 16 supprimees, 9 modifiees; scope Minecraft reste 94 brut / 72 selectionne. JEI a 23 locales upstream; dans le scope, 4 sont completes, 16 ont besoin d'un supplement exact et 52 restent addon-owned. G6 reconstruction/validators sont deja ecrits; brancher la CI puis obtenir un run vert. Regle fixe: un JAR distinct par version Minecraft.

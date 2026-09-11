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

- English: 58 keys = 55 normal + 3 debug-only.
- Selected scope: 60 languages.
- 54 addon-owned full locales: 51 translated/AI-assisted + 3 English fallbacks (`gv_IM`, `kw_GB`, `se_NO`).

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible Forge prototype passes static CI; real runtime test still pending**.

- English: 75 keys = 72 normal + 3 debug-only.
- Exact 1.8 -> 1.8.9 diff: 46 unchanged, 19 added, 2 removed, 10 changed English values.
- 54 absent-locale files reconstruct from G1 + G2.
- Missing-key-only supplements complete `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`.
- Latest successful static prototype build run: `34632859235`.
- JAR SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`.

Do **not** promote to `release-jars/1.8.9/` yet. Remaining blocker: real Minecraft 1.8.9 + compatible Forge + JEI 2.28.18 client test. Details: `packaging/1.8.9/release.json`.

## Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned JEI endpoint:

`b2ffe6bd7734d093006de99f9dc99b2b77ce780d`

Verified:

- Minecraft `1.9`
- JEI `3.3.3`
- Forge `12.16.0.1865-1.9`
- MCP `snapshot_20160421`
- Java 1.7; legacy `.lang`
- 77 keys = 74 normal + 3 debug-only
- scope: 70 languages
- output: 63 complete addon locales + 5 missing-key-only upstream supplements
- complete addon result: 53 translated/AI-assisted + 10 documented English fallbacks
- complete validation run: **34638556534**

Important files:

- `upstream/sources/1.9/en_US.lang`
- `upstream/diffs/1.8.9-to-1.9.json`
- `upstream/minecraft-1.9-language-audit.json`
- `upstream/minecraft-1.9-language-scope.json`
- `translations/g3-mc1.9/`
- `scripts/reconstruct_1_9.py`
- `scripts/validate_1_9_delta.py`
- `scripts/validate_1_9_complete.py`

## Minecraft 1.9.4 / JEI 3.6.8

Status: **exact upstream/language audit complete; translation G4 and deterministic reconstruction are the current work**.

### Pinned endpoint

The current HEAD of the historical upstream branch `1.9` is:

`bd9fcad11a8b92d181fc8c2ec976e31c7467799a`

Verified directly from upstream:

- Minecraft `1.9.4`
- JEI `3.6.8`
- Forge `12.17.0.1962`
- MCP mappings `snapshot_20160518`
- Java source/target 1.7
- legacy `.lang`
- English source `upstream/sources/1.9.4/en_US.lang`
- 80 keys = 77 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### Exact 1.9 -> 1.9.4 localization diff

- **76 unchanged key/value pairs reusable**
- **3 added keys**:
  - `jei.tooltip.cheat.mode=Cheat Mode`
  - `config.jei.advanced.hideLaggyModelsEnabled=Hide Items with Laggy Models`
  - `config.jei.advanced.hideLaggyModelsEnabled.comment=Items with models that cause a long delay will be hidden from the item list.`
- **0 removed**
- **1 changed English value**:
  - `gui.jei.category.craftingTable`: `Crafting Table` -> `Crafting`
- therefore **4 translated/reviewed G4 entries per complete addon locale**

Exact manifest: `upstream/diffs/1.9-to-1.9.4.json`.

### Minecraft language inventory / scope

Minecraft 1.9.4 uses asset index id `1.9`, SHA-1:

`d7aae43ea69d80cc3441bee4179abd791f6534cd`

This is the **exact same asset index** already audited for Minecraft 1.9. Therefore:

- raw language inventory remains 90 codes;
- no vanilla language code was added/removed for this target;
- the frozen selected project scope remains **70 languages**;
- `jbo_EN` / `tzl_TZL` stay deferred; novelty/regional exclusions stay unchanged;
- `no_NO` remains the Minecraft-facing addon locale while upstream `nb_NO` is preserved separately.

Scope manifest: `upstream/minecraft-1.9.4-language-scope.json`.

### JEI 3.6.8 upstream completeness

Only `en_US`, `ru_RU`, and `zh_CN` changed among JEI language files between the pinned 1.9 and 1.9.4 endpoints. `de_DE`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO` are byte-unchanged upstream.

| Locale | Normal present | Missing | Extra | Handling |
|---|---:|---:|---:|---|
| `de_DE` | 53/77 | 24 | 2 | missing-key supplement |
| `en_US` | 77/77 | 0 | 0 | upstream only |
| `fi_FI` | 58/77 | 19 | 2 | missing-key supplement |
| `fr_FR` | 74/77 | 3 | 0 | missing-key supplement |
| `ko_KR` | 5/77 | 72 | 0 | missing-key supplement |
| `nb_NO` | 74/77 | 3 | 0 | preserve upstream; not selected Minecraft code |
| `ru_RU` | 73/77 | 4 | 2 | missing-key supplement |
| `zh_CN` | 74/77 | 3 | 0 | missing-key supplement |

Selected-scope output therefore remains **63 complete addon locales**, but the number of selected upstream supplements becomes **6** (`de_DE`, `fi_FI`, `fr_FR`, `ko_KR`, `ru_RU`, `zh_CN`). Only `en_US` is complete upstream among the selected Minecraft-facing JEI locales.

Critical supplement rule for 1.9.4:

- do **not** blindly carry the 1.9 supplements forward;
- JEI 3.6.8 added many `ru_RU` and `zh_CN` keys upstream, so old addon entries that upstream now owns must disappear from the addon supplement;
- `fr_FR` now needs exactly the three new G4 keys;
- `ko_KR` still lacks `gui.jei.category.craftingTable`, so its addon value must be reviewed for the changed English meaning `Crafting Table` -> `Crafting`;
- for locales where that changed key already exists upstream, preserve the upstream translation and do not override it.

Full audit: `upstream/minecraft-1.9.4-language-audit.json`.

### Current next actions

1. Create G4 four-entry translation delta for all 63 complete addon locales, preserving the ten documented full-English fallback locales.
2. Build exact JEI 3.6.8 missing-key supplements for the six selected upstream locales, filtering out keys now translated upstream.
3. Add deterministic 1.9.4 reconstruction from G3 + G4.
4. Add complete QA/CI: key coverage, placeholders, technical literals, exact fallback policy and no-upstream-overwrite checks.
5. Update `upstream/generations.json`, `docs/VERSION_MATRIX.md`, `docs/TRANSLATION_STATUS.md`, and this file when G4 is green.
6. Then continue chronologically to the next Minecraft version.

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
- `upstream/minecraft-1.9.4-language-audit.json`
- `upstream/minecraft-1.9.4-language-scope.json`
- `packaging/1.8.9/release.json`

## Resume prompt

> Reprends JEI Translation Expansion depuis le depot et lis d'abord `PROJECT_STATUS.md`. Minecraft 1.9 / JEI 3.3.3 est termine au stade traduction/reconstruction, validation verte au run `34638556534`. Minecraft 1.9.4 / JEI 3.6.8 est epingle a `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`; son audit complet est termine: 80 cles, 76 reutilisables, 3 ajoutees, 1 valeur anglaise modifiee, scope identique de 70 langues, 63 locales addon completes et 6 supplements upstream. Prochaine etape: creer G4, reconstruire/valider 1.9.4, mettre les docs/status a jour, puis passer a la version Minecraft suivante. Regle fixe: un JAR distinct par version Minecraft.

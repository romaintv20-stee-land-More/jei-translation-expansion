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

Pinned JEI endpoint: `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`.

- Forge `12.16.0.1865-1.9`; MCP `snapshot_20160421`; Java 1.7; legacy `.lang`.
- 77 keys = 74 normal + 3 debug-only.
- 1.8.9 -> 1.9: 74 unchanged, 2 added, 0 removed, 1 changed English value.
- raw Minecraft inventory: 90 language codes.
- selected project scope: 70 languages.
- output: 63 complete addon locales + 5 missing-key-only selected upstream supplements.
- complete addon result: 53 translated/AI-assisted + 10 documented English fallbacks.
- complete validation run: **34638556534**.

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

Status: **selected 70-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned JEI endpoint: `bd9fcad11a8b92d181fc8c2ec976e31c7467799a` (historical branch `1.9` HEAD).

Verified build metadata:

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
  - `jei.tooltip.cheat.mode`
  - `config.jei.advanced.hideLaggyModelsEnabled`
  - `config.jei.advanced.hideLaggyModelsEnabled.comment`
- **0 removed**
- **1 changed English value**:
  - `gui.jei.category.craftingTable`: `Crafting Table` -> `Crafting`
- four G4 translated/reviewed entries per complete addon locale

Exact manifest: `upstream/diffs/1.9-to-1.9.4.json`.

### Language scope

Minecraft 1.9.4 uses the exact same vanilla asset index as Minecraft 1.9: id `1.9`, SHA-1 `d7aae43ea69d80cc3441bee4179abd791f6534cd`.

Therefore:

- raw inventory remains 90 codes;
- selected project scope remains **70 languages**;
- `jbo_EN` / `tzl_TZL` remain deferred;
- `no_NO` remains the Minecraft-facing addon locale while JEI's upstream `nb_NO` is preserved separately;
- complete addon target remains **63 locales**;
- full result remains **53 translated/AI-assisted + 10 documented English fallbacks**.

### JEI 3.6.8 upstream completeness and ownership

| Locale | Normal present | Missing | Handling |
|---|---:|---:|---|
| `de_DE` | 53/77 | 24 | missing-key supplement |
| `en_US` | 77/77 | 0 | upstream only |
| `fi_FI` | 58/77 | 19 | missing-key supplement |
| `fr_FR` | 74/77 | 3 | missing-key supplement |
| `ko_KR` | 5/77 | 72 | missing-key supplement |
| `nb_NO` | 74/77 | 3 | preserve upstream; not selected Minecraft code |
| `ru_RU` | 73/77 | 4 | missing-key supplement |
| `zh_CN` | 74/77 | 3 | missing-key supplement |

G4 rebuilds supplements against the exact JEI 3.6.8 missing sets instead of blindly inheriting G3. This is important because JEI 3.6.8 added many `ru_RU` and `zh_CN` translations upstream.

Special semantic review:

- `fr_FR` receives exactly the three new G4 keys;
- `ko_KR` still lacks `gui.jei.category.craftingTable` upstream, so its addon value was revised to `제작` for the new generic `Crafting` meaning;
- `ru_RU` outputs only four still-missing keys;
- `zh_CN` outputs only three still-missing keys;
- existing upstream-owned keys are never emitted by the addon supplement.

### G4 data and validation

- source audit: `upstream/minecraft-1.9.4-language-audit.json`
- scope: `upstream/minecraft-1.9.4-language-scope.json`
- delta: `translations/g4-mc1.9.4/delta.tsv`
- policy: `translations/g4-mc1.9.4/policy.json`
- supplement deltas: `translations/g4-mc1.9.4/upstream-supplement-delta/`
- reconstruction: `scripts/reconstruct_1_9_4.py`
- delta QA: `scripts/validate_1_9_4_delta.py`
- complete QA: `scripts/validate_1_9_4_complete.py`
- CI: `.github/workflows/validate.yml`
- successful complete validation run: **34639831977**

The successful run validates exactly **63 complete 80-key addon locale files + 6 selected missing-key-only upstream supplements**, including placeholders, technical literals, debug-English policy, documented fallbacks and no-upstream-overwrite guards.

## Minecraft 1.10 / JEI 3.7.1

Status: **audit/reconstruction work in progress; raw Minecraft language expansion discovered and classified**.

Pinned historical endpoint: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`, the direct parent of commit `c88aa6c5c078586fa23abaa83309d293cd72ea61` (`Update for Minecraft 1.10.2`).

Verified build metadata:

- Minecraft `1.10`
- JEI `3.7.1`
- Forge `12.18.0.1999-1.10.0`
- MCP mappings `snapshot_20160518`
- Java source/target 1.7
- legacy `.lang`
- English source path `src/main/resources/assets/jei/lang/en_US.lang`
- JEI locales remain `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### Exact 1.9.4 -> 1.10 English diff

- target has **78 keys = 75 normal + 3 debug-only**;
- **77 unchanged key/value pairs**;
- **0 added keys**;
- **2 removed keys**:
  - `config.jei.advanced.hideLaggyModelsEnabled`
  - `config.jei.advanced.hideLaggyModelsEnabled.comment`
- **1 changed English value**:
  - `gui.jei.category.craftingTable`: `Crafting` -> `Crafting Table`

This changed value is an exact semantic reversion to G3 / Minecraft 1.9, so G5 reuses the validated G3 translations. In particular, addon-owned `ko_KR` must revert from G4 `제작` to G3 `제작대`.

### Minecraft 1.10 language inventory discovery

The first G5 CI audit (`34641315392`) intentionally fetched the real Mojang 1.9 and 1.10 asset indexes and rejected the initial assumption that the inventory was unchanged.

Verified result:

- Minecraft 1.9 / 1.9.4 raw inventory: **90 codes**;
- Minecraft 1.10 raw inventory: **94 codes**;
- added: `de_AT`, `haw_US`, `mn_MN`, `swg_de`;
- removed: none.

Policy classification:

- `haw_US` — Hawaiian: new real-world primary language, **selected**;
- `mn_MN` — Mongolian: new real-world primary language, **selected**;
- `de_AT` — Austrian German: regional German variant, **deferred** under the existing regional-variant policy;
- `swg_de` — `Oschtallgaierisch`, regional German/Swabian variety, **deferred** under the same policy.

Therefore the correct Minecraft 1.10 target becomes:

- selected scope: **72 languages**;
- inherited selected languages from G4: 70;
- newly selected: `haw_US`, `mn_MN`;
- addon-owned full locales: **65** (63 inherited + 2 new);
- selected upstream-facing locales remain 7;
- exact missing-key-only upstream supplements remain 6.

Because reliable full technical translations are not guaranteed for Hawaiian or Mongolian in this pass, both new full locales will use **documented English fallback** rather than invented translations. This raises documented complete fallbacks from 10 to **12** while preserving the 53 already translated/AI-assisted full locales.

### JEI 3.7.1 upstream ownership

Only `en_US` and `ru_RU` changed from the pinned JEI 3.6.8 endpoint. `de_DE`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO` and `zh_CN` are byte-identical.

Target normal completeness:

- `de_DE`: 53/75, 22 missing;
- `en_US`: 75/75, complete;
- `fi_FI`: 58/75, 17 missing;
- `fr_FR`: 74/75, only `jei.tooltip.cheat.mode` missing;
- `ko_KR`: 5/75, 70 missing; crafting table addon value must be restored to `제작대`;
- `nb_NO`: 74/75, but preserved upstream and not used as Minecraft-facing `no_NO`;
- `ru_RU`: 73/75, only the two color-search keys missing;
- `zh_CN`: 74/75, only `jei.tooltip.cheat.mode` missing.

### G5 implementation state

Already committed:

- `upstream/sources/1.10/en_US.lang`
- `upstream/diffs/1.9.4-to-1.10.json`
- initial `upstream/minecraft-1.10-language-audit.json`
- initial `upstream/minecraft-1.10-language-scope.json`
- `translations/g5-mc1.10/policy.json`
- `scripts/reconstruct_1_10.py`
- `scripts/validate_1_10_delta.py`
- `scripts/validate_1_10_complete.py`
- G5 steps in `.github/workflows/validate.yml`

The audit/scope/policy/reconstruction files must now be corrected from the disproven 90/70/63 assumption to **94 raw / 72 selected / 65 full**, with `haw_US` and `mn_MN` documented as new English fallbacks. Then rerun CI.

## Current task

Finish the corrected Minecraft 1.10 / JEI 3.7.1 G5 implementation, obtain a green CI run, sync manifests/docs/status, then continue chronologically to Minecraft 1.10.2 as its own target/JAR lineage.

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
- `upstream/minecraft-1.10-language-audit.json`
- `upstream/minecraft-1.10-language-scope.json`
- `packaging/1.8.9/release.json`

## Resume prompt

> Reprends JEI Translation Expansion depuis le depot et lis d'abord `PROJECT_STATUS.md`. Minecraft 1.9 / JEI 3.3.3 et Minecraft 1.9.4 / JEI 3.6.8 sont termines au stade traduction/reconstruction. Minecraft 1.10 / JEI 3.7.1 est epingle au commit `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`. Le premier audit CI G5 a prouve que Minecraft 1.10 passe de 90 a 94 langues avec `de_AT`, `haw_US`, `mn_MN`, `swg_de`. Retenir `haw_US` et `mn_MN`, deferer les deux variantes regionales, donc scope 72 et 65 locales addon completes. Utiliser fallback anglais documente pour les deux nouvelles langues. Le diff JEI est 77 paires inchangees, 0 ajout, 2 suppressions et `Crafting` -> `Crafting Table`; restaurer les traductions G3, notamment `ko_KR=제작대`. Corriger G5 puis obtenir CI verte. Regle fixe: un JAR distinct par version Minecraft.

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

## Minecraft 1.9.4 / JEI 3.6.8

Status: **selected 70-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned JEI endpoint: `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`.

- Minecraft `1.9.4`; JEI `3.6.8`; Forge `12.17.0.1962`; MCP `snapshot_20160518`; Java 1.7.
- 80 keys = 77 normal + 3 debug-only.
- 1.9 -> 1.9.4: 76 unchanged, 3 added, 0 removed, 1 changed English value.
- raw Minecraft inventory: 90 codes; selected scope: 70.
- output: 63 complete addon locales + 6 exact missing-key-only upstream supplements.
- complete addon result: 53 translated/AI-assisted + 10 documented English fallbacks.
- complete validation run: **34639831977**.

Important G4 rule: JEI 3.6.8 gained many `ru_RU` and `zh_CN` translations upstream, so supplements are rebuilt against exact current missing sets instead of blindly inheriting G3. `ko_KR` uses `제작` for the G4 generic `Crafting` meaning.

## Minecraft 1.10 / JEI 3.7.1

Status: **selected 72-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned historical endpoint: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`, direct parent of transition commit `c88aa6c5c078586fa23abaa83309d293cd72ea61` (`Update for Minecraft 1.10.2`).

Verified build metadata:

- Minecraft `1.10`
- JEI `3.7.1`
- Forge `12.18.0.1999-1.10.0`
- MCP mappings `snapshot_20160518`
- Java source/target 1.7
- legacy `.lang`
- 78 keys = 75 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### Exact 1.9.4 -> 1.10 localization diff

- **77 unchanged key/value pairs**
- **0 added**
- **2 removed**:
  - `config.jei.advanced.hideLaggyModelsEnabled`
  - `config.jei.advanced.hideLaggyModelsEnabled.comment`
- **1 changed value**:
  - `gui.jei.category.craftingTable`: `Crafting` -> `Crafting Table`

The changed value is an exact semantic return to G3, so G5 restores the validated G3 translations rather than translating again. In particular `ko_KR` returns from G4 `제작` to G3 `제작대`.

### Minecraft 1.10 language inventory

The live Mojang asset-index QA proved that Minecraft 1.10 expands from 90 to **94 raw language codes**:

- `de_AT` — Austrian German: deferred as a regional variant;
- `haw_US` — Hawaiian: selected;
- `mn_MN` — Mongolian: selected;
- `swg_de` — Oschtallgaierisch: deferred as a regional German/Swabian variety.

Therefore:

- selected project scope: **72 languages**;
- inherited selected scope: 70;
- new selected languages: `haw_US`, `mn_MN`;
- complete addon target: **65 locales** = 63 inherited + 2 new;
- translated/AI-assisted complete locales: 53;
- documented full-English fallbacks: **12**, including `haw_US` and `mn_MN`;
- selected upstream supplements: 6.

The two new selected locales intentionally use English fallback because reliable complete technical Hawaiian/Mongolian translations were not guaranteed. No low-confidence translation was invented.

### JEI 3.7.1 upstream completeness

| Locale | Normal present | Missing | Handling |
|---|---:|---:|---|
| `de_DE` | 53/75 | 22 | exact missing-key supplement |
| `en_US` | 75/75 | 0 | upstream only |
| `fi_FI` | 58/75 | 17 | exact missing-key supplement |
| `fr_FR` | 74/75 | 1 | only `jei.tooltip.cheat.mode` |
| `ko_KR` | 5/75 | 70 | exact supplement; G3 `Crafting Table` wording restored |
| `nb_NO` | 74/75 | 1 | preserve upstream; not Minecraft-facing `no_NO` |
| `ru_RU` | 73/75 | 2 | only the two color-search keys |
| `zh_CN` | 74/75 | 1 | only `jei.tooltip.cheat.mode` |

The G5 QA fetches the real Mojang asset indexes plus the exact pinned JEI language files, verifies JEI blob SHAs, and requires addon supplements to equal the exact keys still absent upstream.

### G5 files and validation

- source: `upstream/sources/1.10/en_US.lang`
- exact diff: `upstream/diffs/1.9.4-to-1.10.json`
- source audit: `upstream/minecraft-1.10-language-audit.json`
- scope: `upstream/minecraft-1.10-language-scope.json`
- policy: `translations/g5-mc1.10/policy.json`
- reconstruction: `scripts/reconstruct_1_10.py`
- source/scope/upstream QA: `scripts/validate_1_10_delta.py`
- complete QA: `scripts/validate_1_10_complete.py`
- successful validation workflow run: **34641765047**

Validated result: **65 complete 78-key addon locale files + 6 exact missing-key-only upstream supplements**.

## Current task — Minecraft 1.10.2

Continue chronologically with **Minecraft 1.10.2 as a separate target and future JAR**.

Known transition point:

- commit `c88aa6c5c078586fa23abaa83309d293cd72ea61` changes `mcversion=1.10` -> `1.10.2`;
- at that transition JEI becomes `3.7.2` and Forge becomes `12.18.0.2002-1.10.0`;
- the historical branch later advances far beyond JEI 3.7.2, so do not assume the branch HEAD represents the first or best 1.10.2 endpoint.

Next steps:

1. Determine the correct pinned 1.10.2 endpoint/version from actual branch history and build metadata.
2. Fetch its English source and exact upstream locale set.
3. Compare against G5 / Minecraft 1.10.
4. Audit the Minecraft 1.10.2 asset-index language inventory and classification changes.
5. Reuse G5 only where key + English meaning are identical.
6. Build G6 reconstruction/QA and obtain green CI.
7. Update manifests/docs and this handoff before proceeding further.

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

> Reprends JEI Translation Expansion depuis le depot et lis d'abord `PROJECT_STATUS.md`. Minecraft 1.10 / JEI 3.7.1 est termine au stade traduction/reconstruction: commit `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`, 78 cles, 94 codes Minecraft, scope 72, 65 locales addon completes, 12 fallbacks anglais, 6 supplements exacts, CI 34641765047. Le prochain target est Minecraft 1.10.2. La transition commence au commit `c88aa6c5c078586fa23abaa83309d293cd72ea61` (JEI 3.7.2), mais il faut determiner l'endpoint historique exact a auditer au lieu de prendre aveuglement le HEAD de la branche. Regle fixe: un JAR distinct par version Minecraft.

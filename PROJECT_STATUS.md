# JEI Translation Expansion — Project Status

> **Canonical handoff file. Start here in a new chat.**

Last synchronized: **2026-09-11**

## Fixed project rules

- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Upstream: https://github.com/mezz/JustEnoughItems
- **One Minecraft version per final JAR. Never group multiple Minecraft versions in one artifact.**
- Final runtime-validated JARs go in `release-jars/<minecraft-version>/`; prototypes do not.
- Translation reuse is allowed only when localization key **and English meaning** are unchanged.
- Preserve upstream JEI translations. Selected upstream locales receive only exact missing-key supplements unless an override is explicitly approved.
- Preserve placeholders and technical literals exactly.
- Prefer a documented English fallback over an uncertain translation.
- Initial selected scope focuses on real-world primary Minecraft languages; constructed/novelty languages and most regional variants are deferred.

## Completed translation/reconstruction generations

| Generation | Minecraft | JEI | Keys | Raw/selected MC languages | Addon full | Supplements | Complete upstream selected | CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G1 | 1.8 | 2.15.0 | 58 | — / 60 | 54 | — | — | validator green |
| G2 | 1.8.9 | 2.28.18 | 75 | inherited | 54 | 5 | 1 | prototype `34632859235` |
| G3 | 1.9 | 3.3.3 | 77 | 90 / 70 | 63 | 5 | 1 | `34638556534` |
| G4 | 1.9.4 | 3.6.8 | 80 | 90 / 70 | 63 | 6 | 1 | `34639831977` |
| G5 | 1.10 | 3.7.1 | 78 | 94 / 72 | 65 | 6 | 1 | `34641765047` |
| G6 | 1.10.2 | 3.14.8 | 87 | 94 / 72 | 52 | 16 | 4 | `34642956606` |
| G7 | 1.11 | 4.1.1 | 87 | 95 / 72 | 52 | 16 | 4 | `34644034423` |
| G8 | 1.11.2 | 4.5.1 | 93 | 95 / 72 | 52 | 19 | 1 | `34644712028` |

### Important endpoint history

- G5 Minecraft 1.10 endpoint: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`.
- G6 Minecraft 1.10.2 endpoint: `446af20eaa73d260517f0adc737232437363f78d`.
- G7 Minecraft 1.11 endpoint: `c9fcc36ff0effec2b5239eebd2c9133da04df4bb`.
- G8 Minecraft 1.11.2 endpoint: `11023c1f4449b82d0b88366001b058e6949b40ab`.

From Minecraft 1.11 onward JEI uses lowercase locale filenames (`en_us.lang`).

### G8 — Minecraft 1.11.2 / JEI 4.5.1

Status: **selected 72-language translation/reconstruction scope complete; CI green; final runtime-tested JAR not promoted yet**.

Build metadata:

- Forge `13.20.0.2315`
- MCP `snapshot_20170425`
- Java source/target `1.6`
- legacy lowercase `.lang`

Exact G7→G8 diff:

- 93 target keys = 90 normal + 3 debug
- **85 unchanged**
- **7 added**
- **1 removed** (`gui.jei.category.itemDescription`)
- **1 changed** (`key.jei.recipeBack`: `Show Previous Recipe Page` → `Show Previously Viewed Recipe`)
- 8 reviewed added/changed meanings

Minecraft 1.11.2 reuses the exact 1.11 asset index, so raw/selected language counts remain **95 / 72**.

JEI 4.5.1 ownership within selected scope:

- 52 addon-owned full locales
- 19 exact missing-key-only supplements
- only `en_us` complete upstream
- `ru_ru`, `sv_se`, `uk_ua` become incomplete compared with G7
- 12 documented full-English fallback locales remain

G8 realization:

- unchanged meanings inherit exact G7 values
- reviewed G8 meanings use target-English fallback only when project-owned and missing upstream
- complete QA includes an anti-loss assertion so an unchanged translation cannot silently disappear into English fallback
- source: `upstream/sources/1.11.2/en_us.lang`
- diff: `upstream/diffs/1.11-to-1.11.2.json`
- audit: `upstream/minecraft-1.11.2-language-audit.json`
- scope: `upstream/minecraft-1.11.2-language-scope.json`
- policy: `translations/g8-mc1.11.2/policy.json`
- reconstruction: `scripts/reconstruct_1_11_2.py`
- validators: `scripts/validate_1_11_2_delta.py`, `scripts/validate_1_11_2_complete.py`
- successful full CI: **34644712028**

## Current task — G9 Minecraft 1.12

Upstream branch audit has confirmed the normal `1.12` branch contains three distinct Minecraft targets:

1. **Minecraft 1.12** — last endpoint before commit `e1a1524c9cd9ce17f847be468dcd58950fa10f9f` moves to 1.12.1.
   - endpoint: `6bce08ef068fc0d7ce80ef07512caf85ccd4cab4`
   - JEI `4.7.5`
   - Forge `14.21.1.2413`
   - MCP `snapshot_20170714`
   - Java source/target `1.8`
2. **Minecraft 1.12.1** — last endpoint before commit `a339af3fceb142be5398ef856f81e3c89413349e` moves to 1.12.2.
   - endpoint: `7f4160ed969fad85e8c4a14809c66402c51592b2`
   - JEI `4.7.8`
   - Forge `14.22.0.2452`
   - MCP `snapshot_20170811`
3. **Minecraft 1.12.2** — later branch history; final normal `1.12` branch HEAD currently `f98331af6b1f7d59da01beecacd681c16dd548b9`, JEI `4.16.5`.

The separate `1.12-FG3` branch also ends on Minecraft 1.12.2 / JEI 4.15.0 and must be treated as a build-line variant, not automatically as a separate Minecraft version.

### G9 facts already verified

Pinned Minecraft 1.12 endpoint: `6bce08ef068fc0d7ce80ef07512caf85ccd4cab4`.

- Minecraft `1.12`
- JEI `4.7.5`
- Forge `14.21.1.2413`
- MCP `snapshot_20170714`
- Java source/target `1.8`
- source path `src/main/resources/assets/jei/lang/en_us.lang`
- pinned English blob `e6d5b263e4ebf33e36e7477fddb7537c5ace6abe`
- English content is identical to G8: **93 unchanged key/value pairs**, so no semantic retranslation should be needed unless live QA proves otherwise

Next steps:

1. Store/pin the Minecraft 1.12 English source and exact G8→G9 diff.
2. Audit Mojang 1.12 language inventory and classify any new codes.
3. Audit JEI 4.7.5 upstream locale ownership/completeness.
4. Freeze G9 scope and ownership.
5. Reconstruct G9 deterministically from G8 where semantics are unchanged.
6. Add source/scope and complete QA, obtain green CI.
7. Synchronize manifests/docs before advancing separately to Minecraft 1.12.1.

## Modern endpoint

Branch `26.2` uses JSON language files at `Common/src/main/resources/assets/jei/lang/`; full audit remains pending.

## Important handoff files

- `PROJECT_STATUS.md`
- `README.md`
- `docs/WORKFLOW.md`
- `docs/VERSION_MATRIX.md`
- `docs/TRANSLATION_STATUS.md`
- `upstream/versions.json`
- `upstream/generations.json`
- `upstream/minecraft-1.11.2-language-audit.json`
- `upstream/minecraft-1.11.2-language-scope.json`
- `packaging/1.8.9/release.json`

## Resume prompt

> Reprends JEI Translation Expansion depuis `PROJECT_STATUS.md`. G8 Minecraft 1.11.2 / JEI 4.5.1 est termine: endpoint `11023c1f4449b82d0b88366001b058e6949b40ab`, 93 cles, diff G7→G8 85 inchangees/7 ajoutees/1 supprimee/1 modifiee, Minecraft 95 brut / scope 72, 52 locales addon completes, 19 supplements exacts, `en_us` seul complet upstream, CI `34644712028`. G9 courant = Minecraft 1.12 / JEI 4.7.5 endpoint `6bce08ef068fc0d7ce80ef07512caf85ccd4cab4`, Forge `14.21.1.2413`, Java 8; son anglais 93 cles est identique a G8. Auditer scope Minecraft et ownership JEI avant reconstruction. Regle fixe: un JAR distinct par version Minecraft.

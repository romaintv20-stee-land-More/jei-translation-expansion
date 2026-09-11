# JEI Translation Expansion — Project Status

> Canonical handoff file. Start here in a new chat.

Last synchronized: 2026-09-11

## Core policy

- One Minecraft version per final JAR. Never ship a multi-version Minecraft JAR.
- Final validated JARs must also be retained under `release-jars/<minecraft-version>/`.
- Translation data may reuse earlier generations internally, but final resources must be reconstructed for the exact target version.
- Protect JEI upstream translations by default; for existing locales, add only missing keys unless an override is explicitly reviewed.
- Reuse translations only when both the key and English meaning are unchanged.
- Preserve placeholders and technical literals exactly.
- AI-assisted translation is allowed with automated QA; low-confidence locales may use documented English fallback.

## Current completed translation targets

### Minecraft 1.8 / JEI 2.15.0

- Forge 11.14.4.1577
- Java source/target 1.7
- legacy `.lang`
- English source: `upstream/sources/1.8/en_US.lang`
- 58 keys total, 55 normal translatable keys, 3 debug-only strings
- 54 addon locales in `translations/g1-mc1.8/`
- 51 translated / AI-assisted locales
- 3 documented English fallbacks: `gv_IM`, `kw_GB`, `se_NO`

### Minecraft 1.8.9 / JEI 2.28.18

Verified from upstream branch `1.8.9`:

- Forge build version: 11.15.1.1855
- JEI requires Forge 11.15.1.1808+
- JEI accepts exactly Minecraft `[1.8.9]`
- JEI mod id: `JEI`
- Java source/target 1.7
- legacy `.lang`
- English source: `upstream/sources/1.8.9/en_US.lang`
- 75 keys total
- upstream JEI locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

Exact 1.8 -> 1.8.9 localization diff:

- 46 unchanged/reusable keys
- 19 added keys
- 2 removed keys
- 10 existing keys changed English text/meaning
- 29 translated/reviewed delta entries per addon locale

Machine-readable diff: `upstream/diffs/1.8-to-1.8.9.json`.

`translations/g2-mc1.8.9/` contains six TSV batches covering all 54 addon locale deltas. The same 3 low-confidence locales (`gv_IM`, `kw_GB`, `se_NO`) use documented English fallback.

## Minecraft 1.8.9 reconstruction — implemented

`scripts/reconstruct_1_8_9.py` now reconstructs all complete 1.8.9 locale files from the 1.8 base plus the verified G2 delta.

Normal generated resource path:

`build/reconstructed/1.8.9/assets/jei/lang/`

The script:

1. loads the matching complete 1.8 locale;
2. drops keys not present in 1.8.9;
3. applies the 29-entry 1.8.9 delta;
4. follows the exact 1.8.9 English source order/comments;
5. verifies round-trip parsing and exact 75-key target parity.

CI now runs `python scripts/reconstruct_1_8_9.py --check`, so all 54 complete 1.8.9 locale files must remain reconstructable.

## Minecraft 1.8.9 packaging audit

Version-specific packaging facts are recorded in `packaging/1.8.9/release.json`.

Already verified:

- target Minecraft: 1.8.9 only
- loader: Forge
- upstream JEI: 2.28.18
- JEI mod id: `JEI`
- Forge build version: 11.15.1.1855
- minimum Forge required by JEI: 11.15.1.1808
- language resources belong under `assets/jei/lang/`
- final validated artifact must be stored under `release-jars/1.8.9/`

Still pending before a publishable 1.8.9 JAR:

- finalize the addon's JEI dependency version/range;
- verify whether old Forge needs a minimal `@Mod` entrypoint for this resource addon;
- finalize loader metadata/build setup;
- build and inspect the JAR;
- run an in-game Minecraft 1.8.9 + Forge + JEI test;
- archive only the validated final JAR under `release-jars/1.8.9/`.

## QA / CI

`.github/workflows/validate.yml` runs:

1. `scripts/validate_translations.py` for Minecraft 1.8;
2. `scripts/validate_1_8_9_delta.py` for the 1.8 -> 1.8.9 delta;
3. `scripts/reconstruct_1_8_9.py --check` for complete 1.8.9 reconstruction.

## Modern endpoint already inspected

Upstream branch `26.2` uses JSON language files under `Common/src/main/resources/assets/jei/lang/`. Its English file is about 28.7 KB and contains several hundred entries, so modern JEI is substantially larger than the 1.8-era schemas.

## Next translation task

Identify and verify the official JEI/Minecraft version immediately after 1.8.9, snapshot its real English source, compare it with 1.8.9, and translate only verified new/changed material.

JAR generation may remain deferred while translations advance.

## Resume prompt

Reprends JEI Translation Expansion depuis le depot GitHub. Lis d'abord `PROJECT_STATUS.md`, puis `docs/VERSION_MATRIX.md`, `docs/WORKFLOW.md` et `release-jars/README.md`. Minecraft 1.8 et 1.8.9 ont leurs traductions terminees. La reconstruction complete 1.8.9 est automatisee par `scripts/reconstruct_1_8_9.py`. Continue a la version officielle suivant 1.8.9. Regle fixe: un JAR par version Minecraft, avec les JARs finaux conserves sous `release-jars/<version>/`.

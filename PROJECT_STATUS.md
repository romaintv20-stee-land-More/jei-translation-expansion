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

## Completed translation/reconstruction generations

### G1 — Minecraft 1.8 / JEI 2.15.0

Status: **selected translation scope complete**.

- 58 keys = 55 normal + 3 debug-only
- selected scope 60
- 54 addon-owned full locales
- 51 translated/AI-assisted + 3 documented English fallbacks

### G2 — Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible Forge prototype passes static CI; real runtime test pending**.

- 75 keys = 72 normal + 3 debug-only
- diff from 1.8: 46 unchanged, 19 added, 2 removed, 10 changed
- 54 complete addon locales + 5 selected upstream supplements
- prototype build run `34632859235`
- prototype JAR SHA-256 `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`

Do **not** promote to `release-jars/1.8.9/` before real client runtime validation.

### G3 — Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction scope complete; CI green**.

- pinned commit `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`
- 77 keys = 74 normal + 3 debug-only
- 74 unchanged, 2 added, 0 removed, 1 changed vs 1.8.9
- raw Minecraft inventory 90; selected scope 70
- 63 complete addon locales + 5 exact supplements
- 53 translated/AI-assisted + 10 documented full-English fallbacks
- CI run **34638556534**

### G4 — Minecraft 1.9.4 / JEI 3.6.8

Status: **selected 70-language translation/reconstruction scope complete; CI green**.

- pinned commit `bd9fcad11a8b92d181fc8c2ec976e31c7467799a`
- 80 keys = 77 normal + 3 debug-only
- 76 unchanged, 3 added, 0 removed, 1 changed vs 1.9
- raw inventory 90; selected scope 70
- 63 complete addon locales + 6 exact supplements
- 53 translated/AI-assisted + 10 documented full-English fallbacks
- CI run **34639831977**

G4 rebuilds supplements against exact current upstream missing sets. `ko_KR` uses `제작` for generic `Crafting`.

### G5 — Minecraft 1.10 / JEI 3.7.1

Status: **selected 72-language translation/reconstruction scope complete; CI green**.

Pinned endpoint: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`, direct parent of the Minecraft 1.10.2 transition commit `c88aa6c5c078586fa23abaa83309d293cd72ea61`.

- Forge `12.18.0.1999-1.10.0`; MCP `snapshot_20160518`; Java 1.7; legacy `.lang`
- 78 keys = 75 normal + 3 debug-only
- 77 unchanged, 0 added, 2 removed, 1 changed vs 1.9.4
- `gui.jei.category.craftingTable`: `Crafting` -> `Crafting Table`; exact semantic return to G3, so G3 translations reused
- Minecraft raw inventory 94 after additions `de_AT`, `haw_US`, `mn_MN`, `swg_de`
- selected scope 72: retain `haw_US`, `mn_MN`; defer `de_AT`, `swg_de`
- 65 complete addon locales + 6 exact supplements
- 53 translated/AI-assisted + 12 documented full-English fallbacks
- CI run **34641765047**

### G6 — Minecraft 1.10.2 / JEI 3.14.8

Status: **selected 72-language translation/reconstruction scope complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned final endpoint of historical upstream branch `1.10`:

`446af20eaa73d260517f0adc737232437363f78d`

Verified directly from upstream build files:

- Minecraft `1.10.2`
- JEI `3.14.8`
- Forge `12.18.3.2254`
- MCP mappings `snapshot_20161111`
- Java source/target **1.6**
- legacy `.lang`
- English source `upstream/sources/1.10.2/en_US.lang`

Important correction: an earlier handoff incorrectly recorded Forge `12.18.3.2511` and Java `1.8`. The pinned upstream commit explicitly declares Forge `12.18.3.2254` and `sourceCompatibility`/`targetCompatibility` Java `1.6`; the manifests/docs now use the verified values.

#### Exact G5 -> G6 English diff

Target: **87 keys = 84 normal + 3 debug-only**.

- **53 unchanged key/value pairs** reusable
- **25 added keys**
- **16 removed keys**
- **9 changed English values**
- total reviewed added/changed keys: **34**

Exact manifest: `upstream/diffs/1.10-to-1.10.2.json`.

`gui.jei.category.craftingTable` changes from `Crafting Table` back to `Crafting`, exactly matching G4, so G4 translations are reused. The other 33 added/changed entries use documented target-English fallback when no already-validated exact-semantic translation exists. This avoids inventing low-confidence technical translations and protects new placeholder-bearing strings such as `%CTRL`.

#### Minecraft scope

Minecraft 1.10.2 reuses the exact Minecraft 1.10 asset index:

- asset index id `1.10`
- SHA-1 `7c2800b458376b8fc0b738382fb7784328fddda9`
- raw inventory **94 codes**
- selected scope **72 languages**

#### JEI 3.14.8 ownership

JEI expands to **23 upstream locale files**. Within the selected project scope:

- selected matching upstream locales: **20**
- complete upstream selected locales: **4** — `de_DE`, `en_US`, `ru_RU`, `uk_UA`
- incomplete selected upstream locales requiring exact supplements: **16**
- addon-owned full locales: **52**
- translated/AI-assisted addon full locales: **40**
- documented full-English fallback locales: **12**
- upstream nonmatching/unselected locales preserved untouched: `en_AU`, `nb_NO`, `zh_TW`

The 16 supplement locales are:

`ar_SA`, `bg_BG`, `cs_CZ`, `el_GR`, `es_ES`, `fi_FI`, `fr_FR`, `he_IL`, `it_IT`, `ja_JP`, `ko_KR`, `lt_LT`, `pl_PL`, `pt_BR`, `sv_SE`, `zh_CN`.

#### G6 implementation and validation

- source: `upstream/sources/1.10.2/en_US.lang`
- exact diff: `upstream/diffs/1.10-to-1.10.2.json`
- source audit: `upstream/minecraft-1.10.2-language-audit.json`
- scope: `upstream/minecraft-1.10.2-language-scope.json`
- policy: `translations/g6-mc1.10.2/policy.json`
- audit script: `scripts/audit_1_10_2.py`
- reconstruction: `scripts/reconstruct_1_10_2.py`
- source/scope/upstream QA: `scripts/validate_1_10_2_delta.py`
- complete QA: `scripts/validate_1_10_2_complete.py`
- endpoint audit run: **34642438873**
- successful complete validation run: **34642956606**

Validated result: **52 complete 87-key addon locale files + 16 exact missing-key-only upstream supplements**, with no addon file for the four selected locales already complete upstream.

## Current task — determine G7 chronologically

G6 is complete. Continue from actual JEI upstream history, not assumptions.

Next steps:

1. Enumerate historical upstream branches after `1.10` and identify the next real Minecraft target.
2. Determine whether that branch contains multiple Minecraft patch/minor endpoints; if so, pin each distinct Minecraft version separately.
3. For the first chronological target after 1.10.2, record exact JEI version, commit, Forge/loader metadata, Java source/target and language format.
4. Fetch the exact English source and upstream locale set.
5. Audit the Minecraft language inventory/asset index and selected-scope changes.
6. Compute an exact G6 -> G7 key/English diff and reuse translations only where key + English meaning are identical.
7. Build deterministic reconstruction/QA, obtain green CI, then update this file before advancing again.

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

> Reprends JEI Translation Expansion depuis `PROJECT_STATUS.md`. G6 Minecraft 1.10.2 / JEI 3.14.8 est termine au stade traduction/reconstruction et CI verte: commit upstream `446af20eaa73d260517f0adc737232437363f78d`, Forge `12.18.3.2254`, Java source/target 1.6, 87 cles (84 normales), diff G5->G6 = 53 inchangees, 25 ajoutees, 16 supprimees, 9 modifiees; scope Minecraft 94 brut / 72 selectionne; 52 locales addon completes, 16 supplements exacts, 4 locales completes upstream; CI `34642956606`. Le prochain travail est d'identifier depuis l'historique upstream le premier target Minecraft chronologique apres 1.10.2, puis de creer G7. Regle fixe: un JAR distinct par version Minecraft.

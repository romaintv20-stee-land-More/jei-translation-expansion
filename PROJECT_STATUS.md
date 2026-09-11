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
- Minecraft raw inventory 94; selected scope 72
- 65 complete addon locales + 6 exact supplements
- 53 translated/AI-assisted + 12 documented full-English fallbacks
- CI run **34641765047**

### G6 — Minecraft 1.10.2 / JEI 3.14.8

Status: **selected 72-language translation/reconstruction scope complete; CI green; final runtime-tested JAR not promoted yet**.

Pinned final endpoint of historical upstream branch `1.10`: `446af20eaa73d260517f0adc737232437363f78d`.

Verified build metadata:

- Minecraft `1.10.2`
- JEI `3.14.8`
- Forge `12.18.3.2254`
- MCP mappings `snapshot_20161111`
- Java source/target `1.6`
- legacy `.lang`
- 87 keys = 84 normal + 3 debug-only
- G5 -> G6: 53 unchanged, 25 added, 16 removed, 9 changed
- raw Minecraft inventory 94; selected scope 72
- 52 addon full locales + 16 exact supplements + 4 complete upstream selected locales
- CI run **34642956606**

Important correction: an earlier handoff incorrectly recorded Forge `12.18.3.2511` and Java `1.8`. The pinned upstream commit explicitly declares Forge `12.18.3.2254` and Java source/target `1.6`; current canonical docs use the verified values.

### G7 — Minecraft 1.11 / JEI 4.1.1

Status: **selected 72-language translation/reconstruction scope complete; CI green; final runtime-tested JAR not promoted yet**.

The historical upstream branch `1.11` later changes to Minecraft 1.11.2 at commit `72c7ea7cf2e7f5243e1d7179aaa10fad038574bf` (`"update" for 1.11.2`). The last Minecraft 1.11 endpoint is its parent:

`c9fcc36ff0effec2b5239eebd2c9133da04df4bb`

Verified build metadata:

- Minecraft `1.11`
- JEI `4.1.1`
- Forge `13.19.1.2188`
- MCP mappings `snapshot_20161205`
- Java source/target `1.6`
- legacy `.lang`
- resource locale filenames switch to **lowercase**, e.g. `en_us.lang`
- English source `upstream/sources/1.11/en_us.lang`

#### Exact G6 -> G7 English diff

The pinned JEI 4.1.1 English file is byte-identical to G6 JEI 3.14.8 (same Git blob `75790131d753d64fe0cf98f3ac5c0ee67f6bd545`).

- **87 unchanged key/value pairs**
- **0 added**
- **0 removed**
- **0 changed**
- no new semantic translation entries required

Exact manifest: `upstream/diffs/1.10.2-to-1.11.json`.

#### Minecraft 1.11 scope

Live Mojang audit:

- asset index id `1.11`
- SHA-1 `c64959fe73672e9b053b157f57b6aba318d0b3b5`
- raw language inventory **95 codes**
- only new code vs 1.10/1.10.2: `io_ido`
- `io_ido` is Ido, a constructed language, so it remains deferred by project policy
- selected scope therefore remains **72 languages**

#### JEI 4.1.1 ownership

JEI still ships 23 locale files, now lowercase. Within the selected scope:

- 20 selected matching upstream locales
- 4 complete upstream: `en_us`, `ru_ru`, `sv_se`, `uk_ua`
- 16 incomplete upstream locales requiring exact supplements
- 52 addon-owned full locales
- 12 documented full-English fallback locales

Ownership changes from G6:

- `de_de` was complete in JEI 3.14.8 but is missing 16 keys in JEI 4.1.1. Those 16 values are reused exactly from the pinned G6 upstream `de_DE` translation and stored in `translations/g7-mc1.11/de_de-from-g6-upstream.lang`.
- `sv_se` becomes complete upstream, so the G6 `sv_SE` supplement is retired and no addon `sv_se` file is emitted.
- the other 15 supplement locales reuse their exact G6 project values because all English semantics are unchanged.

#### G7 implementation and validation

- source: `upstream/sources/1.11/en_us.lang`
- exact diff: `upstream/diffs/1.10.2-to-1.11.json`
- audit: `upstream/minecraft-1.11-language-audit.json`
- scope: `upstream/minecraft-1.11-language-scope.json`
- policy: `translations/g7-mc1.11/policy.json`
- audit script: `scripts/audit_1_11.py`
- reconstruction: `scripts/reconstruct_1_11.py`
- source/scope/upstream QA: `scripts/validate_1_11_delta.py`
- complete QA: `scripts/validate_1_11_complete.py`
- initial endpoint audit run: **34643677382**
- successful complete validation run: **34644034423**

Validated result: **52 complete 87-key addon locale files + 16 exact missing-key-only upstream supplements**, all emitted with lowercase locale filenames, with no addon resource for the four selected locales already complete upstream.

## Current task — G8 Minecraft 1.11.2

Minecraft 1.11 and 1.11.2 are separate targets and must eventually receive separate JARs.

Known 1.11.2 history:

- transition commit `72c7ea7cf2e7f5243e1d7179aaa10fad038574bf` changes Minecraft `1.11` -> `1.11.2`, JEI `4.1.1` -> `4.2.0`, Forge `13.19.1.2188` -> `13.20.0.2200`;
- final branch `1.11` HEAD is `11023c1f4449b82d0b88366001b058e6949b40ab`;
- HEAD metadata: Minecraft `1.11.2`, JEI `4.5.1`, Forge `13.20.0.2315`;
- English source remains legacy lowercase `src/main/resources/assets/jei/lang/en_us.lang` but has changed from G7, so G8 requires a real semantic diff.

Next steps:

1. Pin and verify all final 1.11.2 build metadata at `11023c1f4449b82d0b88366001b058e6949b40ab`, including Java source/target.
2. Store the exact G8 English source and compute the exact G7 -> G8 key/value diff.
3. Audit Minecraft 1.11.2 asset-index language inventory and selected-scope changes.
4. Audit exact JEI 4.5.1 upstream locale ownership/completeness.
5. Reuse G7 translations only for unchanged key/value pairs; review every added/changed meaning.
6. Build deterministic G8 reconstruction/QA and obtain green CI.
7. Synchronize `upstream/versions.json`, `upstream/generations.json`, README/docs and this handoff before advancing to the next Minecraft target.

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
- `upstream/minecraft-1.11-language-audit.json`
- `upstream/minecraft-1.11-language-scope.json`
- `packaging/1.8.9/release.json`

## Resume prompt

> Reprends JEI Translation Expansion depuis `PROJECT_STATUS.md`. G7 Minecraft 1.11 / JEI 4.1.1 est termine au stade traduction/reconstruction: endpoint `c9fcc36ff0effec2b5239eebd2c9133da04df4bb`, Forge `13.19.1.2188`, Java 1.6, 87 cles toutes identiques a G6, ressources `.lang` en noms de locales minuscules, Minecraft 95 codes brut / scope 72 (`io_ido` differe), 52 locales addon completes, 16 supplements exacts, 4 locales completes upstream, CI `34644034423`. Le target courant est Minecraft 1.11.2 / JEI 4.5.1 final a `11023c1f4449b82d0b88366001b058e6949b40ab`. Regle fixe: un JAR distinct par version Minecraft.

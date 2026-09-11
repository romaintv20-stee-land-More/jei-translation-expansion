# JEI Translation Expansion — Project Status

> **Canonical handoff file. Start here in a new chat.**

Last synchronized: **2026-09-11**

## Project rules

- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Upstream: https://github.com/mezz/JustEnoughItems
- Unofficial MIT localization companion for JEI; no gameplay content.
- **One Minecraft version per final JAR. Never group multiple Minecraft versions in one artifact.**
- Final runtime-validated JARs go in `release-jars/<minecraft-version>/`; prototypes do not.
- Translation reuse between versions is encouraged only when both localization key and English meaning are unchanged.
- Preserve upstream JEI translations. For a locale already shipped by JEI, add only missing keys unless an override is explicitly approved.
- Preserve placeholders and technical literals exactly. Prefer a documented English fallback to an uncertain translation.
- Initial scope focuses on real-world primary Minecraft languages; novelty/fantasy entries, constructed non-primary languages and most regional variants are excluded/deferred.

## Minecraft 1.8 / JEI 2.15.0

Status: **selected translation scope complete**.

- Forge `11.14.4.1577`; Java source/target 1.7; legacy `.lang`.
- English: 58 keys = 55 normal + 3 debug-only.
- Selected scope: 60 languages.
- 54 addon-owned full locales: 51 translated/AI-assisted + 3 English fallbacks (`gv_IM`, `kw_GB`, `se_NO`).
- Source: `upstream/sources/1.8/en_US.lang`.
- Scope: `upstream/minecraft-1.8-language-scope.json`.

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible Forge prototype passes static CI; real runtime test still pending**.

- Forge `11.15.1.1855`; minimum declared Forge `11.15.1.1808`; Java 1.7; legacy `.lang`.
- English: 75 keys = 72 normal + 3 debug-only.
- Exact 1.8 -> 1.8.9 diff: 46 unchanged, 19 added, 2 removed, 10 changed English values.
- 54 absent-locale files reconstruct from G1 + G2.
- Missing-key-only supplements complete `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN` to 72/72 normal keys.
- Latest successful static prototype build run: `34632859235`.
- JAR: `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`.
- SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`.

Do **not** promote to `release-jars/1.8.9/` yet. Remaining blocker: real Minecraft 1.8.9 + compatible Forge + JEI 2.28.18 client test. Details: `packaging/1.8.9/release.json`.

## Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction stage complete; CI green; final runtime-tested JAR not built/promoted yet**.

### Pinned endpoint

Use JEI commit:

`b2ffe6bd7734d093006de99f9dc99b2b77ce780d`

Do not use the current `1.9` branch HEAD as Minecraft 1.9: the branch later transitioned to Minecraft 1.9.4 at commit `d6b11a003a4a10702a36f8a97fa28cae883c9360`.

Verified snapshot:

- Minecraft `1.9`
- JEI `3.3.3`
- Forge `12.16.0.1865-1.9`
- MCP mappings `snapshot_20160421`
- Java source/target 1.7
- legacy `.lang`
- English source `upstream/sources/1.9/en_US.lang`
- 77 keys = 74 normal + 3 debug-only
- JEI locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### 1.8.9 -> 1.9 diff

- 74 unchanged key/value pairs reusable
- 2 added: `jei.tooltip.shapeless.recipe`, `key.jei.focusSearch`
- 0 removed
- 1 changed English value: `key.jei.toggleOverlay`
- inherited addon locales therefore require only a three-entry G3 delta

Machine-readable diff: `upstream/diffs/1.8.9-to-1.9.json`.

### Language scope and upstream ownership

Minecraft 1.9 raw inventory: 90 language codes. Final project scope: **70 real-world primary-language locales**.

New selected primary languages: `be_BY`, `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `mk_MK`, `so_SO`, `sq_AL`.

Deferred/excluded new codes:

- `en_NZ`: regional English variant;
- `en_UD`, `lol_US`: novelty;
- `jbo_EN` (Lojban), `tzl_TZL` (Talossan): constructed languages, deferred under the initial primary real-world language policy.

Minecraft has `no_NO` and not `nb_NO`; JEI 3.3.3 has `nb_NO` and not `no_NO`. Keep `no_NO` as a distinct Minecraft-facing full addon locale and preserve JEI's `nb_NO` untouched.

Selected-scope output:

- **63 complete addon locales**;
- **5 missing-key-only upstream supplements**: `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`;
- `en_US` and `fr_FR` are complete upstream and are not duplicated.

### Translation realization

Of the 63 complete addon locales:

- 53 inherit G2 and apply `translations/g3-mc1.9/inherited-delta.tsv`;
- the 10 new selected locales have no earlier project base;
- full AI-assisted drafts: `be_BY`, `mk_MK`, `sq_AL`;
- documented English fallbacks: `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `so_SO`;
- inherited English fallbacks remain `gv_IM`, `kw_GB`, `se_NO`.

Final complete-addon result: **53 translated/AI-assisted locales + 10 documented English fallbacks**.

Important files:

- scope: `upstream/minecraft-1.9-language-scope.json`
- raw/upstream audit: `upstream/minecraft-1.9-language-audit.json`
- new-locale confidence policy: `translations/g3-mc1.9/new-full-policy.json`
- inherited delta: `translations/g3-mc1.9/inherited-delta.tsv`
- upstream-new-key delta: `translations/g3-mc1.9/upstream-supplement-delta.tsv`
- reconstruction: `scripts/reconstruct_1_9.py`
- delta QA: `scripts/validate_1_9_delta.py`
- complete QA: `scripts/validate_1_9_complete.py`

Successful complete validation run: **34638556534**. It passed G3 delta validation, deterministic reconstruction of all 63 full locales + five supplements, key coverage, placeholders, technical-token checks, debug-English policy and documented-fallback checks.

## Current task: Minecraft 1.9.4

The 1.9 translation stage is complete. Continue directly with a full Minecraft **1.9.4** audit.

Known transition:

- upstream branch: `1.9`
- transition commit to Minecraft 1.9.4: `d6b11a003a4a10702a36f8a97fa28cae883c9360`
- previously observed branch HEAD metadata: Minecraft `1.9.4`, JEI `3.6.8`, Forge `12.17.0.1962`

Next actions:

1. Query the current upstream `1.9` branch and pin the exact Minecraft 1.9.4 endpoint instead of relying on branch naming.
2. Fetch the exact 1.9.4 English source and build metadata.
3. Compare 1.9 -> 1.9.4 key/value semantics exactly.
4. Audit JEI upstream locales and completeness for the pinned endpoint.
5. Verify Minecraft 1.9.4 raw language inventory and derive the selected scope under existing policy.
6. Reuse G3 translations only for proven unchanged key/value pairs.
7. Translate/review the 1.9.4 delta, build missing-key-only supplements, add deterministic reconstruction/QA, and persist G4.
8. Then continue chronologically to the next Minecraft version.

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
- `upstream/minecraft-1.9-language-audit.json`
- `upstream/minecraft-1.9-language-scope.json`
- `packaging/1.8.9/release.json`

## Resume prompt

> Reprends JEI Translation Expansion depuis le depot et lis d'abord `PROJECT_STATUS.md`. Minecraft 1.9 / JEI 3.3.3 est termine au stade traduction/reconstruction pour le scope selectionne de 70 langues; validation complete verte au run `34638556534`. Ne promeus toujours pas la 1.8.9 avant test reel en jeu. La prochaine cible est Minecraft 1.9.4 sur la branche upstream `1.9`: pince d'abord l'endpoint exact 1.9.4, puis audite source anglaise, diff, langues upstream, inventaire Minecraft, scope, traductions, reconstruction et QA. Regle fixe: un JAR distinct par version Minecraft.

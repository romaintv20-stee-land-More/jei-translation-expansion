# JEI Translation Expansion — Project Status

> **Canonical handoff file. Start here in a new chat.**

Last synchronized: **2026-09-11**

## Project rules

- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Upstream: https://github.com/mezz/JustEnoughItems
- Unofficial MIT localization companion for JEI; no gameplay content.
- **One Minecraft version per final JAR.**
- Final runtime-validated JARs go in `release-jars/<minecraft-version>/`; prototypes do not.
- Reuse a translation only when both localization key and English meaning are unchanged.
- Preserve upstream JEI translations; for locales already shipped by JEI, add missing keys only unless an override is explicitly approved.
- Preserve placeholders/technical literals exactly. Prefer a documented English fallback to an uncertain translation.
- Initial language scope uses real-world primary Minecraft languages; novelty/fantasy languages and most regional variants are excluded/deferred.

## Minecraft 1.8 / JEI 2.15.0

Status: **selected translation scope complete**.

- Forge `11.14.4.1577`; Java source/target 1.7; legacy `.lang`.
- English source: `upstream/sources/1.8/en_US.lang`.
- 58 keys = 55 normal + 3 debug-only.
- Upstream locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`.
- Selected scope: 60 languages; 54 locales absent upstream supplied in `translations/g1-mc1.8/`.
- 51 translated/AI-assisted; English fallback documented for `gv_IM`, `kw_GB`, `se_NO`.
- Exact scope: `upstream/minecraft-1.8-language-scope.json`.

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected translation scope complete; reproducible Forge prototype passes static CI; runtime test still pending**.

Verified upstream:

- Forge build `11.15.1.1855`, minimum declared Forge `11.15.1.1808`.
- JEI mod id `JEI`; accepted Minecraft `[1.8.9]`.
- Java source/target 1.7; legacy `.lang`.
- 75 English keys = 72 normal + 3 debug-only.
- Upstream locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`.

Exact 1.8 -> 1.8.9 localization diff:

- 46 unchanged/reusable keys;
- 19 added;
- 2 removed;
- 10 same-key English values changed;
- 29 new/reviewed entries per absent addon locale.

See `upstream/diffs/1.8-to-1.8.9.json` and `translations/g2-mc1.8.9/`.

`scripts/reconstruct_1_8_9.py` reconstructs all 54 complete absent-locale files. Missing-key-only supplements complete JEI's five existing non-English locales to 72/72 normal keys:

| Locale | Upstream | Supplement | Combined |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

Latest successful static build:

- source commit `ef200a1ac1e03b09fd5c3b950c319e8ebf760647`
- build workflow run `34632859235`
- validation workflow run `34632859278`
- JAR `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`
- SHA-256 `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`
- 59 language resources = 54 complete absent locales + 5 upstream supplements
- 64 JAR entries
- Actions artifact id `10277785240`, retention 14 days

The CI verifies Java 7 bytecode, the exact Forge `@Mod` class-file annotation descriptor, Minecraft/JEI dependency strings, absence of the compile-only Forge annotation stub from the JAR, localization reconstruction and archive contents.

Do **not** promote to `release-jars/1.8.9/` yet. Remaining blocker: real Minecraft 1.8.9 + compatible Forge + JEI 2.28.18 client test, including one absent locale and one supplemented upstream locale. Details: `packaging/1.8.9/release.json`.

## Minecraft 1.9 / JEI 3.3.3

Status: **upstream/key audit complete; translation scope intentionally not started yet**.

Important branch-history finding: the upstream branch named `1.9` later moved to Minecraft 1.9.4. Its branch head is therefore not a valid Minecraft 1.9 audit endpoint. The project pins actual Minecraft 1.9 to upstream commit:

`b2ffe6bd7734d093006de99f9dc99b2b77ce780d`

That is the parent immediately before commit `d6b11a003a4a10702a36f8a97fa28cae883c9360`, which explicitly transitions the branch to Minecraft 1.9.4.

Verified at the pinned snapshot:

- Minecraft `1.9`;
- JEI `3.3.3`;
- Forge `12.16.0.1865-1.9`;
- MCP mappings `snapshot_20160421`;
- Java source/target 1.7;
- legacy `.lang`;
- English source snapshot `upstream/sources/1.9/en_US.lang`;
- 77 keys = 74 normal + 3 debug-only;
- upstream locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`.

Exact 1.8.9 -> 1.9 diff:

- 74 keys unchanged/reusable;
- 2 added: `jei.tooltip.shapeless.recipe`, `key.jei.focusSearch`;
- 0 removed;
- 1 changed English value: `key.jei.toggleOverlay` changes from `Toggle Item List Overlay (Ctrl + )` to `Toggle Item List Overlay`;
- only **3 entries per inherited locale** need new/reviewed translation once the locale scope is fixed.

Machine-readable diff: `upstream/diffs/1.8.9-to-1.9.json`. Generation record: `g3-mc1.9` in `upstream/generations.json`.

### Current 1.9 blocker

JEI 3.3.3 newly ships `fr_FR` and `nb_NO`. The previous project scope used `no_NO`, while this JEI snapshot uses `nb_NO`. Do not create `translations/g3-mc1.9/` until the exact Minecraft 1.9 language identifiers are verified and the Norwegian code is reconciled. Otherwise the project could create a locale Minecraft does not load or duplicate one language under two identifiers.

Next work:

1. verify exact Minecraft 1.9 language codes;
2. resolve `no_NO` versus `nb_NO`;
3. snapshot and audit completeness of the seven non-English JEI 3.3.3 upstream locale files;
4. determine which selected addon locales remain absent upstream;
5. create G3 and translate only the verified 3-key delta plus proven upstream missing-key supplements;
6. add reconstruction/QA, then a one-version-only Minecraft 1.9 JAR pipeline.

## Modern endpoint

Branch `26.2` uses JSON language files at `Common/src/main/resources/assets/jei/lang/`; full audit is still pending.

## Important files

- `PROJECT_STATUS.md` — canonical handoff
- `docs/VERSION_MATRIX.md` — audited endpoints/details
- `docs/TRANSLATION_STATUS.md` — language coverage
- `docs/WORKFLOW.md` — workflow and one-version-per-JAR rule
- `upstream/versions.json` — audited endpoints
- `upstream/generations.json` — translation generations
- `upstream/sources/1.9/en_US.lang` — pinned 1.9 English source
- `upstream/diffs/1.8.9-to-1.9.json` — exact G2 -> G3 diff
- `packaging/1.8.9/release.json` — 1.8.9 release/runtime status

## Resume prompt

> Reprends JEI Translation Expansion depuis le depot. Lis d'abord `PROJECT_STATUS.md`, `docs/VERSION_MATRIX.md`, `upstream/versions.json`, `upstream/generations.json` et `packaging/1.8.9/release.json`. Ne promeus pas la 1.8.9 avant test reel en jeu. Pour Minecraft 1.9, utilise le snapshot upstream epingle `b2ffe6bd7734d093006de99f9dc99b2b77ce780d` (JEI 3.3.3), pas la tete actuelle de la branche `1.9`. Le diff 1.8.9 -> 1.9 est audite: 74 cles reutilisables, 2 ajoutees, 1 valeur anglaise changee, 0 supprimee. Avant de creer G3, verifie les codes langues Minecraft 1.9 et resous `no_NO`/`nb_NO`, puis audite les locales upstream JEI 3.3.3. Regle fixe: un JAR par version Minecraft.

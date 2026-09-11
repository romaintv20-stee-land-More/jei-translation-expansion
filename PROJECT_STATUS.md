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
- Preserve placeholders and technical literals exactly. Prefer a documented English fallback to an uncertain translation.
- Initial scope focuses on real-world primary Minecraft languages; novelty/fantasy languages and most regional variants are excluded/deferred.

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

Exact 1.8 -> 1.8.9 diff: 46 unchanged, 19 added, 2 removed, 10 changed English values; 29 new/reviewed entries per absent addon locale. See `upstream/diffs/1.8-to-1.8.9.json`.

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
- 59 language resources; 64 JAR entries
- Actions artifact id `10277785240`

Do **not** promote to `release-jars/1.8.9/` yet. Remaining blocker: real Minecraft 1.8.9 + compatible Forge + JEI 2.28.18 client test, including one absent locale and one supplemented upstream locale. Details: `packaging/1.8.9/release.json`.

## Minecraft 1.9 / JEI 3.3.3

Status: **English/key audit complete; exact raw Minecraft language inventory verified; final selected language policy has only two new ambiguous codes left to decide**.

### Pinned upstream endpoint

The upstream branch named `1.9` later moved to Minecraft 1.9.4. Its current head is therefore not a valid Minecraft 1.9 reference. The project pins actual Minecraft 1.9 to:

`b2ffe6bd7734d093006de99f9dc99b2b77ce780d`

This is the parent immediately before upstream commit `d6b11a003a4a10702a36f8a97fa28cae883c9360`, which explicitly transitions the branch to Minecraft 1.9.4.

Verified at the pinned snapshot:

- Minecraft `1.9`
- JEI `3.3.3`
- Forge `12.16.0.1865-1.9`
- MCP mappings `snapshot_20160421`
- Java source/target 1.7
- legacy `.lang`
- English snapshot `upstream/sources/1.9/en_US.lang`
- 77 keys = 74 normal + 3 debug-only
- JEI upstream locales: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

Exact 1.8.9 -> 1.9 English diff:

- 74 keys unchanged/reusable
- 2 added: `jei.tooltip.shapeless.recipe`, `key.jei.focusSearch`
- 0 removed
- 1 changed value: `key.jei.toggleOverlay` changes from `Toggle Item List Overlay (Ctrl + )` to `Toggle Item List Overlay`
- inherited locales therefore need only a 3-entry G3 delta

Machine-readable diff: `upstream/diffs/1.8.9-to-1.9.json`.

### Verified Minecraft 1.9 language inventory

A dedicated audit was added:

- script: `scripts/audit_1_9.py`
- workflow: `.github/workflows/audit-1.9.yml`
- successful run: **34635026243**
- audit artifact id: `10277798915`
- permanent summary: `upstream/minecraft-1.9-language-audit.json`

Results:

- **89 external `.lang` files** in the Minecraft 1.9 asset index
- `en_US` is added as the integrated/base language
- **90 raw Minecraft language codes total**
- compared with the project's Minecraft 1.8 raw scope: **15 added codes, 0 removed**

The 15 new codes are:

`be_BY`, `br_FR`, `en_NZ`, `en_UD`, `fo_FO`, `fy_NL`, `gd_GB`, `jbo_EN`, `ksh_DE`, `li_LI`, `lol_US`, `mk_MK`, `so_SO`, `sq_AL`, `tzl_TZL`.

Classification under the existing policy:

- obvious new primary-language candidates: `be_BY`, `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `mk_MK`, `so_SO`, `sq_AL`
- obvious regional variant to defer: `en_NZ`
- obvious novelty entries to exclude: `en_UD`, `lol_US`
- explicit policy decision still required: `jbo_EN` and `tzl_TZL`

Without those two ambiguous constructed-language codes, the provisional selected scope becomes **70 languages**. If both are retained it becomes **72**.

### Norwegian code resolved technically

Minecraft 1.9 assets contain `no_NO` and **do not contain `nb_NO`**. JEI 3.3.3 does the opposite: it ships `nb_NO` but not `no_NO`.

Project handling:

- keep `no_NO` as the Minecraft-facing target;
- do not rename or overwrite JEI's upstream `nb_NO` file;
- treat `no_NO` as absent upstream for addon reconstruction unless an actual runtime alias is later demonstrated.

This removes the previous technical ambiguity; only the broader policy choice for `jbo_EN` / `tzl_TZL` remains.

### JEI 3.3.3 upstream locale completeness

The automated audit compared every upstream locale against the 74 normal English keys:

| Locale | Normal keys present | Missing normal keys | Extra stale keys |
|---|---:|---:|---:|
| `de_DE` | 53/74 | 21 | 2 |
| `en_US` | 74/74 | 0 | 0 |
| `fi_FI` | 58/74 | 16 | 2 |
| `fr_FR` | 74/74 | 0 | 0 |
| `ko_KR` | 5/74 | 69 | 0 |
| `nb_NO` | 74/74 | 0 | 0 |
| `ru_RU` | 53/74 | 21 | 2 |
| `zh_CN` | 21/74 | 53 | 2 |

Implications:

- `fr_FR` is now fully supplied upstream, so the addon must **stop shipping a full French override for the 1.9 target**.
- `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN` still need missing-key-only supplements.
- JEI's complete `nb_NO` is preserved but does not replace Minecraft's `no_NO` target.
- all newly introduced selected primary languages require **full 1.9 translations**, not just the 3-key inherited delta.

For the currently obvious 70-language scope, 7 Minecraft-facing locales are already represented upstream (`en_US`, `de_DE`, `fi_FI`, `fr_FR`, `ko_KR`, `ru_RU`, `zh_CN`), leaving **63 full addon locales**, plus 5 partial supplements. If `jbo_EN` and `tzl_TZL` are retained, that becomes 65 full addon locales plus the same 5 supplements.

### Next 1.9 work

1. Decide whether `jbo_EN` and `tzl_TZL` belong in the project scope.
2. Freeze `upstream/minecraft-1.9-language-scope.json` from the verified audit.
3. Create `translations/g3-mc1.9/`.
4. Reuse G2 values only for the 74 proven unchanged key/value pairs.
5. Translate the 3-key delta for inherited addon locales.
6. Fully translate the newly selected primary languages introduced in Minecraft 1.9.
7. Build missing-key-only supplements for `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`.
8. Add deterministic reconstruction/validation and then the version-specific Minecraft 1.9 Forge JAR pipeline.

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
- `upstream/minecraft-1.9-language-audit.json` — verified Minecraft 1.9 language/upstream completeness audit
- `scripts/audit_1_9.py` — reproducible 1.9 audit
- `packaging/1.8.9/release.json` — 1.8.9 release/runtime status

## Resume prompt

> Reprends JEI Translation Expansion depuis le depot. Lis d'abord `PROJECT_STATUS.md`, `docs/VERSION_MATRIX.md`, `docs/TRANSLATION_STATUS.md`, `upstream/versions.json`, `upstream/generations.json`, `upstream/minecraft-1.9-language-audit.json` et `packaging/1.8.9/release.json`. Ne promeus pas la 1.8.9 avant test reel en jeu. Pour Minecraft 1.9, utilise le snapshot upstream epingle `b2ffe6bd7734d093006de99f9dc99b2b77ce780d` (JEI 3.3.3), pas la tete actuelle de la branche `1.9`. Le raw scope Minecraft 1.9 est verifie a 90 codes; 15 sont nouveaux vs le scope brut 1.8, aucun n'a disparu. `no_NO` est le code Minecraft et `nb_NO` n'existe pas dans l'asset index 1.9. Il reste seulement a decider la politique pour `jbo_EN` et `tzl_TZL` avant de figer G3. Regle fixe: un JAR par version Minecraft.

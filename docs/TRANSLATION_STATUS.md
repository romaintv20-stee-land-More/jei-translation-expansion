# Translation Status

## Minecraft 1.8 / JEI 2.15.0

Status: **language-file stage complete for the selected scope**.

- English source: `upstream/sources/1.8/en_US.lang`
- 58 localization keys total
- 55 normal translatable keys
- 3 debug-only description keys intentionally left in English
- addon target: 54 locale files
- 51 translated / AI-assisted locales
- 3 documented English fallbacks: `gv_IM`, `kw_GB`, `se_NO`

All 54 full locale files are under `translations/g1-mc1.8/`.

`scripts/validate_translations.py` validates exact key parity, placeholders, technical tokens, debug-only text, duplicate keys, expected locale files and documented fallbacks.

## Minecraft 1.8.9 / JEI 2.28.18

Status: **selected primary-language translation scope complete and prototype packaging buildable**.

### English source and G2 delta

- English source: `upstream/sources/1.8.9/en_US.lang`
- 75 keys = 72 normal + 3 debug-only
- compared with Minecraft 1.8: 46 unchanged, 19 added, 2 removed, 10 changed English values
- 29 translated/reviewed delta entries per absent addon locale

Exact comparison: `upstream/diffs/1.8-to-1.8.9.json`.

`translations/g2-mc1.8.9/` covers all 54 absent addon-locale deltas. `scripts/reconstruct_1_8_9.py` deterministically reconstructs all 54 complete 75-key files and CI verifies them.

- 51 locale deltas translated / AI-assisted
- 3 documented English fallback locales: `gv_IM`, `kw_GB`, `se_NO`

### Completion of upstream JEI locales

The addon supplies only keys missing from JEI's existing locale files:

| Locale | Upstream normal keys | Addon supplement | Combined |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

Together with upstream `en_US`, the project's selected 60-language scope is covered for JEI 1.8.9.

### Prototype JAR

Latest successful static build:

- commit `ef200a1ac1e03b09fd5c3b950c319e8ebf760647`
- workflow run `34632859235`
- JAR `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`
- SHA-256 `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`
- 59 language resources

The prototype is **not final**. In-game Minecraft 1.8.9 + Forge + JEI runtime validation is still required before promotion to `release-jars/1.8.9/`.

## Minecraft 1.9 / JEI 3.3.3

Status: **translation data not created yet; source/diff/raw-language/upstream-completeness audit complete**.

The actual Minecraft 1.9 endpoint is pinned to JEI upstream commit `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`. The branch head must not be used because the branch later moved to Minecraft 1.9.4.

### English/G3 delta

- source: `upstream/sources/1.9/en_US.lang`
- 77 keys = 74 normal + 3 debug-only
- versus 1.8.9: 74 unchanged, 2 added, 0 removed, 1 changed English value
- inherited locales therefore require only **3 new/reviewed entries**

Exact diff: `upstream/diffs/1.8.9-to-1.9.json`.

### Minecraft language audit

`script/audit_1_9.py` is not a path; the implemented script is `scripts/audit_1_9.py`. It runs in `.github/workflows/audit-1.9.yml`.

Successful audit run: `34635026243`.

Verified:

- 89 external Minecraft 1.9 `.lang` files
- plus base `en_US`
- **90 raw language codes**
- **15 new codes** versus the project's Minecraft 1.8 raw scope
- **0 removed codes**

New codes:

`be_BY`, `br_FR`, `en_NZ`, `en_UD`, `fo_FO`, `fy_NL`, `gd_GB`, `jbo_EN`, `ksh_DE`, `li_LI`, `lol_US`, `mk_MK`, `so_SO`, `sq_AL`, `tzl_TZL`.

Current policy classification:

- obvious primary candidates requiring full new translations: `be_BY`, `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `mk_MK`, `so_SO`, `sq_AL`
- defer regional `en_NZ`
- exclude novelty `en_UD`, `lol_US`
- explicit project decision pending: `jbo_EN`, `tzl_TZL`

Provisional selected scope: **70 languages** without those two pending codes, or **72** if both are retained.

Permanent audit summary: `upstream/minecraft-1.9-language-audit.json`.

### Norwegian locale handling

Minecraft 1.9 has `no_NO` and not `nb_NO`. JEI 3.3.3 has `nb_NO` and not `no_NO`.

The addon will continue targeting `no_NO` for Minecraft. JEI's upstream `nb_NO` file is preserved and is not treated as a replacement or overwritten.

### JEI upstream completeness

| Locale | Normal present | Missing normal | Project handling |
|---|---:|---:|---|
| `de_DE` | 53/74 | 21 | missing-key-only supplement |
| `en_US` | 74/74 | 0 | upstream only |
| `fi_FI` | 58/74 | 16 | missing-key-only supplement |
| `fr_FR` | 74/74 | 0 | upstream only; no full addon override |
| `ko_KR` | 5/74 | 69 | missing-key-only supplement |
| `nb_NO` | 74/74 | 0 | preserve upstream; not a Minecraft 1.9 asset code |
| `ru_RU` | 53/74 | 21 | missing-key-only supplement |
| `zh_CN` | 21/74 | 53 | missing-key-only supplement |

For the obvious 70-language scope, the expected output structure is **63 full addon locale files + 5 upstream missing-key supplements**. If `jbo_EN` and `tzl_TZL` are retained, it becomes **65 full addon locale files + 5 supplements**.

Important workload distinction:

- inherited addon locales can reuse 74 unchanged G2 key/value pairs and need only the 3-entry G3 delta;
- the newly selected Minecraft 1.9 primary languages have no G2 base and require full 74-normal-key translations;
- upstream `fr_FR` is complete and must not be duplicated as a full addon locale;
- upstream incomplete locales receive missing-key-only files, never full overrides.

### Next translation step

Before creating `translations/g3-mc1.9/`, decide the scope policy for `jbo_EN` and `tzl_TZL`. Then freeze `upstream/minecraft-1.9-language-scope.json`, generate the inherited-locale delta set, translate new full locales, create upstream supplements, and add deterministic G3 validation/reconstruction.

## Release limitation

Minecraft 1.8.9 still requires real runtime validation before publication. Minecraft 1.9 is at the audited pre-translation stage and has no release JAR yet.

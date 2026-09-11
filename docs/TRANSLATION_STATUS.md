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

The prototype JAR remains non-final until a real Minecraft 1.8.9 + Forge + JEI runtime test is completed.

## Minecraft 1.9 / JEI 3.3.3

Status: **selected 70-language translation/reconstruction stage complete; CI green; version-specific JAR not finalized yet**.

The actual Minecraft 1.9 endpoint is pinned to JEI upstream commit `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`. The branch head must not be used because the branch later moved to Minecraft 1.9.4.

### English/G3 delta

- source: `upstream/sources/1.9/en_US.lang`
- 77 keys = 74 normal + 3 debug-only
- versus 1.8.9: 74 unchanged, 2 added, 0 removed, 1 changed English value
- inherited addon locales require only a 3-entry delta

Exact diff: `upstream/diffs/1.8.9-to-1.9.json`.

### Frozen Minecraft language scope

The verified Minecraft 1.9 raw inventory contains 90 codes. The selected project scope is frozen at **70 real-world primary-language locales** in `upstream/minecraft-1.9-language-scope.json`.

New selected primary languages:

`be_BY`, `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `mk_MK`, `so_SO`, `sq_AL`.

Policy exclusions/deferments added in 1.9:

- regional English variant deferred: `en_NZ`
- novelty entries excluded: `en_UD`, `lol_US`
- constructed languages deferred: `jbo_EN` (Lojban), `tzl_TZL` (Talossan)

### Full addon locales

There are **63 addon-owned full locales** for 1.9:

- 53 inherited from G2 and reconstructed with `translations/g3-mc1.9/inherited-delta.tsv`;
- 10 newly selected locales with no earlier project base.

For the ten new locales, the current confidence realization is deliberately conservative:

- full AI-assisted drafts: `be_BY`, `mk_MK`, `sq_AL`;
- documented English fallbacks: `br_FR`, `fo_FO`, `fy_NL`, `gd_GB`, `ksh_DE`, `li_LI`, `so_SO`.

The older documented fallback locales `gv_IM`, `kw_GB`, and `se_NO` also remain English. Therefore the reconstructed 63 full addon files contain **53 translated/AI-assisted locales and 10 explicit English fallbacks**.

Policy manifest: `translations/g3-mc1.9/new-full-policy.json`.

### Upstream JEI locale handling

JEI 3.3.3 ships `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`.

- `en_US` and `fr_FR` are complete upstream and receive no addon override.
- `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN` receive missing-key-only supplements.
- Minecraft uses `no_NO`; JEI ships `nb_NO`. The project keeps `no_NO` as a separate full addon locale and preserves upstream `nb_NO` untouched.

Supplement coverage:

| Locale | Upstream normal | Addon supplement | Combined |
|---|---:|---:|---:|
| `de_DE` | 53/74 | 21 | 74/74 |
| `fi_FI` | 58/74 | 16 | 74/74 |
| `ko_KR` | 5/74 | 69 | 74/74 |
| `ru_RU` | 53/74 | 21 | 74/74 |
| `zh_CN` | 21/74 | 53 | 74/74 |

### Automation and CI

- delta QA: `scripts/validate_1_9_delta.py`
- deterministic reconstruction: `scripts/reconstruct_1_9.py`
- complete output QA: `scripts/validate_1_9_complete.py`
- CI workflow: `.github/workflows/validate.yml`
- successful complete validation run: **34638556534**

The reconstruction generates exactly 63 complete addon locales and 5 missing-key-only upstream supplements, validates source key parity, debug-only English policy, placeholders, technical literals and documented fallbacks.

## Next version

The next translation target is **Minecraft 1.9.4**. It must be audited from the historical upstream 1.9 branch after the transition commit, with an exact pinned endpoint rather than assuming the current branch head is representative of every historical 1.9.4 JEI state.

## Release limitation

Minecraft 1.8.9 still requires real runtime validation before final publication. Minecraft 1.9 has complete translation/reconstruction data but does not yet have a finalized runtime-tested release JAR. Audit/translation work may continue to later Minecraft versions before those JARs are finalized.

# Translation Status

This file summarizes completed localization generations. Exact endpoint metadata lives in `upstream/versions.json`; generation/reuse metadata lives in `upstream/generations.json`. Fixed rule: **one Minecraft version per final JAR**.

## Completed generations

| Generation | Minecraft | JEI | Keys | Selected scope | Addon full | Supplements | Complete upstream | CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G1 | 1.8 | 2.15.0 | 58 | 60 | 54 | — | 6 JEI files audited | complete |
| G2 | 1.8.9 | 2.28.18 | 75 | inherited | 54 | 5 | 1 | prototype `34632859235` |
| G3 | 1.9 | 3.3.3 | 77 | 70 | 63 | 5 | 1 | `34638556534` |
| G4 | 1.9.4 | 3.6.8 | 80 | 70 | 63 | 6 | 1 | `34639831977` |
| G5 | 1.10 | 3.7.1 | 78 | 72 | 65 | 6 | 1 | `34641765047` |
| G6 | 1.10.2 | 3.14.8 | 87 | 72 | 52 | 16 | 4 | `34642956606` |
| G7 | 1.11 | 4.1.1 | 87 | 72 | 52 | 16 | 4 | `34644034423` |
| G8 | 1.11.2 | 4.5.1 | 93 | 72 | 52 | 19 | 1 | `34644712028` |
| G9 | 1.12 | 4.7.5 | 93 | 80 | 60 | 18 | 2 | `34668113754` |
| G10 | 1.12.1 | 4.7.8 | 93 | 80 | 60 | 18 | 2 | `34668344181` |
| G11 | 1.12.2 | 4.16.5 | 115 | 80 | 55 | 24 | 1 | `34668803121` |
| G12 | 1.13 | 4.14.4 | 105 | 83 | 62 | 12 | 9 | `34671542080` |

All rows marked by a CI run are complete at the **translation/reconstruction QA** stage, not automatically runtime-tested JAR releases.

## G9 — Minecraft 1.12 / JEI 4.7.5

- Pinned `6bce08ef068fc0d7ce80ef07512caf85ccd4cab4`.
- English source is semantically identical to G8: 93/93 unchanged.
- Minecraft raw language inventory grows from 95 to 107.
- Selected scope expands to 80 with eight new real-world languages: `bs_ba`, `ig_ng`, `kab_kab`, `kn_in`, `oj_ca`, `ta_in`, `vec_it`, `yo_ng`.
- Ownership: 60 addon full + 18 exact supplements + complete upstream `en_us`, `ja_jp`.
- New selected languages begin as documented English fallbacks.

## G10 — Minecraft 1.12.1 / JEI 4.7.8

- Pinned `7f4160ed969fad85e8c4a14809c66402c51592b2`.
- Same 93-key English source, same Minecraft asset index, same JEI language ownership as G9.
- G10 resources are exact deterministic G9 localization inheritance.

## G11 — Minecraft 1.12.2 / JEI 4.16.5

- Pinned final normal-branch endpoint `f98331af6b1f7d59da01beecacd681c16dd548b9`.
- Forge `14.23.5.2860`; RetroFuturaGradle mappings `stable` / `39`; Java 8.
- 115 keys = 112 normal + 3 debug.
- G10→G11: 41 unchanged, 33 added, 11 removed, 41 changed; 71 normal added/changed meanings reviewed.
- Selected scope remains 80.
- Ownership becomes 55 addon full + 24 supplements + `en_us` complete upstream.
- Only exact unchanged semantics are inherited. Missing changed/new meanings use exact target-English fallback instead of guessed technical translations.

## G12 — Minecraft 1.13 / JEI 4.14.4

- Pinned `380bc11efb548abd804c65b763c911ebf9d06e2c`, immediately before the branch jumps to 1.13.2.
- Forge `24.0.181-1.13-pre`; mappings `snapshot` / `20180921-1.13`; Java 8.
- First project generation using **JSON** language resources.
- 105 semantic keys = 102 normal + 3 debug. JSON `_comment` entries are metadata, not localization keys.
- G11→G12: 59 unchanged, 4 added, 14 removed, 42 changed; 43 normal added/changed meanings reviewed.
- Minecraft raw language inventory = 113. `ksh_de` migrates to `ksh`; `nuk`, `ovd`, `szl` join the selected scope, bringing it to 83.
- Ownership: 62 addon full + 12 missing-key-only JSON supplements + 9 complete selected upstream locales.
- 23 complete English fallback locales; 39 translated/AI-assisted addon-full locales.
- Reuse policy searches exact G11 semantics first, then exact G10 semantic reversions. It never transfers translations across renamed keys, so Tag keys do not inherit removed Ore Dictionary keys.
- The reconstruction also rejects historical values that lose placeholders or fixed technical literals. This caught and safely replaced one old `no_no` value that omitted `JEI`.
- Full QA green on run **34671542080**.

Files:
- `upstream/sources/1.13/en_us.json`
- `upstream/diffs/1.12.2-to-1.13.json`
- `upstream/minecraft-1.13-language-audit.json`
- `upstream/minecraft-1.13-language-scope.json`
- `translations/g12-mc1.13/policy.json`
- `scripts/reconstruct_1_13.py`
- `scripts/validate_1_13_delta.py`
- `scripts/validate_1_13_complete.py`

## Next version

G12 is complete at translation/reconstruction stage. Next chronological target is **Minecraft 1.13.2 / JEI 5.0.0** on the same historical upstream branch. There is no separate 1.13.1 endpoint in the audited branch history.

## Release limitations

- G2/1.8.9 still requires a real client runtime test before promotion to `release-jars/1.8.9/`.
- Starting with G12, partial JSON supplements must also receive a real runtime merge test before their version-specific JAR is promoted.
- Chronological translation auditing can continue independently of those runtime release gates.

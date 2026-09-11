# JEI Translation Expansion — Project Status

> **Canonical handoff file. Start here in a new chat.**

Last synchronized: **2026-09-11**

## Repository and purpose

- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Upstream JEI: https://github.com/mezz/JustEnoughItems
- Project: unofficial localization companion for Just Enough Items (JEI)
- License: MIT
- No gameplay content; localization resources plus only the minimum loader metadata/code needed to load them.

## Fixed project policy

- **One Minecraft version per final JAR. Never ship a multi-version Minecraft JAR.**
- Final runtime-validated JARs must also be retained under `release-jars/<minecraft-version>/`.
- Prototype/draft JARs do not belong in `release-jars/`.
- Translation generations/deltas may reuse earlier translations internally, but final resources are reconstructed for the exact Minecraft/JEI target.
- Preserve JEI upstream translations by default. For locales already shipped by JEI, add only missing keys unless an override is explicitly reviewed.
- Reuse translations only when both key and English meaning are unchanged.
- Preserve placeholders and technical literals exactly.
- AI-assisted translation is permitted with automated QA and community correction.
- Prefer documented English fallback over a low-confidence fabricated translation.
- Initial scope focuses on real-world primary Minecraft languages; novelty/fantasy languages and most regional variants are excluded/deferred.

## Minecraft 1.8 / JEI 2.15.0

Translation stage: **complete for selected scope**.

- Forge: 11.14.4.1577
- Java source/target: 1.7
- format: legacy `.lang`
- English source: `upstream/sources/1.8/en_US.lang`
- 58 keys total = 55 normal + 3 debug-only
- upstream locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- selected primary language scope: 60 languages
- 54 locales absent upstream are supplied under `translations/g1-mc1.8/`
- 51 translated / AI-assisted
- 3 documented English fallbacks: `gv_IM`, `kw_GB`, `se_NO`

Exact scope: `upstream/minecraft-1.8-language-scope.json`.

## Minecraft 1.8.9 / JEI 2.28.18

Selected primary-language translation scope: **complete**.
Prototype version-specific Forge JAR: **builds reproducibly and passes static CI inspection**.
Final release: **not yet runtime-tested**.

### Verified upstream facts

- upstream branch: `1.8.9`
- Minecraft: 1.8.9
- JEI: 2.28.18
- JEI mod id: `JEI`
- JEI accepted Minecraft versions: `[1.8.9]`
- Forge used by upstream build: 11.15.1.1855
- minimum Forge declared by JEI: 11.15.1.1808
- Java source/target: 1.7
- format: legacy `.lang`
- English source: `upstream/sources/1.8.9/en_US.lang`
- 75 keys total = 72 normal + 3 debug-only
- upstream locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

### Exact 1.8 -> 1.8.9 transition

- 46 keys unchanged in identifier and English meaning: safely reusable
- 19 keys added
- 2 keys removed
- 10 existing keys changed English text/meaning
- 29 entries per absent addon locale require new/reviewed translation

Machine-readable diff: `upstream/diffs/1.8-to-1.8.9.json`.

`translations/g2-mc1.8.9/` stores six TSV batches covering all 54 absent addon-locale deltas. The same three low-confidence locales (`gv_IM`, `kw_GB`, `se_NO`) remain documented English fallbacks.

`scripts/reconstruct_1_8_9.py` deterministically reconstructs all **54 complete 75-key absent-locale files** from G1 + G2 and CI checks the reconstruction.

### Completion of JEI's own incomplete 1.8.9 locales

The five non-English locales already shipped by JEI are incomplete relative to the 72 normal English keys. Their exact upstream snapshots are stored in:

`upstream/sources/1.8.9/official/`

Missing-key-only supplement files are stored in:

`translations/g2-mc1.8.9/upstream-supplements/`

The supplements intentionally contain **no key that already exists in the corresponding upstream locale**.

Validated coverage:

| Locale | Upstream normal keys | Supplement keys | Combined normal coverage |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

Validator: `scripts/validate_1_8_9_upstream_supplements.py`.

With upstream `en_US`, those 5 completed upstream locales, and the 54 absent addon locales, the selected **60-primary-language scope is covered for JEI 1.8.9**.

### 1.8.9 prototype packaging implementation

Files now implemented:

- `packaging/1.8.9/release.json` — machine-readable packaging/release status
- `packaging/1.8.9/src/JeiTranslationExpansion.java.in` — tiny client-only Forge entrypoint template
- `packaging/1.8.9/mcmod.info.in` — metadata template
- `packaging/1.8.9/compile-stubs/net/minecraftforge/fml/common/Mod.java` — compile-only annotation signature; **never packaged**
- `scripts/build_1_8_9.py` — deterministic JAR builder
- `.github/workflows/build-1.8.9.yml` — prototype build/inspection/artifact workflow

Current prototype dependency policy is intentionally conservative:

- Minecraft exactly 1.8.9
- Forge `11.15.1.1808+`
- JEI exactly `2.28.18`
- client-side-only addon; remote/server side does not require the addon

The exact JEI dependency remains narrow until a wider 1.8.9 JEI compatibility range is explicitly audited.

The old Forge Maven endpoint returned HTTP 403 to the CI downloader. To avoid depending on unavailable legacy ForgeGradle/Maven infrastructure, the tiny entrypoint is compiled with Java 7 bytecode against a local **compile-only** copy of the public Forge `@Mod` annotation signature. The builder checks that this stub does not leak into the output JAR; Forge supplies the actual annotation class at runtime.

### Successful 1.8.9 prototype build

GitHub Actions run: **34632271287**
Source commit: `8100b0bf500a9a98957a090b3b758f99fe07b576`
Result: **success**.

All workflow stages passed:

1. delta QA;
2. upstream-locale supplement QA;
3. complete 54-locale reconstruction;
4. Java entrypoint compilation;
5. JAR build;
6. JAR content inspection;
7. artifact upload.

Prototype output:

- filename: `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`
- SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`
- 59 language resources = 54 complete absent locales + 5 upstream missing-key supplements
- 64 total JAR entries
- temporary Actions artifact: `jei-translation-expansion-mc1.8.9-prototype`
- Actions artifact ID: `10276756264`
- prototype artifact retention: 14 days from build

This JAR is **not promoted to `release-jars/1.8.9/`**, because final archive policy requires a runtime-validated build.

### Remaining before Minecraft 1.8.9 can be called final/publishable

1. Run an actual Minecraft 1.8.9 + compatible Forge + JEI 2.28.18 client test.
2. Confirm Forge discovers `jei_translation_expansion` without server-side requirement/conflict.
3. Confirm an absent locale (for example `fr_FR`) loads JEI translations from the addon.
4. Confirm an upstream-existing locale (for example `de_DE` or `ko_KR`) keeps upstream strings while the addon's missing-key supplement fills absent keys.
5. Confirm no crash/resource conflict and normal JEI behavior.
6. If runtime test passes, build the chosen final project version, record its SHA-256 and store the JAR under `release-jars/1.8.9/`.

## QA / CI

`.github/workflows/validate.yml` currently checks:

- Minecraft 1.8 translations;
- Minecraft 1.8.9 G2 delta;
- Minecraft 1.8.9 upstream-locale supplements;
- deterministic reconstruction of complete 1.8.9 absent-locale resources.

The latest validation associated with the successful prototype-build source also completed successfully.

## Modern endpoint already inspected

Upstream branch `26.2` uses JSON language files under `Common/src/main/resources/assets/jei/lang/`. Its English file is about 28.7 KB and has several hundred entries, substantially larger than the 1.8-era schemas.

## Recommended next development work

The 1.8.9 translation/build pipeline is now far enough advanced that the only major blocker to final release is an **in-game runtime test**. Since publication is not immediate, translation work can continue to the next official JEI/Minecraft version while this final runtime check remains pending.

Next translation audit:

1. identify the official JEI/Minecraft target immediately after 1.8.9;
2. snapshot its actual English localization source;
3. record JEI/Forge/Java metadata;
4. compare exact key/value semantics against 1.8.9;
5. reuse only proven unchanged translations;
6. translate/QA only new or changed material.

## Important files

- `PROJECT_STATUS.md` — canonical handoff
- `docs/TRANSLATION_STATUS.md` — language coverage details
- `docs/VERSION_MATRIX.md` — audited version/build matrix
- `docs/WORKFLOW.md` — project workflow and one-version-per-JAR rule
- `release-jars/README.md` — final artifact archive policy
- `upstream/generations.json` — translation generations
- `upstream/sources/1.8.9/official/` — snapshots of JEI's own non-English 1.8.9 locales
- `translations/g2-mc1.8.9/upstream-supplements/` — missing-key-only additions for upstream locales
- `packaging/1.8.9/release.json` — complete machine-readable 1.8.9 packaging state
- `scripts/build_1_8_9.py` — 1.8.9 deterministic prototype builder

## Resume prompt

> Reprends JEI Translation Expansion depuis https://github.com/romaintv20-stee-land-More/jei-translation-expansion. Lis d'abord `PROJECT_STATUS.md`, puis `docs/TRANSLATION_STATUS.md`, `docs/VERSION_MATRIX.md`, `docs/WORKFLOW.md` et `packaging/1.8.9/release.json`. Minecraft 1.8.9 a une couverture complete du scope primaire selectionne et un prototype Forge reproductible qui a passe la CI (run 34632271287, SHA-256 JAR `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`). Ne le promouvoir dans `release-jars/1.8.9/` qu'apres un test reel en jeu. Pour continuer les traductions, audite la version officielle suivant 1.8.9. Regle fixe : un JAR par version Minecraft.

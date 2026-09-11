# JEI Version Matrix

This document tracks verified JEI/Minecraft translation endpoints. It is intentionally incomplete until the full upstream audit is finished.

## Verified endpoints

| Upstream branch | Minecraft | JEI | Loader(s) | Translation format | English keys | Project status |
|---|---:|---:|---|---|---:|---|
| `1.8` | 1.8 | 2.15.0 | Forge | legacy `.lang` | 58 | translation scope complete |
| `1.8.9` | 1.8.9 | 2.28.18 | Forge | legacy `.lang` | 75 | selected scope complete + reproducible prototype JAR builds |
| `1.9` pinned at `b2ffe6b` | 1.9 | 3.3.3 | Forge | legacy `.lang` | 77 | upstream/key audit complete; locale-code scope reconciliation pending |
| `26.2` | 26.2 | audit pending exact JEI release | audit pending | JSON | several hundred | partially verified |

## Minecraft 1.8 details

Verified from official upstream branch `1.8` on 2026-09-11:

- `mcversion=1.8`
- `forgeversion=11.14.4.1577`
- JEI `2.15.0`
- Java source/target compatibility in upstream build: `1.7`
- 58 English localization keys
- Official JEI locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

No upstream `1.7` branch was found in the initial audit, so Minecraft 1.8 is the current oldest support target.

## Minecraft 1.8.9 details

Verified from official upstream branch `1.8.9` on 2026-09-11:

- `mcversion=1.8.9`
- build Forge version: `11.15.1.1855`
- JEI `2.28.18`
- JEI's `@Mod` annotation accepts exactly Minecraft `[1.8.9]`
- JEI's `@Mod` annotation requires Forge `11.15.1.1808` or newer
- JEI mod id: `JEI`
- Java source/target compatibility in upstream build: `1.7`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- 75 English localization keys: 72 normal + 3 debug-only
- Official JEI locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

### 1.8 -> 1.8.9 localization transition

Compared with JEI 2.15.0 / Minecraft 1.8:

- 46 keys are unchanged in both key and English meaning and are safe to reuse;
- 19 keys are new;
- 2 keys are removed;
- 10 existing keys keep the same identifier but change English text/meaning;
- therefore 29 translation entries per absent addon locale require a new or reviewed 1.8.9 value.

Exact machine-readable comparison: `upstream/diffs/1.8-to-1.8.9.json`.

The 54 complete absent-locale files are deterministically reconstructable from G1 + G2 with `scripts/reconstruct_1_8_9.py`.

### Existing JEI locale completeness

The five non-English locale files shipped by JEI are preserved as upstream-owned translations. The addon adds only their missing normal keys.

| Locale | Upstream normal keys | Addon supplement | Combined normal coverage |
|---|---:|---:|---:|
| `de_DE` | 53 | 19 | 72/72 |
| `fi_FI` | 58 | 14 | 72/72 |
| `ko_KR` | 5 | 67 | 72/72 |
| `ru_RU` | 53 | 19 | 72/72 |
| `zh_CN` | 21 | 51 | 72/72 |

Upstream snapshots: `upstream/sources/1.8.9/official/`.
Missing-key-only project files: `translations/g2-mc1.8.9/upstream-supplements/`.
Validator: `scripts/validate_1_8_9_upstream_supplements.py`.

The selected primary-language scope therefore covers 60 languages for JEI 1.8.9 when upstream `en_US`, the five completed upstream locales, and the 54 addon locales are counted together. Three low-confidence addon locales remain documented English fallbacks by policy.

### 1.8.9 prototype packaging

A version-specific Forge prototype build is implemented with:

- minimal client-only mod id `jei_translation_expansion`;
- exact Minecraft target `[1.8.9]`;
- current safe JEI dependency `required-after:JEI@[2.28.18]`;
- Forge dependency `required-after:Forge@[11.15.1.1808,)`;
- Java source/target 7 entrypoint bytecode;
- 54 complete absent-locale resources + 5 partial upstream-locale supplements = 59 `.lang` resources;
- deterministic ZIP/JAR metadata;
- `LICENSE`, `NOTICE`, `mcmod.info` and manifest.

Because the old Forge Maven endpoint rejects the CI downloader, the tiny entrypoint is compiled against a compile-only local copy of the public Forge `@Mod` annotation signature. That compile stub is explicitly excluded from the output JAR; Forge supplies the real annotation class at runtime.

Latest successful CI prototype build after strengthening the Forge annotation inspection:

- source commit: `ef200a1ac1e03b09fd5c3b950c319e8ebf760647`
- workflow run: `34632859235`
- filename: `jei-translation-expansion-0.1.0-ci-mc1.8.9-forge.jar`
- SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`
- language files inside JAR: 59
- total JAR entries: 64
- Actions artifact ID: `10277785240`

The prototype passed translation validation, reconstruction, build, Java 7 bytecode inspection, Forge `@Mod` runtime-annotation descriptor checks, dependency-string checks and archive inspection. It is **not yet a final release**, because an in-game Minecraft 1.8.9 + Forge + JEI 2.28.18 runtime test is still pending. Only after that test should a final-version build be placed under `release-jars/1.8.9/`.

Version-specific machine-readable packaging status: `packaging/1.8.9/release.json`.

## Minecraft 1.9 / JEI 3.3.3 details

The upstream branch named `1.9` currently points at later Minecraft 1.9.4 work, so the project does **not** use the branch head as the Minecraft 1.9 reference. The exact Minecraft 1.9 endpoint is pinned to upstream commit:

`b2ffe6bd7734d093006de99f9dc99b2b77ce780d`

This is the parent immediately before upstream commit `d6b11a003a4a10702a36f8a97fa28cae883c9360`, whose change explicitly transitions the branch to Minecraft 1.9.4.

Verified at the pinned Minecraft 1.9 snapshot:

- Minecraft: `1.9`
- JEI: `3.3.3`
- Forge: `12.16.0.1865-1.9`
- MCP mappings: `snapshot_20160421`
- Java source/target: `1.7`
- language format: legacy `.lang`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- project snapshot: `upstream/sources/1.9/en_US.lang`
- 77 English keys = 74 normal + 3 debug-only
- upstream locale files: `de_DE`, `en_US`, `fi_FI`, `fr_FR`, `ko_KR`, `nb_NO`, `ru_RU`, `zh_CN`

### 1.8.9 -> 1.9 localization transition

The change is small:

- 74 keys keep the same identifier and English value and are safe to reuse;
- 2 keys are added: `jei.tooltip.shapeless.recipe` and `key.jei.focusSearch`;
- 0 keys are removed;
- 1 existing key changes English text: `key.jei.toggleOverlay` loses the old ` (Ctrl + )` suffix;
- therefore only **3 entries per inherited locale** require a new/reviewed value once the Minecraft 1.9 locale scope is finalized.

Exact comparison: `upstream/diffs/1.8.9-to-1.9.json`.

### Locale-scope blocker before G3 translation

JEI 3.3.3 now ships `fr_FR` and `nb_NO` upstream in addition to the earlier locales. This changes the merge plan: upstream-owned locale keys must be preserved and only missing keys may be supplemented.

The project has intentionally **not created `translations/g3-mc1.9/` yet**. The actual Minecraft 1.9 locale identifiers must first be verified, especially Norwegian: the previous selected project scope used `no_NO`, while this JEI snapshot contains `nb_NO`. Reusing or renaming that locale without verification could create a file Minecraft never loads or an unnecessary parallel locale.

Next step for 1.9 is therefore: verify the Minecraft 1.9 language-code set, reconcile `no_NO`/`nb_NO`, audit completeness of all seven non-English upstream JEI locale files, then translate only the required three-key delta plus any proven missing-key supplements.

## Audit rules

For every upstream branch/version added to this table, record actual values from upstream instead of inferring them from the branch name.

For each audited version, collect where practical:

- English translation key count;
- normalized English key/value comparison with adjacent versions;
- official locale list and missing-key coverage;
- loader metadata;
- Java requirement/source target;
- resource/language format;
- semantic changes to existing keys.

## Generation rule

Translation generations may inherit from earlier versions only when the key and English meaning are demonstrably unchanged. Release builds must reconstruct and validate complete resources against the exact target version.

## Distribution rule

Project policy is **one Minecraft version per release JAR**. No final JAR may claim multiple Minecraft versions. Final runtime-validated artifacts must additionally be retained under `release-jars/<minecraft-version>/`.

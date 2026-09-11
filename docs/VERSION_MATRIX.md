# JEI Version Matrix

This document tracks verified JEI/Minecraft translation endpoints. It is intentionally incomplete until the full upstream audit is finished.

## Verified endpoints

| Upstream branch | Minecraft | JEI | Loader(s) | Translation format | English keys | English source | Status |
|---|---:|---:|---|---|---:|---|---|
| `1.8` | 1.8 | 2.15.0 | Forge | legacy `.lang` | 58 | `src/main/resources/assets/jei/lang/en_US.lang` | verified |
| `1.8.9` | 1.8.9 | 2.28.18 | Forge | legacy `.lang` | 75 | `src/main/resources/assets/jei/lang/en_US.lang` | verified + reconstruction-ready |
| `26.2` | 26.2 | audit pending exact JEI release | audit pending | JSON | several hundred | `Common/src/main/resources/assets/jei/lang/en_us.json` | partially verified |

## Minecraft 1.8 details

Verified from official upstream branch `1.8` on 2026-09-11:

- `mcversion=1.8`
- `forgeversion=11.14.4.1577`
- JEI `2.15.0`
- Java source/target compatibility in upstream build: `1.7`
- 58 English localization keys
- Official JEI locales: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

No upstream `1.7` branch was found in the branch search performed when the project was initialized, so **Minecraft 1.8 is the current oldest support target**.

## Minecraft 1.8.9 details

Verified from official upstream branch `1.8.9` on 2026-09-11:

- `mcversion=1.8.9`
- build Forge version: `11.15.1.1855`
- JEI `2.28.18`
- JEI's `@Mod` annotation accepts exactly Minecraft `[1.8.9]`
- JEI's `@Mod` annotation requires Forge `11.15.1.1808` or newer
- JEI mod id: `JEI`
- Java source/target compatibility in upstream build: `1.7`
- 75 English localization keys
- Official JEI locales remain: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`

Compared with JEI 2.15.0 / Minecraft 1.8:

- 46 keys are unchanged in both key and English meaning and are safe to reuse;
- 19 keys are new;
- 2 keys are removed;
- 10 existing keys keep the same identifier but change English text/meaning;
- therefore 29 translation entries per addon locale require a new or reviewed 1.8.9 value.

The exact machine-readable comparison is in `upstream/diffs/1.8-to-1.8.9.json`.

The 54 complete addon locale files can now be deterministically reconstructed from G1 + G2 with `scripts/reconstruct_1_8_9.py`. CI runs the script in `--check` mode so release resources are proven reconstructable before packaging. Version-specific packaging facts are recorded in `packaging/1.8.9/release.json`.

Remaining 1.8.9 release work is loader packaging rather than translation: finalize the addon JEI dependency range, choose/test the minimal Forge entrypoint strategy, build the version-specific JAR, and run an in-game test.

## Audit rules

For every upstream branch/version added to this table, record the actual values from upstream instead of inferring them from the branch name. A branch name alone is not sufficient proof of the Minecraft target.

For each audited version, also collect:

- English translation key count;
- hash of the normalized English key/value set where useful;
- official locale list;
- missing-key count per official locale where useful;
- loader metadata;
- Java requirement/source target where relevant;
- resource pack/language format details;
- whether key meanings changed compared with adjacent generations.

## Generation rule

Two versions may be placed in the same localization generation only when their translation schema is compatible and any changed English meanings have been explicitly handled.

A later generation may be stored as a verified delta from an earlier generation when unchanged key/value translations are demonstrably reusable. Release builds must reconstruct complete locale files and validate them against the exact target English source before packaging.

## Distribution rule

Project policy is **one Minecraft version per release JAR**. Translation generations may inherit data from earlier versions, but no final JAR may claim multiple Minecraft versions.

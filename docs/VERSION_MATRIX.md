# JEI Version Matrix

This document tracks verified JEI/Minecraft translation endpoints. It is intentionally incomplete until the full upstream audit is finished.

## Verified endpoints

| Upstream branch | Minecraft | JEI | Loader(s) | Translation format | English source | Status |
|---|---:|---:|---|---|---|---|
| `1.8` | 1.8 | 2.15.0 | Forge | legacy `.lang` | `src/main/resources/assets/jei/lang/en_US.lang` | verified |
| `26.2` | 26.2 | audit pending exact JEI release | audit pending | JSON | `Common/src/main/resources/assets/jei/lang/en_us.json` | partially verified |

## Minecraft 1.8 details

Verified from official upstream branch `1.8` on 2026-09-11:

- `mcversion=1.8`
- `forgeversion=11.14.4.1577`
- `version_major=2`
- `version_minor=15`
- `version_patch=0`
- Java source/target compatibility in upstream build: `1.7`
- Official translation files found:
  - `de_DE.lang`
  - `en_US.lang`
  - `fi_FI.lang`
  - `ko_KR.lang`
  - `ru_RU.lang`
  - `zh_CN.lang`

No upstream `1.7` branch was found in the branch search performed when the project was initialized, so **Minecraft 1.8 is the current oldest support target**.

## Audit rules

For every upstream branch/version added to this table, record the actual values from upstream instead of inferring them from the branch name. A branch name alone is not sufficient proof of the Minecraft target.

For each audited version, also collect:

- English translation key count;
- hash of the normalized English key/value set;
- official locale list;
- missing-key count per official locale;
- loader metadata;
- Java requirement/source target where relevant;
- resource pack/language format details;
- whether key meanings changed compared with adjacent generations.

## Generation rule

Two versions may be placed in the same localization generation only when their translation schema is compatible and any changed English meanings have been explicitly handled. Distribution JAR grouping is a separate decision and must also account for loader/resource metadata compatibility.

# Translation Benchmark

## Pilot — Minecraft 1.8 / JEI 2.15.0

Date: 2026-09-11

This pilot was requested to estimate the time needed once the project reaches the translation stage.

### Source set

- Upstream branch: `1.8`
- Source file: `src/main/resources/assets/jei/lang/en_US.lang`
- Snapshot in this repository: `upstream/sources/1.8/en_US.lang`
- Total localization keys in the source: **58**
- Debug-only keys explicitly marked by upstream as not needing translation: **3**
- Keys translated per locale: **55**

### Pilot locales

The five selected primary languages were absent from JEI's upstream 1.8 language folder:

- `fr_FR` — French
- `es_ES` — Spanish (Spain)
- `it_IT` — Italian
- `pt_BR` — Brazilian Portuguese
- `nl_NL` — Dutch

Total translated entries produced in the pilot: **275** (55 × 5).

### Timing

Timing was measured from the point where the upstream English source had been loaded and translation work began until the five locale drafts and placeholder/key QA were complete.

- Start: **12:40:38 CEST**
- Translation + initial QA complete: **12:42:14 CEST**
- Elapsed: **1 minute 36 seconds**
- Average measured elapsed time: about **19 seconds per locale** for this small legacy set.

This timing excludes GitHub upload/commit time and should **not** be extrapolated directly to modern JEI. Modern branches contain several hundred strings, more placeholders, more existing upstream translations to protect, and more semantic changes to audit.

### QA performed for the pilot

- exact key-set parity for all 55 translatable keys;
- preserved Java formatting placeholders including `%,d`, `%s`, and `%MODNAME`;
- preserved technical literals such as `/give`, `@ModName`, `modId:name[:meta]`, `NBT`, `ItemStack`, `JEI`, and `mB` where required;
- kept the three upstream debug-description strings in English as instructed by the upstream comment;
- retained legacy `.lang` structure and locale naming conventions.

### Important status

These five files are a **translation-stage pilot**, not proof that Minecraft 1.8 is already release-ready. The full JEI version/generation audit and final packaging/loader QA still need to be completed before publishing a release.

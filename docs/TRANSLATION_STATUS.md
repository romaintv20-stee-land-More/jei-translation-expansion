# Translation Status

## Minecraft 1.8 / JEI 2.15.0

Status: **language-file stage complete for the selected scope**.

### Source

- Upstream JEI branch: `1.8`
- Source file: `src/main/resources/assets/jei/lang/en_US.lang`
- Local audited source snapshot: `upstream/sources/1.8/en_US.lang`
- 58 localization keys total
- 55 normal translatable keys
- 3 debug-only description keys intentionally left in English, following the upstream comment

### Language scope

Minecraft 1.8 exposes 75 language codes in the audited asset set when `en_US` is included.

Project policy for this generation:

- 3 novelty/fantasy languages excluded: `en_PT`, `qya_AA`, `tlh_AA`
- 12 regional/orthographic variants deferred for now
- 60 primary languages retained
- JEI itself already provides 6 of those: `en_US`, `de_DE`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- Addon target: 54 locale files

### Current result

All **54 addon target locale files are present** under `translations/g1-mc1.8/`.

- **51 locales** contain translated / AI-assisted localized text.
- **3 locales** intentionally use a documented English fallback because translation confidence was not high enough:
  - `gv_IM` — Manx
  - `kw_GB` — Cornish
  - `se_NO` — Northern Sami

The English fallbacks are deliberate and should be replaced only when a sufficiently reliable translation or native-speaker review is available.

### QA

`scripts/validate_translations.py` validates the Minecraft 1.8 generation for:

- presence of all 54 expected addon locale files;
- exact key-set parity with the audited English source;
- duplicate keys;
- formatting placeholder parity (`%,d`, `%s`, `%MODNAME`);
- important technical tokens such as `/give`, `@ModName`, `modId:name[:meta]`, `NBT`, `ItemStack`, `JEI`, `Minecraft`, `mB`, and `Ctrl`;
- debug-only keys remaining in English;
- English fallback being used only for the three explicitly documented low-confidence locales.

A GitHub Actions workflow at `.github/workflows/validate.yml` runs this validator on pushes and pull requests.

### Important limitation

This completes the **translation-file stage for Minecraft 1.8**, not the entire release.

Before publishing a 1.8 JAR, the project still needs to finish version-generation auditing, verify packaging/loader metadata and runtime compatibility, and determine whether adjacent JEI branches can safely share this localization generation or distribution artifact.

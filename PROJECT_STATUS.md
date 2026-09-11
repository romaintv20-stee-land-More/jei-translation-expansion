# JEI Translation Expansion — Project Status

> **Start here in a new chat. This file is the canonical handoff for the project and should be enough to resume work without relying on previous conversation history.**

Last synchronized: **2026-09-11**

## Repository

- Project: **JEI Translation Expansion**
- Repository: https://github.com/romaintv20-stee-land-More/jei-translation-expansion
- Default branch: `main`
- Upstream JEI repository: https://github.com/mezz/JustEnoughItems
- Upstream CurseForge: https://www.curseforge.com/minecraft/mc-mods/jei
- Current upstream default branch when this project was initialized: `26.2`
- License: MIT

## Purpose

Create an **unofficial localization companion for Just Enough Items (JEI)** that adds missing languages and fills missing translation keys across JEI/Minecraft generations and loaders while preserving JEI's own translations whenever possible.

The addon must not add gameplay content. It exists only to provide localization resources and any minimal loader metadata/stub code required to make those resources load correctly.

## Current phase

**Phase 1 — upstream audit and architecture.**

Do **not** begin mass translation before the version/key audit is complete. JEI has existed across many Minecraft versions and its translation schema has changed over time. The project must first identify localization generations by comparing the real upstream English source for each relevant branch/version.

## Current repository state

Already initialized on `main`:

- `README.md` — public project description, goals, AI policy and licensing summary.
- `PROJECT_STATUS.md` — this canonical handoff.
- `docs/VERSION_MATRIX.md` — verified version audit facts collected so far.
- `docs/WORKFLOW.md` — audit, translation, QA and release workflow.
- `upstream/versions.json` — machine-readable partial upstream version audit.
- `upstream/generations.json` — generation schema placeholder; intentionally empty until the comparison audit is complete.
- `upstream/official-locales.json` — partial inventory of locales shipped by JEI.
- `overrides/approved-overrides.json` — empty allowlist for reviewed overrides of upstream translations.
- `LICENSE` — MIT.
- `NOTICE` — unofficial-project notice and JEI attribution.

Still to create after/during the full audit:

- `scripts/audit_jei.py`
- `scripts/compare_keys.py`
- `scripts/validate_translations.py`
- `scripts/build_release.py`
- generation translation directories under `translations/`
- GitHub Actions workflow(s) for validation/builds

## Verified oldest starting point

The official JEI GitHub repository has a branch named **`1.8`**, and no `1.7` branch was found in the upstream branch search performed on 2026-09-11.

For upstream branch `1.8`:

- Minecraft: **1.8**
- JEI version in `gradle.properties`: **2.15.0**
- Forge version: **11.14.4.1577**
- Translation format: legacy `.lang`
- English source: `src/main/resources/assets/jei/lang/en_US.lang`
- Upstream locales present in that folder at audit time: `de_DE`, `en_US`, `fi_FI`, `ko_KR`, `ru_RU`, `zh_CN`
- `build.gradle` sets Java source/target compatibility to **1.7**. Runtime Java support should be audited separately before release metadata is finalized.

Therefore the oldest Minecraft version currently planned for support is **Minecraft 1.8**.

## Modern endpoint already inspected

On upstream branch `26.2`:

- JEI uses JSON language files under `Common/src/main/resources/assets/jei/lang/`.
- `en_us.json` is substantially larger than Catalogue's translation set and contains several hundred UI/config/tooltips/messages entries.
- Existing translations are uneven in completeness. For example, `fr_fr.json` is missing newer English keys and still contains older translation structure in places.
- This makes JEI a suitable target for both:
  - adding completely missing languages;
  - completing missing keys in languages already shipped by JEI.

## Translation policy

1. **Upstream-first protection** — Existing JEI translations are protected by default. Do not overwrite a key merely because the addon has another translation.
2. **Fill missing keys** — For locales shipped by JEI, generate only the keys missing for the targeted generation unless an override has been explicitly approved.
3. **Complete absent locales** — If JEI does not ship a locale at all, the addon may provide the complete translation set for that generation.
4. **Semantic reuse only** — Reuse a translation between generations only when the key and the English meaning are unchanged.
5. **Placeholder preservation** — Preserve `%s`, `%d`, indexed format specifiers, escaped newlines, literal symbols, key names, resource identifiers and other technical tokens exactly as required.
6. **No blind key migration** — Renamed keys must be mapped deliberately; do not assume similar names mean identical semantics.
7. **Low-confidence fallback** — Prefer documented English fallback over a made-up or low-confidence translation.
8. **AI transparency** — AI-assisted translations are permitted, but must undergo automated QA and should be open to community/human correction.
9. **Language scope** — Focus on real-world primary languages. Exclude novelty/fantasy languages such as Pirate Speak, LOLCAT, Klingon, Quenya and similar entries. Initially defer most regional/orthographic variants when a primary form is already covered.
10. **No unnecessary gameplay/code copying** — Only copy or derive what is necessary for translation compatibility, preserving upstream attribution and license requirements.

## Planned architecture

The repository separates **localization generations** from **distribution JAR groups**.

A generation is defined by a compatible set of JEI translation keys/English meanings. Generation names must be based on the completed audit rather than guessed in advance, for example:

```text
translations/
  g1-legacy-lang-.../
  g2-.../
  g3-.../
```

Distribution JARs may cover multiple Minecraft versions when loader metadata/resource compatibility makes that safe. The goal is to avoid one JAR per Minecraft version and keep the total number of downloadable files practical.

## QA requirements

Before a generated translation or release is accepted, QA should check at minimum:

- valid `.lang`/JSON syntax for the target era;
- exact required key names;
- no accidental duplicate keys;
- placeholder parity with English;
- preservation of escaped characters and technical literals;
- no unexpected English-key semantic reuse across generations;
- upstream-protected keys are not overwritten unless allowlisted;
- translation coverage report per locale;
- loader/version metadata matches the actual target;
- build artifacts are reproducible from checked-in source data.

## Release policy

- JEI must be declared as a required dependency where loader metadata supports dependencies.
- The addon should be client-side where appropriate, but exact loader/environment metadata must be verified per generation.
- Release files should clearly state Minecraft version range, loader, Java requirement, JEI version/range and release type.
- Do not claim compatibility for versions that have not been audited.
- Prefer grouped JARs only when compatibility is demonstrably safe.

## License and attribution

JEI is MIT licensed. This project is also MIT licensed.

When JEI source translation material or other MIT-covered upstream material is redistributed, retain the relevant JEI copyright/license notice. Keep the project visibly unofficial and link to the original JEI project.

## Immediate next steps

1. Start the detailed audit from **Minecraft 1.8**, then move forward through the JEI branches/releases toward `26.2`.
2. For each branch, record:
   - actual Minecraft version;
   - JEI version;
   - loader(s);
   - Java requirement/source compatibility where relevant;
   - language file path and format;
   - English key count;
   - official locales present.
3. Compare English translation keys and values between adjacent versions.
4. Define verified localization generations.
5. Determine which generations can share distribution JARs.
6. Only then begin translation work, starting with a carefully chosen set of high-value languages and expanding gradually.
7. Add automation/scripts and GitHub Actions for audit, validation and reproducible builds.
8. Update this file after every significant architectural or release change.

## Resume prompt for a future ChatGPT conversation

Use this prompt:

> Reprends le projet JEI Translation Expansion depuis https://github.com/romaintv20-stee-land-More/jei-translation-expansion. Lis d'abord `PROJECT_STATUS.md`, puis `README.md`, `docs/VERSION_MATRIX.md` et `docs/WORKFLOW.md`. Vérifie l'état actuel de l'upstream `mezz/JustEnoughItems` avant de modifier quoi que ce soit. Continue à partir des étapes restantes indiquées dans `PROJECT_STATUS.md` et mets ce fichier à jour après les changements importants.

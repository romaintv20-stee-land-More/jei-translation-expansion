# Project Workflow

## 1. Audit before translation

Never start a new JEI/Minecraft generation by copying the newest language file backward. Fetch the real upstream English language source for each relevant branch and compare it with adjacent versions.

The audit should determine:

- actual Minecraft version;
- JEI version;
- loader(s);
- Java compatibility/requirement;
- language file format and path;
- English keys and values;
- official locales and their coverage;
- semantic changes to existing keys.

## 2. Define localization generations

Create a generation only after key/value comparison. A generation may span several Minecraft versions if the translation schema is compatible.

If a key keeps the same identifier but its English meaning changes, treat the changed meaning as a new semantic translation state and do not blindly reuse the old translation.

## 3. Translation source strategy

For each locale and generation:

- use upstream JEI text as the protected base when it exists;
- add missing keys from this project;
- for a locale absent from JEI, provide the complete required set;
- keep explicitly approved corrections in `overrides/approved-overrides.json`;
- use English fallback for entries where a reliable translation is not available.

## 4. AI-assisted translation

AI assistance is allowed and should be disclosed publicly. AI-generated text must be treated as a draft subject to QA.

Automated checks should include:

- placeholder parity;
- syntax validity;
- key completeness;
- duplicate key detection;
- untranslated technical tokens;
- accidental changes to resource IDs, keybind names or format codes;
- suspicious untranslated English in languages expected to be translated;
- suspiciously identical translations across unrelated languages.

Community corrections should take priority over generated text once reviewed.

## 5. Language scope

Initial target: real-world primary languages used by Minecraft players.

Initially exclude/defer:

- novelty/fantasy languages;
- deliberately transformed English variants;
- most regional variants when a primary language version is already covered;
- low-confidence locales until a trustworthy translation can be produced.

The exact language manifest should be generated from the Minecraft language set appropriate to each era, not from the newest Minecraft version alone.

## 6. Distribution JAR strategy

Localization generations and distributable JAR groups are independent concepts.

A JAR may cover multiple Minecraft versions only if all of the following are safe:

- loader metadata accepts the range;
- resource format is compatible;
- JEI dependency range is correct;
- translation resources work for all included versions;
- any minimal entrypoint/stub code works on the full range.

Do not claim a broad version range simply to reduce the number of files.

## 7. Release QA

Before release:

1. Run translation validators.
2. Generate coverage report.
3. Build all JARs reproducibly.
4. Inspect JAR metadata and resource contents.
5. Check hashes.
6. Test representative endpoints in-game where practical, especially the oldest and newest version in a grouped JAR range.
7. Update `PROJECT_STATUS.md` and `docs/VERSION_MATRIX.md`.

## 8. Future-chat continuity

`PROJECT_STATUS.md` is the canonical handoff. Every substantial audit, architectural decision, generation addition, release or compatibility change must be summarized there so another conversation can continue without access to prior chat history.

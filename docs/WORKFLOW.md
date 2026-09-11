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

Create a generation only after key/value comparison. A generation may inherit translations from an earlier generation when the key and English meaning are unchanged.

If a key keeps the same identifier but its English meaning changes, treat the changed meaning as a new semantic translation state and do not blindly reuse the old translation.

Localization generations are an internal translation/reuse mechanism only. They do not determine how many Minecraft versions a release JAR may target.

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

**Project decision: one Minecraft version per release JAR.**

A final JAR must target exactly one Minecraft version. Do not group multiple Minecraft versions into one downloadable artifact, even if their translation schemas are identical or highly compatible.

Translation reuse between versions is still encouraged internally. A later version may inherit unchanged translations from an earlier generation, but its final complete resources are reconstructed and packaged into its own version-specific JAR.

Loader support for a given Minecraft version must still be audited. If one physical JAR can safely support all required loaders for that same Minecraft version, that is acceptable; otherwise loader-specific artifacts may be required. In every case, no JAR should claim more than one Minecraft version.

This policy simplifies CurseForge/Modrinth metadata, compatibility claims, testing, troubleshooting and future updates.

## 7. Release QA

Before release for each Minecraft version:

1. Run translation validators.
2. Reconstruct complete locale files from any stored deltas.
3. Generate a coverage report.
4. Build that version's JAR reproducibly.
5. Inspect JAR metadata and resource contents.
6. Check hashes.
7. Verify JEI dependency and loader metadata.
8. Test the version in-game where practical.
9. Update `PROJECT_STATUS.md` and `docs/VERSION_MATRIX.md`.

## 8. Current working cadence

The project may continue auditing and translating many Minecraft versions before final JAR generation. It is not necessary to stop after each translation stage to publish or finalize the JAR.

When release packaging begins, the build system should generate one complete JAR per audited Minecraft version from the stored full translations/deltas and version metadata.

## 9. Future-chat continuity

`PROJECT_STATUS.md` is the canonical handoff. Every substantial audit, architectural decision, generation addition, release or compatibility change must be summarized there so another conversation can continue without access to prior chat history.

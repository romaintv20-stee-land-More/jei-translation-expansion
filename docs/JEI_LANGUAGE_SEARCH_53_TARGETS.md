# JEI language selection search — exact target coverage

**Source-only project. No JAR has been built or released.**

The official JEI project supports **Minecraft 1.8.8**, and the previous 52-version JEI Translation Expansion matrix omitted it between Minecraft 1.8 and 1.8.9. See [official JEI 2.12.0.49](https://www.curseforge.com/minecraft/mc-mods/jei/files/2271876). The search matrix now tracks 53 distinct Minecraft targets, while the release/translation inventory correctly still has only 52 completed generations.

## Current source-only progress

All 53 distinct Minecraft targets have an explicit source route:

| Status | Targets | Count |
|---|---|---:|
| Draft search adapter source stored on this PR branch | Minecraft 1.8–1.21.11 (including 1.8.8) | 48 |
| Use the game's native search, no duplicate input | Minecraft 26.1, 26.1.1, 26.1.2, 26.2, 26.3 | 5 |
| **Missing source draft** | | **0** |
| **Runtime-verified client adapters** | | **0** |
| **Total** | | **53** |

These are **source-only drafts**, NOT 48 compiled or working Minecraft
versions. They require target-specific API checking, client compilation
and real Minecraft testing before any search functionality can be
considered complete. They are deliberately not wired into the JAR builders.

The 30 newest draft variants are stored under
`features/language-search/drafts/mc<version>/`. They were adapted
from neighboring API versions and **must not be packaged unverified**.
The shared matcher and `LanguageListFilter` preserve original row
identity and ordering, and their Java-only smoke tests pass in CI.

### Recovered missing Minecraft 1.8.8 translation generation

- Upstream: JEI 2.12.0.49, official CurseForge file 2271876, audited
  SHA-256 in `upstream/sources/1.8.8/provenance.json`.
- Exactly **56 English keys**, all semantically byte-for-byte unchanged from
  the preceding 1.8 generation.
- All **54 previously approved JEI 1.8 fallback locales** were therefore
  safely reconstructed into `translations/staged-mc1.8.8/`. No translated
  meaning was guessed or re-used after a source-English change.
- The upstream JEI 1.8.8 JAR already includes `de_de`, `en_us`,
  `fi_fi`, `ko_kr`, `ru_ru`, and `zh_cn`. Their existing translations
  retain priority; some upstream files are partial and their missing keys
  still need separate coverage decisions.
- This is **staged text only**. The 1.8.8 version is not inserted into the
  completed-build matrix, and no JAR is generated.

### Rules

- The search must filter Minecraft's **language selection screen**, not JEI's own recipe/ingredient search.
- Match language code, native name, English/French name; ignore case/accents; allow clearing search.
- Keep the vanilla row objects, original ordering, selection and scrollbar behavior.
- Detect an existing search input, especially Beyond & More, and do not add another.
- Respect API and Java-generation differences, including Java 7 for early Forge builds.
- Compile and test each Minecraft/loader target separately; do not claim universal compatibility on the strength of a shared matcher.
- Only add Minecraft 1.8.8 to the packaging version list after its complementary fallback translations, exact-version loader metadata and in-game tests have been completed.
- Do not generate, upload or publish any JAR without the user's next authorization.

### Files

- `features/language-search/common/` — common source for accent-insensitive matching.
- `features/language-search/legacy_1_8_to_1_12/` — draft older Forge search adapter.
- `features/language-search/forge_1_16_5/` — draft Forge 1.16.5 adapter.
- `features/language-search/mc1_21_1/` — draft NeoForge 1.21.1 port.
- `features/language-search/forge_1_18_2/`, `forge_1_19_2/`, `forge_1_20_1/`, `neoforge_1_21_4/` — four additional API-specific draft adapters.
- `features/language-search/target-matrix.json` — complete 53-target registry.
- `scripts/validate_all_language_search_targets.py` — static coverage/safety checks.

### Still unfinished

Exact-version API review and compilation of 48 draft adapters, runtime focus/render/input tests, coexistence tests, supplementary keys missing from upstream 1.8.8 official locales, two earlier unpublished/uncorroborated original JEI audit targets, and human review of newly added translations. All remain prerequisites to the next release.

## CI validation contract

- All 53 targets must have a source draft or use native Minecraft search.
- Every draft Java file is parsed by Tree-sitter Java. This proves **syntax only**, never API compatibility.
- A Java-only test verifies the common filter preserves language-row identity and ordering when searching and clearing.
- The 20 updated JEI generations and their 1,694 staged translation files are validated for keys and formatting.
- The new 1.8.8 locale stage is deterministic and checked against the official English baseline.
- No source-only CI job runs `jar`, creates a release artifact or alters the public 1.0.0 release.

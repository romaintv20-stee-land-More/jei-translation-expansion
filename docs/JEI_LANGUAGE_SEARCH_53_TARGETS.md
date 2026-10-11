# JEI language selection search — exact target coverage

**Source-only project. No JAR has been built or released.**

The official JEI project supports **Minecraft 1.8.8**, and the previous 52-version JEI Translation Expansion matrix omitted it between Minecraft 1.8 and 1.8.9. See [official JEI 2.12.0.49](https://www.curseforge.com/minecraft/mc-mods/jei/files/2271876). The search matrix now tracks 53 distinct Minecraft targets, while the release/translation inventory correctly still has only 52 completed generations.

## Current source-only progress

| Status | Minecraft versions | Count |
|---|---|---:|
| Draft legacy Forge list-search source (uncompiled) | 1.8, **1.8.8**, 1.8.9, 1.9, 1.9.4, 1.10, 1.10.2, 1.11, 1.11.2, 1.12, 1.12.1, 1.12.2 | 12 |
| Draft Forge search sources (uncompiled) | 1.16.5, **1.18.2**, **1.19.2**, **1.20.1** | 4 |
| Draft NeoForge search sources (uncompiled) | 1.21.1, **1.21.4** | 2 |
| Minecraft's built-in search preserved | 26.1, 26.1.1, 26.1.2, 26.2, 26.3 | 5 |
| Still missing version-specific GUI adapter source | All other listed Minecraft targets | 30 |
| **Total tracked** | | **53** |

The **18 source-prepared targets are NOT compiled or functional in release JARs**.
The 1.8.8 target additionally needs a localization inventory. 26.x keeps
Minecraft's own language search, avoiding duplicate widgets.

New Java-only shared filter: `LanguageListFilter.java`; it keeps the original
vanilla row objects and row order and restores them when a query is cleared.
Its Java source and tests run in GitHub PR validation. The actual Forge/NeoForge
GUI adapters still require their exact client classpaths and in-game tests.

The last official **JEI 1.8.8 version is 2.12.0.49**, published on 22 December
2015 ([CurseForge file 2271876](https://www.curseforge.com/minecraft/mc-mods/jei/files/2271876)),
not the initial JEI 2.0.0 beta. The 1.8.8 language audit is pending.

### Rules

- The search must filter Minecraft's **language selection screen**, not JEI's own recipe/ingredient search.
- Match language code, native name, English/French name; ignore case/accents; allow clearing search.
- Keep the vanilla row objects, original ordering, selection and scrollbar behavior.
- Detect an existing search input, especially Beyond & More, and do not add another.
- Respect API and Java-generation differences, including Java 7 for early Forge builds.
- Compile and test each Minecraft/loader target separately; do not claim universal compatibility on the strength of a shared matcher.
- Only add Minecraft 1.8.8 to the packaging version list after its upstream language audit and version-specific metadata have been completed.
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

30 GUI adapters, full version-specific client compilation, runtime focus/render/input tests, coexistence tests, upstream 1.8.8 language audit, two earlier unpublished/uncorroborated original JEI audit targets, and human review of newly added translations. All remain prerequisites to the next release.

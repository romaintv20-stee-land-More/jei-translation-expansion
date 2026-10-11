# JEI language selection search — exact target coverage

**Source-only project. No JAR has been built or released.**

The official JEI project supports **Minecraft 1.8.8**, and the previous 52-version JEI Translation Expansion matrix omitted it between Minecraft 1.8 and 1.8.9. See [official JEI 2.12.0.49](https://www.curseforge.com/minecraft/mc-mods/jei/files/2271876). The search matrix now tracks 53 distinct Minecraft targets, while the release/translation inventory correctly still has only 52 completed generations.

## Current source-only progress

| Status | Minecraft versions | Count |
|---|---|---:|
| Legacy Forge search adapter prepared, *uncompiled* | 1.8, **1.8.8**, 1.8.9, 1.9, 1.9.4, 1.10, 1.10.2, 1.11, 1.11.2, 1.12, 1.12.1, 1.12.2 | 12 |
| Forge 1.16.5 adapter prepared, *uncompiled* | 1.16.5 | 1 |
| NeoForge 1.21.1 port prepared, *uncompiled* | 1.21.1 | 1 |
| Minecraft's own search retained | 26.1, 26.1.1, 26.1.2, 26.2, 26.3 | 5 |
| Needs generation-specific search adapter | Remaining 1.13–1.21.11 supported targets | 34 |

There is **no evidence yet of functioning mod-provided search on the 14 source-prepared versions**, because the Minecraft/Forge/NeoForge client classes and event subscriptions have not been compiled or tested in game. The existing JAR builder still packages translation-only mods, and deliberately does not include these source files.

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
- `features/language-search/target-matrix.json` — complete 53-target registry.
- `scripts/validate_all_language_search_targets.py` — static coverage/safety checks.

### Still unfinished

34 GUI adapters, full version-specific client compilation, runtime focus/render/input tests, coexistence tests, upstream 1.8.8 language audit, two earlier unpublished/uncorroborated original JEI audit targets, and human review of newly added translations. All remain prerequisites to the next release.

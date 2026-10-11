# Language search — source-only work in progress

Shared Java 7 compatible accent-insensitive language matcher in common/.
Minecraft NeoForge 1.21.1 B&M-style language screen integration in mc1_21_1/.
The target-matrix.json records all 52 Minecraft targets; native search retained on 26.x.
Older versions need distinct GUI integration adapters and real classpath compile/in-game tests.
The existing translation-only JAR builder does NOT package these sources.
No JAR is generated, no UI support is claimed for untested versions.

## Missing Minecraft 1.8.8 tracked (October 2026)

- JEI 2.0.0 originally supported Minecraft 1.8.8; the final published 1.8.8 release is JEI 2.12.0.49, absent from our historical G1-G52 builds.
- `target-matrix.json` now lists **53 Minecraft versions**, while `completed-versions.json` still correctly lists **52 completed translation generations**.
- Legacy Forge 1.8-1.12.2 search adapter source: `legacy_1_8_to_1_12/.../LanguageSearchLegacyForge.java`. This hooks `GuiLanguage` and filters the existing `GuiSlot` code list, preserving vanilla language selection.
- The legacy adapter is **source-only**, has not been compiled against every Forge GUI API, and is not bundled by any builder. It must be registered in a suitable versioned client mod entrypoint only after testing.
- Each Minecraft version must have its own corresponding release artifact once the user explicitly authorizes JAR builds.

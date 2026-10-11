# Forge compilation-only matrix

Use `gradle compileJava` with `-Pmc_version`, `-Pforge_version` and
`-Psource_variant` for staged search adapters. No `jar`, `build`, or
publish tasks are permitted, and the mod JAR output task is disabled.

This is a real official Minecraft/Forge client API compilation smoke test.
It does NOT establish in-game correctness, keyboard focus, selection,
resource overrides or compatibility with a second mod.

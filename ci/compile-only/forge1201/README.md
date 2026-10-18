# Actual Forge 1.20.1 API compilation (NO JAR)

This isolated fixture compiles only the staged Java language-filter and
Minecraft 1.20.1 client adapter against Forge 47.3.0 via ForgeGradle.

Run only `gradle compileJava` on a disposable GitHub Actions runner.
NEVER run `jar`, `build`, `reobfJar`, `publish`, or archive binaries.
Bytecode may exist ephemerally in the CI build directory, but no user-facing
JAR or release is created.

An API failure is expected if a copied Minecraft GUI method is incorrect.
Fix the source against actual Minecraft and rerun. Runtime in-game testing
still requires explicit authorization to test JARs later.

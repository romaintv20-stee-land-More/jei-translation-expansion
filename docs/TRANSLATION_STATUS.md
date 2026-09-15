# Translation Status

This file summarizes completed localization generations. The canonical continuation handoff is `PROJECT_STATUS.md`. Fixed rule: **one Minecraft version per final JAR**.

A generation marked complete here has passed translation/reconstruction QA. That does **not** mean its JAR has passed the separate runtime promotion gate.

## Completed generations

| G | Minecraft | JEI | Keys | Selected | Addon full / override | Supplements | Complete upstream | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| G1 | 1.8 | 2.15.0 | 58 | 60 | 54 | 0 | audited | complete |
| G2 | 1.8.9 | 2.28.18 | 75 | inherited | 54 | 5 | 1 | complete |
| G3 | 1.9 | 3.3.3 | 77 | 70 | 63 | 5 | 1 | complete |
| G4 | 1.9.4 | 3.6.8 | 80 | 70 | 63 | 6 | 1 | complete |
| G5 | 1.10 | 3.7.1 | 78 | 72 | 65 | 6 | 1 | complete |
| G6 | 1.10.2 | 3.14.8 | 87 | 72 | 52 | 16 | 4 | complete |
| G7 | 1.11 | 4.1.1 | 87 | 72 | 52 | 16 | 4 | complete |
| G8 | 1.11.2 | 4.5.1 | 93 | 72 | 52 | 19 | 1 | complete |
| G9 | 1.12 | 4.7.5 | 93 | 80 | 60 | 18 | 2 | complete |
| G10 | 1.12.1 | 4.7.8 | 93 | 80 | 60 | 18 | 2 | complete |
| G11 | 1.12.2 | 4.16.5 | 115 | 80 | 55 | 24 | 1 | complete |
| G12 | 1.13 | 4.14.4 | 105 | 83 | 62 | 12 | 9 | complete |
| G13 | 1.13.2 | 5.0.0 | 106 | 87 | 66 | 19 | 2 | complete |
| G14 | 1.14.2 | 6.0.0 | 109 | 91 | 70 | 19 | 2 | complete |
| G15 | 1.14.3 | 6.0.0 | 109 | 91 | 70 | 18 | 3 | complete |
| G16 | 1.14.4 | 6.0.1 | 109 | 91 | 70 | 16 | 5 | complete |
| G17 | 1.15.1 | 6.0.0 | 109 | 87 | 66 | 16 | 5 | complete |
| G18 | 1.15.2 | 6.0.2 | 110 | 87 | 66 | 18 | 3 | complete |
| G19 | 1.16.1 | 7.0.1 | 110 | 88 | 67 | 18 | 3 | complete |
| G20 | 1.16.2 | 7.3.2 | 114 | 88 | 67 | 19 | 2 | complete |
| G21 | 1.16.3 | 7.6.0 | 114 | 88 | 67 | 18 | 3 | complete |
| G22 | 1.16.4 | 7.6.1 | 114 | 88 | 67 | 16 | 5 | complete |
| G23 | 1.16.5 | 7.7.1 | 119 | 88 | 66 | 15 | 7 | complete |
| G24 | 1.17.1 | 8.3.0 | 141 | 86 | 64 | 21 | 1 | complete |
| G25 | 1.18 | 9.0.0 | 141 | 86 | 64 | 21 | 1 | complete |
| G26 | 1.18.1 | 9.4.1 | 149 | 86 | 64 | 21 | 1 | complete |
| G27 | 1.18.2 | 10.1.0 | 154 | 86 | 64 | 21 | 1 | complete |
| G28 | 1.19 | 11.1.1 | 154 | 86 | 64 | 19 | 3 | complete |
| G29 | 1.19.1 | 11.2.0 | 153 | 86 | 64 | 19 | 3 | complete |
| G30 | 1.19.2 | 11.5.0 | 153 | 86 | 64 | 19 | 3 | complete |
| G31 | 1.19.3 | 12.3.0 | 156 | 88 | 66 | 21 | 1 | complete |
| G32 | 1.19.4 | 13.1.0 | 156 | 88 | 66 | 20 | 2 | complete |
| G33 | 1.20 | 14.0.0 | 156 | 90 | 68 | 20 | 2 | complete |
| G34 | 1.20.1 | 15.2.0 | 156 | 90 | 68 | 20 | 2 | complete |
| G35 | 1.20.2 | 16.0.0 | 156 | 90 | 68 | 20 | 2 | complete |
| G36 | 1.20.4 | 17.3.0 | 157 | 90 | 67 | 22 | 1 | complete |
| G37 | 1.20.6 | 18.0.0 | 157 | 90 | 67 | 22 | 1 | complete |
| G38 | 1.21 | 19.8.2 | 176 | 90 | 67 | 21 | 2 | complete |
| G39 | 1.21.1 | 19.21.1 | 286 | 90 | 64 | 24 | 2 | complete |
| G40 | 1.21.4 | 20.0.0 | 288 | 90 | 64 | 25 | 1 | complete |
| G41 | 1.21.5 | 21.4.0 | 290 | 90 | 65 | 24 | 1 | complete |

## Reuse and ownership rules

- Reuse is permitted only for the **same localization key** when the English value/meaning is identical.
- Cross-key reuse is forbidden, including apparently related renamed or split semantics.
- Existing valid JEI target-locale values remain upstream-owned.
- Incomplete valid upstream locales receive only exact missing **normal** keys; debug-only content is not added through supplements.
- Every complete addon-owned locale must cover the exact target key set and preserve placeholders and fixed technical literals.
- If a target-language translation is uncertain, exact target English is preferred over an invented technical translation.
- Documented full-English fallback locales are explicit policy, not accidental untranslated output.

## Modern generation milestones

### G31–G35

- G31 / Minecraft 1.19.3 expands the selected scope to 88 with `nah` and `ry_ua`.
- G33 / Minecraft 1.20 expands the selected historical scope to 90 with Lao (`lo_la`) and Yakut (`sah_sah`).
- G33→G35 remains semantically stable at 156 JEI keys while Minecraft/JEI packaging targets advance through 1.20, 1.20.1 and 1.20.2.

### G36–G38

- G36 / Minecraft 1.20.4 contains 157 keys and 90 selected languages.
- G37 / Minecraft 1.20.6 moves the packaging toolchain to Java 21.
- G38 / Minecraft 1.21 contains 176 keys while retaining the 90-language selected scope.

### G39 — Minecraft 1.21.1 / JEI 19.21.1

- 286 total keys.
- Ownership: 64 full + 24 supplements + 2 complete upstream.
- Packaging moves to the dedicated NeoForge candidate path.
- Full G1→G39 regression validation was green after the historical G14 technical-token boundary correction.

### G40 — Minecraft 1.21.4 / JEI 20.0.0

- 288 total keys = 282 normal + 6 debug.
- G39→G40: 285 unchanged, 3 added, 1 removed, 0 changed-English values.
- The generic Fuel category is replaced by separate smelting, smoking and blasting fuel categories. No translation is copied across those different keys.
- Ownership: 64 full + 25 supplements + 1 complete upstream (`en_us`).
- `ja_jp` becomes incomplete because it does not yet contain the three new fuel-category semantics.
- Translation/reconstruction QA and deterministic NeoForge packaging are green; the canonical candidate is persisted under `candidate-jars/1.21.4/`.

### G41 — Minecraft 1.21.5 / JEI 21.4.0

- Final maintained endpoint: `0772287a157beb93f438ee10f88afe402e262856` on the dedicated upstream 1.21.5 branch.
- 290 total keys = 284 normal + 6 debug.
- G40→G41: 288 unchanged, 2 added, 0 removed, 0 changed-English values.
- New semantics: `gui.jei.category.grindstone.experience` and `jei.message.missing.recipes.from.server`.
- Ownership: 65 addon/full-override + 24 supplements + 1 complete upstream (`en_us`).
- Pinned upstream `uk_ua.json` is malformed JSON. Ukrainian is therefore emitted as an explicit valid full repair override: known syntax defects are repaired, safe upstream target values are preserved, and only missing same-key semantics are filled from deterministic inheritance/fallback.
- Full reproducible QA run `34930359475` is green.
- NeoForge packaging-validation run `34930428119` is green with candidate SHA-256 `d07378fa02b78dd7e55c63144030d737a44f1f1dc575a488d88e36915a816638`.

## Current generation

G42 targets **Minecraft 1.21.6 / JEI 22.0.0** at `2a57409c2af0ce9716749a0329166a41cbcf453f`. Its next-version boundary is exact because Minecraft 1.21.7 port commit `8a22d93e6e903142c9dbcdf699496f435d1c569d` directly follows that endpoint.

Preliminary frozen English delta: 289 surviving meanings unchanged, 0 added, 1 removed, 0 changed-English values. The removed key is `gui.jei.category.grindstone.experience`. Full scope/ownership/reconstruction validation is in progress on `work/g42-mc1.21.6-audit`.

## Release limitations

- G2 / Minecraft 1.8.9 still requires a real client runtime test before promotion to `release-jars/1.8.9/`.
- Starting with G12 / Minecraft 1.13, missing-key-only JSON supplements require a real runtime resource-stack merge test before version-specific candidate promotion.
- NeoForge static candidates are still subject to their version-specific runtime checks.
- Chronological translation auditing and static candidate generation can continue independently of those runtime release gates.

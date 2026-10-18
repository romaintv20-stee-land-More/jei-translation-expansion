# Audit Translation Expansions — 2026-10-11

## User decision rule
Do not publish a new version without new upstream translation strings or a real translation conflict requiring repair. Add language-selection search only where a new update is justified, and do not duplicate a native/Beyond & More bar.

## Published CurseForge builds
- JEI Translation Expansion 1.0.0 (last released Sept 25, 2026). https://www.curseforge.com/minecraft/mc-mods/jei-translation-expansion/files/all
- Controlling Language Expansion 1.0.1, INCLUDING Marathi all-in-one (Sept 25, 2026; CurseForge file 8974779). https://www.curseforge.com/minecraft/mc-mods/controlling-language-expansion/files/8974779
- Catalogue Translation Expansion 1.0.1 (Sept 25, 2026; 26.3 releases). https://www.curseforge.com/minecraft/mc-mods/catalogue-translation-expansion/files/all

## Confirmed current upstream differences
### Just Enough Items (JEI): update REQUIRED
- Target 26.3: JEI 31.7.0 pinned commit 0aed0ce vs official JEI 31.10.0.63 (CurseForge file 9115761, Oct 10 2026): 43 English keys ADDED, 15 REMOVED, 11 existing values CHANGED; previous raw Common+Debug JSON 587 entries including metadata, current JAR English 615 entries.
- Target 26.2: pinned f93563c vs official 30.39.0.233 (file 9068093, Oct 5): 331 added, 54 removed, 92 changed; baseline raw 337, current official 614.
- Target 26.1.2: pinned d7c73ed vs official 29.43.0.107 (file 9068105, Oct 5): 280 added, 54 removed, 90 changed; baseline raw 337, current official 563.
- Target 1.21.1: G39 pin 28eb51f vs maintained source branch head 4dd9225f1a5c (Oct 2026): Common en_us 310 added, 58 removed, 90 changed; baseline 287, current 539. This result is from SOURCE branch head and must still be matched to newest published JAR before releasing.
- Re-audit ALL other published Minecraft targets before versioning, especially 1.21.11 and 1.19.2, to avoid stale locales.
- Preserve official upstream locale entries and exact key+meaning semantics, placeholders, fixed technical strings. Existing 52 one-Minecraft-version-per-JAR policy.
- Do not blindly reuse old translations for changed English meanings; new texts need native-language review.
- Search bar only for language selection on 1.21.1 if missing. Minecraft 26.x native language search stays untouched.
- Full machine-readable data saved to C:\Users\romai\AppData\Local\Temp\localization_3projects_audit_20261011\audit.json and jei_other_deltas.json.

### Controlling: NO new English keys, but one upstream translation conflict
- Original Controlling 26.3.4 (CurseForge file 9110876, Oct 9): exactly 12 English keys (unchanged generation).
- First official Spanish (Argentina) es_ar.json now shipped; 25 official language files.
- Published Controlling Language Expansion 1.0.1 (file 8974779) contains es_ar.json with 10 entries, ALL 10 overlap the new official 12.
- Some translations differ (Confirm Reset vs ¿Confirmás? etc). The low-priority principle must be verified in game.
- A one-JAR 1.21.9–26.3 package cannot simply remove Spanish Argentina fallback without harming 1.21.9–26.2 users; consider version-scoped pack or 26.3-specific JAR if runtime precedence fails.
- No language search bar justified by new keys here; only localized priority correction if necessary.

### Catalogue: NO update needed
- Latest audited original upstream 26.3 branch ef1104820b04612487094cb7e07d7fa843ede82a (Sept 17) has 34 English keys.
- Matches project's G6 34-key version, published 1.0.1 already supports 26.3 with Fabric/NeoForge.
- Do not rebuild or add language search.

## Current action status
Audit only. No new releases/branches, no language-search modifications, and no source changes to JEI / Controlling / Catalogue repositories made during this audit.

[executed on device: DESKTOP-AOJJNVS (e26481f7-4664-4beb-92b0-24b48bd5a962)]
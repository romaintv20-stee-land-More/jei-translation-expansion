# JEI Version Matrix

Verified historical JEI/Minecraft translation endpoints. Values are taken from actual upstream commits; branch names alone are never treated as authoritative.

| Upstream branch / pin | Minecraft | JEI | Forge | Java | Format | English keys | Status |
|---|---:|---:|---|---:|---|---:|---|
| `1.8` | 1.8 | 2.15.0 | 11.14.4.1577 | 1.7 | `.lang` mixed-case | 58 | scope complete |
| `1.8.9` | 1.8.9 | 2.28.18 | 11.15.1.1855 | 1.7 | `.lang` mixed-case | 75 | scope complete; prototype JAR |
| `1.9@b2ffe6b` | 1.9 | 3.3.3 | 12.16.0.1865-1.9 | 1.7 | `.lang` mixed-case | 77 | scope complete; CI green |
| `1.9@bd9fcad` | 1.9.4 | 3.6.8 | 12.17.0.1962 | 1.7 | `.lang` mixed-case | 80 | scope complete; CI green |
| `1.10@7f4e95d` | 1.10 | 3.7.1 | 12.18.0.1999-1.10.0 | 1.7 | `.lang` mixed-case | 78 | scope complete; CI green |
| `1.10@446af20` | 1.10.2 | 3.14.8 | 12.18.3.2254 | 1.6 | `.lang` mixed-case | 87 | scope complete; CI green |
| `1.11@c9fcc36` | 1.11 | 4.1.1 | 13.19.1.2188 | 1.6 | `.lang` lowercase | 87 | scope complete; CI green |
| `1.11@11023c1` | 1.11.2 | 4.5.1 | 13.20.0.2315 | 1.6 | `.lang` lowercase | 93 | scope complete; CI green |
| `26.2` | 26.2 | exact release audit pending | audit pending | audit pending | JSON | several hundred | partially verified |

## Historical endpoint notes

### Minecraft 1.8 / 1.8.9

Minecraft 1.8 is the oldest verified JEI branch currently found upstream. Minecraft 1.8.9 has a reproducible static prototype JAR but still needs real client runtime validation before promotion to `release-jars/1.8.9/`.

Prototype run: **34632859235**. Prototype SHA-256: `029d6cdcc0f83b098a8b96f423e8fefef6722e8c0db9cd205ef33bf23e22a1e0`.

### Minecraft 1.9 / 1.9.4

The upstream `1.9` branch contains two distinct Minecraft targets. Minecraft 1.9 is pinned to `b2ffe6bd7734d093006de99f9dc99b2b77ce780d`; branch HEAD `bd9fcad11a8b92d181fc8c2ec976e31c7467799a` is Minecraft 1.9.4. They remain separate JAR targets.

### Minecraft 1.10 / 1.10.2

The upstream `1.10` branch transitions to 1.10.2 at `c88aa6c5c078586fa23abaa83309d293cd72ea61`.

- Last 1.10 endpoint: `7f4e95d5b7620a0d304aa73243cd9b3f9737e247`, JEI 3.7.1, 78 keys.
- Final 1.10.2 endpoint: `446af20eaa73d260517f0adc737232437363f78d`, JEI 3.14.8, 87 keys.
- Correct verified 1.10.2 build metadata is Forge `12.18.3.2254`, Java source/target `1.6`.

Minecraft 1.10 expands the raw vanilla language inventory to 94. Selected scope becomes 72 after adding Hawaiian and Mongolian while deferring regional/dialect variants `de_AT` and `swg_de`.

### Minecraft 1.11 / 1.11.2

The upstream `1.11` branch transitions to 1.11.2 at `72c7ea7cf2e7f5243e1d7179aaa10fad038574bf`.

#### Minecraft 1.11 / JEI 4.1.1

Pinned endpoint: `c9fcc36ff0effec2b5239eebd2c9133da04df4bb`.

- Forge `13.19.1.2188`; MCP `snapshot_20161205`; Java source/target `1.6`.
- 87 keys = 84 normal + 3 debug.
- English source is byte-identical to JEI 3.14.8: G6→G7 = 87 unchanged, no semantic changes.
- Locale filenames switch to lowercase (`en_us.lang`).
- Minecraft raw languages = 95; only new code is constructed language `io_ido`, deferred; selected scope remains 72.
- Ownership = 52 full addon locales + 16 exact supplements + 4 complete selected upstream locales (`en_us`, `ru_ru`, `sv_se`, `uk_ua`).
- `de_de` becomes incomplete; its 16 lost JEI translations are recovered exactly from pinned G6 upstream. `sv_se` becomes complete and its older supplement is retired.
- CI **34644034423**.

#### Minecraft 1.11.2 / JEI 4.5.1

Pinned final endpoint: `11023c1f4449b82d0b88366001b058e6949b40ab`.

- Forge `13.20.0.2315`; MCP `snapshot_20170425`; Java source/target `1.6`.
- 93 keys = 90 normal + 3 debug.
- G7→G8 = 85 unchanged, 7 added, 1 removed, 1 changed.
- Minecraft 1.11.2 reuses the exact 1.11 asset index; raw/selected remains 95 / 72.
- Ownership = 52 full addon locales + 19 supplements + only `en_us` complete upstream.
- `ru_ru`, `sv_se` and `uk_ua` become incomplete because of new JEI strings.
- CI **34644712028**.

Exact G8 sources and policies:

- `upstream/diffs/1.11-to-1.11.2.json`
- `upstream/minecraft-1.11.2-language-audit.json`
- `upstream/minecraft-1.11.2-language-scope.json`
- `translations/g8-mc1.11.2/policy.json`

## Next branch family

The next upstream branches are `1.12` and `1.12-FG3`. Their actual Minecraft endpoints, branch relationship and patch-version transitions must be audited before defining G9.

## Audit and distribution rules

For every version, record actual English key counts, Minecraft language inventory, JEI locale ownership, Forge/loader metadata, Java target and resource format. Translation generations may inherit only unchanged key + English meaning pairs. Final distribution is always **one Minecraft version per JAR**.

# JEI Version Matrix

Verified historical JEI/Minecraft translation endpoints. Branch names alone are never treated as authoritative. Final distribution is always **one Minecraft version per JAR**.

| Generation | Upstream pin | Minecraft | JEI | Forge | Mappings | Java | Format | English keys | Scope status |
|---|---|---:|---:|---|---|---:|---|---:|---|
| G1 | `1.8` | 1.8 | 2.15.0 | 11.14.4.1577 | historical | 1.7 | `.lang` mixed-case | 58 | complete |
| G2 | `1.8.9` | 1.8.9 | 2.28.18 | 11.15.1.1855 | historical | 1.7 | `.lang` mixed-case | 75 | complete; runtime JAR pending |
| G3 | `b2ffe6b` | 1.9 | 3.3.3 | 12.16.0.1865-1.9 | snapshot_20160421 | 1.7 | `.lang` mixed-case | 77 | complete |
| G4 | `bd9fcad` | 1.9.4 | 3.6.8 | 12.17.0.1962 | snapshot_20160518 | 1.7 | `.lang` mixed-case | 80 | complete |
| G5 | `7f4e95d` | 1.10 | 3.7.1 | 12.18.0.1999-1.10.0 | snapshot_20160518 | 1.7 | `.lang` mixed-case | 78 | complete |
| G6 | `446af20` | 1.10.2 | 3.14.8 | 12.18.3.2254 | snapshot_20161111 | 1.6 | `.lang` mixed-case | 87 | complete |
| G7 | `c9fcc36` | 1.11 | 4.1.1 | 13.19.1.2188 | snapshot_20161205 | 1.6 | `.lang` lowercase | 87 | complete |
| G8 | `11023c1` | 1.11.2 | 4.5.1 | 13.20.0.2315 | snapshot_20170425 | 1.6 | `.lang` lowercase | 93 | complete |
| G9 | `6bce08e` | 1.12 | 4.7.5 | 14.21.1.2413 | snapshot_20170714 | 1.8 | `.lang` lowercase | 93 | complete |
| G10 | `7f4160e` | 1.12.1 | 4.7.8 | 14.22.0.2452 | snapshot_20170811 | 1.8 | `.lang` lowercase | 93 | complete |
| G11 | `f98331a` | 1.12.2 | 4.16.5 | 14.23.5.2860 | stable / 39 | 1.8 | `.lang` lowercase | 115 | complete |
| G12 | `380bc11` | 1.13 | 4.14.4 | 24.0.181-1.13-pre | snapshot / 20180921-1.13 | 1.8 | `.json` lowercase | 105 | complete |

## Important endpoint transitions

- `1.9` contains separate 1.9 and 1.9.4 targets.
- `1.10` transitions from 1.10 to 1.10.2 at `c88aa6c5c078586fa23abaa83309d293cd72ea61`.
- `1.11` transitions from 1.11 to 1.11.2 at `72c7ea7cf2e7f5243e1d7179aaa10fad038574bf`.
- `1.12` contains distinct 1.12, 1.12.1 and 1.12.2 endpoints. The normal `1.12` lineage, not `1.12-FG3`, is canonical for final 1.12.2.
- `1.13` is pinned at `380bc11efb548abd804c65b763c911ebf9d06e2c`; the next transition commit `a05771ea4ff870381302afe76d5c2298e0a1efe8` jumps directly to Minecraft 1.13.2. No separate 1.13.1 JEI endpoint has been found.

## Scope progression

- G3/G4: 70 selected real-world primary languages.
- G5–G8: 72 selected languages.
- G9–G11: 80 selected languages.
- G12: 83 selected languages after adding `nuk`, `ovd`, `szl`; `ksh_de` migrates to runtime code `ksh`.

## Resource-format transition

G12 is the first JSON-language generation. Exact semantic reuse remains based on **same localization key + identical English source value**. Partial JSON supplements are still release-gated until a real Minecraft 1.13 runtime test confirms the intended resource-stack merge behavior.

## Validation runs

G3 `34638556534`; G4 `34639831977`; G5 `34641765047`; G6 `34642956606`; G7 `34644034423`; G8 `34644712028`; G9 `34668113754`; G10 `34668344181`; G11 `34668803121`; G12 `34671542080`.

## Next target

Audit the final historical **Minecraft 1.13.2 / JEI 5.0.0** endpoint on branch `1.13`. The previously observed branch HEAD is `2d16f4210cbae340ad76b483b4aa8b461561e86f`; verify it again before freezing G13.

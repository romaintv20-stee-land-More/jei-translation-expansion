#!/usr/bin/env python3
"""Synchronize canonical project/status documentation through completed G46."""
from pathlib import Path

PROJECT = Path("PROJECT_STATUS.md")
TRANSLATION = Path("docs/TRANSLATION_STATUS.md")


def sync_project() -> None:
    text = PROJECT.read_text(encoding="utf-8")
    row45 = "| G45 | 1.21.9 | 25.0.1 | `bdfdb4c` | 305 | 90 | 65 | 24 | 1 | complete; NeoForge packaging validated |"
    row46 = "| G46 | 1.21.10 | 26.2.0 | `621ddf0` | 308 | 90 | 64 | 25 | 1 | complete; NeoForge packaging validated |"
    if row46 not in text:
        if row45 not in text:
            raise RuntimeError("G45 PROJECT_STATUS row not found")
        text = text.replace(row45, row45 + "\n" + row46, 1)

    milestone = """### G46 — Minecraft 1.21.10 / JEI 26.2.0

- final 1.21.10 mainline endpoint `621ddf003a8eceffcba0fd808a955e280f87a4c0`
- next Minecraft port `6b615d15ef776abf139339779985a91c59c9c324` targets 1.21.11 and is directly parented by the G46 endpoint; upstream explicitly marks 1.21.11 as Maven-only
- build: NeoForge `21.10.64`, minimum `[21.9.2-beta,)`, Java 21
- 308 keys = 302 normal + 6 debug
- G45→G46 semantic delta = 305 unchanged + 3 added + 0 removed + 0 changed-English values
- added keys: `jei.config.client.tooltips.enableRecipesGuiIngredientsSummary`, `jei.config.client.tooltips.enableRecipesGuiIngredientsSummary.description`, and `jei.tooltip.recipe.tooltips.craft.ingredients`
- selected scope remains 90; ownership = 64 addon-full locales + 25 missing-key/safety-override supplements + 1 complete upstream (`en_us`)
- `uk_ua` is valid upstream again in G46 and returns to supplement ownership instead of a full repair override
- 92 frozen upstream-owned values require literal-safety overrides; all emitted/combined values preserve required placeholders and fixed technical literals
- deterministic NeoForge candidate SHA-256 `f0370c0a9bd5bc26d98ae624237a0b39a14c275eeaf54964ffd2c8caef223f8d`
- final packaging-validation run `34964123873`, green
- runtime promotion remains separately gated

"""
    marker = "## Candidate packaging state\n"
    if "### G46 — Minecraft 1.21.10 / JEI 26.2.0" not in text:
        if marker not in text:
            raise RuntimeError("PROJECT_STATUS candidate marker not found")
        text = text.replace(marker, milestone + marker, 1)

    text = text.replace(
        "- The canonical candidate inventory on `main` contains **44 version-specific 1.0.0 candidates through Minecraft 1.21.8**.\n- G45 has passed complete translation/reconstruction QA and deterministic NeoForge packaging on the work branch; canonical `candidate-jars/1.21.9/` persistence follows merge to `main`.",
        "- The canonical candidate inventory on `main` contains **45 version-specific 1.0.0 candidates through Minecraft 1.21.9**.\n- G46 has passed complete translation/reconstruction QA and deterministic NeoForge packaging on the work branch; canonical `candidate-jars/1.21.10/` persistence follows merge to `main`.",
        1,
    )
    text = text.replace(
        "- Merge the completed G45 / Minecraft 1.21.9 work and let the main packaging workflow persist its NeoForge candidate.\n- The chronological next audit target is **G46 = Minecraft 1.21.10**.",
        "- Merge the completed G46 / Minecraft 1.21.10 work and let the main packaging workflow persist its NeoForge candidate.\n- The chronological next audit target is **G47 = Minecraft 1.21.11**; upstream explicitly states that this JEI target is Maven-only, so translation auditing and public packaging must remain distinct decisions.",
        1,
    )
    text = text.replace(
        "`PROJECT_STATUS.md`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through completed G45.",
        "`PROJECT_STATUS.md`, `upstream/versions.json`, and `upstream/generations.json` are synchronized through completed G46.",
        1,
    )
    text = text.replace("G39–G45 NeoForge candidates remain static candidates", "G39–G46 NeoForge candidates remain static candidates", 1)
    PROJECT.write_text(text, encoding="utf-8")


def sync_translation() -> None:
    text = TRANSLATION.read_text(encoding="utf-8")
    row45 = "| G45 | 1.21.9 | 25.0.1 | 305 | 90 | 65 | 24 | 1 | complete |"
    row46 = "| G46 | 1.21.10 | 26.2.0 | 308 | 90 | 64 | 25 | 1 | complete |"
    if row46 not in text:
        if row45 not in text:
            raise RuntimeError("G45 TRANSLATION_STATUS row not found")
        text = text.replace(row45, row45 + "\n" + row46, 1)

    milestone = """### G46 — Minecraft 1.21.10 / JEI 26.2.0

- Final endpoint: `621ddf003a8eceffcba0fd808a955e280f87a4c0`.
- Direct next port: `6b615d15ef776abf139339779985a91c59c9c324` → Minecraft 1.21.11; upstream marks that target Maven-only.
- Build: NeoForge `21.10.64`, minimum `[21.9.2-beta,)`, Java 21.
- 308 keys = 302 normal + 6 debug.
- G45→G46: 305 unchanged, 3 added, 0 removed, 0 changed-English values.
- Selected scope remains 90; ownership is 64 addon-full + 25 supplements + 1 complete upstream (`en_us`).
- `uk_ua` is valid upstream again and is supplement-owned rather than a full repair override.
- Complete reconstruction and deterministic NeoForge packaging are green.
- Candidate SHA-256: `f0370c0a9bd5bc26d98ae624237a0b39a14c275eeaf54964ffd2c8caef223f8d`.

"""
    marker = "## Current generation\n"
    if "### G46 — Minecraft 1.21.10 / JEI 26.2.0" not in text:
        if marker not in text:
            raise RuntimeError("TRANSLATION_STATUS current marker not found")
        text = text.replace(marker, milestone + marker, 1)
    text = text.replace(
        "G45 translation/reconstruction and static candidate packaging are complete on its work branch. After merge and canonical candidate persistence, the next chronological audit target is **G46 / Minecraft 1.21.10**.",
        "G46 translation/reconstruction and static candidate packaging are complete on its work branch. After merge and canonical candidate persistence, the next chronological audit target is **G47 / Minecraft 1.21.11**, which upstream explicitly marks as Maven-only.",
        1,
    )
    TRANSLATION.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sync_project()
    sync_translation()
    print("PASS: synchronized PROJECT_STATUS.md and docs/TRANSLATION_STATUS.md through G46")

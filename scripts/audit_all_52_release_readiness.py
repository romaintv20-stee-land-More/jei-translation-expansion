#!/usr/bin/env python3
"""Audit EXACTLY the 52 historical JEI JARs, publishing a falsifiable release matrix.

The preflight intentionally BLOCKS release if a JAR has not integrated recent
translations, working language search and glyph/font runtime verification.
No binary is modified or published by this tool.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "features/language-search"
STAGING = ROOT / "translations/staged-published-2026-10-11"
VERSION_LIST = ROOT / "packaging/completed-versions.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "build/all-52-readiness")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero until ALL 52 are truly release-ready")
    args = parser.parse_args()
    versions = read(VERSION_LIST)["versions"]
    matrix = read(FEATURE / "target-matrix.json")["minecraft_targets"]
    staging = read(STAGING / "SUMMARY.json")["versions"]
    legacy = read(STAGING / "legacy-SUMMARY.json")
    latest = {x["minecraft"]: x for x in staging}
    # The legacy audit has a different schema; preserve only verified references.
    legacy_list = legacy.get("versions", []) if isinstance(legacy, dict) else []
    if isinstance(legacy_list, list):
        for x in legacy_list:
            if isinstance(x, dict) and "minecraft" in x and "current_jei" in x:
                latest[x["minecraft"]] = x
    if len(versions) != 52 or len({x["minecraft"] for x in versions}) != 52:
        raise ValueError("Expected 52 unique historical targets")
    targets = {x["minecraft"]: x for x in matrix}
    if len(matrix) != 53 or set(targets) - {v["minecraft"] for v in versions} != {"1.8.8"}:
        raise ValueError("Expected 52 historical targets + staged missing 1.8.8")
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for v in versions:
        mc = v["minecraft"]
        loader = v.get("loader", "forge")
        java = v["java_target"]
        name = f"jei-translation-expansion-1.0.0-mc{mc}-{loader}.jar"
        jarpath = ROOT / "candidate-jars" / mc / name
        if not jarpath.is_file():
            raise FileNotFoundError(jarpath)
        with zipfile.ZipFile(jarpath) as jar:
            names = jar.namelist()
            if jar.testzip() or len(set(names)) != len(names):
                raise ValueError("Corrupt candidate JAR: " + mc)
            jar_languages = [x for x in names if x.startswith("assets/jei/lang/")
                             and x.endswith(".lang" if v["format"] == "lang" else ".json")]
            if len(jar_languages) != v["full"] + v["supplements"]:
                raise ValueError(f"Language count drift {mc}: {len(jar_languages)}")
            search_compiled = any(re.search(
                r"(?:LanguageSearch|LanguageListFilter|LanguageSearchMatcher)[^/]*\.class$", x)
                for x in names)
            font_assets = [x for x in names if x.startswith("assets/") and "/font/" in x]
        native_search = targets[mc]["status"] == "native"
        new_jei = latest.get(mc, {}).get("current_jei")
        updated_translation = bool(new_jei and new_jei == v["jei"])
        # For older versions without a newer upstream audit, the old candidate
        # must still be rebuilt with the final feature set before promotion.
        translations_confirmed = (new_jei is None) or updated_translation
        search_confirmed = native_search or search_compiled
        # Packaging/resource inspection alone cannot certify real glyph coverage,
        # scrolling/focus or coexistence with another mod. Never claim otherwise.
        in_game_verified = False
        font_verified = False
        ready = (translations_confirmed and search_confirmed and in_game_verified
                 and font_verified)
        results.append({
            "Minecraft": mc,
            "Version JAR inspectée": "1.0.0",
            "Loader": "NeoForge" if loader == "neoforge" else "Forge",
            "Java": java,
            "JEI du JAR": v["jei"],
            "JEI plus récent préparé": new_jei or "",
            "Traductions à mettre à jour": "Oui" if new_jei and not updated_translation else "Non / audit à confirmer",
            "Recherche native": "Oui" if native_search else "Non",
            "Recherche embarquée dans ce JAR": "Oui" if search_compiled else "Non",
            "Polices trouvées dans JAR": len(font_assets),
            "Test accents/glyphes en jeu": "À faire",
            "Test clavier/scroll/conflits en jeu": "À faire" if not native_search else "Native / à vérifier",
            "Publication nouvelle version possible": "Oui" if ready else "NON",
            "Nom fichier": name,
        })
    assert len(results) == 52
    columns = list(results[0])
    with (output / "ETAT_52_VERSIONS.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(results)
    (output / "ETAT_52_VERSIONS.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outdated = [x for x in results if x["Traductions à mettre à jour"] == "Oui"]
    nosearch = [x for x in results if x["Recherche native"] == "Non"
                and x["Recherche embarquée dans ce JAR"] == "Non"]
    lines = [
        "# État réel des 52 JAR — blocages avant remplacement des versions publiques",
        "",
        "**Aucun des 52 JAR 1.0.0 ne peut être promu automatiquement comme complet.**",
        "",
        f"- {len(results)} JARs analysés, 52 cibles Minecraft uniques.",
        f"- {len(outdated)} JARs avec une version JEI plus récente préparée dans les sources.",
        f"- {len(nosearch)} JARs anciens sans classe de recherche des langues embarquée.",
        "- 5 versions 26.x conservent la recherche native Minecraft, sans doublon à injecter.",
        "- Font, glyphes, recherche, navigation et coexistence B&M : tests en jeu à effectuer.",
        "",
        "Les audits de traduction peuvent contenir des textes anglais de secours : ne pas les annoncer comme des traductions revues.",
        "Le JAR 1.0.1-rc.1 Minecraft 26.3 et les nouveaux candidats 26.x sont traités séparément des 52 JAR 1.0.0.",
        "Minecraft 1.8.8 est un 53e cible en cours de préparation, pas dans ces 52 JAR.",
        "",
        "| Minecraft | Loader | Java | JEI ancien | JEI préparé | Recherche JAR 1.0.0 | Statut |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in results:
        search = "Native" if row["Recherche native"] == "Oui" else (
            "Embarquée" if row["Recherche embarquée dans ce JAR"] == "Oui" else "Absente"
        )
        lines.append(f"| {row['Minecraft']} | {row['Loader']} | {row['Java']} "
                     f"| {row['JEI du JAR']} | {row['JEI plus récent préparé'] or '—'} "
                     f"| {search} | À valider |")
    (output / "ETAT_52_VERSIONS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"VERSION_READINESS 52; needs upstream updates={len(outdated)}; missing embedded search={len(nosearch)}; all final release gates BLOCKED")
    if args.strict:
        print("BLOCKED: no version has proven complete runtime/font validation")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

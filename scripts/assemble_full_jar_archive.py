#!/usr/bin/env python3
"""Create a dated ZIP of every existing JEI Translation Expansion candidate JAR.

The archive is an inventory for publication preparation, NOT a validated
multi-version mod release. JARs remain specific to their Minecraft version.
Runs in GitHub Actions, not on the user's computer.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import shutil
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/jar-archive-2026-10-18"
MOD_VERSION = "1.0.0"
DATE = "2026-10-18"
REPO = "https://github.com/romaintv20-stee-land-More/jei-translation-expansion"
PREVIEW = ROOT / "downloaded-preview/jei-translation-expansion-1.0.1-rc.1-mc26.3-neoforge.jar"
PREVIEW_HASH = "2cb1ae577608ca610b8740c71dd7ce73e85aa13d79511bbba0be983b24b38ff4"
ZIP_NAME = "JEI_Translation_Expansion_Tous_les_JAR_2026-10-18.zip"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads((ROOT / "packaging/completed-versions.json").read_text(encoding="utf-8"))
    versions = manifest["versions"]
    if len(versions) != 52 or len({x["minecraft"] for x in versions}) != 52:
        raise ValueError("Expected 52 unique Minecraft versions in canonical manifest")
    if not PREVIEW.is_file() or sha256(PREVIEW) != PREVIEW_HASH:
        raise ValueError("Published RC1 JAR missing or SHA256 mismatch")
    if OUT.exists():
        shutil.rmtree(OUT)
    staging = OUT / "archive"
    folder = staging / "JAR"
    folder.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    for cfg in versions:
        mc = cfg["minecraft"]
        loader = cfg.get("loader", "forge")
        suffix = f"jei-translation-expansion-1.0.0-mc{mc}-{loader}.jar"
        source = ROOT / "candidate-jars" / mc / suffix
        if not source.is_file():
            raise FileNotFoundError(f"Missing canonical JAR: {source}")
        target = folder / suffix
        shutil.copyfile(source, target)
        with zipfile.ZipFile(target) as jar:
            if jar.testzip() is not None:
                raise ValueError(f"Invalid JAR archive: {suffix}")
        published = mc != "26.3"
        asset = (f"{REPO}/releases/download/v1.0.0-mc{mc}-{loader}/{suffix}"
                 if published else f"{REPO}/blob/main/candidate-jars/{mc}/{suffix}")
        items.append({
            "Minecraft": mc,
            "Mod": "1.0.0",
            "Loader": "NeoForge" if loader == "neoforge" else "Forge",
            "Java": cfg["java_target"],
            "JEI": cfg["jei"],
            "NeoForge ciblé": cfg.get("neoforge", ""),
            "NeoForge minimum": cfg.get("neoforge_version_range", ""),
            "Statut": "JAR 1.0.0 publié, tests en jeu non documentés" if published
                      else "Candidat statique, pas de release 1.0.0",
            "Polices": "À vérifier en jeu",
            "Recherche de langues": "Recherche native" if mc.startswith("26.")
                                    else "Non intégrée dans le JAR 1.0.0",
            "Fichier": suffix,
            "SHA256": sha256(target),
            "Lien Github": asset
        })
    preview_target = folder / PREVIEW.name
    shutil.copyfile(PREVIEW, preview_target)
    with zipfile.ZipFile(preview_target) as jar:
        if jar.testzip() is not None:
            raise ValueError("Invalid 26.3 preview JAR")
    items.append({
        "Minecraft": "26.3",
        "Mod": "1.0.1-rc.1",
        "Loader": "NeoForge",
        "Java": 25,
        "JEI": "31.10.0.63",
        "NeoForge ciblé": "26.3.0.7-beta",
        "NeoForge minimum": "[26.3.0.1-beta,)",
        "Statut": "Préversion GitHub publiée, NON testée en jeu",
        "Polices": "À vérifier en jeu",
        "Recherche de langues": "Recherche native Minecraft 26.3",
        "Fichier": PREVIEW.name,
        "SHA256": PREVIEW_HASH,
        "Lien Github": f"{REPO}/releases/download/v1.0.1-rc.1-mc26.3-neoforge/{PREVIEW.name}"
    })
    if len(items) != 53 or len(set(x["Fichier"] for x in items)) != 53:
        raise AssertionError("Expected 53 unique original JAR files")
    def sort_key(x: dict):
        # Naturally order by Minecraft version, then release version.
        return (tuple(int(part) for part in x["Minecraft"].split(".")),
                x["Mod"] == "1.0.1-rc.1")
    items.sort(key=sort_key, reverse=True)

    fields = list(items[0])
    with (staging / "Inventaire_JAR.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(items)
    with (staging / "Inventaire_JAR.json").open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    with (staging / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for row in sorted(items, key=lambda d: d["Fichier"]):
            f.write(f'{row["SHA256"]}  JAR/{row["Fichier"]}\n')

    tip = (
        "Cet ensemble contient 52 candidats JAR 1.0.0 et une RC1 de Minecraft 26.3. "
        "51 candidats 1.0.0 ont une publication individuelle GitHub ; le 1.0.0 MC 26.3 est uniquement candidat. "
        "Aucune publication n'atteste à elle seule de tests en jeu. "
        "Les nouvelles traductions et la recherche des langues préparées sur une branche ne sont pas forcément présentes "
        "dans les JAR 1.0.0. Aucune version Fabric n'existe dans cet inventaire."
    )
    (staging / "LIRE_AVANT_PUBLICATION.txt").write_text(
        "JEI Translation Expansion — archive JAR de travail\n"
        f"Créée le {DATE} depuis le manifeste du dépôt officiel.\n\n"
        f"{tip}\n\n"
        "Toujours sélectionner UN SEUL JAR correspondant exactement à Minecraft, au loader et à Java.\n"
        "Ne pas installer l'archive ZIP elle-même comme un mod.\n"
        "Les cibles NeoForge sont les versions utilisées pour assembler les métadonnées, "
        "et non des garanties de compatibilité avec toutes les variantes du loader.\n"
        "Les versions Forge précises ne figurent pas dans la configuration du projet.\n"
        "La RC1 26.3 cible JEI 31.10.0.63 et la plage [31.10.0.63,31.11.0).\n"
        "Vérifier en jeu JEI, les traductions, l'affichage de la police, les accents et les glyphes avant publication finale.\n",
        encoding="utf-8"
    )

    def h(v: object) -> str:
        return html.escape(str(v or ""))
    data_rows = []
    for row in items:
        mark = "preview" if "rc." in row["Mod"] else ("candidate" if "Candidat" in row["Statut"] else "released")
        cells = [f'<td>{h(row[key])}</td>' for key in ["Minecraft", "Mod", "Loader", "Java", "JEI",
                                                        "NeoForge ciblé", "NeoForge minimum", "Statut"]]
        cells.append(f'<td><a href="JAR/{h(row["Fichier"])}" download>Télécharger</a></td>')
        data_rows.append(f'<tr class="{mark}" data-loader="{h(row["Loader"])}" data-java="{h(row["Java"])}">'
                         + "".join(cells) + "</tr>")
    template = """<!doctype html><html lang="fr"><head><meta charset="UTF-8"/>
<title>JEI Translation Expansion – Catalogue des JAR</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
:root{color-scheme:light}body{margin:0;background:#f3f6fa;color:#18324c;font:15px system-ui,Arial,sans-serif}
header{background:linear-gradient(135deg,#10273e,#134d57);color:white;padding:32px max(24px,calc((100vw - 1240px)/2))}
h1{margin:0;font-size:28px}h2{font-size:17px}.sub{color:#c4e2e4}.wrap{max-width:1240px;margin:auto;padding:24px}
.cards{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:12px;margin-top:-26px}
.card{background:white;border-radius:12px;padding:20px;box-shadow:0 5px 25px #19324d14}.num{font-size:32px;font-weight:750;color:#077f7c}.label{color:#607184}
.note{background:#fff8e7;border-left:5px solid #d89f30;padding:16px;border-radius:8px;margin:22px 0;line-height:1.55}
.tools{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 20px}
input,select{border:1px solid #c5d2df;border-radius:8px;padding:12px;background:white;font:inherit;flex:1;min-width:160px}
.table{overflow-x:auto;background:white;border-radius:12px;border:1px solid #dde6ec}
table{border-collapse:collapse;width:100%;white-space:nowrap}th{text-align:left;background:#e8f1f4;color:#143d50;position:sticky;top:0}
td,th{padding:13px;border-bottom:1px solid #e7edf3}tr:hover{background:#f4f8fc}
tr.preview{background:#e9faf7}tr.candidate{background:#fff8e7}
a{color:#077f7c;font-weight:700;text-decoration:none}
.footer{font-size:13px;color:#5d6a78;margin-top:28px}@media(max-width:720px){.cards{grid-template-columns:1fr 1fr}h1{font-size:23px}}
</style></head><body>
<header><h1>JEI Translation Expansion</h1><p class="sub">Inventaire des versions Minecraft · GitHub · 18 octobre 2026</p></header>
<main class="wrap"><div class="cards"><div class="card"><div class="num">53</div><div class="label">JAR inclus</div></div>
<div class="card"><div class="num">52</div><div class="label">Versions Minecraft</div></div>
<div class="card"><div class="num">51</div><div class="label">Publications 1.0.0</div></div>
<div class="card"><div class="num">1</div><div class="label">Préversion RC1</div></div></div>
<div class="note"><b>Important :</b> __TIP__</div><h2>Trouver le bon fichier</h2>
<div class="tools"><input id="search" type="search" placeholder="Recherche : 1.21.1, NeoForge, 31.10..."/>
<select id="loader"><option value="">Tous les loaders</option><option>Forge</option><option>NeoForge</option></select>
<select id="java"><option value="">Toutes les versions Java</option><option>7</option><option>8</option><option>16</option><option>17</option><option>21</option><option>25</option></select>
</div><div class="table"><table><thead><tr><th>Minecraft</th><th>Version du mod</th><th>Loader</th><th>Java</th><th>JEI</th><th>NeoForge ciblé</th><th>NeoForge min.</th><th>Statut</th><th>Fichier du ZIP</th></tr></thead>
<tbody id="body">__ROWS__</tbody></table></div><p class="footer">Les liens « Télécharger » fonctionnent après extraction du ZIP (le HTML référence le sous-dossier JAR). Le tableau complet CSV/JSON et les sommes SHA-256 sont inclus. Source : __REPO__</p></main>
<script>
function filt(){let q=document.getElementById('search').value.toLocaleLowerCase('fr');
let l=document.getElementById('loader').value,j=document.getElementById('java').value;
document.querySelectorAll('#body tr').forEach(tr=>tr.hidden=!(tr.textContent.toLocaleLowerCase('fr').includes(q)&&(!l||tr.dataset.loader===l)&&(!j||tr.dataset.java===j)));}
['search','loader','java'].forEach(id=>document.getElementById(id).addEventListener('input',filt));
</script></body></html>"""
    webpage = (template.replace("__TIP__", h(tip))
               .replace("__ROWS__", "\n".join(data_rows))
               .replace("__REPO__", f'<a href="{REPO}" target="_blank">{REPO}</a>'))
    (staging / "Catalogue_Visuel.html").write_text(webpage, encoding="utf-8")

    zip_target = OUT / ZIP_NAME
    with zipfile.ZipFile(zip_target, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as archive:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                # JAR already compressed: avoid expensive re-compression.
                archive.write(path, path.relative_to(staging),
                              compress_type=zipfile.ZIP_STORED if path.suffix == ".jar" else zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(zip_target) as test:
        if test.testzip() is not None:
            raise ValueError("Generated master ZIP failed CRC test")
        if len([x for x in test.namelist() if x.endswith(".jar")]) != 53:
            raise ValueError("Master ZIP does not contain 53 JAR entries")
    print("ARCHIVE_OK", zip_target)
    print("JAR_COUNT", len(items))
    print("TOTAL_BYTES", zip_target.stat().st_size)
    print("LOADERS", dict(Counter(x["Loader"] for x in items)))
    print("SHA256", sha256(zip_target))


if __name__ == "__main__":
    main()

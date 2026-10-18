#!/usr/bin/env python3
"""Package ONLY real compiled preview JARs; refuse historical translation-only binaries."""
from pathlib import Path
from zipfile import ZipFile,ZIP_STORED,ZIP_DEFLATED
import csv,hashlib,html,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/"downloaded-review-runs"
OUT=ROOT/"build/compiled-review-collection"
DATE="2026-10-18"
NAME="JEI_Translation_Expansion_JAR_recompiles_46_non_testes.zip"
MC_FORGE=["1.8.9","1.10.2","1.11","1.11.2","1.12","1.12.1","1.12.2","1.14.2","1.14.3","1.14.4","1.15.1","1.15.2","1.16.1","1.16.2","1.16.3","1.16.4","1.16.5",
          "1.17.1","1.18","1.18.1","1.18.2","1.19","1.19.1","1.19.2","1.19.3",
          "1.19.4","1.20","1.20.1","1.20.2","1.20.4","1.20.6","1.21"]
MC_NEO=["1.21.1","1.21.4","1.21.5","1.21.6","1.21.7","1.21.8","1.21.9",
        "1.21.10","1.21.11","26.1","26.1.1","26.1.2","26.2","26.3"]
EXPECTED={(x,"Forge") for x in MC_FORGE}|{(x,"NeoForge") for x in MC_NEO}
assert len(EXPECTED)==46
manifest=json.loads((ROOT/"packaging/completed-versions.json").read_text(encoding="utf-8"))
baseline={q["minecraft"]:q for q in manifest["versions"]}
staged=json.loads((ROOT/"translations/staged-published-2026-10-11/SUMMARY.json").read_text(encoding="utf-8"))
newer={q["minecraft"]:q["current_jei"] for q in staged["versions"]}
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    actual={}
    for p in sorted(SOURCES.rglob("*.jar")):
        if p.name.endswith("-sources.jar"): continue
        mat=re.fullmatch(r"jei-translation-expansion-1\.0\.1-rc\.1-mc([0-9.]+)-(forge|neoforge)(?:-1\.0\.1-rc\.1)?\.jar",p.name)
        if not mat: raise RuntimeError(f"Unexpected JAR filename in review archive: {p.name}")
        mc,loader=mat.group(1),mat.group(2).capitalize()
        if loader=="Neoforge":loader="NeoForge"
        if (mc,loader) not in EXPECTED:raise RuntimeError("Unexpected preview: "+p.name)
        if (mc,loader) in actual:raise RuntimeError("Duplicate review artifact for "+mc)
        data=p.read_bytes()
        with ZipFile(p) as z:
            if z.testzip():raise RuntimeError("Damaged JAR: "+p.name)
            names=z.namelist()
            if not any(s.startswith("assets/jei/lang/") for s in names):
                raise RuntimeError("Missing language files: "+p.name)
            if not mc.startswith("26.") and not any("LanguageSearch" in s and s.endswith(".class") for s in names):
                raise RuntimeError("Missing compiled language-search code: "+p.name)
            if loader=="NeoForge" and "META-INF/neoforge.mods.toml" not in names:
                raise RuntimeError("Missing NeoForge metadata: "+p.name)
            if loader=="Forge" and "META-INF/mods.toml" not in names:
                raise RuntimeError("Missing Forge metadata: "+p.name)
            lang_count=sum(s.startswith("assets/jei/lang/") and (s.endswith(".json") or s.endswith(".lang")) for s in names)
            code_count=sum("LanguageSearch" in s and s.endswith(".class") for s in names)
        actual[(mc,loader)]=(p,data,lang_count,code_count)
    missing=EXPECTED-set(actual)
    if missing:raise RuntimeError("Missing compiled builds: "+str(sorted(missing)))
    out_dir=OUT/"archive";out_dir.mkdir(parents=True,exist_ok=True)
    jar_dir=out_dir/"JAR";jar_dir.mkdir(exist_ok=True)
    rows=[]
    for mc,loader in sorted(EXPECTED,key=lambda t:(tuple(map(int,t[0].split("."))),t[1])):
        p,data,count,code=actual[(mc,loader)]
        canonical = "jei-translation-expansion-1.0.1-rc.1-mc"+mc+"-"+loader.lower()+".jar"
        target=jar_dir/canonical
        target.write_bytes(data)
        cfg=baseline[mc]
        row={
            "Minecraft":mc,
            "Version du mod":"1.0.1-rc.1",
            "Loader":loader,
            "Version Java":cfg["java_target"],
            "Version JEI ciblée":newer.get(mc,cfg["jei"]) if mc!="26.3" else "31.10.0.63",
            "Fichiers de traduction":count,
            "Classes de recherche":code,
            "Recherche native":"Oui" if mc.startswith("26.") else "Non",
            "Test en jeu":"NON",
            "Test des polices":"NON",
            "Statut":"CANDIDAT DE REVUE - NE PAS PRÉSENTER COMME VERSION FINALE",
            "Fichier":canonical,
            "SHA256":sha(data),
        }
        rows.append(row)
    with (out_dir/"INVENTAIRE.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=";");w.writeheader();w.writerows(rows)
    (out_dir/"INVENTAIRE.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
    (out_dir/"SHA256SUMS.txt").write_text("".join(
        row["SHA256"]+"  JAR/"+row["Fichier"]+"\n" for row in rows),encoding="utf-8")
    (out_dir/"LIRE_AVANT_PUBLICATION.txt").write_text(
        "JEI Translation Expansion - 46 JAR recompilés (version 1.0.1-rc.1)\n\n"
        "Ces 46 JAR sont compilés et inspectés, PAS encore testés en jeu. "
        "La barre de recherche a son bytecode intégré sur les 32 versions non-26.x ; "
        "la recherche native est utilisée sur Minecraft 26.x. "
        "Les traductions sont héritées des packs existants ou des sources JEI récentes "
        "et certaines valeurs sont toujours en anglais de secours. "
        "Les glyphes et polices, la barre de recherche, les conflits et la compatibilité "
        "doivent être réellement testés avant les publications stables.\n"
        "L'archive contient uniquement les versions compilées, pas les 15 versions "
        "Minecraft encore en chantier. Une archive précédente comportant 52 JAR 1.0.0 "
        "ne représente PAS les nouvelles fonctionnalités.\n",
        encoding="utf-8")
    heads=list(rows[0]); td="\n".join(
        "<tr>"+ "".join("<td>"+html.escape(str(row[k]))+"</td>" for k in heads[:-2])
        +f'<td><a href="JAR/{html.escape(row["Fichier"])}">{html.escape(row["Fichier"])}</a></td><td>{row["SHA256"]}</td></tr>'
        for row in rows)
    (out_dir/"CATALOGUE.html").write_text(
        "<!DOCTYPE html><html lang='fr'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>JEI - 46 JAR recompilés</title><style>body{font:14px system-ui;margin:30px;color:#223;background:#fafafa}"
        "table{border-collapse:collapse}td,th{padding:9px;border:1px solid #ddd}th{background:#e8f1f4}"
        "a{color:#075c74}input{padding:10px;width:300px}</style><h1>JEI Translation Expansion — 46 nouveaux candidats</h1>"
        "<p>Compilés mais NON validés en jeu / polices. 15 autres versions toujours en chantier.</p>"
        "<input type='search' placeholder='Minecraft, Forge, JEI, Java...' oninput='q=this.value.toLowerCase();"
        "document.querySelectorAll(\"tbody tr\").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))'>"
        "<table><thead><tr>"+ "".join("<th>"+html.escape(x)+"</th>" for x in heads)+"</tr></thead><tbody>"+td+"</tbody></table></html>",
        encoding="utf-8")
    zip_path=OUT/NAME
    with ZipFile(zip_path,"w",compression=ZIP_DEFLATED) as z:
        for p in sorted(out_dir.rglob("*")):
            if p.is_file():z.write(p,p.relative_to(out_dir),compress_type=ZIP_STORED if p.suffix==".jar" else ZIP_DEFLATED)
    with ZipFile(zip_path) as z:
        if z.testzip() or len([x for x in z.namelist() if x.endswith(".jar")])!=46:
            raise RuntimeError("Bad archive or count")
    print("VERIFIED_RECOMPILED_JARS=46",zip_path,"SIZE=",zip_path.stat().st_size,"SHA256=",sha(zip_path.read_bytes()))
if __name__=="__main__":main()

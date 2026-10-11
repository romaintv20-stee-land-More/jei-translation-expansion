#!/usr/bin/env python3
"""Static checks only. Compiles a standalone language matcher, no mod JAR."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
FEATURE=ROOT/"features/language-search"
G53=ROOT/"translations/g53-mc26.3-31.10.0.63"
def test_language_search():
 cfg=json.loads((ROOT/"packaging/completed-versions.json").read_text(encoding="utf-8"))["versions"]
 m=json.loads((FEATURE/"target-matrix.json").read_text(encoding="utf-8"))
 assert len(cfg)==52
 assert len(m["minecraft_targets"])==53
 assert m["minecraft_targets"][1]["minecraft"]=="1.8.8"
 assert [t["minecraft"] for t in m["minecraft_targets"] if t["minecraft"]!="1.8.8"]==[t["minecraft"] for t in cfg]
 assert sum(t["status"]=="native" for t in m["minecraft_targets"])==5
 p=next((FEATURE/"common").rglob("LanguageSearchMatcher.java"))
 filter_java=next((FEATURE/"common").rglob("LanguageListFilter.java"))
 assert filter_java.exists()
 assert p.exists()
 a=next((FEATURE/"mc1_21_1").rglob("LanguageSearch1211.java"))
 b=next((FEATURE/"mc1_21_1").rglob("LanguageSearchEvents1211.java"))
 assert 'ModList.get().isLoaded("steel_and_more")' in a.read_text(encoding="utf-8")
 assert "instanceof EditBox" in a.read_text(encoding="utf-8")
 legacy=next((FEATURE/"legacy_1_8_to_1_12").rglob("LanguageSearchLegacyForge.java"))
 body=legacy.read_text(encoding="utf-8")
 for required in (
     "GuiScreenEvent.InitGuiEvent.Post",
     "GuiScreenEvent.KeyboardInputEvent.Pre",
     "GuiScreenEvent.MouseInputEvent.Pre",
     "GuiScreenEvent.DrawScreenEvent.Post",
     "GuiScreenEvent.ActionPerformedEvent.Pre",
     "LanguageSearchMatcher.matches(",
     "CONTROLS.put(screen",
     "slot.setDimensions",
 ):
     assert required in body, required
 assert all(t["status"]=="native" for t in m["minecraft_targets"] if t["minecraft"].startswith("26."))
 assert any(t["minecraft"]=="1.8.8" and "pending" in t["status"] for t in m["minecraft_targets"])
 source_files = {
  "1.18.2": ("forge_1_18_2", "ScreenEvent.InitScreenEvent.Post"),
  "1.20.1": ("forge_1_20_1", "ScreenEvent.Init.Post"),
  "1.19.2": ("forge_1_19_2", "ScreenEvent.Init.Post"),
  "1.21.4": ("neoforge_1_21_4", "ScreenEvent.Init.Post"),
 }
 for version,(folder,event_name) in source_files.items():
  matches=list((FEATURE/folder).rglob("LanguageSearch*.java"))
  assert len(matches)==1,(version,matches)
  body=matches[0].read_text(encoding="utf-8")
  assert event_name in body,(version,event_name)
  assert "LanguageListFilter" in body
  assert "instanceof EditBox" in body
  assert next(x for x in m["minecraft_targets"] if x["minecraft"]==version)["status"]=="source_prepared_uncompiled"
 assert len([x for x in m["minecraft_targets"] if "source_prepared" in x["status"]])==18
 assert len([x for x in m["minecraft_targets"] if x["status"]=="pending_versioned_gui_adapter"])==30


 assert 'modid="jei_translation_expansion"' in b.read_text(encoding="utf-8")
 java=r"""
import io.github.romaintv20.jeitranslationexpansion.search.LanguageSearchMatcher;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import io.github.romaintv20.jeitranslationexpansion.search.LanguageListFilter;

public final class LanguageSearchMatcherCheck {
    private static void test(String query, String code, String nativeName, boolean expected) {
        boolean got=LanguageSearchMatcher.matches(query,code,nativeName,"");
        if (got!=expected) throw new AssertionError(query+" / "+code+": "+got);
    }
    public static void main(String[] args) {
        test("francais","fr_fr","Français",true);
        test("FR_FR","fr_fr","Français",true);
        test("de-de","de_de","Deutsch",true);
        test("german","de_de","Deutsch",true);
        test("japanese","ja_jp","日本語",true);
        test("ja_jp","ja_jp","日本語",true);
        test("esperanto","eo_uy","Esperanto",true);
        test("welsh","fr_fr","Français",false);
        test("uk","de_de","Deutsch",false);
        test("","de_de","Deutsch",true);
        String fr=new String("fr_fr");
        String en=new String("en_us");
        String de=new String("de_de");
        List<String> displayed=new ArrayList<String>(Arrays.asList(fr,en,de));
        LanguageListFilter<String> list=new LanguageListFilter<String>(
            displayed, new LanguageListFilter.RowReader<String>() {
                public String code(String row) { return row; }
                public String nativeName(String row) {
                    return row.equals("fr_fr") ? "Français" :
                        row.equals("de_de") ? "Deutsch" : "English";
                }
            }
        );
        if (!list.canModify(displayed)) throw new AssertionError("mutability");
        list.show(displayed,"francais");
        if(displayed.size()!=1 || displayed.get(0)!=fr)
            throw new AssertionError("row identity not preserved");
        list.show(displayed,"zzzzz");
        if(!displayed.isEmpty()) throw new AssertionError("unknown query");
        list.show(displayed,"");
        if(displayed.size()!=3 || displayed.get(0)!=fr ||
                displayed.get(1)!=en || displayed.get(2)!=de)
            throw new AssertionError("order/identity lost");
        if(!list.belongs(en))throw new AssertionError("membership");
        System.out.println("SEARCH MATCHER + ROW FILTER PASS");
    }
}
"""
 with tempfile.TemporaryDirectory() as folder:
  d=Path(folder)
  q=d/"LanguageSearchMatcherCheck.java";q.write_text(java,encoding="utf-8")
  # Compilation of a pure Java source only: no jar, no mod pack.
  javac=shutil.which("javac")
  if not javac:
   raise RuntimeError("JDK with javac required for matcher tests")
  subprocess.run([javac,"--release","8","-d",str(d),str(p),str(filter_java),str(q)],check=True)
  subprocess.run([shutil.which("java"),"-cp",str(d),"LanguageSearchMatcherCheck"],check=True)
 print("SEARCH TARGET MATRIX PASS",len(m["minecraft_targets"]),"targets (52 existing + 1.8.8 pending)")
def test_staged_translations():
 audit=json.loads((G53/"audit.json").read_text(encoding="utf-8"))
 english=json.loads((G53/"upstream/en_us.json").read_text(encoding="utf-8"))
 assert len(english)==614
 assert (audit["keys_added"],audit["keys_removed"],audit["english_values_changed"])==(43,13,11)
 assert len(audit["locales"])==89
 for loc,relative in audit["files"].items():
  data=json.loads((ROOT/relative).read_text(encoding="utf-8"))
  assert data and not (set(data)-set(english)),loc
  assert len(data)+audit["locales"][loc].get("upstream_owned",0)==len(english),(loc,len(data))
  assert all(isinstance(v,str) and v.strip() for v in data.values()),loc
 print("G53 STAGED SOURCES PASS",len(audit["locales"]),"locales; no output JAR")
if __name__=="__main__":
 test_language_search()
 test_staged_translations()

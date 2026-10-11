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
 assert len(m["minecraft_targets"])==len(cfg)==52
 assert [t["minecraft"] for t in m["minecraft_targets"]]==[t["minecraft"] for t in cfg]
 assert sum(t["status"]=="native" for t in m["minecraft_targets"])==5
 p=next((FEATURE/"common").rglob("LanguageSearchMatcher.java"))
 assert p.exists()
 a=next((FEATURE/"mc1_21_1").rglob("LanguageSearch1211.java"))
 b=next((FEATURE/"mc1_21_1").rglob("LanguageSearchEvents1211.java"))
 assert 'ModList.get().isLoaded("steel_and_more")' in a.read_text(encoding="utf-8")
 assert "instanceof EditBox" in a.read_text(encoding="utf-8")
 assert 'modid="jei_translation_expansion"' in b.read_text(encoding="utf-8")
 java=r"""
import io.github.romaintv20.jeitranslationexpansion.search.LanguageSearchMatcher;
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
        System.out.println("SEARCH MATCHER PASS");
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
  subprocess.run([javac,"--release","8","-d",str(d),str(p),str(q)],check=True)
  subprocess.run([shutil.which("java"),"-cp",str(d),"LanguageSearchMatcherCheck"],check=True)
 print("SEARCH TARGET MATRIX PASS",len(cfg),"targets")
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

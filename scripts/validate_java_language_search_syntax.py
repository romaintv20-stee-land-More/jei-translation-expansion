#!/usr/bin/env python3
"""Parse ALL Java language-search source files for syntax errors, no builds or JARs.

Using tree-sitter-java recognizes modern Minecraft GUI Java syntax while also
supporting pre-Java-8 source. This is NOT bytecode or loader API validation.
"""
from pathlib import Path
import sys
from tree_sitter import Language, Parser
import tree_sitter_java

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"features/language-search"
parser=Parser(Language(tree_sitter_java.language()))
sources=sorted(SOURCE.rglob("*.java"))
assert len(sources)>=40,len(sources)
errors=[]
for path in sources:
    data=path.read_bytes()
    tree=parser.parse(data)
    if tree.root_node.has_error:
        def find_error(node):
            if node.type=="ERROR" or node.is_missing:
                return node
            for child in node.children:
                bad=find_error(child)
                if bad is not None:return bad
            return node if node.has_error else None
        bad=find_error(tree.root_node)
        errors.append(f"{path.relative_to(ROOT)}:{bad.start_point.row+1 if bad else '?'}: Java parse error: {bad.type if bad else 'unknown'}")
    else:
        print("JAVA PARSE PASS",path.relative_to(ROOT))
if errors:
    print("\n".join(errors),file=sys.stderr)
    sys.exit(1)
print(f"SUCCESS: {len(sources)} Java source files parsed; no JAR created")
print("NOTE: This does not verify Minecraft Forge/NeoForge symbols or in-game behavior.")

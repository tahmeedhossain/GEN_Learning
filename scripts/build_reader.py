"""Inject the compiled reader data into the page template.

Usage: python3 -I scripts/build_reader.py <reader.json> <page/reader.html> <out.html>
"""
import sys, json
from pathlib import Path

net = json.loads(Path(sys.argv[1]).read_text())
T = {"observable": "O", "model": "M", "state": "S"}
nodes = []
for n in net["nodes"]:
    x = {"id": n["id"], "t": T[n["type"]], "label": n["label"], "symbol": n["symbol"], "era": n["era"],
         "description": n["description"], "vol": n["vol"], "section": n["section"], "chapter": n["chapter"],
         "paragraph": n["paragraph"]}
    if n["primitive"]: x["primitive"] = True
    if n["postulate"]: x["postulate"] = True
    if n["math_structure"]: x["math_structure"] = n["math_structure"]
    if n["properties"]: x["properties"] = n["properties"]
    if n["book_terms"]: x["book_terms"] = n["book_terms"]
    nodes.append(x)
routes = []
for r in net["routes"]:
    x = {"id": r["id"], "target": r["target"],
         "inputs": [[i["node"], i["role"]] if i["role"] else [i["node"]] for i in r["inputs"]],
         "formula": r["formula"], "title": r["title"], "description": r["description"], "tags": r["tags"],
         "vol": r["vol"], "section": r["section"], "chapter": r["chapter"], "kind": r["kind"],
         "paragraph": r["paragraph"]}
    routes.append(x)
paras = []
for p in net["paragraphs"]:
    x = {"k": p["k"], "vol": p["vol"], "ch": p["ch"], "section": p["section"], "text": p["text"], "links": p["links"]}
    if p["eqs"]: x["eqs"] = p["eqs"]
    if p["new_nodes"]: x["new_nodes"] = p["new_nodes"]
    if p["new_routes"]: x["new_routes"] = p["new_routes"]
    paras.append(x)
cover = []
for c in net["coverage"]:
    if c["status"] == "node":
        cover.append([c["vol"], c["section"], c["term"], "n", c["node"]])
    elif c["status"] == "node by reference":
        cover.append([c["vol"], c["section"], c["term"], "r", c["node"]])
    else:
        cover.append([c["vol"], c["section"], c["term"], "x" if c["status"] == "not modelled" else "m", c.get("reason", "")])
data = {"stats": net["stats"], "source": net["source"], "chapters": net["chapters"],
        "nodes": nodes, "routes": routes, "paragraphs": paras, "coverage": cover}
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = Path(sys.argv[2]).read_text()
assert "__DATA__" in html
html = html.replace("__DATA__", blob)
Path(sys.argv[3]).write_text(html)
print(f"{len(html.encode())/1024:.0f} KiB written ({len(blob.encode())/1024:.0f} KiB data)")

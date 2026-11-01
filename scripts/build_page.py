"""Inject the compiled network into the page template.
Usage: python3 -I scripts/build_page.py <network.json> <template.html> <out.html>"""
import sys, json
from pathlib import Path
net = json.loads(Path(sys.argv[1]).read_text())
keep_node = ["id", "type", "label", "symbol", "era", "primitive", "postulate", "description", "math_structure",
             "properties", "book_terms", "vol", "section", "chapter", "event"]
keep_route = ["id", "target", "inputs", "logic", "formula", "title", "description", "tags", "vol", "section", "chapter", "kind", "event"]
data = {
    "stats": net["stats"], "source": net["source"],
    "chapters": net["chapters"],
    "nodes": [{k: n[k] for k in keep_node} for n in net["nodes"]],
    "routes": [{k: r[k] for k in keep_route} for r in net["routes"]],
    "events": [{k: e[k] for k in ("kind", "node", "routes", "index", "chapter_key", "section", "vol")} for e in net["events"]],
    "coverage": net["coverage"],
}
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = Path(sys.argv[2]).read_text().replace("__DATA__", blob)
Path(sys.argv[3]).write_text(html)
print(f"{len(html)/1024:.0f} KiB written")

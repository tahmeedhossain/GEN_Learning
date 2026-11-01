"""Write placeholder reading-text files for developing the reader page.

Usage: python3 -I scripts/make_skeleton.py data/v2/src build/skeleton

For every network source file, the output has the same records with § lines for
every section of its chapters (including the introductions <ch>.0) and one P line
per node block (the node with the routes that follow it) or per group of routes
that come before the first node of a section. Every node is linked where it is
introduced; every route paragraph links the route's target and inputs. The text
is placeholder text built from labels and descriptions; it is replaced by the
written text in data/v2/book/.
"""
import sys, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
STRUCT = json.loads((ROOT / "data" / "openstax_structure.json").read_text())
CHAP_SECS = {(b["vol"], c["ch"]): [(s["num"], s["title"]) for s in c["sections"]]
             for b in STRUCT for c in b["chapters"]}
CHAP_TITLE = {(b["vol"], c["ch"]): c["title"] for b in STRUCT for c in b["chapters"]}

labels = {}
for p in sorted(src_dir.glob("*.gen")):
    for line in p.read_text().splitlines():
        if line.startswith("N "):
            parts = [x.strip() for x in line[2:].rstrip().rstrip("|").split(" | ")]
            labels[parts[0].split()[1]] = parts[1]


def clean(s):
    return re.sub(r"[\[\]|*]", "", s).strip()


def link(i):
    return f"[[{i}|{clean(labels[i])}]]"


for src in sorted(src_dir.glob("*.gen")):
    lines = src.read_text().splitlines()
    head, sections, cur = [], [], None
    for line in lines:
        if line.startswith("§ "):
            v, n = line[2:].split()
            cur = {"key": (int(v), n), "lines": [line]}
            sections.append(cur)
        elif cur is None:
            head.append(line)
        else:
            cur["lines"].append(line)
    by_key = {s["key"]: s for s in sections}
    chapters = sorted({(k[0], int(k[1].split(".")[0])) for k in by_key})
    out = head[:]
    for ch in chapters:
        for num, title in CHAP_SECS[ch]:
            key = (ch[0], num)
            if key not in by_key:
                out.append(f"§ {ch[0]} {num}")
                if num.endswith(".0"):
                    out.append(f"P Placeholder introduction to Chapter {ch[1]}, {CHAP_TITLE[ch]}. The written text replaces this paragraph.")
                else:
                    out.append(f"P Placeholder text for section {num}, {title}. This section has no new concepts in the network.")
                out.append("")
                continue
            sl = by_key[key]["lines"]
            # find insertion points: before each N line, and before the first R line if it precedes every N
            starts, seen_n, seen_r = [], False, False
            for i, line in enumerate(sl):
                if line.startswith("N "):
                    starts.append(i); seen_n = True
                elif line.startswith("R") and not seen_n and not seen_r:
                    starts.append(i); seen_r = True
            groups = []
            for j, s in enumerate(starts):
                e = starts[j + 1] if j + 1 < len(starts) else len(sl)
                nodes, routes, desc = [], [], {}
                for line in sl[s:e]:
                    if line.startswith("N "):
                        nid = line[2:].split(" | ")[0].split()[1]
                        nodes.append(nid); desc[nid] = ""
                    elif line.startswith("d ") and nodes:
                        desc[nodes[-1]] = (desc[nodes[-1]] + " " + line[2:]).strip()
                    elif line.startswith("R"):
                        rest = line.partition(" ")[2]
                        headr, _, tail = rest.partition(":")
                        tgt, _, ins = headr.partition("<-")
                        fields = [f.strip() for f in tail.split(" | ")]
                        routes.append((tgt.strip(), [x.strip() for x in ins.split(",") if x.strip()],
                                       fields[0], fields[1] if len(fields) > 2 else "Link"))
                parts = [f"{link(n)}: {clean(desc[n])}" for n in nodes]
                for tgt, ins, formula, ttl in routes:
                    parts.append(f"{clean(ttl)}: {link(tgt)} from {', '.join(link(i) for i in ins)}.")
                text = " ".join(parts) if parts else "Placeholder."
                eq = clean(routes[0][2]) if routes and routes[0][2] else ""
                groups.append((s, text, eq))
            ins_at = {s: (t, q) for s, t, q in groups}
            if not starts:
                # section with only X lines: one placeholder paragraph after the header
                sl = [sl[0], f"P Placeholder text for section {num}, {title}."] + sl[1:]
            else:
                new = []
                for i, line in enumerate(sl):
                    if i in ins_at:
                        t, q = ins_at[i]
                        new.append("P " + t)
                        if q:
                            new.append("Q " + q)
                    new.append(line)
                sl = new
            out.extend(sl)
    (out_dir / src.name).write_text("\n".join(out) + "\n")
    print(f"{src.name}: {sum(1 for l in out if l.startswith('P '))} placeholder paragraphs")

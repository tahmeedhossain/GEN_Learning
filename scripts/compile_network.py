"""Compile the curated network source (data/v1/src/*.gen) into one JSON file and
check it against the book structure.

Usage: python3 -I scripts/compile_network.py <structure.json> <out.json> <report.md> <src...>

Source format (one record per line, UTF-8):
  # comment
  § <vol> <ch>.<sec>                     current section (all records below belong to it)
  N <O|M|S> <id> | <label> | <symbol> | <flags>
        flags: prim (primitive observable), ax (postulate / primitive model),
               rel (relativistic era), q (quantum era)
  d <text>      description of the last node
  m <text>      mathematical structure (states)
  p a; b; c     properties (models)
  g a; b        book key terms covered by the last node (glossary or bold term)
  R[tags] <target> <- <in1>, <in2> : <formula> | <title> | <description>
        tags: def, law, thm, read, approx, lim, gen, meas, fail, analog
  > <input id>: <role>                   optional role of one input of the last route
  X a; b :: <reason>                     book key terms of this section not modelled, with reason
"""
import sys, json, re
from pathlib import Path
from collections import defaultdict, OrderedDict

struct_path, out_path, report_path = map(Path, sys.argv[1:4])
srcs = [Path(p) for p in sys.argv[4:]]
BOOK = json.loads(struct_path.read_text())

def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("ӧ", "ö").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()

# ---- book index -----------------------------------------------------------
SEC = OrderedDict()            # (vol, "ch.sec") -> section record
CHAP = OrderedDict()           # (vol, ch) -> chapter record
for b in BOOK:
    for c in b["chapters"]:
        CHAP[(b["vol"], c["ch"])] = c
        for s in c["sections"]:
            SEC[(b["vol"], s["num"])] = dict(s, vol=b["vol"], ch=c["ch"], chapter_title=c["title"])
SEC_ORDER = {k: i for i, k in enumerate(SEC)}
CHAP_ORDER = {k: i for i, k in enumerate(CHAP)}

errors, warns = [], []
nodes, routes, excl = OrderedDict(), [], []
events = []          # reading-order events
cur_sec = None
last_node = None
last_route = None
TAGS = {"def", "law", "thm", "read", "approx", "lim", "gen", "meas", "fail", "analog"}

def new_event(kind, sec, node=None, route=None):
    events.append({"kind": kind, "sec": sec, "node": node, "routes": [route] if route else []})

for src in srcs:
    for ln, raw in enumerate(src.read_text().splitlines(), start=1):
        line = raw.rstrip()
        where = f"{src.name}:{ln}"
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        tag, _, rest = line.partition(" ")
        rest = rest.strip()
        if tag == "§":
            vol, num = rest.split()
            key = (int(vol), num)
            if key not in SEC:
                errors.append(f"{where}: unknown section {key}")
                continue
            if cur_sec and SEC_ORDER[key] < SEC_ORDER[cur_sec]:
                errors.append(f"{where}: section {key} goes backwards")
            cur_sec = key
            last_node = last_route = None
        elif tag == "N":
            if rest.endswith(" |"): rest = rest[:-2]
            parts = [p.strip() for p in rest.split(" | ")]
            if len(parts) < 3:
                errors.append(f"{where}: bad node line"); continue
            t_id = parts[0].split()
            if len(t_id) != 2 or t_id[0] not in "OMS":
                errors.append(f"{where}: bad type/id"); continue
            T, nid = t_id
            if nid in nodes:
                errors.append(f"{where}: duplicate id {nid}"); continue
            flags = set(parts[3].split()) if len(parts) > 3 and parts[3] else set()
            bad = flags - {"prim", "ax", "rel", "q"}
            if bad: errors.append(f"{where}: unknown flags {bad}")
            era = "quantum" if "q" in flags else ("relativistic" if "rel" in flags else "classical")
            n = {"id": nid, "type": {"O": "observable", "M": "model", "S": "state"}[T],
                 "label": parts[1], "symbol": parts[2], "era": era,
                 "primitive": "prim" in flags, "postulate": "ax" in flags,
                 "description": "", "math_structure": None, "properties": None,
                 "book_terms": [], "vol": cur_sec[0], "section": cur_sec[1],
                 "chapter": int(cur_sec[1].split(".")[0]), "order": len(nodes), "src": where}
            nodes[nid] = n
            last_node, last_route = n, None
            new_event("node", cur_sec, node=nid)
        elif tag in ("d", "m", "p", "g"):
            if last_node is None:
                errors.append(f"{where}: '{tag}' without node"); continue
            if tag == "d":
                last_node["description"] = (last_node["description"] + " " + rest).strip()
            elif tag == "m":
                last_node["math_structure"] = rest
            elif tag == "p":
                last_node["properties"] = [x.strip() for x in rest.split(";") if x.strip()]
            else:
                last_node["book_terms"] += [x.strip() for x in rest.split(";") if x.strip()]
        elif tag.startswith("R"):
            m = re.match(r"R(?:\[([^\]]*)\])?$", tag)
            if not m:
                errors.append(f"{where}: bad route tag"); continue
            tags = [x.strip() for x in (m.group(1) or "").split(",") if x.strip()]
            if set(tags) - TAGS: errors.append(f"{where}: unknown route tags {set(tags)-TAGS}")
            head, _, tail = rest.partition(":")
            if "<-" not in head:
                errors.append(f"{where}: route without '<-'"); continue
            tgt, _, ins = head.partition("<-")
            tgt = tgt.strip(); ins = [x.strip() for x in ins.split(",") if x.strip()]
            fields = [f.strip() for f in tail.split(" | ")]
            formula = fields[0] if fields else ""
            title = fields[1] if len(fields) > 2 else ""
            desc = fields[2] if len(fields) > 2 else (fields[1] if len(fields) > 1 else "")
            for x in [tgt] + ins:
                if x not in nodes:
                    errors.append(f"{where}: route endpoint '{x}' not defined before this line")
            if tgt in ins: errors.append(f"{where}: route target is also an input")
            r = {"id": f"r{len(routes)+1}", "target": tgt, "inputs": [{"node": x, "role": None} for x in ins],
                 "logic": "AND" if len(ins) > 1 else "single", "formula": formula, "title": title,
                 "description": desc, "tags": tags, "vol": cur_sec[0], "section": cur_sec[1],
                 "chapter": int(cur_sec[1].split(".")[0]), "src": where}
            routes.append(r)
            last_route = r
            # attach to the current node event if the newest node is an endpoint
            if last_node is not None and events and events[-1]["kind"] == "node" \
               and events[-1]["node"] == last_node["id"] and last_node["id"] in [tgt] + ins:
                events[-1]["routes"].append(r["id"])
            else:
                new_event("route", cur_sec, route=r["id"])
        elif tag == ">":
            if last_route is None:
                errors.append(f"{where}: role without route"); continue
            k, _, v = rest.partition(":")
            hit = [i for i in last_route["inputs"] if i["node"] == k.strip()]
            if not hit: errors.append(f"{where}: role for non-input {k}")
            else: hit[0]["role"] = v.strip()
        elif tag == "X":
            terms, _, reason = rest.partition("::")
            for t in terms.split(";"):
                if t.strip():
                    excl.append({"term": t.strip(), "reason": reason.strip(), "vol": cur_sec[0], "section": cur_sec[1]})
        else:
            errors.append(f"{where}: unknown record '{tag}'")

# ---- derived fields ---------------------------------------------------------
NID = {k: i for i, k in enumerate(nodes)}
for r in routes:
    if r["target"] not in nodes or any(i["node"] not in nodes for i in r["inputs"]):
        r["kind"] = "invalid"; continue
    te = nodes[r["target"]]["era"]
    ie = {nodes[i["node"]]["era"] for i in r["inputs"]}
    if "fail" in r["tags"]:
        r["kind"] = "failed"
    elif ie <= {te}:
        r["kind"] = te
    elif te == "quantum":
        r["kind"] = "to_quantum"
    elif te == "relativistic":
        r["kind"] = "to_relativistic" if "quantum" not in ie else "mixed"
    else:
        r["kind"] = "to_classical"
    if r["kind"] == "mixed":
        warns.append(f"{r['src']}: route with quantum inputs and relativistic target")

# chapter key and global step index
def chap_key(vol, sec): return (vol, int(sec.split(".")[0]))
for i, e in enumerate(events):
    e["index"] = i
    e["chapter_key"] = list(chap_key(*e["sec"]))
    e["section"] = e["sec"][1]; e["vol"] = e["sec"][0]
    del e["sec"]
rid_event = {}
for e in events:
    for rid in e["routes"]: rid_event[rid] = e["index"]
nid_event = {e["node"]: e["index"] for e in events if e["kind"] == "node"}
for r in routes: r["event"] = rid_event[r["id"]]
for n in nodes.values(): n["event"] = nid_event[n["id"]]

# ---- coverage of book key terms ----------------------------------------------
# A glossary entry (section S, term t) counts as modelled when a node of the same
# chapter lists t, or when an X record in that chapter says "= <node id>" (the
# concept already has a node).  Otherwise it must be excluded with a reason.
gloss_by_sec, inline_by_sec = defaultdict(list), defaultdict(list)
term_home = defaultdict(list)
for key, s_ in SEC.items():
    for g in s_["glossary"]:
        gt = g["term"] if isinstance(g, dict) else g
        gloss_by_sec[key].append(gt); term_home[norm(gt)].append(key)
    for t in s_["terms"]:
        inline_by_sec[key].append(t["term"])
        if key not in term_home[norm(t["term"])]:
            term_home[norm(t["term"])].append(key)
def chap_of(key): return (key[0], key[1].split(".")[0])
node_terms_by_chap = defaultdict(set)
for n in nodes.values():
    key = (n["vol"], n["section"])
    for t in n["book_terms"]:
        k = norm(t)
        homes = term_home.get(k, [])
        if not homes:
            errors.append(f"{n['src']}: term '{t}' of node {n['id']} is not a key term anywhere in the book")
        elif key not in homes and not [h for h in homes if chap_of(h) == chap_of(key)]:
            warns.append(f"{n['src']}: term '{t}' of {n['id']} placed in {key}, book has it in {homes}")
        node_terms_by_chap[chap_of(key)].add(k)
excl_by_chap = defaultdict(dict)
for x in excl:
    k = norm(x["term"]); key = (x["vol"], x["section"])
    if k not in term_home:
        errors.append(f"exclusion '{x['term']}' ({x['section']}) is not a key term")
    if x["reason"].startswith("="):
        ref = x["reason"][1:].strip()
        if ref not in nodes:
            errors.append(f"exclusion '{x['term']}' refers to unknown node {ref}")
        x["refers_to"] = ref
    excl_by_chap[chap_of(key)][k] = x
coverage = []          # one row per glossary entry
for key, terms in gloss_by_sec.items():
    for t in terms:
        k = norm(t); ck = chap_of(key)
        if k in node_terms_by_chap[ck]:
            nid = [n["id"] for n in nodes.values() if chap_of((n["vol"], n["section"])) == ck and k in map(norm, n["book_terms"])]
            coverage.append({"vol": key[0], "section": key[1], "term": t, "status": "node", "node": nid[0]})
        elif k in excl_by_chap[ck]:
            x = excl_by_chap[ck][k]
            if "refers_to" in x:
                coverage.append({"vol": key[0], "section": key[1], "term": t, "status": "node by reference", "node": x["refers_to"]})
            else:
                coverage.append({"vol": key[0], "section": key[1], "term": t, "status": "not modelled", "reason": x["reason"]})
        else:
            coverage.append({"vol": key[0], "section": key[1], "term": t, "status": "missing"})
missing = [((c["vol"], c["section"]), c["term"]) for c in coverage if c["status"] == "missing"]

# order inside a section against the book's first appearance of the term
order_warn = []
for key in SEC:
    inl = [norm(t) for t in inline_by_sec[key]]
    pos = []
    for n in nodes.values():
        if (n["vol"], n["section"]) != key: continue
        idx = [inl.index(norm(t)) for t in n["book_terms"] if norm(t) in inl]
        if idx: pos.append((n["order"], min(idx), n["id"]))
    for a, b in zip(pos, pos[1:]):
        if b[1] < a[1]:
            order_warn.append(f"{key}: {b[2]} appears in the book before {a[2]}")

# nodes with no inbound route must be primitive or postulates
indeg = defaultdict(int); outdeg = defaultdict(int)
for r in routes:
    indeg[r["target"]] += 1
    for i in r["inputs"]: outdeg[i["node"]] += 1
for n in nodes.values():
    if indeg[n["id"]] == 0 and not (n["primitive"] or n["postulate"]):
        warns.append(f"{n['src']}: {n['id']} has no route and is not marked prim/ax")
    if indeg[n["id"]] == 0 and outdeg[n["id"]] == 0:
        warns.append(f"{n['src']}: {n['id']} is isolated")
    if not n["description"]:
        errors.append(f"{n['src']}: {n['id']} has no description")
    if n["type"] == "state" and not n["math_structure"]:
        warns.append(f"{n['src']}: state {n['id']} has no math structure")
    if n["type"] == "model" and not n["properties"]:
        warns.append(f"{n['src']}: model {n['id']} has no properties")
for r in routes:
    if not r["description"]:
        warns.append(f"{r['src']}: route {r['id']} has no description")

# ---- chapters, carry-in sets ----------------------------------------------------
chapters = []
for (vol, ch), c in CHAP.items():
    ck = [vol, ch]
    ev = [e["index"] for e in events if e["chapter_key"] == ck]
    new_nodes = [n["id"] for n in nodes.values() if (n["vol"], n["chapter"]) == (vol, ch)]
    rts = [r for r in routes if (r["vol"], r["chapter"]) == (vol, ch)]
    carried = OrderedDict()
    for r in rts:
        for x in [r["target"]] + [i["node"] for i in r["inputs"]]:
            n = nodes[x]
            if CHAP_ORDER[(n["vol"], n["chapter"])] < CHAP_ORDER[(vol, ch)]:
                carried.setdefault(x, r["event"])
    chapters.append({"vol": vol, "ch": ch, "unit": c["unit"], "title": c["title"],
                     "sections": [{"num": s["num"], "title": s["title"], "url": s["url"]} for s in c["sections"]],
                     "events": [ev[0], ev[-1]] if ev else None,
                     "new_nodes": len(new_nodes), "routes": len(rts),
                     "carried_in": [{"node": k, "first_needed_event": v} for k, v in carried.items()]})

stats = {
    "nodes": len(nodes), "routes": len(routes), "events": len(events),
    "by_type": {t: sum(1 for n in nodes.values() if n["type"] == t) for t in ("observable", "model", "state")},
    "by_era": {t: sum(1 for n in nodes.values() if n["era"] == t) for t in ("classical", "relativistic", "quantum")},
    "route_kinds": {k: sum(1 for r in routes if r.get("kind") == k) for k in
                    ("classical", "relativistic", "quantum", "to_relativistic", "to_quantum", "to_classical", "failed", "mixed")},
    "and_routes": sum(1 for r in routes if r["logic"] == "AND"),
    "or_targets": sum(1 for t, k in indeg.items() if k > 1),
    "glossary_terms": sum(len(v) for v in gloss_by_sec.values()),
    "glossary_node": sum(1 for c in coverage if c["status"] == "node"),
    "glossary_node_by_reference": sum(1 for c in coverage if c["status"] == "node by reference"),
    "glossary_not_modelled": sum(1 for c in coverage if c["status"] == "not modelled"),
    "glossary_missing": len(missing),
}

out = {
    "schema": "gen-epistemic-network/1-book",
    "title": "University Physics as a growing network",
    "time_axis": "reading event (book order)",
    "source": {
        "book": "University Physics, Volumes 1-3 (OpenStax, Rice University)",
        "authors": "Samuel J. Ling, Jeff Sanny, William Moebs (senior contributing authors)",
        "licence": "CC BY-NC-SA 4.0",
        "licence_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "repository": "https://github.com/openstax/osbooks-university-physics-bundle",
        "urls": ["https://openstax.org/details/books/university-physics-volume-1",
                 "https://openstax.org/details/books/university-physics-volume-2",
                 "https://openstax.org/details/books/university-physics-volume-3"],
    },
    "stats": stats, "chapters": chapters,
    "nodes": list(nodes.values()), "routes": routes, "events": events,
    "excluded_terms": excl, "coverage": coverage,
}
for n in out["nodes"]: n.pop("src", None)
for r in out["routes"]: r.pop("src", None)
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=0))

rep = ["# Compile report", "", "## Statistics", "```", json.dumps(stats, indent=1), "```", "",
       f"## Errors ({len(errors)})"] + [f"- {e}" for e in errors] + \
      ["", f"## Warnings ({len(warns)})"] + [f"- {w}" for w in warns] + \
      ["", f"## Order warnings ({len(order_warn)})"] + [f"- {w}" for w in order_warn] + \
      ["", f"## Key terms neither modelled nor excluded ({len(missing)})"] + \
      [f"- V{k[0]} §{k[1]}: {t}" for k, t in missing]
report_path.write_text("\n".join(rep))
print(json.dumps(stats))
print(f"errors {len(errors)}, warnings {len(warns)}, order {len(order_warn)}, missing terms {len(missing)}")
for e in errors[:40]: print("E", e)

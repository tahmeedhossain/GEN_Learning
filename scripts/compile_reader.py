"""Compile the reading text and the network (data/v2/book/*.gen) into one JSON file
for the reader page, and check both against the book structure.

Usage: python3 -I scripts/compile_reader.py <structure.json> <out.json> <report.md> <book files...>

Book files are the network source files (data/v2/src/*.gen) with reading text added:
  § <vol> <ch>.<sec>    section header (every section of a covered chapter needs text)
  P <text>              one paragraph; [[id]] or [[id|text]] link a node, *text* emphasis
  Q <text>              display equation under the paragraph above
Every N and R record belongs to the nearest P line above it in its section; that
paragraph is where the node or route appears in the reader's graph.

All checks of compile_network.py are kept (unknown endpoints, forward references,
duplicates, tags, key-term placement and order, coverage of every key term).
Text checks (as scripts/check_book.py, across all files):
  E  records differ from data/v2/src/<name> (when that file exists)
  E  N/R record with no paragraph above it in its section
  E  a section of a covered chapter without a paragraph
  E  a paragraph does not link a node it introduces, or the target of a route it introduces
  E  a link to an unknown node or to a node introduced in a later paragraph
  E  malformed markup
  W  a route input not linked in the route's paragraph; paragraph length outside 30-170 words
"""
import sys, json, re
from pathlib import Path
from collections import defaultdict, OrderedDict

ROOT = Path(__file__).resolve().parent.parent
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

errors, warns, text_warns = [], [], []
nodes, routes, excl = OrderedDict(), [], []
paras = []
cur_sec = None
cur_para = None
last_node = None
last_route = None
sections_seen = []
TAGS = {"def", "law", "thm", "read", "approx", "lim", "gen", "meas", "fail", "analog"}
RECORD_TAGS = {"N", "d", "m", "p", "g", ">", "X"}
LINK = re.compile(r"\[\[([A-Za-z0-9_]+)(?:\|([^\[\]|]+))?\]\]")


def records_of(path):
    """Record lines (N d m p g R > X) with their section, for the integrity check."""
    out, cur = [], None
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        tag = line.partition(" ")[0]
        if tag == "§":
            cur = tuple(line.partition(" ")[2].split())
        elif tag in RECORD_TAGS or tag.startswith("R"):
            out.append((cur, line))
    return out


for src in srcs:
    ref = ROOT / "data" / "v2" / "src" / src.name
    if ref.exists() and ref.resolve() != src.resolve():
        a, b = records_of(ref), records_of(src)
        if a != b:
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    errors.append(f"{src.name}: record {i+1} differs from data/v2/src/{src.name}: '{x[1][:70]}' vs '{y[1][:70]}'")
                    break
            else:
                errors.append(f"{src.name}: record count {len(b)} differs from data/v2/src/{src.name} ({len(a)})")
    for ln, raw in enumerate(src.read_text().splitlines(), start=1):
        line = raw.rstrip()
        where = f"{src.name}:{ln}"
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        tag, _, rest = line.partition(" ")
        rest = rest.strip()
        if tag == "§":
            try:
                vol, num = rest.split()
                key = (int(vol), num)
            except ValueError:
                errors.append(f"{where}: bad section line"); continue
            if key not in SEC:
                errors.append(f"{where}: unknown section {key}")
                continue
            if cur_sec and SEC_ORDER[key] < SEC_ORDER[cur_sec]:
                errors.append(f"{where}: section {key} goes backwards")
            if key in sections_seen:
                errors.append(f"{where}: section {key} appears twice")
            cur_sec = key
            sections_seen.append(key)
            last_node = last_route = cur_para = None
        elif tag == "P":
            if cur_sec is None:
                errors.append(f"{where}: paragraph before any section"); continue
            cur_para = {"k": len(paras), "vol": cur_sec[0], "ch": int(cur_sec[1].split(".")[0]),
                        "section": cur_sec[1], "text": rest, "eqs": [], "new_nodes": [], "new_routes": [],
                        "src": where}
            paras.append(cur_para)
        elif tag == "Q":
            if cur_para is None:
                errors.append(f"{where}: display equation without a paragraph above it")
            elif "[[" in rest:
                errors.append(f"{where}: no links inside display equations")
            else:
                cur_para["eqs"].append(rest)
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
                 "chapter": int(cur_sec[1].split(".")[0]), "order": len(nodes), "src": where,
                 "paragraph": None}
            if cur_para is None:
                errors.append(f"{where}: node {nid} has no paragraph above it in its section")
            else:
                n["paragraph"] = cur_para["k"]; cur_para["new_nodes"].append(nid)
            nodes[nid] = n
            last_node, last_route = n, None
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
                 "chapter": int(cur_sec[1].split(".")[0]), "src": where, "paragraph": None}
            if cur_para is None:
                errors.append(f"{where}: route into {tgt} has no paragraph above it in its section")
            else:
                r["paragraph"] = cur_para["k"]; cur_para["new_routes"].append(r["id"])
            routes.append(r)
            last_route = r
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

# ---- text checks ----------------------------------------------------------------
covered = sorted({(k[0], int(k[1].split(".")[0])) for k in sections_seen}, key=lambda c: CHAP_ORDER[c])
with_text = {(p["vol"], p["section"]) for p in paras}
for ch in covered:
    for s in CHAP[ch]["sections"]:
        if (ch[0], s["num"]) not in with_text:
            errors.append(f"section V{ch[0]} {s['num']} ({s['title']}) has no paragraph")
route_by_id = {r["id"]: r for r in routes}
words_total = 0
for p in paras:
    t, where, k = p["text"], p["src"], p["k"]
    if t.count("[[") != t.count("]]"):
        errors.append(f"{where}: unbalanced [[ ]]")
    links = []
    for m in LINK.finditer(t):
        if m.group(1) not in links:
            links.append(m.group(1))
    plain = LINK.sub(lambda m: m.group(2) or nodes.get(m.group(1), {}).get("label", "X"), t)
    if "[[" in plain or "]]" in plain:
        errors.append(f"{where}: malformed link markup")
    if plain.count("*") % 2:
        errors.append(f"{where}: unbalanced *emphasis*")
    if re.search(r"[_^]\{[^}]*$|[_^]\{[^}]*\{", plain):
        errors.append(f"{where}: unclosed sub/superscript group")
    if re.search(r"<[a-zA-Z/]", plain):
        errors.append(f"{where}: looks like HTML")
    for bad in ("TODO", "TBD", "XXX", "Lorem"):
        if bad in t:
            errors.append(f"{where}: placeholder '{bad}'")
    for nid in links:
        if nid not in nodes:
            errors.append(f"{where}: link to unknown node '{nid}'")
        elif nodes[nid]["paragraph"] is not None and nodes[nid]["paragraph"] > k:
            errors.append(f"{where}: link to '{nid}' before the paragraph that introduces it")
    for nid in p["new_nodes"]:
        if nid not in links:
            errors.append(f"{where}: paragraph introduces '{nid}' but does not link it")
    for rid in p["new_routes"]:
        r = route_by_id[rid]
        if r["target"] not in links:
            errors.append(f"{where}: paragraph introduces {rid} into '{r['target']}' but does not link it")
        miss = [i["node"] for i in r["inputs"] if i["node"] not in links]
        if miss:
            text_warns.append(f"{where}: {rid} ({r['target']} <- {', '.join(i['node'] for i in r['inputs'])}): inputs not linked: {', '.join(miss)}")
    n_words = len(plain.split())
    words_total += n_words
    if n_words < 30 or n_words > 170:
        text_warns.append(f"{where}: paragraph has {n_words} words")
    p["links"] = links
    p["words"] = n_words

# ---- derived fields ---------------------------------------------------------
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

# ---- coverage of book key terms (as in compile_network.py) ---------------------
gloss_by_sec, inline_by_sec = defaultdict(list), defaultdict(list)
term_home = defaultdict(list)
for key, s_ in SEC.items():
    for g in s_["glossary"]:
        term = g["term"] if isinstance(g, dict) else g
        gloss_by_sec[key].append(term); term_home[norm(term)].append(key)
    for t in s_["terms"]:
        inline_by_sec[key].append(t["term"])
        if key not in term_home[norm(t["term"])]:
            term_home[norm(t["term"])].append(key)
def chap_of(key): return (key[0], key[1].split(".")[0])
covered_keys = {(c[0], str(c[1])) for c in covered}
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
coverage = []
for key, terms in gloss_by_sec.items():
    if chap_of(key) not in covered_keys:
        continue
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
for (vol, ch) in covered:
    c = CHAP[(vol, ch)]
    pk = [p["k"] for p in paras if (p["vol"], p["ch"]) == (vol, ch)]
    new_nodes = [n["id"] for n in nodes.values() if (n["vol"], n["chapter"]) == (vol, ch)]
    rts = [r for r in routes if (r["vol"], r["chapter"]) == (vol, ch)]
    carried = OrderedDict()
    for r in sorted(rts, key=lambda r: (r["paragraph"] if r["paragraph"] is not None else 10**9)):
        for x in [r["target"]] + [i["node"] for i in r["inputs"]]:
            n = nodes[x]
            if CHAP_ORDER[(n["vol"], n["chapter"])] < CHAP_ORDER[(vol, ch)]:
                carried.setdefault(x, r["paragraph"])
    secs = []
    for s in c["sections"]:
        sk = [p["k"] for p in paras if (p["vol"], p["section"]) == (vol, s["num"])]
        secs.append({"num": s["num"], "title": s["title"], "url": s["url"],
                     "p0": sk[0] if sk else None, "p1": sk[-1] if sk else None})
    chapters.append({"vol": vol, "ch": ch, "unit": c.get("unit"), "title": c["title"],
                     "p0": pk[0] if pk else None, "p1": pk[-1] if pk else None,
                     "sections": secs, "new_nodes": len(new_nodes), "routes": len(rts),
                     "carried_in": [{"node": k, "first_needed_paragraph": v} for k, v in carried.items()]})

stats = {
    "nodes": len(nodes), "routes": len(routes), "paragraphs": len(paras), "words": words_total,
    "by_type": {t: sum(1 for n in nodes.values() if n["type"] == t) for t in ("observable", "model", "state")},
    "by_era": {t: sum(1 for n in nodes.values() if n["era"] == t) for t in ("classical", "relativistic", "quantum")},
    "route_kinds": {k: sum(1 for r in routes if r.get("kind") == k) for k in
                    ("classical", "relativistic", "quantum", "to_relativistic", "to_quantum", "to_classical", "failed", "mixed")},
    "and_routes": sum(1 for r in routes if r["logic"] == "AND"),
    "or_targets": sum(1 for t, k in indeg.items() if k > 1),
    "glossary_terms": len(coverage),
    "glossary_node": sum(1 for c in coverage if c["status"] == "node"),
    "glossary_node_by_reference": sum(1 for c in coverage if c["status"] == "node by reference"),
    "glossary_not_modelled": sum(1 for c in coverage if c["status"] == "not modelled"),
    "glossary_missing": len(missing),
}

out = {
    "schema": "gen-epistemic-network/2-reader",
    "title": "University Physics as a growing network, with reading text",
    "time_axis": "paragraph of the reading text (book order)",
    "source": {
        "book": "University Physics, Volumes 1-3 (OpenStax, Rice University)",
        "authors": "Samuel J. Ling, Jeff Sanny, William Moebs (senior contributing authors)",
        "licence": "CC BY-NC-SA 4.0",
        "licence_url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "repository": "https://github.com/openstax/osbooks-university-physics-bundle",
        "urls": ["https://openstax.org/details/books/university-physics-volume-1",
                 "https://openstax.org/details/books/university-physics-volume-2",
                 "https://openstax.org/details/books/university-physics-volume-3"],
        "text": "The reading text is written for this network and follows the section structure of the book; it does not reproduce the book's text.",
    },
    "stats": stats, "chapters": chapters,
    "paragraphs": [{k: p[k] for k in ("k", "vol", "ch", "section", "text", "eqs", "new_nodes", "new_routes", "links")} for p in paras],
    "nodes": list(nodes.values()), "routes": routes,
    "excluded_terms": excl, "coverage": coverage,
}
for n in out["nodes"]:
    n.pop("src", None)
for r in out["routes"]:
    r.pop("src", None)
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=0))

per_chap = []
for c in chapters:
    ps = [p for p in paras if (p["vol"], p["ch"]) == (c["vol"], c["ch"])]
    per_chap.append(f"| V{c['vol']} {c['ch']} | {c['title']} | {len(ps)} | {sum(p['words'] for p in ps)} | {c['new_nodes']} | {c['routes']} | {len(c['carried_in'])} |")
rep = ["# Compile report (reader)", "", "## Statistics", "```", json.dumps(stats, indent=1), "```", "",
       "## Text per chapter", "", "| Chapter | Title | Paragraphs | Words | New nodes | Routes | Carried in |", "|---|---|---|---|---|---|---|"] + per_chap + [
       "", f"## Errors ({len(errors)})"] + [f"- {e}" for e in errors] + \
      ["", f"## Network warnings ({len(warns)})"] + [f"- {w}" for w in warns] + \
      ["", f"## Text warnings ({len(text_warns)})"] + [f"- {w}" for w in text_warns] + \
      ["", f"## Order warnings ({len(order_warn)})"] + [f"- {w}" for w in order_warn] + \
      ["", f"## Key terms neither modelled nor excluded ({len(missing)})"] + \
      [f"- V{k[0]} §{k[1]}: {t}" for k, t in missing]
report_path.write_text("\n".join(rep) + "\n")
print(json.dumps(stats))
print(f"errors {len(errors)}, network warnings {len(warns)}, text warnings {len(text_warns)}, "
      f"order {len(order_warn)}, missing terms {len(missing)}")
for e in errors[:40]:
    print("E", e)
sys.exit(1 if errors else 0)

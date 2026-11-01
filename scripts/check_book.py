"""Check one reading-text file (data/v2/book/<name>.gen) against the network source.

Usage:  python3 -I scripts/check_book.py data/v2/book/v1b.gen [--quiet]

The reading-text file is the network source file data/v2/src/<name>.gen with three
kinds of lines added:
  § <vol> <ch>.<sec>   section headers for sections that have no records yet
                       (including the chapter introduction <ch>.0)
  P <text>             one paragraph of the reading text
  Q <text>             a display equation shown under the paragraph above

Every N and R record belongs to the nearest P line above it in the same
section; that paragraph is where the node or route appears in the graph.

Checks (errors must be fixed, warnings should be rare and deliberate):
  E  record lines (N d m p g R > X) differ from data/v2/src/<name>.gen in content,
     order or section
  E  an N or R record with no P line above it in its section
  E  a section of the file's chapters without any P line, or out of book order
  E  a paragraph does not link a node introduced under it
  E  a paragraph does not link the target of a route introduced under it
  E  a link to an unknown node, or to a node introduced later in the reading
  E  malformed markup ([[ ]], *emphasis*, _{ } and ^{ } groups)
  W  a route input not linked in the paragraph that introduces the route
  W  paragraph length outside 30-170 words; unbraced multi-letter sub/superscripts
"""
import sys, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
QUIET = "--quiet" in sys.argv
if len(args) != 1:
    sys.exit(__doc__)
book_path = Path(args[0])
src_path = ROOT / "data" / "v2" / "src" / book_path.name
STRUCT = json.loads((ROOT / "data" / "openstax_structure.json").read_text())

# ---- book structure -------------------------------------------------------
SEC_ORDER, CHAP_SECS = {}, {}
for b in STRUCT:
    for c in b["chapters"]:
        CHAP_SECS[(b["vol"], c["ch"])] = [s["num"] for s in c["sections"]]
        for s in c["sections"]:
            SEC_ORDER[(b["vol"], s["num"])] = len(SEC_ORDER)

# ---- global node order from all source files -----------------------------
SRC_FILES = sorted((ROOT / "data" / "v2" / "src").glob("*.gen"))
if src_path not in SRC_FILES:
    sys.exit(f"no source file {src_path}")
FILE_IDX = {p.name: i for i, p in enumerate(SRC_FILES)}
node_file = {}
for p in SRC_FILES:
    for line in p.read_text().splitlines():
        if line.startswith("N "):
            nid = line[2:].split(" | ")[0].split()[1]
            node_file[nid] = FILE_IDX[p.name]
me = FILE_IDX[book_path.name]

RECORD_TAGS = {"N", "d", "m", "p", "g", ">", "X"}
LINK = re.compile(r"\[\[([A-Za-z0-9_]+)(?:\|([^\[\]|]+))?\]\]")


def parse(path, with_text):
    """Return records [(section, line)], sections [(key, lineno)], paragraphs."""
    recs, secs, paras, errs = [], [], [], []
    cur, para = None, None
    for ln, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        tag, _, rest = line.partition(" ")
        where = f"{path.name}:{ln}"
        if tag == "§":
            try:
                v, n = rest.split()
                cur = (int(v), n)
            except ValueError:
                errs.append(f"{where}: bad section line"); continue
            secs.append((cur, ln)); para = None
        elif tag == "P":
            if not with_text:
                errs.append(f"{where}: P line in source file"); continue
            if cur is None:
                errs.append(f"{where}: paragraph before any section"); continue
            para = {"sec": cur, "ln": ln, "text": rest.strip(), "nodes": [], "routes": [], "eqs": []}
            paras.append(para)
        elif tag == "Q":
            if para is None:
                errs.append(f"{where}: display equation without a paragraph above it")
            else:
                para["eqs"].append((ln, rest.strip()))
        elif tag in RECORD_TAGS or tag.startswith("R"):
            recs.append((cur, line))
            if tag == "N":
                nid = rest.split(" | ")[0].split()[1]
                if with_text:
                    if para is None:
                        errs.append(f"{where}: node {nid} has no P line above it in its section")
                    else:
                        para["nodes"].append(nid)
            elif tag.startswith("R"):
                head = rest.partition(":")[0]
                tgt, _, ins = head.partition("<-")
                r = (tgt.strip(), [x.strip() for x in ins.split(",") if x.strip()], ln)
                if with_text:
                    if para is None:
                        errs.append(f"{where}: route into {r[0]} has no P line above it in its section")
                    else:
                        para["routes"].append(r)
        else:
            errs.append(f"{where}: unknown line tag '{tag}'")
    return recs, secs, paras, errs


src_recs, src_secs, _, e0 = parse(src_path, False)
book_recs, book_secs, paras, errors = parse(book_path, True)
errors = e0 + errors
warns = []

# ---- 1. records unchanged ----------------------------------------------------
if src_recs != book_recs:
    for i, (a, b) in enumerate(zip(src_recs, book_recs)):
        if a != b:
            errors.append(f"record {i+1} differs from the source:\n    source: [{a[0]}] {a[1]}\n    book:   [{b[0]}] {b[1]}")
            break
    else:
        errors.append(f"record count differs: source {len(src_recs)}, book {len(book_recs)}")

# ---- 2. sections ---------------------------------------------------------------
chapters = sorted({(k[0], int(k[1].split(".")[0])) for k, _ in src_secs})
seen = {}
prev = -1
for key, ln in book_secs:
    if key not in SEC_ORDER:
        errors.append(f"{book_path.name}:{ln}: unknown section {key}"); continue
    if key in seen:
        errors.append(f"{book_path.name}:{ln}: section {key} appears twice")
    if SEC_ORDER[key] < prev:
        errors.append(f"{book_path.name}:{ln}: section {key} is out of book order")
    prev = SEC_ORDER[key]; seen[key] = ln
with_p = {p["sec"] for p in paras}
for ch in chapters:
    for num in CHAP_SECS[ch]:
        if (ch[0], num) not in with_p:
            errors.append(f"section V{ch[0]} {num} has no paragraph")

# ---- 3. links -------------------------------------------------------------------
node_para = {}
for i, p in enumerate(paras):
    for nid in p["nodes"]:
        node_para[nid] = i
words_total = 0
per_sec = {}
for i, p in enumerate(paras):
    t = p["text"]
    where = f"{book_path.name}:{p['ln']}"
    if t.count("[[") != t.count("]]"):
        errors.append(f"{where}: unbalanced [[ ]]")
    links = [m.group(1) for m in LINK.finditer(t)]
    plain = LINK.sub(lambda m: m.group(2) or "X", t)
    if "[[" in plain or "]]" in plain:
        errors.append(f"{where}: malformed link markup")
    if plain.count("*") % 2:
        errors.append(f"{where}: unbalanced *emphasis*")
    for grp in re.findall(r"[_^]\{[^}]*$|[_^]\{[^}]*\{", plain):
        errors.append(f"{where}: unclosed sub/superscript group '{grp}'")
    for m in re.finditer(r"[_^]([A-Za-z]{2,}[A-Za-z0-9]*)", plain):
        warns.append(f"{where}: '{m.group(0)}' renders all of '{m.group(1)}' as sub/superscript; use braces if that is not meant")
    if re.search(r"<[a-zA-Z/]", plain):
        errors.append(f"{where}: looks like HTML")
    for bad in ("TODO", "TBD", "XXX", "Lorem"):
        if bad in t:
            errors.append(f"{where}: placeholder '{bad}'")
    for nid in links:
        if nid not in node_file:
            errors.append(f"{where}: link to unknown node '{nid}'")
        elif node_file[nid] > me:
            errors.append(f"{where}: link to '{nid}', which is introduced in a later file")
        elif node_file[nid] == me and node_para.get(nid, 10**9) > i:
            errors.append(f"{where}: link to '{nid}' before the paragraph that introduces it")
    for nid in p["nodes"]:
        if nid not in links:
            errors.append(f"{where}: paragraph introduces '{nid}' but does not link it")
    for tgt, ins, rln in p["routes"]:
        if tgt not in links:
            errors.append(f"{where}: paragraph introduces the route at line {rln} into '{tgt}' but does not link '{tgt}'")
        miss = [x for x in ins if x not in links]
        if miss:
            warns.append(f"{where}: route at line {rln} ({tgt} <- {', '.join(ins)}): inputs not linked here: {', '.join(miss)}")
    for qln, q in p["eqs"]:
        if "[[" in q:
            errors.append(f"{book_path.name}:{qln}: no links inside display equations")
    n = len(plain.split())
    words_total += n
    if n < 30 or n > 170:
        warns.append(f"{where}: paragraph has {n} words")
    per_sec.setdefault(p["sec"], []).append(n)

# ---- report -----------------------------------------------------------------------
print(f"{book_path.name}: {len(paras)} paragraphs, {words_total} words, "
      f"{len(per_sec)} sections with text, {sum(len(p['nodes']) for p in paras)} nodes and "
      f"{sum(len(p['routes']) for p in paras)} routes placed")
print(f"errors {len(errors)}, warnings {len(warns)}")
for e in errors:
    print("E", e)
if not QUIET:
    for w in warns:
        print("W", w)
sys.exit(1 if errors else 0)

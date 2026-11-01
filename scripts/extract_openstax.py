"""Extract book structure and key terms (in reading order) from the OpenStax
University Physics CNXML source.  Usage: python3 -I extract_openstax.py <repo> <out.json>
Only structure, titles and term strings are kept; definitions are kept for the
curator's reference in a separate file and are not shown on the page."""
import sys, re, json, unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
NS = {"col": "http://cnx.rice.edu/collxml", "md": "http://cnx.rice.edu/mdml",
      "c": "http://cnx.rice.edu/cnxml"}
C = "{http://cnx.rice.edu/cnxml}"

def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()

CYR = {"о": "o", "ӧ": "o", "е": "e", "а": "a", "с": "c", "р": "p"}
def slugify(s):
    s = "".join(CYR.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("’", "").replace("'", "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s

def module_info(mid):
    root = ET.parse(repo / "modules" / mid / "index.cnxml").getroot()
    title = text_of(root.find(C + "title"))
    content = root.find(C + "content")
    terms, seen = [], set()
    for t in content.iter(C + "term"):
        s = text_of(t)
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        terms.append({"term": s, "emph": t.get("class") != "no-emphasis"})
    gloss = []
    g = root.find(C + "glossary")
    if g is not None:
        for d in g.findall(C + "definition"):
            gloss.append({"term": text_of(d.find(C + "term")),
                          "meaning": text_of(d.find(C + "meaning"))})
    keyeq = []
    for sec in content.iter(C + "section"):
        if sec.get("class") == "key-equations":
            for row in sec.iter(C + "row"):
                ents = row.findall(C + "entry")
                if ents:
                    keyeq.append(text_of(ents[0]))
    return title, terms, gloss, keyeq

books = []
for vol in (1, 2, 3):
    slug = f"university-physics-volume-{vol}"
    col = ET.parse(repo / "collections" / f"{slug}.collection.xml").getroot()
    chapters = []
    def walk(node, unit):
        for sub in node.findall("col:content/col:subcollection", NS):
            title = sub.find("md:title", NS).text
            mods = [m.get("document") for m in sub.findall("col:content/col:module", NS)]
            subs = sub.findall("col:content/col:subcollection", NS)
            if subs:
                walk(sub, title)
            else:
                chapters.append((unit, title, mods))
    walk(col, None)
    vchap = []
    for ci, (unit, ctitle, mods) in enumerate(chapters, start=1):
        secs = []
        for si, mid in enumerate(mods):
            title, terms, gloss, keyeq = module_info(mid)
            num = f"{ci}.{si}" if si else f"{ci}.0"
            s = f"{ci}-{si}-{slugify(title)}" if si else f"{ci}-introduction"
            secs.append({"num": num, "module": mid, "title": title,
                         "url": f"https://openstax.org/books/{slug}/pages/{s}",
                         "terms": terms, "glossary": gloss, "key_equations": keyeq})
        vchap.append({"vol": vol, "ch": ci, "unit": unit, "title": ctitle, "sections": secs})
    books.append({"vol": vol, "slug": slug, "chapters": vchap})

out.write_text(json.dumps(books, indent=1, ensure_ascii=False))
for b in books:
    nt = sum(len(s["terms"]) for c in b["chapters"] for s in c["sections"])
    ng = sum(len(s["glossary"]) for c in b["chapters"] for s in c["sections"])
    print(f"Vol {b['vol']}: {len(b['chapters'])} chapters, "
          f"{sum(len(c['sections'])-1 for c in b['chapters'])} sections, {nt} inline terms, {ng} glossary terms")

"""Headless checks of the reader page (Playwright, Chromium).

Usage: python3 scripts/check_reader.py <build/reader.html> <reader.json> <outdir>

Checks, at desktop 1440x900 (light), medium 1024x768 (light) and phone 390x844 (dark):
  - no console errors, no horizontal overflow;
  - for sampled reading positions k, the number of drawn concepts and links equals the
    number computed from the data (chapter nodes with paragraph <= k, plus earlier-chapter
    nodes first needed at or before k; chapter links with paragraph <= k whose target and
    some input are drawn);
  - the earlier-chapter modes and "Whole chapter" change the counts as expected;
  - clicking a term, a node, an edge and a route chip opens the card with the right title
    and the paragraph that introduces it; Esc closes it;
  - the chapter select moves the reading position into that chapter.
Screenshots go to <outdir>.
"""
import sys, json, random
from pathlib import Path
from playwright.sync_api import sync_playwright

page_path, data_path, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
out.mkdir(parents=True, exist_ok=True)
D = json.loads(data_path.read_text())
CH = D["chapters"]
CI = {(c["vol"], c["ch"]): i for i, c in enumerate(CH)}
P = D["paragraphs"]
NODES = {n["id"]: n for n in D["nodes"]}


def expected(k, mode="needed", whole=False):
    p = P[k]
    ci = CI[(p["vol"], p["ch"])]
    c = CH[ci]
    K = c["p1"] if whole else k
    vis = {n["id"] for n in D["nodes"] if (n["vol"], n["chapter"]) == (c["vol"], c["ch"]) and n["paragraph"] <= K}
    if mode == "needed":
        vis |= {x["node"] for x in c["carried_in"] if x["first_needed_paragraph"] <= K}
    elif mode == "all":
        vis |= {x["node"] for x in c["carried_in"]}
    rts = [r for r in D["routes"] if (r["vol"], r["chapter"]) == (c["vol"], c["ch"]) and r["paragraph"] <= K
           and r["target"] in vis and any(i["node"] in vis for i in r["inputs"])]
    return ci, len(vis), len(rts)


SKEL = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0;font:14px system-ui}img{max-width:100%}</style></head><body>"""
wrapped = out / "wrapped.html"
wrapped.write_text(SKEL + page_path.read_text() + "</body></html>")

ch5 = CH[CI[(1, 5)]]
k_mid = (ch5["p0"] + ch5["p1"]) // 2
k_fail = next(p["k"] for p in P if p["vol"] == 3 and any(r["kind"] == "failed" and r["paragraph"] == p["k"] for r in D["routes"]))
random.seed(7)
sample = sorted(random.sample(range(len(P)), 40) + [0, len(P) - 1, k_mid, k_fail])
problems = []
cases = [("desktop", 1440, 900, "light"), ("medium", 1024, 768, "light"), ("phone", 390, 844, "dark")]
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, w, h, scheme in cases:
        ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, device_scale_factor=1)
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.goto(wrapped.as_uri())
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(out / f"{name}_start.png"))
        bad = 0
        for k in sample:
            pg.evaluate(f"UPNET.goTo({k})")
            st = pg.evaluate("UPNET.state()")
            ci, en, er = expected(k)
            dom = pg.evaluate("document.querySelectorAll('#graph .node').length")
            if st["K"] != k or st["ci"] != ci or st["nodes"] != en or st["routes"] != er or dom != en:
                bad += 1
                if bad <= 5:
                    problems.append(f"{name}: k={k} state={st} expected ci={ci} nodes={en} routes={er} dom={dom}")
        print(f"{name}: {len(sample)} reading positions checked, {bad} mismatches")
        # reading position mid chapter 5
        pg.evaluate(f"UPNET.goTo({k_mid})"); pg.wait_for_timeout(1100)
        pg.screenshot(path=str(out / f"{name}_v1c5.png"))
        ov = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        if ov[0] > ov[1]:
            problems.append(f"{name}: horizontal overflow {ov}")
        # modes
        for mode in ("all", "off", "needed"):
            pg.click(f".seg label:has(input[value={mode}])")
            st = pg.evaluate("UPNET.state()")
            ci, en, er = expected(k_mid, mode)
            if st["nodes"] != en:
                problems.append(f"{name}: mode {mode} nodes {st['nodes']} expected {en}")
        pg.click("label:has(#whole)")
        st = pg.evaluate("UPNET.state()")
        ci, en, er = expected(k_mid, "needed", whole=True)
        if st["nodes"] != en or st["routes"] != er:
            problems.append(f"{name}: whole chapter {st} expected {en}/{er}")
        pg.click("label:has(#whole)")
        # click a term in the active paragraph
        term = pg.locator("p.para.active .term").first
        nid = term.get_attribute("data-node")
        term.click()
        pg.wait_for_timeout(200)
        title = pg.inner_text("#card .ctitle") if pg.is_visible("#card") else None
        intext = pg.inner_text("#card .intext") if pg.is_visible("#card .intext") else ""
        if title != NODES[nid]["label"] or len(intext) < 20:
            problems.append(f"{name}: term click gave card title {title!r}, expected {NODES[nid]['label']!r}; intext {len(intext)} chars")
        sel_terms = pg.evaluate("document.querySelectorAll('#readerIn .term.sel').length")
        if sel_terms < 1:
            problems.append(f"{name}: selected term not marked in the text")
        pg.screenshot(path=str(out / f"{name}_term_card.png"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(100)
        if pg.is_visible("#card"):
            problems.append(f"{name}: Esc did not close the card")
        # click a node in the graph
        node = pg.locator("#graph .node").first
        nid = node.get_attribute("data-id")
        node.click()
        title = pg.inner_text("#card .ctitle") if pg.is_visible("#card") else None
        if title != NODES[nid]["label"]:
            problems.append(f"{name}: node click gave {title!r}, expected {NODES[nid]['label']!r}")
        pg.keyboard.press("Escape")
        # click an edge (input path of a route)
        rid = pg.evaluate("(() => { const e = document.querySelector('#graph .route path.hit[data-in]'); if (!e) return null; e.dispatchEvent(new MouseEvent('click', {bubbles: true})); return e.closest('.route').getAttribute('data-rid'); })()")
        if rid:
            r = next(x for x in D["routes"] if x["id"] == rid)
            title = pg.inner_text("#card .ctitle") if pg.is_visible("#card") else ""
            if (r["title"] or "Link") not in title and "→" not in title:
                problems.append(f"{name}: edge click card {title!r} for {rid}")
            pg.screenshot(path=str(out / f"{name}_edge_card.png"))
            pg.keyboard.press("Escape")
        # route chip under a paragraph
        chip = pg.locator("p.para.active ~ .rl .rchip, .rl .rchip").first
        rid = chip.get_attribute("data-route")
        pg.evaluate(f"document.querySelector('.rchip[data-route=\"{rid}\"]').click()")
        r = next(x for x in D["routes"] if x["id"] == rid)
        title = pg.inner_text("#card .ctitle") if pg.is_visible("#card") else ""
        if title != (r["title"] or "Link"):
            problems.append(f"{name}: route chip card {title!r}, expected {r['title']!r}")
        pg.keyboard.press("Escape")
        # failed-prediction position
        pg.evaluate(f"UPNET.goTo({k_fail})"); pg.wait_for_timeout(1100)
        pg.screenshot(path=str(out / f"{name}_failed.png"))
        # chapter select
        target_ci = CI[(2, 7)]
        if name == "phone":
            pg.select_option("#chapterM", value=str(target_ci))
        else:
            pg.select_option("#chapter", value=str(target_ci))
        pg.wait_for_timeout(1400)
        st = pg.evaluate("UPNET.state()")
        if st["ci"] != target_ci:
            problems.append(f"{name}: chapter select gave ci {st['ci']}, expected {target_ci}")
        pg.screenshot(path=str(out / f"{name}_chapter_select.png"))
        if name == "desktop":
            pg.click("#themeBtn"); pg.wait_for_timeout(200)
            pg.evaluate(f"UPNET.goTo({k_mid})"); pg.wait_for_timeout(300)
            pg.locator("p.para.active .term").first.click()
            pg.screenshot(path=str(out / "desktop_dark_card.png"))
            pg.click("#themeBtn")
            pg.click("#keyBtn"); pg.wait_for_timeout(150)
            pg.screenshot(path=str(out / "desktop_key.png"))
            pg.click("#keyBtn")
            # the reading position survives a reload; a #v<vol>c<ch> hash opens that chapter
            pg.evaluate(f"UPNET.goTo({k_fail})"); pg.wait_for_timeout(500)
            pg.reload(); pg.wait_for_timeout(1000)
            st = pg.evaluate("UPNET.state()")
            if st["K"] != k_fail:
                problems.append(f"{name}: after reload K={st['K']}, expected {k_fail}")
            pg.goto(wrapped.as_uri() + "#v2c9"); pg.wait_for_timeout(1000)
            st = pg.evaluate("UPNET.state()")
            if st["ci"] != CI[(2, 9)]:
                problems.append(f"{name}: hash #v2c9 gave ci {st['ci']}")
            # resizing to phone width and back keeps the reading position in the same chapter
            pg.evaluate(f"UPNET.goTo({k_mid})"); pg.wait_for_timeout(300)
            pg.set_viewport_size({"width": 390, "height": 844}); pg.wait_for_timeout(600)
            st1 = pg.evaluate("UPNET.state()")
            ov = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            pg.set_viewport_size({"width": 1440, "height": 900}); pg.wait_for_timeout(600)
            st2 = pg.evaluate("UPNET.state()")
            if st1["ci"] != CI[(1, 5)] or st2["ci"] != CI[(1, 5)] or ov[0] > ov[1]:
                problems.append(f"{name}: resize lost the chapter or overflowed: {st1['K']} {st2['K']} {ov}")
        if name == "phone":
            pg.screenshot(path=str(out / "phone_full_top.png"), full_page=False)
        errs = [e for e in errs if "fonts.g" not in e and "net::" not in e]
        if errs:
            problems.append(f"{name}: console {errs[:5]}")
        print(f"{name}: console errors {len(errs)}")
        ctx.close()
    b.close()
print("problems:", len(problems))
for p in problems:
    print(" -", p)
sys.exit(1 if problems else 0)

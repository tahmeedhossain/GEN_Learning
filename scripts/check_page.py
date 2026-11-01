"""Headless checks of the built page: console errors, horizontal overflow, screenshots.
Usage: python3 scripts/check_page.py <page.html> <outdir>"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
page_path, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
url = page_path.as_uri()
SKEL = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>"""
wrapped = out / "wrapped.html"
wrapped.write_text(SKEL + page_path.read_text() + "</body></html>")
cases = [("desktop_light", 1440, 900, "light"), ("medium_light", 1024, 820, "light"), ("phone_dark", 390, 844, "dark")]
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, w, h, scheme in cases:
        ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, device_scale_factor=1)
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.type + ": " + m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.goto(wrapped.as_uri())
        pg.wait_for_timeout(700)
        ov = pg.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        pg.screenshot(path=str(out / f"{name}.png"), full_page=(w < 1100))
        print(name, "overflow:", ov, "errors:", [e for e in errs if "fonts.g" not in e][:5])
        if name == "desktop_light":
            # interaction: step back to the start, step forward 3 times, trace, chapter change
            pg.click("#toStart"); pg.click("#fwd"); pg.click("#fwd"); pg.click("#fwd")
            pg.wait_for_timeout(300)
            print("  step text:", pg.inner_text("#stepText"), "| card:", pg.inner_text("#card h3"))
            pg.screenshot(path=str(out / "desktop_step3.png"))
            pg.select_option("#chapter", label="6. Photons and Matter Waves")
            pg.wait_for_timeout(300)
            pg.click("#graph .node[data-id='photon']")
            pg.click("label:has(#trace-2)")
            pg.wait_for_timeout(300)
            print("  card:", pg.inner_text("#card h3"), "| nodes drawn:", pg.evaluate("document.querySelectorAll('#graph .node').length"))
            pg.screenshot(path=str(out / "desktop_trace.png"))
            print("  errors after interaction:", [e for e in errs if "fonts.g" not in e][:5])
        ctx.close()
    b.close()

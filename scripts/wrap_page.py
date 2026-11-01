"""Wrap a built page (a fragment: <title>, <link>, <style>, markup, <script>) in a
full HTML document for the GitHub Pages site, and add the version switcher.

Usage: python3 -I scripts/wrap_page.py <built fragment.html> <version id> <out index.html>
e.g.   python3 -I scripts/wrap_page.py build/reader.html v2 v2/index.html
"""
import sys
from pathlib import Path

src, vid, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
body = src.read_text()
if body.lstrip().lower().startswith("<!doctype"):
    sys.exit("already a full document")
head = ('<!doctype html>\n<html lang="en" data-gen-version="' + vid + '">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0}</style>\n'
        '</head>\n<body>\n')
tail = '\n<script src="../assets/versions.js"></script>\n</body>\n</html>\n'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(head + body + tail)
print(f"wrote {out} ({out.stat().st_size // 1024} KiB)")

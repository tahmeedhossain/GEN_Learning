"""Print the reading text of book files for review: one line per paragraph or
display equation, prefixed by file:line and section; links shown as their text.

Usage: python3 -I scripts/dump_text.py data/v2/book/v1a.gen [more files]
"""
import sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABEL = {}
for p in sorted((ROOT / "data" / "v2" / "src").glob("*.gen")):
    for line in p.read_text().splitlines():
        if line.startswith("N "):
            parts = line[2:].split(" | ")
            LABEL[parts[0].split()[1]] = parts[1].strip()
LINK = re.compile(r"\[\[([A-Za-z0-9_]+)(?:\|([^\[\]|]+))?\]\]")
for f in sys.argv[1:]:
    sec = None
    for ln, line in enumerate(Path(f).read_text().splitlines(), 1):
        if line.startswith("§ "):
            sec = line[2:].strip()
        elif line.startswith("P ") or line.startswith("Q "):
            text = LINK.sub(lambda m: m.group(2) or LABEL.get(m.group(1), m.group(1)), line[2:])
            tag = "EQ " if line[0] == "Q" else ""
            print(f"{Path(f).name}:{ln} [{sec}] {tag}{text}")

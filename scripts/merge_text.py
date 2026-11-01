"""Merge reading-text blocks into a copy of the source file.

Usage: python3 -I scripts/merge_text.py data/v2/src/<name>.gen <draft.txt> data/v2/book/<name>.gen

spec.txt: blocks introduced by a line '@@ <n>' (insert before source line n,
1-based; n = len+1 appends at the end). Every following line up to the next
'@@' is inserted verbatim, except lines starting with '%%' (spec comments)
and the literal '<blank>', which becomes an empty line. Empty lines in the
spec are ignored.
"""
import sys
from pathlib import Path

src, spec, out = map(Path, sys.argv[1:4])
lines = src.read_text().split("\n")
if lines and lines[-1] == "":
    lines = lines[:-1]
ins = {}
cur = None
for raw in spec.read_text().split("\n"):
    if raw.startswith("@@ "):
        cur = int(raw[3:].split()[0])
        if cur in ins:
            sys.exit(f"duplicate anchor {cur}")
        ins[cur] = []
        continue
    if raw.startswith("%%") or raw.strip() == "":
        continue
    if cur is None:
        sys.exit("text before first anchor")
    ins[cur].append("" if raw == "<blank>" else raw.rstrip())
res = []
for i, line in enumerate(lines, start=1):
    res.extend(ins.pop(i, []))
    res.append(line)
res.extend(ins.pop(len(lines) + 1, []))
if ins:
    sys.exit(f"unused anchors: {sorted(ins)}")
out.write_text("\n".join(res) + "\n")
print(f"wrote {out}: {len(res)} lines")

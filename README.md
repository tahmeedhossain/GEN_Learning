# GEN Learning: University Physics Network

**Live site:** https://tahmeedhossain.github.io/GEN_Learning/ · reader: [`v2/`](https://tahmeedhossain.github.io/GEN_Learning/v2/) · explorer: [`v1/`](https://tahmeedhossain.github.io/GEN_Learning/v1/)

The calculus-based general physics course of OpenStax *University Physics* (Volumes 1–3), written as a growing concept graph of **observables**, **models** and **states** in the reading order of the book, with a concise reading text beside it. It is the fifth instance of the Great Epistemic Network (GEN), after the electromagnetism reader ([GEN_epistemic_evolution](https://github.com/tahmeedhossain/GEN_epistemic_evolution)), the local/global conservation pages ([GEN_LocGlob_Flow](https://github.com/tahmeedhossain/GEN_LocGlob_Flow)), the nonclassicality network ([GEN_GPT_Level](https://github.com/tahmeedhossain/GEN_GPT_Level)) and the quantum resource theory network ([GEN_QRT_Level](https://github.com/tahmeedhossain/GEN_QRT_Level)).

**Why.** Science starts from observations of observables, which hint at the state of a system; the observe → hypothesise → check loop turns hypotheses into models, which give observable outcomes for a given state and the evolution of states. Layering observables, states and models and labelling every edge with its mathematical step turns a large body of physics into edges that can each be checked. GEN uses this to make a field easy to review and to visualise, and to automate research-idea generation (a missing or unverified edge is a candidate question). GEN Learning applies it to teaching: a student sees how each new idea rests on earlier ones, which earlier chapters a chapter really uses, and where classical reasoning gives way to relativity and quantum theory.

## Versions

| Version | Page | What it is |
|---|---|---|
| v2, reader (latest) | [`v2/`](v2/) | A concise physics text (620 paragraphs, 80 195 words, 44 chapters, 314 sections) with the network beside it. As you scroll, each concept appears at the paragraph that introduces it and each link at the paragraph that explains it. Clicking a coloured word, a node, an edge or a link chip opens its explanation together with the paragraph from the text. |
| v1, chapter explorer | [`v1/`](v1/) | The same network stepped through concept by concept, chapter by chapter, with links out to the OpenStax sections and a book map. No text on the page. |

Both pages carry a version switcher (bottom left). See `CHANGELOG.md`.

## Why this book

Young & Freedman and Halliday–Resnick–Krane are copyrighted. OpenStax *University Physics* covers the same calculus-based course, and its source is public on GitHub. Its licence is **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike), stated in the book's preface and in every collection file of the source repository. This work is an adaptation, so it carries the same licence.

## The reading text (v2)

The text is written for this page; OpenStax wording is not reproduced. It follows the book's 44 chapters and 314 sections, chapter introductions included, and introduces exactly the network's concepts in the book's order. Each section links to its OpenStax page for the full treatment, with figures, examples and problems.

- **Format.** The network source files gained three kinds of line: `§` section headers, `P` paragraphs and `Q` display equations (`data/v2/book/*.gen`). Every node record (`N`) and route record (`R`) belongs to the nearest paragraph above it, and that paragraph is where it appears in the graph. Paragraph markup is `[[id]]` or `[[id|text]]` for a concept and `*text*` for a book key term that is not a node.
- **Checked rules** (`scripts/check_book.py`, repeated across all files by `scripts/compile_reader.py`):
  - the network records are identical to the network source;
  - every section has text;
  - a paragraph links every concept it introduces, and the target of every link it introduces;
  - no paragraph links a concept before it is introduced;
  - the markup is well formed.
  
  Unlinked link inputs and paragraphs outside 30–170 words are reported as warnings. The final build has 0 errors and 0 warnings.
- **How it was written and checked.** Chapter 1 was written as the exemplar. The other chapters were written by AI writers following `docs/writing_spec.md`. Five independent AI reviewers then read the whole text for physics errors and recomputed every worked number. They found no definite errors. They flagged 13 imprecisions, all fixed: for example the proportional limit in Hooke's law, the microscope formula marked as approximate, the Penzias–Wilson detection year (1964, reported 1965), and the "closed system" convention.

### Corrections to the network records in v2

The writers and reviewers also found faults in the network records. They are corrected in v2; v1 is left as published.

- Proper length: the description of length contraction said a body is *shortest* in its rest frame. It is *longest*.
- Electron spin magnetic moment: −(e/mₑ)S⃗, not +(e/mₑ)S⃗.
- Lenz's law: the link input is now the first law of thermodynamics (energy conservation in general form), not conservation of mechanical energy.
- Hydrogen radial probability: P(r) = r²|R_nl|², which equals 4πr²|ψ|² only for l = 0.
- Particle conservation laws: the total lepton number is conserved, while the separate electron, muon and tau numbers are broken by neutrino oscillations. The record previously called lepton number "absolute".
- Mutual inductance: it depends on geometry *and* on any magnetic material near the coils.
- Thin films: the phase change of π occurs on reflection from a medium of higher refractive index.
- Reflection from wavelets: both wavelets are in one medium.
- Instantaneous acceleration: the second derivative of x(t), not its "curvature".
- Vector product: it obeys the Jacobi identity instead of associativity.
- Speed of light: exactly 299 792 458 m/s.
- Notation fixes so that subscripts render correctly: A_{x}B_{x}, qv_{d}B, r_{j}ω, I_{CM}ω², nC_{V}ΔT.

## What the network contains

| | Count |
|---|---|
| Concepts (nodes) | 445: 191 observables, 172 models, 82 states |
| Eras | 365 classical, 22 relativistic, 58 quantum |
| Links (routes) | 516: 401 with several inputs (AND), 72 concepts with alternative routes (OR) |
| Route kinds | 411 classical, 8 relativistic, 23 quantum, 13 classical → relativistic, 38 into quantum theory, 17 quantum or relativistic → classical, 6 failed classical predictions |
| Reading steps | v2: 620 paragraphs; v1: 465 events (a new concept, or a new link between known concepts) |
| Book key terms | 1024: 915 drawn as nodes, 40 matched to a node of another section, 69 not drawn (reason recorded for each), 0 unaccounted |

The six failed classical predictions are those the book itself discusses:
- equipartition and the heat capacity of hydrogen (V2 §2.3);
- Galilean velocity addition and the Michelson–Morley result (V3 §5.1);
- the ultraviolet catastrophe (V3 §6.1);
- the wave picture of the photoelectric effect (V3 §6.2);
- the collapsing planetary atom (V3 §6.4);
- the impenetrable classical barrier (V3 §7.6).

## Reading the page (v2)

The reading line sits at about 40 % of the text column. The graph shows the chapter of the paragraph you are reading, as far as that paragraph. Concepts and links introduced in the current paragraph are highlighted; concepts named in it carry a halo. Concepts from earlier chapters appear only when a link made in this chapter uses them. There are three settings: *As needed* (they appear when the first such link is read), *All* and *Hide*. Two more controls: *Whole chapter* shows the complete chapter regardless of reading position, and *Follow* keeps new concepts in view. The card for a concept shows the paragraph that introduces it, the other paragraphs that discuss it, how it is obtained so far (AND/OR), what it feeds into, and optionally where it comes from (1, 2, 3 steps or all). The card for a link shows its formula, inputs and roles, and the paragraph that explains it.

## Repository layout

```
index.html                         project home (GitHub Pages)
v2/index.html                      reader (latest);  v1/index.html  chapter explorer
latest/index.html                  redirect to the latest version
assets/versions.js                 version switcher shown on both pages
versions.json                      list of versions (machine-readable)
data/v2/university_physics_network_v2.json   compiled network with text (schema gen-epistemic-network/2-reader)
data/v2/reader_report.md           compile report: statistics, text per chapter, coverage of every key term
data/v2/coverage.csv               one row per book key term: volume, section, term, status, node or reason
data/v2/book/*.gen                 v2 source: network records + reading text (one file per chapter group)
data/v2/src/*.gen                  v2 network records only, the integrity reference for data/v2/book
data/v1/                           v1 compiled network (schema gen-epistemic-network/1-book), source and coverage
data/openstax_structure.json       book structure and key terms from the OpenStax source (no definitions)
docs/writing_spec.md               rules the text was written to
docs/reader_design.md              design of the reader page
page/reader_v2.html, page/explorer_v1.html   page templates (data injected at __DATA__)
scripts/                           extraction, compilers, checkers, page builds, headless page checks, wrapper
```

## Rebuild

```bash
# v2
B=$(ls data/v2/book/*.gen | tr '\n' ' ')
python3 -I scripts/compile_reader.py data/openstax_structure.json data/v2/university_physics_network_v2.json data/v2/reader_report.md $B
python3 -I scripts/build_reader.py data/v2/university_physics_network_v2.json page/reader_v2.html /tmp/reader.html
python3 -I scripts/wrap_page.py /tmp/reader.html v2 v2/index.html
python3 scripts/check_reader.py /tmp/reader.html data/v2/university_physics_network_v2.json /tmp/shots   # needs playwright + chromium
python3 -I scripts/check_book.py data/v2/book/v1b.gen        # check one text file while editing it

# v1
python3 -I scripts/compile_network.py data/openstax_structure.json data/v1/university_physics_network_v1.json data/v1/coverage_report.md $(ls data/v1/src/*.gen)
python3 -I scripts/build_page.py data/v1/university_physics_network_v1.json page/explorer_v1.html /tmp/explorer.html
python3 -I scripts/wrap_page.py /tmp/explorer.html v1 v1/index.html
```

To re-extract the book structure: `git clone https://github.com/openstax/osbooks-university-physics-bundle`, then `python3 -I scripts/extract_openstax.py osbooks-university-physics-bundle data/openstax_structure.json`.

## Contributing

Corrections to the physics, the text or the links are welcome as issues or pull requests. Edit `data/v2/book/*.gen` (and, for a change to a concept or link record, the same line in `data/v2/src/*.gen`), run `scripts/check_book.py` on the file, then rebuild as above.

## Credits and licence

Source: *University Physics*, Volumes 1–3, senior contributing authors Samuel J. Ling (Truman State University), Jeff Sanny (Loyola Marymount University) and William Moebs; OpenStax, Rice University. Access for free at https://openstax.org/details/books/university-physics-volume-1 (and volumes 2, 3). Licence: CC BY-NC-SA 4.0, https://creativecommons.org/licenses/by-nc-sa/4.0/.

This adaptation (reading text, network data and descriptions) is shared under CC BY-NC-SA 4.0. Prepared with AI assistance (Claude, Anthropic). The text was AI-written and AI-reviewed; the person who publishes it is responsible for the content.

Code (page HTML/JavaScript, `assets/`, `scripts/`) is under the MIT licence; see `LICENSE`. Cite with `CITATION.cff`.

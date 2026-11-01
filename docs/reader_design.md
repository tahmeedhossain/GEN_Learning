# Reader page (version 2): design

> Working document from the build of version 2. Paths here are those of the build folder: `data/book/` and `data/src/` correspond to `data/v2/book/` and `data/v2/src/` in this repository; `build/reference.txt` and `build/review.txt` were working files and are not included.

Goal (the user's words): "as a reader read through the text, the network will evolve and add new nodes and edges. Clicking on nodes and edges explains them, at the same time they see it on textbook." The model is the EM historical reader (`/root/GEN_epistemic_evolution/v3.1/index.html`): text pane plus growing graph, `[[id|text]]` coloured terms, a reading line that sets the step, and a card for nodes and routes. The graph drawing, chapter view, colours and card content come from version 1 (`page/template.html`). Version 1 stays published as it is.

## 1. Source and compiler

- Source: `data/book/v1a.gen … v3c.gen`. These are the network records of `data/src/*.gen` with `§`, `P` (paragraph) and `Q` (display equation) lines added (see `docs/writing_spec.md` and `scripts/check_book.py`). Every N and R record belongs to the nearest P above it in its section.
- `scripts/make_skeleton.py data/src build/skeleton` writes placeholder book files for development. Each section of the book (including x.0) gets one P line per node block or route block, built from labels and descriptions. Every node is linked where it is introduced, and every route paragraph links its target and inputs. The real files replace them when the writers finish.
- `scripts/compile_reader.py <structure.json> <out.json> <report.md> <book files…>` extends `compile_network.py`. It keeps all of its checks and coverage, and adds the checks of `check_book.py` across all files: integrity against `data/src` when the source exists, links, forward links, targets linked, every section with text. Its output is schema `gen-epistemic-network/2-reader`:
  - `paragraphs`: `[{k, vol, ch, section, text, eqs, new_nodes, new_routes, links}]`, where `k` is the global index in reading order, `text` is the raw markup (`[[id|text]]`, `*em*`), `links` are the linked ids in order, and `new_*` are the records bound to this paragraph.
  - `nodes`: as in version 1, but `event` is replaced by `paragraph` (the index where the node is introduced).
  - `routes`: as in version 1, but `event` is replaced by `paragraph`.
  - `chapters`: `[{vol, ch, unit, title, p0, p1, sections: [{num, title, url, p0, p1}], new_nodes, routes, carried_in: [{node, first_needed_paragraph}]}]`. `carried_in` lists earlier-chapter nodes that are an endpoint of a route made in this chapter, as in version 1. `first_needed_paragraph` is the paragraph of the first such route.
  - `stats`: the version 1 statistics, plus `paragraphs` and `words`; also `coverage` and `excluded_terms` as before; `source` (OpenStax credit, CC BY-NC-SA 4.0).
- Route ids stay r1…r516 in record order, which is unchanged from version 1.

## 2. Page `page/reader.html` → `build/reader.html`

Same contract as version 1: one self-contained file, with data injected at `__DATA__` by `scripts/build_reader.py`. Google Fonts only, no other external resources (D3 is not needed). Theme tokens in light and dark, on `:root`, `@media (prefers-color-scheme: dark)` with the `:root:not([data-theme="light"])` guard, and `:root[data-theme="dark"]`, with an explicit body background. No horizontal page scroll at 390 px. Title "University Physics Network". Keep version 1's colour tokens, shapes and fonts.

### Layout, desktop (≥ 900 px)

- Header row: title; chapter select (all 44 chapters, "V1 · 5 Newton's Laws of Motion"); previous and next chapter buttons; Key; Theme.
- The book arc map from version 1 sits under the header as a compact rail (about 64–80 px): volume groups and chapter ticks, with the current chapter marked and arcs from the earlier chapters that feed it. Clicking a chapter scrolls the reader to that chapter's start.
- Main area, two columns as in the EM reader: the **reader** on the left (`minmax(380px, 44%)`, scrolling) and the **graph pane** on the right.
- Reader: the whole book as one continuous scroll. Volume heading, then for each chapter a chapter heading ("Chapter 5" and the title), then sections (heading "5.1 Forces" with a small "OpenStax ↗" link to the section's page). Paragraphs are serif, with coloured term buttons in the EM `.term` style (amber O, violet M, teal S; a vermilion ring for quantum, a green ring for relativistic). Display equations sit in a centred math box under their paragraph. Under a paragraph that introduces routes, a small muted line shows the route titles as clickable chips, each with a short arrow in its route colour (AND, OR, quantum, relativistic, failed). Bottom padding of about 55 vh lets the last paragraph reach the reading line.
- Graph pane:
  - Caption: chapter and the current section ("§5.3 Newton's Second Law · paragraph 2 of 3").
  - Controls: Earlier chapters (As needed / All / Hide, as in version 1), Whole chapter (checkbox: the chapter's complete graph, independent of the reading position), Follow (checkbox: keep the newest nodes in view), Key.
  - Below that, sticky column heads (Models | States | Observables) and the scrolling SVG, with the version 1 layout, section bands, anchors, AND junctions, OR colours, era gradients and failed ✕.
- Card: an overlay at the right of the graph pane (EM style, about 360 px wide, closable, Esc closes). On a phone it is a bottom sheet.

### Reading position

- The reading line sits at 38 % of the reader's height (desktop). The current paragraph `k` is the last one whose top is above the line; at the very end it is the last paragraph. Update with requestAnimationFrame on scroll.
- The current chapter is the chapter of `k`. The graph shows that chapter's nodes with `paragraph ≤ k`, plus the carried-in nodes: As needed shows those with `first_needed_paragraph ≤ k`, All shows all of them, Hide shows none. It also shows the chapter's routes with `paragraph ≤ k` whose target and at least one input are visible. Traces work as in version 1, using introduction-time routes (`paragraph` instead of `event`).
- Fresh: nodes and routes introduced at `k` get the fresh style (thicker stroke and a one-time pulse; none under reduced motion). Nodes linked in paragraph `k` get the focus halo (EM `.focus`).
- The active paragraph has a coloured left border. The current section's band in the graph is emphasised.
- Layout stability: positions are computed per chapter from all of the chapter's nodes and all carried-in nodes, as in version 1, so nodes never jump as reading proceeds. In the earlier band, order nodes by `first_needed_paragraph` so that slots fill in reading order. Crop the SVG height to the lowest visible element plus padding, so there is no long empty area below.
- Follow: when new nodes appear, scroll the graph pane smoothly so the fresh nodes are visible. Do nothing if they already are.
- Remember the reading position and settings in localStorage, inside try/catch. A hash `#v1c5` on load jumps to that chapter; update the hash with `history.replaceState` when the chapter changes.

### Selection: nodes and edges explained with the text alongside

- Clicking a term in the text, a node in the graph, or a chip in the card selects that node. The card shows:
  - Type and era badges, the symbol (via `fmt`), the label and the description.
  - The math structure (states) and properties (models).
  - "In the text": the paragraph that introduces the node, rendered with its terms, the selected term marked, and labelled "§5.3, paragraph 2". A "Go to this paragraph" button scrolls the reader there.
  - "Discussed in": the other paragraphs that link it, as snippets with section labels, clickable. A paragraph after the reading position is shown faded.
  - "How it is obtained so far" (routes into it with `paragraph ≤ k`: AND/OR, route blocks) and "Feeds into".
  - "Show where it comes from" (trace depth 1/2/3/all), as in version 1.
  - Book key terms and the OpenStax link of its section.
  - For a node from an earlier chapter that is not drawn in this chapter's view, the card says so ("from V1 Ch 3; no link in this chapter uses it").
- Clicking an edge, an AND junction, or a route chip under a paragraph selects that route. The card shows the title, kind (classical, relativistic, quantum, crossings, failed), tags, formula, description, the target, the inputs with their roles, and "In the text": the paragraph that introduces the route, with the endpoints' terms marked and a "Go to this paragraph" button. Clicking one input edge also shows that input's role, as in EM `selEdge`.
- The text highlights the selection: every visible mention of the selected node gets the selected style (a solid outline). For a route, the mentions of its endpoints are marked and its introducing paragraph gets a side mark.
- Hovering a term halos the node in the graph. Hovering a node gives its visible mentions in the text a light background.
- In the graph, selection dims what is unrelated, as in version 1 and EM.

### Phone (< 900 px)

The EM pattern applies. The graph pane is sticky at the top (about 46 vh) with compact controls. The reader follows, scrolling with the window, and its reading line sits 30 % below the graph. The arc map is hidden, and chapter navigation is the select box. The card is a bottom sheet with a maximum height of 56 vh.

### Key

The version 1 legend: shapes, AND/OR, era colours and gradients, failed ✕, fresh and focus. It explains in one sentence that the network grows as the reader reads, and that earlier-chapter nodes appear only when a link in this chapter uses them.

### Footer and credit

At the end of the reader: "The text is written for this page and follows the section structure of OpenStax University Physics (Ling, Sanny, Moebs; OpenStax, Rice University), CC BY-NC-SA 4.0; each section links to the book. The network data and text are shared under the same licence. Prepared with AI assistance (Claude, Anthropic)."

## 3. Checks (`scripts/check_reader.py`, Playwright Chromium)

- Screenshots: desktop 1440×900 light, 1024×768 light, phone 390×844 dark, at several reading positions (Ch 1 start, mid V1 Ch 5, V3 Ch 6 where failed routes appear).
- No console errors, and no horizontal overflow on the phone.
- Scrolling to paragraph k gives exactly the expected number of visible nodes, computed from the data.
- Clicking a term opens the card with the right label and the "In the text" paragraph. Clicking an edge opens the route card. Esc closes.
- Chapter select and map clicks scroll to the chapter. The earlier-chapters modes change the visible counts as expected.

# Writing the reading text of the University Physics network

> Working document from the build of version 2. Paths here are those of the build folder: `data/book/` and `data/src/` correspond to `data/v2/book/` and `data/v2/src/` in this repository; `build/reference.txt` and `build/review.txt` were working files and are not included.

## What this is for

The page is a reader in the style of the Great Epistemic Network's electromagnetism reader. On the left is a textbook text. As the reader scrolls, the network on the right grows. Each concept (node) appears at the paragraph that introduces it. Each link between concepts (route) appears at the paragraph that explains it. Clicking a coloured word in the text, or a node or edge in the graph, opens its explanation, and the paragraph that introduces it is shown with it.

The text is an original, compact general-physics textbook. It follows the chapter and section structure of OpenStax *University Physics* Volumes 1–3, so each section can link to the matching OpenStax page. The network already exists: 445 nodes and 516 routes in `data/src/*.gen`, placed section by section in the book's order. Your job is to write the text for one source file, so that the existing nodes and routes are introduced and explained in readable prose.

## Files

- Read-only: `data/src/<name>.gen` (the network records of your chapters), `build/review.txt` (every node and route of the whole book, chapter by chapter; grep it for ids of earlier concepts), `build/reference.txt` (each section's title, learning objectives and the book's key terms in order of appearance), `data/openstax_structure.json`.
- You write `data/book/<name>.gen`. If it does not exist, start it as an exact copy of `data/src/<name>.gen` (`cp`). Then insert reading-text lines. Do not touch any other file in the project.

## The three kinds of line you add

```
§ <vol> <ch>.<sec>     a section header, for every section of your chapters that has no § line yet,
                       including the chapter introduction <ch>.0; insert it at its place in book order
P <paragraph text>     one paragraph, on one line
Q <display equation>   optional; shown centred under the paragraph above it (at most two per paragraph)
```

Never change, reorder, add or delete any existing line that starts with § N d m p g R > X. The checker compares your file with the source and reports any difference.

## How paragraphs bind to the network

1. Every `N` record (a node, with its `d m p g` lines) and every `R` record (a route, with its `>` lines) belongs to the nearest `P` line above it in the same section. That paragraph is where the node or route appears in the graph.
2. Each section therefore needs a `P` line before its first `N` or `R` record. To spread a section's records over several paragraphs, insert further `P` lines between complete records. Never insert a `P` line between an `N` line and its `d/m/p/g` lines, or between an `R` line and its `>` lines.
3. A paragraph must link every node introduced under it, with `[[id]]` or `[[id|text]]`.
4. A paragraph must link the target of every route introduced under it. It should also link every input of the route. The checker warns about unlinked inputs, so explain the route with its inputs named.
5. A paragraph may link any node already introduced: earlier in your file, under the same paragraph, or in an earlier source file (earlier chapters; find ids in `build/review.txt`). It must not link a node introduced later. Name later concepts in plain words if you must mention them.
6. Because the record order is fixed, the paragraphs follow it. If a section's records are A, B, C, the paragraph that introduces B cannot come before the one that introduces A. Put records in one paragraph when the prose needs them together. Within a paragraph, mention them in any order.

## Markup

- `[[id]]` shows the node's label; `[[id|text]]` shows your text. Use the second form for natural grammar: `[[v|instantaneous velocity]]`, `[[F|forces]]`, `[[n2|Newton's second law]]`. Link text names the concept; never link "this" or "it".
- Link a concept where it first matters in a paragraph; do not link every repetition. Linking an earlier concept again in a later section is good when the paragraph uses it.
- `*text*` for emphasis, for book key terms that are not nodes. Nothing else: no HTML, no Markdown headings, bold, lists or links. Do not use `*` for multiplication.
- Math inline, in Unicode: × · − ± ≈ ≠ ≤ ≥ ∝ ∞ ∫ ∮ ∂ ∇ Δ δ √ ∑ π θ φ ω λ μ ε ρ σ τ, and so on. Use the minus sign "−" (U+2212) in formulas.
- Subscripts and superscripts: Unicode where it exists (x₀, v₁, m², 10⁻³, s⁻¹); otherwise `_{...}` and `^{...}`. An unbraced `_` or `^` applies to the whole following run of letters and digits, so write `v_{0}t`, not `v_0t`; `F_net` renders as F with subscript "net".
- Vectors: letter followed by the combining arrow U+20D7, written `F⃗`, `v⃗`, `p⃗`, `r⃗`, as in the node symbols. Unit vectors î ĵ k̂.
- Use the same symbols as the node symbols and route formulas of the network.
- A display equation (`Q`) holds a formula only, with no links. Use it for a section's key result.

## Structure and length

- Chapter introduction (`§ v ch.0`): one paragraph of 50–110 words, saying what the chapter is about and how it follows from what came before. It may link earlier nodes. It links this chapter's nodes only if the source puts records in the `.0` section.
- Content sections: 1–4 paragraphs, depending on how much the section introduces. As a rough guide, one paragraph covers 1–3 nodes and their routes.
- A section with no records still gets one paragraph of 50–130 words on what the section does, such as an application, a problem-solving strategy or a device. Link the existing nodes it uses.
- Paragraphs: 40–150 words. The checker warns below 30 or above 170.
- Use the book's key terms of each section (`build/reference.txt`, "terms in order") in the text. Link a term if it is a node; otherwise put it in *emphasis* where it is defined or first used.

## Content and style

- **Original wording.** Do not copy or closely paraphrase OpenStax sentences, learning objectives or examples. Use `build/reference.txt` only to see what a section covers. Write as an independent compact textbook with your own explanations and your own small examples.
- **Explain the logic the network encodes.** Say what is measured or defined (observables), what law or mathematical structure relates quantities (models), and what describes the system (states). Say how each route follows. For a definition, say what is defined. For a law, say what experiment establishes. For a derivation, give the key step. For an approximation, state the condition. For a limit, name the limit. For a generalisation, say what it generalises. For a measurement, say how the quantity is measured. For a failed prediction, give the classical argument, what is observed instead, and what this forced.
- **Era changes.** When a relativistic or quantum concept enters, state the new postulate or result and the classical limit where the route gives one.
- **Precise and plain.** Short declarative sentences, one idea per sentence. No rhetoric, no exclamation marks, no "fascinating", "remarkably", "let's", "dive", "journey", "powerful". Use "we" sparingly. Use transitions between paragraphs and sections, but no filler.
- **Correct physics.** State conditions of validity: constant acceleration, small angles, ideal gas, quasi-static process, non-relativistic speed, and so on. Work in SI. Small worked numbers are welcome but must be exact; check the arithmetic. Use standard values, for example:
  g = 9.80 m/s², G = 6.674 × 10⁻¹¹ N·m²/kg², c = 3.00 × 10⁸ m/s (exactly 299 792 458 m/s), h = 6.626 × 10⁻³⁴ J·s, ħ = 1.055 × 10⁻³⁴ J·s, e = 1.602 × 10⁻¹⁹ C, mₑ = 9.11 × 10⁻³¹ kg, mₚ = 1.673 × 10⁻²⁷ kg, k_B = 1.381 × 10⁻²³ J/K, N_A = 6.022 × 10²³ mol⁻¹, R = 8.314 J/(mol·K), σ = 5.67 × 10⁻⁸ W/(m²·K⁴), ε₀ = 8.854 × 10⁻¹² C²/(N·m²), k = 1/(4πε₀) = 8.99 × 10⁹ N·m²/C², μ₀ = 4π × 10⁻⁷ T·m/A (to better than one part in 10⁹), 1 eV = 1.602 × 10⁻¹⁹ J, 1 u = 1.661 × 10⁻²⁷ kg, 1 atm = 1.013 × 10⁵ Pa, Earth M = 5.97 × 10²⁴ kg and R = 6.37 × 10⁶ m.
- **History.** Name people and years only when you are certain. Otherwise leave them out.
- **Agree with the records.** Use the same formulas and conditions as the node descriptions and route formulas. If you think a record is wrong, do not edit it. Write the text correctly and report the record (file:line, what is wrong) in your final message.
- **Do not mention the network,** nodes, routes, colours or the page. The text is a textbook.

## Check

```
python3 -I scripts/check_book.py data/book/<name>.gen
```

Fix every error. Keep warnings rare and deliberate. An unlinked route input should have a reason.

## Exemplar

Chapter 1 of `data/book/v1a.gen` (sections 1.0–1.7) shows the intended format, density and tone.

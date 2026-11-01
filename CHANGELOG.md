# Changelog

## v2.0, reader (2026-10-26; published here 2026-11-01)

- New page: a concise reading text (620 paragraphs, 80 195 words; 44 chapters, 314 sections including chapter introductions) with the network beside it. Scrolling sets the reading position; each concept appears at the paragraph that introduces it and each link at the paragraph that explains it.
- Coloured terms in the text, nodes, edges, AND junctions and link chips under paragraphs open a card that shows the explanation together with the introducing paragraph, other paragraphs that discuss the concept, routes into it so far, what it feeds, and its ancestry (1, 2, 3 steps or all).
- Chapter view kept from v1: earlier-chapter concepts appear only when a link in the current chapter uses them (as needed / all / hide); new controls Whole chapter and Follow.
- Source format: `data/v2/book/*.gen` adds `§`, `P` and `Q` lines to the network records; schema `gen-epistemic-network/2-reader`.
- Corrections to network records (listed in README): proper length, electron spin moment sign, Lenz's law input, hydrogen radial probability, lepton-number conservation, mutual inductance, thin-film phase change, reflection wavelets, instantaneous acceleration, Jacobi identity, exact speed of light, subscript notation.

## v1.0, chapter explorer (2026-10-26)

- 445 concepts and 516 links placed section by section in the book's order, checked against the book's 1024 key terms.
- Chapter view with earlier-chapter concepts shown only when used; step-by-step reveal; book arc map; concept and link cards; links out to OpenStax sections.

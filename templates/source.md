---
type: source
bibkey: ""
doi: ""
zotero_key: ""
title: ""
year: ""
authors: ""
venue: ""
domain: ""
relevance: ""
read_status: ""
project: ""
created: ""
tags:
  - source
related: []
---

<!--
One note per paper. The filename should be the bibkey.

REQUIRED
  bibkey       the identifier this paper carries everywhere else: your .bib
               entry key, the pinned Citation Key in Zotero, the row in your
               library table. This is the spine; get it wrong and nothing lines
               up.

STRONGLY RECOMMENDED
  doi          without it, cross-registry matching falls back to comparing
               normalised titles, which is less reliable
  zotero_key   from: python -m ledger.zot find --doi <DOI>

read_status deserves an explicit vocabulary. Distinguish at minimum:
  full         you read the whole thing
  partial      you read the sections that mattered
  abstract     you read the abstract only

That last value matters more than it looks. An abstract-only note must never
carry an argument: abstracts routinely omit which assumptions hold, which port
or frame a result is stated in, and what the authors themselves flag as
limitations. Keep the distinction visible so you cannot forget it later.

必填 bibkey；强烈建议填 doi 与 zotero_key。read_status 请显式区分
full / partial / abstract —— 仅摘要级的笔记绝不可承载论证。
-->

# <!-- title -->

## Record

- **bibkey**: `` — matches your `.bib` entry and the pinned key in Zotero
- **Year / first author / venue**:
- **Where the file is**:

## The claim, in one sentence

<!-- What does this paper actually assert? Not what it is "about" — what it
claims to have established. If you cannot write this line, you have not
finished reading. -->

## Key equations / method

<!-- Quote equation numbers from the original so you can find them again.
Copy the authors' own wording for anything you might later cite; paraphrase
drifts, and drifted paraphrase is how misattribution happens. -->

## Scope and assumptions

<!-- The part abstracts leave out, and the part reviewers ask about:
  - what is assumed to hold, explicitly and implicitly
  - the range (frequency, gain, amplitude, operating point) where it holds
  - simulation, hardware, or both
  - which port / frame / coordinate system results are stated in
A result can be entirely correct and still not apply to your case. -->

## Relation to my work

<!-- Which specific argument does this support, threaten, or bound?
Be concrete: name the section or claim of yours it touches.

If it looks like a threat, check whether it actually is. A paper whose title
closely resembles your contribution can turn out on a full read to support it,
because the mechanism, the port, or the assumptions differ. The reverse also
happens. -->

## Annotation evidence

<!-- Generate with:
     python -m ledger.zot annotations <zotero_key>

These are the passages YOU chose to highlight while reading. That is a different
and more trustworthy signal than a model's guess at what mattered. Keep the page
numbers. -->

## Related notes

- [[]]

## Notes

<!-- Author-declared limitations (often the most citable thing in a paper).
Open questions. Which reference you still need to chase, and why. -->

# Study-Module Contract

> **Experimental, pre-1.0 contract.** The contract and prompts may change. The public repository
> does not bundle a generic study-module validator. If no course-specific validator is
> configured, an executor must stop rather than claim validation. Do not scale generation until
> one pilot module, a working validator, and independent subject-matter review exist.

A **study module** is the unit of output for the [study-layer workflow](study-layer-workflow.md):
a bounded set of exactly five files covering one topic block of a unit, generated from a curated,
hash-verified private source pack. This document defines the contract every module follows,
using only fictional placeholders — no example here refers to any real unit, file, or question.

```text
<ignored-course-root>/study/<topic-slug>/
├── STUDY_GUIDE.md
├── QUESTION_BANK.md
├── ANSWER_KEY.md
├── COVERAGE_MATRIX.md
└── source-map.json
```

Every module uses exactly these five files. A module should not add extra files "for
convenience" — if something doesn't fit one of the five, it usually belongs inside one of them,
or it's evidence the module's scope is too broad.

## File responsibilities

### `STUDY_GUIDE.md`

A revision-oriented explanation of the topic, organized into numbered sections, built only from
the curated sources selected for this module. Every substantive claim carries a tag (below).
A guide typically closes with a "common errors" section and a skills checklist — both useful
anchors for the question bank and for a later error-diagnosis question type.

### `QUESTION_BANK.md`

Active-recall questions, grouped into named sections (e.g. "Definitions and recall," "Error
diagnosis," "Exam-style mixed problems"). Every question has a stable ID, a difficulty, a type,
at least one source citation, and a data-needed classification (see [Question
metadata](#question-metadata)).

### `ANSWER_KEY.md`

Exactly one answer per question ID, in exact 1:1 correspondence with `QUESTION_BANK.md` (see
[Question/answer parity](#questionanswer-parity)). Calculation answers show independently
recomputed working, not a copied source figure.

### `COVERAGE_MATRIX.md`

Maps concepts to sources and to question IDs; records which concepts are strongly covered, which
appear only once, which source material has no matching question, which questions rest on
synthesis rather than direct source statement, and any known gaps or limitations — including
explicit statements about what assessment-relevance claims the module can and cannot support.

### `source-map.json`

The machine-checkable provenance record: every mapped source (with its stable ID, curated path,
and content hash), every deliberately excluded source (with a reason), and which of the module's
own artifacts cite which source IDs. This file is what a validator actually checks against.

## The `[S]` / `[E]` / `[H]` tagging convention

Every substantive line in `STUDY_GUIDE.md` (and, where useful, in `ANSWER_KEY.md`) carries one of:

- **`[S]`** — *source-supported*: stated directly in a cited source.
- **`[E]`** — *explanatory synthesis*: the module author's joining-up of source statements, or a
  direct algebraic/logical consequence of a boxed `[S]` result. Not a quotation, and worth
  independent verification.
- **`[H]`** — *heuristic*: a suggested problem-solving habit, not something the source itself
  asserts as doctrine.

This distinction exists so a reader can tell, line by line, what is directly attributable to a
source versus what the module's own reasoning added — and so a later reviewer can specifically
audit the `[E]` lines, which are where an error is most likely to have been introduced.

## Stable question IDs

- Each module uses its own short, unique namespace (2–4 letters), e.g. `TOPIC-DR-01`,
  `TOPIC-EX-03` for a module namespaced `TOPIC`.
- IDs combine namespace, a two-to-three-letter section code, and a running number:
  `<NAMESPACE>-<SECTION>-<NN>`.
- **A question ID, once written, is never renumbered or reused for a different question.** Other
  artifacts (a course-level revision plan, a later module's descriptive cross-reference) may cite
  it by exact ID; renumbering silently breaks every such reference with no mechanical way to
  detect that the break was intentional.
- A subpart reference like `TOPIC-EX-01(c)` is acceptable in prose and resolves against the
  top-level ID with the subpart suffix ignored.

## Stable source IDs

- Each curated physical file gets a short, stable source ID (e.g. `LEC-TOPIC-01` for a lecture,
  `TUT-TOPIC-01` for a tutorial's question sheet).
- If a later module reuses the **same physical file** (for example, a shared lecture that covers
  two topics), it reuses that file's existing source ID unchanged — this is expected and is not a
  defect. A source ID should never refer to two different physical files across modules.
- Excluded sources (curated files considered but not used) are recorded too, each with an
  explicit reason — "inspected, contains no relevant content" is a legitimate reason and should
  be stated plainly, not omitted.

## Question metadata

Every question in `QUESTION_BANK.md` states:

| Field | Meaning |
|---|---|
| Difficulty | e.g. `foundational`, `intermediate`, `advanced` |
| Type | e.g. `recall`, `conceptual`, `calculation`, `error diagnosis` |
| Source | one or more source IDs the question traces to — never empty, even for a self-contained numeric question, since the *skill or structure* being tested still comes from a source |
| Data needed | a fixed small vocabulary, e.g. `none` (answerable from understanding alone), `given` (every number needed is stated in the question), `tables` (a value must be looked up in a reproduced source table) |

## Question/answer parity

`ANSWER_KEY.md` must contain exactly one answer per question ID in `QUESTION_BANK.md`, and no
answer for an ID that doesn't exist there. This is checked mechanically (an ID-set comparison),
not just asserted, before a module is considered complete.

## `source-map.json` requirements

- Valid JSON, with a `sources` array (mapped sources) and an `excluded_sources` array.
- Every mapped source: a stable `source_id`, a curated path relative to the course root (never an
  absolute path), a content hash matching the curation manifest, and enough locator detail
  (page/section) to find the specific material used.
- Every excluded source: the curated path and a specific reason; a hash is recorded where
  available, but its absence is a warning, not a hard failure, since an excluded source's
  provenance is lower-stakes than a mapped one's.
- An `artifacts` section (or equivalent) recording which of the module's own Markdown files cite
  which source IDs, so a validator can cross-check citations against the map rather than trusting
  prose alone.

## Mapped versus excluded sources

A source being **excluded** is not itself a defect — it is a documented scoping decision. What
matters is that the exclusion is explicit and reasoned ("inspected in full; contains only
administrative/assessment-structure content, no topic-relevant material") rather than silent. A
reader should be able to tell, from `source-map.json` alone, exactly which curated files this
module drew from and which it deliberately set aside, and why.

## Relative paths and hash provenance

- Every path inside a module's artifacts is relative to the course root — never an absolute
  filesystem path.
- Every mapped source's hash is re-checked against the curation manifest **and** against the file
  currently on disk at generation time; a mismatch anywhere in that chain is treated as a hard
  error, not a warning.

## Treatment of unavailable data

If a question would require data that does not exist anywhere in the curated pack (a table range
never reproduced, a value never published), the module does not invent it. Choices, in order of
preference:

1. Don't write the question — design an equivalent question using data that **is** available.
2. Write the question with a symbolic/procedural answer instead of a specific numeric one, if the
   method is still worth testing.
3. If a source's own published answer can't be independently verified for this reason, record
   that explicitly (see [Source discrepancies](#source-discrepancies)) rather than silently
   reproducing an unverified figure as if it were checked.

## Synthesis-heavy questions

Some questions necessarily combine more than one source statement, or extend a source's own
worked example's structure to a new (but equivalent) case. These are legitimate, but must be
flagged — typically in `COVERAGE_MATRIX.md`, naming the specific question ID and describing
exactly what synthesis step it rests on — so a reader can tell "this is a direct source
transcription" from "this required a documented additional step" at a glance.

## Source discrepancies

When an independently recomputed answer disagrees with a source's own published figure, that
disagreement is **recorded, not silently corrected**. Distinguish, explicitly:

- a **confirmed discrepancy** in the source itself (e.g. a labelling inconsistency in a published
  answer), stated as an observation about the source, not as "the source is wrong, use my number
  instead";
- an **unresolved precision limitation**, where the method is independently confirmed sound (for
  example, against an adjacent worked example using the same governing relations) but the
  specific published figure can't be reproduced at the source's own numeric precision;
- **missing source data**, where no comparison is even possible because the required value was
  never published anywhere in the curated pack.

## Cross-module reference rules

When one module's prose needs to refer to another module's content, use **descriptive prose**
("the prerequisite module's steady-state balance equation"), never a bare question or source ID
token from a module that isn't the one being written. A bare ID-shaped token is exactly what a
validator's cross-reference check looks for, and a token belonging to a different module's
namespace will not resolve inside this module's own `source-map.json` or `QUESTION_BANK.md`.

## Prohibition on silently renumbering stable IDs

Once a module has been generated and any other artifact (a course-level index, a later module's
prose, a student's own notes) might reference one of its question or source IDs by exact value,
**that ID is permanent.** If a question turns out to be wrong or needs replacing, retire it
explicitly (state that it was retired and why) rather than reusing its ID for different content,
and add a new question under a new ID rather than renumbering.

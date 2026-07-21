# Study-Layer Validation Model

> **Experimental, pre-1.0 model.** This describes the intended checks; the public repository
> does not bundle a generic study-module validator. If no course-specific validator is
> configured, an executor must stop rather than claim validation. Do not scale module generation
> until one pilot module, a working validator, and independent subject-matter review exist.

A study module (see [`docs/study-module-contract.md`](study-module-contract.md)) is checked at
two distinct layers that must not be conflated: **mechanical validation** (structure and
provenance) and **subject-matter validation** (correctness and quality). This document describes
both, and the rules governing how defects found by either are handled.

## Mechanical validation

Mechanical validation is what an automated, subject-agnostic tool can check without understanding
the topic at all. A reusable validator for this layer typically checks:

- **Required files.** All five contract files present, readable, and non-empty.
- **Valid JSON.** `source-map.json` parses and matches its expected schema (required fields,
  array shapes, no unexpected top-level keys).
- **Source-ID resolution.** Every source ID cited anywhere in the module's Markdown files
  resolves to an entry in `source-map.json`'s mapped sources — including a citation used as a
  question's `Source` field, not just prose references.
- **Hash reconciliation.** Every mapped source's recorded hash matches both the curation
  manifest's record for that file and the file's current on-disk content; a mismatch anywhere in
  that three-way chain is an error.
- **Question metadata.** Every question has a valid difficulty, a stated type, at least one
  resolvable source ID, and a valid data-needed classification.
- **Answer parity.** Every question has exactly one answer, and vice versa.
- **Coverage references.** Every question ID and source ID referenced from the coverage analysis
  (and from any cross-references between the module's own files) resolves.
- **Stated-count consistency.** Where a coverage analysis states a mechanical count (questions
  generated, counts by section/difficulty/data-needed), that count is recomputed independently
  and compared — a stated count that doesn't match a fresh recount is an error, not a rounding
  note.
- **Relative-path safety.** No absolute filesystem path, home-directory path, drive-letter path,
  or path-traversal sequence appears in a curated path or a generated artifact.
- **Sensitive-content scan.** A conservative sweep for patterns shaped like emails, phone numbers,
  authentication/session tokens, or student-identity/grade data — deliberately permissive enough
  to avoid false confidence, and expected to occasionally flag ordinary prose for human judgment
  rather than silently pass it.
- **Internal-link checks**, where the module (or a course-level layer built from several modules)
  contains relative Markdown links: every link should resolve to a real file.

### Error versus warning

- **Errors** are things that make a module's own claims about itself internally inconsistent or
  factually wrong: a broken hash, an unresolved ID, a missing answer, a stated count that doesn't
  match a recount, an absolute or escaping path. These block the module from being considered
  complete.
- **Warnings** are worth a human's attention but don't block completion: an unexpected extra
  file, a sensitive-content pattern that may well be ordinary prose, an excluded source missing a
  recorded hash, or a near-miss ID-shaped token that doesn't quite match the expected pattern.

Every diagnostic should carry a stable code, a severity, an affected file, a line where
available, and a human-readable message — both for a human reading the output and for any
downstream tool consuming a machine-readable (e.g. JSON) form of the same result.

### The no-weakening rule

**When a mechanical check reports a genuine defect, fix the module's content — never loosen,
bypass, or remove the check to obtain a passing result.** A validator that can be satisfied by
weakening itself provides no actual guarantee. If a check turns out to be based on a wrong
assumption about a legitimate pattern (for example, a subpart reference like `TOPIC-EX-01(c)`
that should resolve against its parent ID), the correct fix is to make the check's understanding
of that pattern more precise — not to disable the check.

## Subject-matter validation

Subject-matter validation is what a mechanical tool cannot do: it requires actually understanding
the topic. This layer is not automated by the reusable validator and must be performed
separately, typically by the same process (human or model) that generated the module's content.

- **Independent numeric recomputation.** Every generated numeric answer should be recomputed
  independently — not re-derived from memory of how it was first computed, and not simply
  eyeballed for plausibility. A disposable verification script is a reasonable way to do this; see
  [`docs/study-layer-workflow.md`](study-layer-workflow.md) for how that fits into the broader
  lifecycle.
- **Equation and assumption review.** For each calculation, confirm the governing relation is the
  correct one for the stated conditions, and that every simplifying assumption (steady state,
  negligible term, ideal behavior, reversibility, or an equivalent in a non-numeric subject) is
  actually justified by the question as posed, not merely convenient.
- **Units and sign/notation conventions.** Confirm consistency throughout a multi-step
  calculation or derivation — a subject-specific convention (a sign convention, an absolute-vs-
  relative scale, a notation convention) should be applied the same way in every question that
  uses it.
- **Source-answer comparison.** Wherever a source publishes its own answer to a question a module
  adapts or references, that published answer should be independently checked, not assumed
  correct or silently trusted. See the [contract's source-discrepancy
  guidance](study-module-contract.md#source-discrepancies) for how to record a disagreement once
  found.
- **Handling ambiguity and missing data.** Where the source material is ambiguous or a needed
  value simply isn't available anywhere in the curated pack, that must be surfaced explicitly —
  see the [contract's unavailable-data
  guidance](study-module-contract.md#treatment-of-unavailable-data) — rather than resolved by
  invention.
- **Pedagogical review.** Beyond correctness: are questions genuinely testing the concept they
  claim to, is the difficulty labelling reasonable, does the question bank actually exercise the
  concepts the coverage analysis claims it does, and is any question a near-duplicate of another
  in a way a human reviewer would object to.

## What mechanical validation cannot establish

**Passing mechanical validation is necessary but not sufficient.** It says nothing about whether:

- the subject-matter reasoning in a guide or answer key is actually correct;
- a numeric answer is scientifically/mathematically correct;
- a question is pedagogically good, well-targeted, or meaningfully distinct from another;
- an `[S]`/`[E]`/`[H]` synthesis classification is intellectually justified, rather than merely
  present;
- a module actually, fully covers a named assessment — this is a claim about the world a
  mechanical tool has no way to check, and a module should never assert it does without an
  explicit, bounded qualification (e.g. "if this assessment draws only on the material this
  module covers").

Treat a passing mechanical validator run as confirmation that a module is **structurally and
provenance-sound** — and nothing more. Subject-matter review is a separate, equally necessary
step, not a formality to skip once the mechanical check is green.

# Generate a Study Module

> **Experimental, pre-1.0 prompt.** The five-file contract and these instructions may change.
> The public repository does not bundle a generic study-module validator. If the target course
> has no configured validator, stop rather than claim validation or completion. Do not scale
> generation beyond a pilot until a validator and independent subject-matter review exist.

## Prompt

Create one bounded study module for **[topic name]** in **[unit/course identifier]**, under the
private course root **[path to ignored private course root, e.g. `private/courses/<course-code>/`]**.

Follow the [study-layer workflow](../docs/study-layer-workflow.md) and the
[study-module contract](../docs/study-module-contract.md). This produces exactly five files
under `<course root>/study/[topic-slug]/`:

```text
STUDY_GUIDE.md
QUESTION_BANK.md
ANSWER_KEY.md
COVERAGE_MATRIX.md
source-map.json
```

Use the question-ID namespace **[2-4 letter namespace, e.g. `TOPIC`]** for this module, and
confirm it is not already used by another module in this course before starting.

## Repository boundaries

- Work only under the ignored private course root given above. Do not modify the public
  repository tree, any already-completed study module, the curation manifest, or the validator
  implementation.
- Do not install dependencies. Do not stage, commit, or push anything — no commit is authorized
  by this prompt alone.
- Inspect `git status --short` before and after. If any change appears outside the new module's
  own directory, stop and report it before proceeding.

## Required inspection, before writing anything

- The course's curation manifest, to identify which curated source files are candidates for this
  topic, and to obtain each candidate's recorded content hash.
- Every candidate lecture, tutorial, and (where relevant) laboratory source for this topic —
  read in full, not skimmed. Hash-verify each one against the manifest before treating its
  content as trustworthy.
- Any already-completed module in this course, to reuse its conventions (header format, tagging
  style, source-ID reuse for any shared physical file) rather than inventing a new variant.
- The unit outline and program calendar (or equivalent), only for the scheduling/scope context
  needed to state where this topic sits — not to be treated as technical content.

**Do not open, or reason about the content of, any quiz, test, or exam attempt.** Scheduling
information (which week a topic is taught, when an assessment is due) may be recorded; assessment
*content* must never be inspected or assumed.

## Content requirements

- Tag every substantive `STUDY_GUIDE.md` claim `[S]` (source-supported), `[E]` (explanatory
  synthesis), or `[H]` (heuristic), per the contract.
- Give every source a stable ID; reuse an existing module's source ID unchanged if the same
  physical file is being cited again.
- Give every question a stable ID that will never be renumbered, with a difficulty, a type, at
  least one resolvable source citation, and a data-needed classification.
- Where this module needs a concept from an earlier module, cite it **descriptively** — never by
  a bare cross-module question or source ID.
- Do not invent numeric values, table entries, or source facts that are not present in the
  curated pack. If a needed value is unavailable, say so explicitly rather than fabricating it.
- Independently recompute every generated numeric answer before writing it into `ANSWER_KEY.md`
  — a disposable verification script is an acceptable and recommended method, but delete it once
  its results are transcribed. Independently check every source-published answer this module
  reproduces or adapts, and record any disagreement rather than silently resolving it.

<!-- Subject-specific validation requirements: replace this block with the checks that matter
     for this particular subject before running the executor — e.g. a list of specific reasoning
     errors to screen for, unit/notation conventions to enforce, or a class of problem requiring
     a particular verification method. Leave unresolved if the subject has no such list yet. -->

**[Subject-specific validation requirements go here.]**

## Mechanical validation

Run the course's configured study-module validator against this module, in at least:

- the single-module mode;
- a machine-readable (e.g. `--json`) mode, parsed rather than only read as text;
- the "all modules" mode, to confirm no other module in this course was affected.

If the validator reports a genuine defect, fix the module's content. **Do not weaken, bypass, or
disable a validator check to obtain a passing result.**

## Reporting

When the module is complete and passing, report:

1. the five files created, and their location;
2. every source inspected, which were mapped and which excluded, and the hash-verification
   result for each;
3. any source-format difficulty encountered and how it was handled;
4. question counts by section, difficulty, and data-needed classification;
5. the numeric-verification result: how many generated answers were independently checked, how
   many source-published answers were checked, and any discrepancies or unresolved-precision
   findings;
6. the mechanical validator's result, for both this module alone and the "all modules" run;
7. confirmation that any temporary verification script was deleted;
8. the exact `git status --short` before and after, and confirmation nothing outside the new
   module's directory changed;
9. confirmation that no commit was created.

Stop after the module is created and validated. Do not begin a second module, and do not modify
any other file, unless separately instructed.

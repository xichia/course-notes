# Generate a Course-Level Study Index

> **Experimental, pre-1.0 prompt.** The five-file contract and these instructions may change.
> The public repository does not bundle a generic study-module validator. If the target course
> has no configured validator, stop rather than claim validation or completion. Do not scale
> generation beyond a pilot until a validator and independent subject-matter review exist.

## Prompt

Build a course-level study index for **[unit/course identifier]**, connecting its completed study
modules into one revision system, under the private course root **[path to ignored private
course root, e.g. `private/courses/<course-code>/`]**.

Follow the [study-layer workflow](../docs/study-layer-workflow.md) and reuse the
[study-module contract's](../docs/study-module-contract.md) conventions when citing question or
source IDs. This prompt produces three files directly under `<course root>/study/`:

```text
STUDY_INDEX.md
REVISION_PLAN.md
SOURCE_ISSUES.md
```

List the completed modules to connect: **[list each module's directory name under `study/`]**.

## Repository boundaries

- Work only under the ignored private course root given above.
- **Do not modify any existing study module** (its five files or its directory) — this prompt
  only reads them.
- Do not modify the curation manifest, any coverage/audit report, or the validator
  implementation.
- Do not install dependencies. Do not stage, commit, or push anything — no commit is authorized
  by this prompt alone.
- Inspect `git status --short` before and after. Confirm nothing outside the three new
  course-level files changed.

## Required inspection

For each listed module, read its own five files — `STUDY_GUIDE.md`, `QUESTION_BANK.md`,
`ANSWER_KEY.md`, `COVERAGE_MATRIX.md`, `source-map.json` — as the source of truth. Also read the
unit outline, the program calendar (or equivalent scheduling source), and any existing
course-level curation/coverage report.

**Do not re-read every underlying raw lecture or tutorial source.** The completed modules'
artifacts are themselves the authoritative summary; only fall back to a raw source if a specific
course-level statement genuinely cannot be resolved from the modules' own files.

## `STUDY_INDEX.md` requirements

- A course overview stating what the study layer is, that it supplements rather than replaces
  the authoritative course material, and explaining the `[S]`/`[E]`/`[H]` convention and the
  question-ID/answer-key/coverage-matrix/source-map roles.
- A recommended learning order based on **prerequisite logic**, not merely copied semester
  order — state the dependency reasoning for each step, grounded in what each module's own
  `source-map.json` says about which sources or concepts it reuses from another module.
- A module directory: for each module, relative links to its five files, a topic summary,
  prerequisite modules, and its question count, difficulty distribution, and data-needed
  distribution — **extracted from the module's own artifacts or mechanically recounted, never
  invented.**
- A cross-module concept map showing where each major concept is introduced and reused.
- A repeatable study workflow (read → attempt → self-mark → review → spaced retry → find gaps
  via the coverage matrix → return to source when needed).
- A blank completion-tracking template — do not populate it with invented performance data.

## `REVISION_PLAN.md` requirements

- At least three plan variants at different time budgets (e.g. a multi-week steady plan, a
  compressed intensive plan, and a short, deliberately selective emergency plan). The shortest
  plan must state plainly that it is selective, not a claim that everything can be covered.
- Every question ID or ID range cited must be verified to actually exist in the named module's
  question bank — never invented, and never referencing only the hardest questions.
- A repeatable session structure, with flexible (not rigid) timing suggestions.
- Evidence-based readiness checks per stage — demonstrable skills, not grade or outcome
  guarantees.
- A final mixed/cumulative review chaining concepts across modules in prerequisite order.

## `SOURCE_ISSUES.md` requirements

- Consolidate source issues **already documented** inside each module's own
  `COVERAGE_MATRIX.md` or `source-map.json` — this file summarizes and links back to the fuller
  account, it does not investigate new issues or re-litigate resolved ones.
- For each issue: which module, the source context, the nature of the issue, its effect on study
  or verification, a recommended action, and a status (e.g. confirmed discrepancy, precision
  limitation, missing source data, scope limitation, clarification recommended).
- **Do not silently resolve or "correct" any recorded source issue.**

## Mechanical checks

Before completion, verify (a temporary, disposable script is a reasonable way to do this):

1. every module directory referenced actually exists;
2. every file the index links to actually exists;
3. every question ID or range referenced in `REVISION_PLAN.md` exists in the correct module's
   question bank;
4. every reported question/difficulty/data-needed count matches an independent recount of the
   module's own question bank, not a hand-typed figure;
5. every relative Markdown link across the three new files resolves;
6. no absolute path appears;
7. no personal, authentication, grade, submission, or student-identity data appears;
8. no unresolved bare cross-module question or source ID appears — every cross-module reference
   is descriptive prose;
9. no existing module file was modified by this process.

Delete the temporary check script afterward. Then run the course's configured study-module
validator in its "all modules" mode, to confirm every referenced module still independently
passes — this prompt does not require the validator to check the three new course-level files
themselves, only to confirm the modules they reference are unaffected.

## Reporting

When complete, report:

1. the three files created;
2. every module artifact inspected;
3. the total question count represented across all referenced modules;
4. the key prerequisite relationships identified, and their source;
5. a summary of each revision-plan variant;
6. how many representative question IDs each plan variant references;
7. how many source issues were consolidated;
8. the mechanical-check result (item by item above);
9. the "all modules" validator result;
10. confirmation every referenced module remained unchanged;
11. confirmation the temporary check script was deleted;
12. the exact `git status --short` before and after;
13. confirmation nothing outside the three new files changed;
14. confirmation no commit was created.

**Do not make any claim about grade outcomes or guaranteed assessment coverage anywhere in the
output.** Stop after the three files are created and validated.

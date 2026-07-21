# Study-Layer Workflow

> **Experimental, pre-1.0 workflow.** The contract and prompts are experimental. The public
> repository does not bundle a generic study-module validator. If no course-specific validator
> is configured, an executor must stop rather than claim validation. Do not scale module
> generation until one pilot module, a working validator, and independent subject-matter review
> are in place.

The study layer is a second, heavier-weight workflow for turning a curated private source pack
into a structured, self-testing revision system for one unit — distinct from the lighter
concept-note system described in the root [`README.md`](../README.md). Where a concept note
captures one durable idea, a **study module** is a bounded, five-file package covering one topic
block of a unit: a guide, a question bank, an answer key, a coverage analysis, and a provenance
map. This document describes the end-to-end lifecycle; see
[`docs/study-module-contract.md`](study-module-contract.md) for the file contract itself and
[`docs/study-layer-validation.md`](study-layer-validation.md) for how a module is checked.

This is a **private-first workflow**. Everything it produces starts, and normally stays, under
the Git-ignored `private/` tree. See [Private/public boundary](#privatepublic-boundary) below.

## Prerequisites

1. **A curated, hash-verified source pack.** Before any study module is generated, the raw
   source material for a unit (lecture slides, tutorial questions, lab instructions, the unit
   outline, a program calendar) must already be collected under a private, ignored path and
   recorded in a manifest that pairs each curated file's destination path with a content hash
   (e.g. SHA-256). A study module never trusts a source file's content without re-checking that
   hash at generation time.
2. **A course-level directory convention.** Study modules for one unit live under a single
   `study/` directory inside that unit's private course root, one subdirectory per topic module.
3. **A validator you intend to run.** The workflow assumes a mechanical validator exists (or will
   be built during the first pilot module) that checks structure and provenance, not subject
   correctness — see [`docs/study-layer-validation.md`](study-layer-validation.md).

## Lifecycle

1. **The source pack is curated and verified.** A separate curation step produces the manifest
   above, with every record's hash confirmed against the file currently on disk. This step is
   not part of study-module generation itself — it is a precondition.
2. **Approved sources are selected for one topic.** For a given topic (e.g. `<UNIT-TOPIC-01>`),
   identify the specific curated lecture/tutorial/lab files that cover it, and — just as
   importantly — identify which curated files were considered and **excluded**, with a reason.
3. **One bounded module is generated.** A single topic's worth of content becomes one
   self-contained set of five files. A module should not span multiple unrelated topics, and a
   topic should not span multiple modules without a clear, documented reason (e.g. a topic split
   across two lecture blocks that share almost no content).
4. **Provenance and stable identifiers are recorded.** Every source file used gets a stable,
   short ID (reused unchanged if the same physical file is used again by a later module); every
   generated question gets a stable, namespaced ID that is never renumbered once written. See
   [`docs/study-module-contract.md`](study-module-contract.md) for the exact rules.
5. **Numerical and subject-matter checks are performed.** Every generated numeric answer is
   independently recomputed — typically with a disposable verification script, not by visual
   inspection — before it is written into the answer key. Every answer that can be checked
   against a source's own published figure is checked, and any disagreement is recorded, not
   silently resolved. See [`docs/study-layer-validation.md`](study-layer-validation.md) for the
   full subject-matter-review expectations.
6. **Mechanical validation runs.** The module-level validator checks file presence, JSON
   validity, source-ID resolution, hash reconciliation, question/answer metadata and parity,
   coverage cross-references, and a conservative sensitive-content sweep.
7. **Defects are corrected without weakening checks.** When the validator reports a genuine
   defect, the fix is to correct the module's content (add a missing source citation, replace a
   bare cross-module ID with descriptive prose, fix a stated count) — never to loosen or bypass
   the check that caught it.
8. **All modules are validated collectively.** Once more than one module exists for a unit, an
   "all modules" validator run confirms that a change to one module did not silently break
   another (for example, by reusing a source ID inconsistently).
9. **A course-level revision layer is generated.** After every module independently passes,
   a course-level index, a revision plan, and a consolidated source-issue register are built —
   from the **existing module artifacts**, not by re-reading every raw source again. This layer
   maps prerequisite order across modules, links every module's five files, builds a cross-module
   concept map, and proposes revision plans that cite real question IDs drawn from the modules'
   own question banks.
10. **Human review controls publication and commits.** No step in this workflow authorizes a Git
    commit, a push, or promotion of any file out of `private/`. A human decides when (and
    whether) any of this material is committed privately, and separately, whether any part of it
    is ever sanitized for public release (see [Private/public boundary](#privatepublic-boundary)).

## Inputs and outputs

| Stage | Input | Output |
|---|---|---|
| Curation | raw source files | a manifest with hashed, categorized records |
| Module generation | the manifest + selected curated files | five module files under `study/<topic>/` |
| Mechanical validation | the five module files + the manifest | a pass/fail result with typed errors/warnings |
| Numeric/subject review | the module's own draft answers | a verified answer key, with disagreements flagged, not hidden |
| Course-level layer | every completed module's own five files | a study index, a revision plan, a source-issue register |

## Approval gates

- **Before generation**: the source selection for a topic (which files are in scope, which are
  excluded and why) should be reasoned about explicitly, not assumed.
- **Before finalizing an answer key**: every numeric answer must have been independently
  recomputed, and every answer checkable against a published source figure must have been
  checked.
- **Before declaring a module done**: the mechanical validator must pass for that module, and for
  the full "all modules" run.
- **Before any commit or publication**: a human reviews the actual diff. No step in this workflow
  stages, commits, or pushes anything, and none should be interpreted as authorizing that.

## Failure and recovery behavior

- A validator failure names a specific file, a specific defect code, and (where available) a
  line — treat this as the thing to fix, not as license to relax the check.
- A numeric disagreement between an independently recomputed answer and a source's own published
  figure is not automatically an error in either direction. Before concluding the source is
  wrong: confirm the *method* independently, for example against a closely related worked example
  elsewhere in the same source, if one exists. Record the outcome as one of: a confirmed
  discrepancy in the source, an unresolved precision limitation, or a genuine data gap — these
  are different findings and should not be collapsed into one.
- If a generation session is interrupted (a model or context switch, a truncated turn), recovery
  should begin by **inspecting the actual files on disk** — the manifest, the already-written
  module files, the validator's own last output — rather than trusting a narrated summary of
  prior work at face value. Re-run any hash or mechanical check a summary claims already
  succeeded before building further on top of it.
- A conversational summary (in a chat transcript or a completion report) is not itself an
  artifact. If a stated count or claim needs to be trusted later, it belongs in a file the
  validator can check, not only in a chat message.

## Private/public boundary

- This entire workflow operates under the Git-ignored `private/` tree, per the repository's
  [publication policy](publication-policy.md) and [repository layout](repository-layout.md).
  Nothing it produces is committed or pushed by default.
- The curated source pack, the study modules themselves, and the course-level revision layer are
  all, by default, private and source-risky — they are derived from real lecture/tutorial/exam
  material and must never be promoted into the tracked `courses/` tree without a separate,
  explicit sanitization pass.
- What **is** safe to generalize into the public repository is the *method*: the module contract,
  the validator's checks, and reusable executor prompts that operate on placeholders — never the
  generated content itself. See [`docs/study-module-contract.md`](study-module-contract.md) and
  the [`prompts/generate-study-module.md`](../prompts/generate-study-module.md) /
  [`prompts/generate-course-study-index.md`](../prompts/generate-course-study-index.md) prompts
  for what was actually extracted into the public framework from this workflow.

## Definition of done

A single study module is done when:

- all five contract files exist, are non-empty, and are internally consistent (question/answer
  ID parity, resolvable source and coverage references);
- the mechanical validator passes for that module with zero errors;
- every numeric answer has been independently recomputed, and every answer checkable against a
  published source figure has been checked, with any disagreement explicitly recorded rather than
  silently resolved;
- known gaps and limitations (missing source data, unverifiable states, scope boundaries) are
  documented in the module's own coverage analysis, not implied or omitted.

The course-level layer is done when:

- every module it references independently passes the mechanical validator;
- every question ID and internal link it cites resolves against the real module artifacts,
  confirmed mechanically rather than by inspection alone;
- it makes no unqualified claim about assessment coverage or outcome — scheduling links to a
  named assessment are stated as inferences from a calendar, not as confirmed syllabus content,
  since no assessment content is opened by this workflow.

## Recommended model workflow

- **Pilot before scaling.** Build one bounded module first, and let it establish the concrete
  shape of the five-file contract and any tagging/ID conventions, rather than deciding the
  contract in the abstract before any real content exists. A validator written against a single
  guessed schema is far more likely to need rework than one written against one or two real,
  already-built modules.
- **Treat repository evidence as authoritative over model self-reports.** When resuming after an
  interruption, or when a later step depends on an earlier step's result, re-derive that result
  from the files on disk rather than trusting a summary of what was supposedly done.
- **Keep verification tooling disposable, keep verification *evidence* durable.** A temporary
  numeric-verification script can be written, run, and deleted within one module's build; the
  benchmark table it produces (computed vs. published, matched vs. flagged) belongs in the
  module's answer key permanently.
- **Let later modules reuse earlier modules' conventions by reading their files**, not by relying
  on a separate style guide. If a validator exists, it enforces the parts of the convention that
  matter mechanically; the rest is visible directly in the prior modules' own Markdown.

## Reasons to pilot before scaling

- The first module has to invent decisions (file schema, tagging convention, ID-namespace shape,
  what "excluded source" means and how it's recorded) that every later module then simply
  inherits. Making those decisions against one concrete, real topic surfaces edge cases that
  would otherwise only appear once several modules already exist and are expensive to retrofit.
- A validator built after one or two real modules exist can be tested against genuine variation
  (different section counts, different data-needed distributions, at least one module with a
  format quirk in its source PDFs) rather than a single hypothetical shape.
- Mistakes in a single pilot module are cheap to fix; the same mistake, repeated identically
  across five modules because it was baked into an untested template, is not.

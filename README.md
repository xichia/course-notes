# Course Notes

A Markdown-first system for durable learning notes, selective LLM retrieval, review queues, and study workflows. Markdown files under `courses/` are the source of truth; the manifest and review queue are generated views.

> This is a sanitized public-release candidate. Its only course tree is explicitly synthetic and contains no real university course material.
>
> License: MIT. See [LICENSE](LICENSE). The scripts, templates, prompts, and documentation are MIT licensed. Real course-derived notes should not be published through this repository unless separately cleared.

## Quickstart

For a human overview, open [INDEX.md](INDEX.md). For an LLM session, provide [LLM_GUIDE.md](LLM_GUIDE.md) and [manifest.json](manifest.json) first. For today's study priorities, open [REVIEW_QUEUE.md](REVIEW_QUEUE.md).

After adding or changing notes, run the normal workflow:

```bash
make all
```

This validates notes, rebuilds generated files, and runs tests. If Make is unavailable, use the direct commands:

```bash
python3 validate_notes.py
python3 build_manifest.py
python3 build_review_queue.py
python3 -m unittest discover -s tests
```

Individual Make targets are also available:

```bash
make validate
make manifest
make review
make test
make all
```

Make is only a convenience; the scripts require Python 3, use only the standard library, and remain directly runnable.

## Public/private content policy

The publishable work in this repository is original study material, not reproduced lecture material.

| Public Course Notes material | Private by default |
|---|---|
| Templates, scripts, prompts, docs, metadata schemas, validation logic, generated-file conventions, and synthetic examples | Real lecture-derived notes, problem sheets, exam maps/questions, lecturer hints, LMS material, assessment material, personal study evidence, and course-specific examples |

Keep the real study repository private when it contains actual course notes. If a public version is useful, create a separately reviewed, sanitized public repository using synthetic/demo content. AI summarization or paraphrasing alone does not make protected course material safe to publish.

Read [docs/publication-policy.md](docs/publication-policy.md) before changing visibility or preparing a release, and use [docs/public-release-checklist.md](docs/public-release-checklist.md) before making any repository public.

This sanitized candidate contains only `public-framework` or `public-original` notes with `source-risk: original`; `make validate-public` must pass before release.

### Public vs private notes

This repository is a public Course Notes repository. It contains tooling, templates, prompts, documentation, validation logic, and synthetic/demo content.

Real course notes should live in a separate private repository or private copy. A private notes repository may intentionally fail `make validate-public` because it can contain `visibility: private` or course-derived material. A public release must always pass `make pre-release`.

## Repository Structure

```text
course-notes/
├── courses/
│   └── <course-code>/
│       ├── course.md          course metadata, resources, and priorities
│       ├── syllabus.md        official outcomes and confirmed coverage
│       ├── concepts/          durable, one-concept-per-file notes
│       ├── lectures/          chronological lecture records
│       ├── problem-sheets/    attempts, corrections, and reflections
│       ├── exam/              exam maps and revision summaries
│       └── glossary.md        course terminology
├── docs/                           onboarding and friction-test checklists
├── prompts/                        reusable LLM study workflows
├── templates/                      course, syllabus, and raw lecture templates
├── Makefile                        optional command shortcuts
├── TEMPLATE.md                     canonical concept-note template
├── LLM_GUIDE.md                    LLM navigation and editing protocol
├── INDEX.md                        maintained human navigation
├── manifest.json                   generated machine-readable index
└── REVIEW_QUEUE.md                 generated ranked review list
```

The included `courses/demo-course/` tree is fictional and exists only to demonstrate the system. Replace it with other synthetic material—not real course notes—when preparing a public variant.

## Source of Truth and Generated Files

- Markdown under `courses/` is the source of truth for course knowledge, evidence, and review metadata.
- `manifest.json` is a generated retrieval index. Its top-level `_generated` field says how to rebuild it.
- `REVIEW_QUEUE.md` is a generated study-priority view and begins with a generated-file warning.
- `INDEX.md` and course `README.md` files are maintained human navigation.
- Files under `prompts/` are reusable instructions, not course facts.

Never edit `manifest.json` or `REVIEW_QUEUE.md` manually. Update source Markdown and run `make manifest`, `make review`, or `make all`.

**Determinism:** Generated files use a date-only `generated-at` field (no time). Running `make all` multiple times on the same day produces no diff when notes are unchanged. For fully reproducible builds, set the `SOURCE_DATE_EPOCH` environment variable (Unix timestamp) or pass `--today` to `build_review_queue.py`.

## Command Reference

| Command | Purpose |
|---|---|---|
| `make validate` | Check metadata, IDs, dates, links, required sections, and mistake structure |
| `make validate-public` | Apply the stricter public-release gate; expected to fail in a real private study repo |
| `make manifest` | Validate and rebuild `manifest.json` |
| `make review` | Validate and rebuild `REVIEW_QUEUE.md` for today; set `DATE=YYYY-MM-DD` for a reproducible date |
| `make test` | Run the dependency-free regression suite |
| `make pre-release` | Run the public-release gate, regenerate all files, and run tests (for release readiness) |
| `make all` | Run normal validation, both generators, and all tests |
| `python3 build_review_queue.py --today YYYY-MM-DD` | Generate the review queue for a specific date |

The equivalent direct Python commands are shown in Quickstart.

CI runs on every push and pull request: `make all`, `make validate-public`, `make pre-release`, and a generated-file staleness check. See [ci.yml](.github/workflows/ci.yml).

## Adding a new course

The full copy-and-check workflow is in [docs/course-onboarding.md](docs/course-onboarding.md). In short:

1. Create `courses/<course-code>/` with `concepts/`, `lectures/`, `problem-sheets/`, and `exam/`.
2. Copy `templates/course.md` to `courses/<course-code>/course.md` and replace every placeholder.
3. Copy `templates/syllabus.md` to `courses/<course-code>/syllabus.md`; add only official or explicitly sourced material.
4. Copy `templates/lecture.md` into `lectures/` for each raw chronological lecture record.
5. Use `prompts/import-lecture.md` to propose durable concept extraction, then create approved concepts from `TEMPLATE.md`.
6. Put attempts, corrections, and evidenced mistakes under `problem-sheets/`.
7. Put confirmed exam information and outcome maps under `exam/`.
8. Run `make validate`.
9. Run `make manifest`, `make review`, and `make test` (or simply `make all`).

Set every document's `course` field to the exact directory name. Keep raw lecture notes intact, preserve source paths, and keep missing official information visibly unknown.

After the first import, run the ten-minute [course import friction test](docs/friction-test.md).

## Add a Concept Note

1. Copy `TEMPLATE.md` to `courses/<course-code>/concepts/readable-filename.md`.
2. Give it a repository-unique, permanent `id`. For new notes, `<course-code>-<concept-slug>` is a useful convention.
3. Fill in every metadata field and write the note in your own words.
4. Use note IDs, not filenames, in `prerequisites` and `related`.
5. Validate, then regenerate the manifest and review queue.

Keep filenames readable and stable. A concept note should grow as understanding improves instead of being replaced by dated copies.

## Daily Study

1. Run `make review` (or `python3 build_review_queue.py`).
2. Open `REVIEW_QUEUE.md`, or give `prompts/daily-study.md` to an LLM with repository access.
3. Study the highest-priority item through active recall before rereading it.
4. Update review dates and Mistake Log items only after checking your performance.
5. Run `make all` after changing source notes.

For a weekly planning session, run `make all`, then use `prompts/weekly-review.md` with the refreshed manifest and queue.

## Metadata Contract

Every study document under `courses/` (except navigational `README.md` files) uses the same frontmatter keys:

| Field | Meaning |
|---|---|
| `id` | Permanent, repository-unique identifier; lowercase letters, numbers, dots, and hyphens |
| `title` | Human title, matching the document's `#` heading |
| `course` | Course directory name |
| `type` | `concept`, `lecture`, `problem-sheet`, `exam-map`, `glossary`, or `reference` |
| `topic` | Stable topic slug within the course |
| `aliases` | Alternative search terms as an inline list |
| `prerequisites` | Note IDs needed first |
| `related` | Other relevant note IDs |
| `exam-weight` | `none`, `low`, `medium`, or `high` |
| `status` | `new`, `learning`, `shaky`, `solid`, `mastered`, `reference`, or `archived` |
| `last-reviewed` | Last active-recall date as `YYYY-MM-DD`, or blank |
| `review-after` | Next review date as `YYYY-MM-DD`, or blank |
| `source` | Lecture, text, problem sheet, URL, or an honest note that the source is unknown |
| `visibility` | Optional publication classification: `private`, `public-framework`, `public-original`, or `public-open-licensed` |
| `source-risk` | Optional provenance risk: `lecture-derived`, `problem-sheet-derived`, `exam-derived`, `lms-derived`, `open-licensed`, `original`, or `unknown` |

Lists use the simple inline form `[first-id, second-id]`. This constrained frontmatter format keeps the scripts dependency-free and the files easy to inspect.

## Status and Review Workflow

Use status as a judgment about recall, not note polish:

- `new`: captured but not learned
- `learning`: partly understood; cannot yet reproduce reliably
- `shaky`: previously learned but errors or gaps remain
- `solid`: can explain and solve representative problems
- `mastered`: reliable after repeated delayed review
- `reference`: useful navigation material, not a review item
- `archived`: retained but excluded from active review

After an active review:

1. Update `last-reviewed`.
2. Set `review-after` to the next useful date. A practical starting cadence is 1–3 days for `new`/`shaky`, 7–14 days for `learning`, 30 days for `solid`, and 60–90 days for `mastered`.
3. Propose a `status` change separately from making it. Upgrade only after repeated recall or application evidence; downgrade when repeated mistakes demonstrate a real gap.
4. Record any evidenced error with the structured Mistake Log convention below.
5. Regenerate `manifest.json` and `REVIEW_QUEUE.md`.

Use `prompts/update-status.md` after a quiz, problem sheet, or timed recall session. One good answer, confidence alone, or improved prose is not enough to upgrade status. A useful upgrade normally needs successful evidence from at least two attempts separated by time or using different task types.

## Recording Mistakes

Mistakes are immutable evidence, not a to-do list. Add one five-field block under `## Mistake Log` only when an actual quiz, problem sheet, exam, or recall attempt exposed the error:

```md
- date: 2026-06-30
  source: problem-sheet-01
  mistake: Describe what went wrong.
  correction: Record the action or idea to apply next time.
  tags: [exam-trap, procedure]
```

Use one line per field and inline slug-style tags. `date: unknown` is allowed only when migrating a genuine older mistake whose date was never recorded. Do not delete old entries when they improve; their recent-priority effect expires automatically after 30 days, while the history remains useful.

## Practice Questions

Every concept note has `## Practice Questions` with `### Easy`, `### Medium`, and `### Exam-style` groups. Questions are ordinary Markdown bullets. Empty groups use `_No practice questions recorded yet._`; never create filler questions merely to satisfy validation.

The manifest records counts by difficulty plus `has-practice-questions`. It also records whether the note has a substantive worked example, allowing weekly review to expose thin notes.

## Review Priority

The generated queue documents the same additive formula beside its results:

- status: shaky +40, new +32, learning +26, solid +8, mastered +0;
- exam weight: high +25, medium +14, low +5, none +0;
- review timing: +30 when due, plus up to +30 for overdue days; missing `review-after` +10;
- review age: never reviewed +20, otherwise up to +20 after the first seven days;
- mistakes: +5 each up to +20, plus +12 for each dated mistake in the last 30 days up to +36;
- missing practice questions on a concept: +10;
- high exam weight combined with shaky status: +15.

The score ranks attention; it is not a grade or automatic status decision. Use `python3 build_review_queue.py --today YYYY-MM-DD` for a reproducible queue on a specified date.

## Manifest-First LLM Use

`manifest.json` contains metadata, publication classifications, short summaries, headings, mistake counts/dates/tags, worked-example coverage, and practice-question counts for every study document. An LLM should:

1. Read the manifest first.
2. Filter to relevant course, topic, type, status, aliases, or exam weight.
3. Open only the selected files listed in `file`.
4. Follow prerequisite and related IDs only when needed.
5. Treat the Markdown notes as authoritative and generated files as disposable indexes.

See [LLM_GUIDE.md](LLM_GUIDE.md) for the full protocol and [prompts/](prompts/) for ready-to-use study workflows.

## LLM Workflow Reference

| Workflow | Prompt |
|---|---|
| Import a rough lecture safely | [prompts/import-lecture.md](prompts/import-lecture.md) |
| Run today's study session | [prompts/daily-study.md](prompts/daily-study.md) |
| Quiz one topic interactively | [prompts/quiz-me.md](prompts/quiz-me.md) |
| Explain a selected concept | [prompts/explain-a-concept.md](prompts/explain-a-concept.md) |
| Improve or extract a durable note | [prompts/improve-this-note.md](prompts/improve-this-note.md) |
| Generate source-backed flashcards | [prompts/generate-flashcards.md](prompts/generate-flashcards.md) |
| Prepare for an exam | [prompts/prepare-for-an-exam.md](prompts/prepare-for-an-exam.md) |
| Plan the next week | [prompts/weekly-review.md](prompts/weekly-review.md) |
| Evaluate a status change from evidence | [prompts/update-status.md](prompts/update-status.md) |

Every workflow must distinguish repository evidence from external explanation, preserve uncertainty, and avoid inventing course content.

## Validation and Generated Files

`validate_notes.py` catches missing fields, malformed dates/lists, malformed structured mistakes, invalid status/weight/visibility/source-risk values, duplicate IDs, broken ID and Markdown links, absolute machine-specific links anywhere in repository Markdown, type/course-directory mismatches, title mismatches, and missing concept sections such as Practice Questions. Errors name the affected file and field or section, show the bad value when useful, and suggest a repair. The command exits non-zero on errors.

`python3 validate_notes.py --public-release` (or `make validate-public`) adds a conservative publication gate. It fails on private visibility, course-derived or unknown source risk, missing publication classifications, and local paths. Do not weaken this check to make a real private repository pass.

`build_manifest.py` and `build_review_queue.py` validate before writing. They will not replace their outputs when notes are malformed. `manifest.json` carries a top-level `_generated` warning; `REVIEW_QUEUE.md` begins with a generated-file HTML comment. Never edit either file manually: change the source Markdown and rebuild it.

For documentation navigation and repository-maintenance checks, see [docs/README.md](docs/README.md).

# Repository Layout

This repository uses a **one-folder workflow**: a single working copy, a single
Git history, and a single public remote. Public-safe and private material are
separated by directory and Git tracking, not by repository.

## Directory map

```text
course-notes/
├── courses/                        tracked, public-safe polished notes only
│   └── <course-code>/
│       ├── course.md          course metadata, resources, and priorities
│       ├── syllabus.md        official outcomes and confirmed coverage
│       ├── concepts/          durable, one-concept-per-file notes
│       ├── lectures/          chronological lecture records
│       ├── problem-sheets/    attempts, corrections, and reflections
│       ├── exam/              exam maps and revision summaries
│       └── glossary.md        course terminology
├── private/                        Git-ignored; never committed or pushed
│   ├── courses/               private/source-risky notes (mirrors the courses/ layout)
│   ├── raw/                   raw source material
│   ├── drafts/                 work in progress
│   └── framework-feedback.md  scratch notes about the framework itself
├── docs/                           onboarding, layout, and friction-test guides
├── prompts/                        reusable LLM study workflows
├── templates/                      course, syllabus, and raw lecture templates
├── Makefile                        optional command shortcuts
├── TEMPLATE.md                     canonical concept-note template
├── LLM_GUIDE.md                    LLM navigation and editing protocol
├── INDEX.md                        maintained human navigation
├── manifest.json                   generated machine-readable index
└── REVIEW_QUEUE.md                 generated ranked review list
```

## What is tracked

Git tracks the framework — scripts, templates, prompts, docs, metadata schema,
validation logic, generated-file conventions — plus the `courses/` tree.
Everything under `courses/` must be safe to publish: it is what the GitHub remote
ever exposes. `make validate-public` scans only `courses/` and fails on
`visibility: private`, course-derived or unknown `source-risk`, missing
publication classifications, and local paths.

## What is not tracked

The entire `private/` directory is ignored by Git (see the `private/` rule in
[../.gitignore](../.gitignore)). It is local working storage only:

- `private/courses/` mirrors the `courses/` layout for private notes. A private
  note keeps `visibility: private` and an honest `source-risk`; it may
  intentionally fail `make validate-public`, but that gate never scans it.
- `private/raw/` holds raw source material (slides, handouts, transcripts, LMS
  exports) that must never be committed.
- `private/drafts/` holds work in progress.
- `private/framework-feedback.md` holds scratch notes about the framework itself.

Because `private/` is Git-ignored, it is never committed and never pushed.
Keeping material there is **not** sanitization: promoting a private note into
`courses/` requires an explicit sanitization and review step (see
[publication policy](publication-policy.md) and the
[public release checklist](public-release-checklist.md)).

## Working in this layout

- Add and study real notes under `private/courses/<course>/...` while their
  provenance or publication status is uncertain.
- **Study commands** mirror the public targets but operate on `private/courses/`:

  | Command | Purpose |
  |---|---|
  | `make study-validate` | Validate notes under `private/courses/` |
  | `make study-manifest` | Build `private/manifest.json` from study notes |
  | `make study-review` | Build `private/REVIEW_QUEUE.md` from study notes |
  | `make study-all` | Run study-validate, study-manifest, and study-review |
  | `make study-reviewed NOTE=<id>` | Mark a study note as reviewed |

- The public `make manifest`, `make review`, and `make validate` still operate on
  `courses/` only. Private notes never leak into the public generated files.
- To publish a note, sanitize it into a `courses/<course>/` file with an allowed
  `visibility` and `source-risk`, then run `make pre-release`.
- Run `make public-safety` to validate the public tree and run all tests.
- `private/` is deliberately untracked: back it up independently, since Git
  provides no history for its contents.
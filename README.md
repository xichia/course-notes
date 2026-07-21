# Course Notes

> **Experimental / pre-1.0:** interfaces and conventions may still change. The lightweight
> Markdown-note workflow is usable today; the advanced study-module workflow remains an
> experiment and is not turnkey.

Course Notes is a Markdown-first framework for durable study notes, active recall, and
source-aware review. It keeps public framework work separate from ignored private study files
and uses dependency-free Python tools for validation and generated views.

No database, server, package installation, or specific editor is required.

## Choose your workflow

| Goal | Current status | Start here |
|---|---|---|
| Try the fictional demo | Implemented | Run the non-mutating [quick start](#quick-start) |
| Create lightweight private notes | Implemented | Follow [manual course onboarding](docs/course-onboarding.md) |
| Use experimental five-file study modules | Experimental; not turnkey | Read the [study-layer workflow](docs/study-layer-workflow.md) |
| Contribute to the public framework | Implemented contribution path | Read [CONTRIBUTING.md](CONTRIBUTING.md) |

## Quick start

Course Notes supports Python **3.9 or newer** and uses only the standard library. GNU Make is
an optional command wrapper; the Python implementation and minimum version are unchanged.

```bash
git clone https://github.com/xichia/course-notes.git
cd course-notes
make check
```

The direct equivalent without GNU Make is:

```bash
python3 validate_notes.py
python3 -m unittest discover -s tests -v
```

`make check` validates the tracked public notes and runs the regression suite without changing
files. The included `demo-course` is entirely fictional, so it can be explored without using
real course material.

Useful demo views:

- [INDEX.md](INDEX.md) — maintained navigation;
- [manifest.json](manifest.json) — generated retrieval index;
- [REVIEW_QUEUE.md](REVIEW_QUEUE.md) — generated study priorities.

## Start a first private course

Follow [Course onboarding](docs/course-onboarding.md) to create the ignored private directory
manually from the canonical course and syllabus templates, record verified details, and run the
private-note checks.

> **Private data and backup warning**
>
> The outer public repository ignores `private/`. Files there are absent from its commits,
> remote, clones, and Git history. This project provides **no backup** for them. Maintain an
> independent encrypted backup before adding irreplaceable notes or source material.
>
> Raw, personal, restricted, unsanitized, or uncleared material must remain private. AI
> summarization, rewriting, or paraphrasing does **not** establish publication rights.

For long-term adoption, upstream updates, and optional nested private Git, read
[Adopting the framework](docs/adopting-the-framework.md).

## Feature maturity

| Capability | Status | What that means |
|---|---|---|
| Lightweight public Markdown notes | Implemented | Templates, validation, generated views, and fictional examples ship here |
| Lightweight private Markdown notes | Implemented | Ignored workspace and `study-*` commands are available; backup is separate |
| Manifest and review queue | Implemented | Deterministic generated public views |
| Public-safety gate, hooks, and tests | Implemented | Conservative automated safeguards; human review still controls publication |
| Course scaffolding | Manual; automated initializer not bundled | The documented onboarding path uses the shipped templates |
| Five-file study-module contract and prompts | Experimental | Pilot-oriented specifications that may change |
| Generic study-module validator | Not bundled | A configured course-specific validator is required before claiming validation |
| End-to-end synthetic study-module example | Not bundled | The advanced workflow is not yet demonstrated as a turnkey public example |
| LMS/source importing | Not bundled | Existing importing is project-specific, not a reusable public feature |
| Private-file backup | User-managed | No backup, synchronization, or recovery service is provided |

The detailed implementation matrix and deferred work are recorded in
[PROJECT_STATE.md](PROJECT_STATE.md).

## Repository map

```text
course-notes/
├── courses/          tracked public notes and the fictional demo
├── private/          ignored local work; not part of public Git history
├── docs/             adoption, operation, publication, and workflow guides
├── prompts/          reusable human/executor workflows
├── templates/        canonical note and course templates
├── scripts/          optional managed Git hooks
├── tests/            standard-library regression tests
├── manifest.json     generated public retrieval index
└── REVIEW_QUEUE.md   generated public review priorities
```

`TEMPLATE.md` defines lightweight concept notes. `studylib.py` contains shared parsing,
validation, and generation-date behavior. Generated files must be rebuilt, not hand-edited.

Private files can occupy the same workspace, but the outer repository does not track them. See
[Repository layout](docs/repository-layout.md) for the precise trust boundaries.

## Common commands

| Command | Behavior |
|---|---|
| `make help` | List the principal targets |
| `make check` | Validate public notes and run tests without changing files |
| `make refresh` | **Mutating:** validate and rebuild both public generated views for the working date |
| `make verify-generated` | Deterministically regenerate from the HEAD timestamp and fail on drift |
| `make all` | Preserve the original validate, regenerate, and test workflow |
| `make public-safety` | Run the canonical publication-safety gate and tests |
| `make study-all` | Validate and refresh lightweight private notes |
| `make reviewed NOTE=<id>` | Record a public-note review using the configured cadence |
| `make install-hooks` | Install optional managed pre-commit and pre-push hooks |

`SOURCE_DATE_EPOCH` controls deterministic dates for both generated public views. Review-queue
date precedence is `--today`, then `DATE`, then `SOURCE_DATE_EPOCH`, then the current date.

## Documentation by task

| Task | Guide |
|---|---|
| Adopt and maintain your own copy | [Adopting the framework](docs/adopting-the-framework.md) |
| Add a real private course | [Course onboarding](docs/course-onboarding.md) |
| Understand public/private boundaries | [Repository layout](docs/repository-layout.md) |
| Run daily and release checks | [Operating checklist](docs/operating-checklist.md) |
| Decide what may be public | [docs/publication-policy.md](docs/publication-policy.md) |
| Review a publication candidate | [docs/public-release-checklist.md](docs/public-release-checklist.md) |
| Understand lightweight note fields | [TEMPLATE.md](TEMPLATE.md) |
| Use repository-aware retrieval | [LLM_GUIDE.md](LLM_GUIDE.md) |
| Pilot experimental study modules | [Study-layer workflow](docs/study-layer-workflow.md) |
| Browse reusable prompts | [Prompt index](prompts/README.md) |
| Contribute framework changes | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Scope, limitations, and licence

Course Notes provides an inspectable framework, not:

- an LMS mirror or generic source importer;
- a turnkey study-module generator;
- a publication-clearance or copyright-determination service;
- proof that course-derived material may be redistributed;
- a backup service for ignored private files;
- a guarantee that generated explanations, calculations, or questions are correct.

`make public-safety` reduces accidental disclosure through Git-boundary checks, conservative
pattern scanning, public-note validation, and tests. It cannot understand every confidentiality,
copyright, institutional-policy, or provenance issue. Human review remains the publication
authority, and validator checks must not be weakened merely to obtain a pass.

Framework code, templates, prompts, and documentation are licensed under the [MIT License](LICENSE).
That licence does not extend to private or third-party course content added by a user.

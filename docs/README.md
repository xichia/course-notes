# Documentation Index

This directory contains the operational guides for the course-notes system. Course knowledge remains in Markdown under `courses/`; these files explain how to add and maintain it.

## Guides

| Guide | Use it when |
|---|---|
| [Adopting the framework](adopting-the-framework.md) | Maintaining a personal copy, preserving upstream, and backing up ignored work |
| [Course onboarding](course-onboarding.md) | Adding real material under ignored `private/courses/` before any separate public promotion |
| [Course import friction test](friction-test.md) | Checking whether a newly imported course is quick to navigate, study, and update |
| [LLM guide](../LLM_GUIDE.md) | Giving an LLM the repository's retrieval, evidence, and editing rules |
| [Publication policy](publication-policy.md) | Deciding what belongs in the tracked `courses/` tree and what stays under `private/` |
| [Repository layout](repository-layout.md) | One-folder workflow: tracked `courses/` plus the Git-ignored `private/` directory |
| [Operating checklist](operating-checklist.md) | Quick reference for the daily study and pre-commit workflow |
| [Public release checklist](public-release-checklist.md) | Manually sanitizing and reviewing material before it enters `courses/` |
| [Study-layer workflow](study-layer-workflow.md) | Generating one source-linked study module from a curated private source pack |
| [Study-module contract](study-module-contract.md) | Understanding the five-file study-module schema and its stable-ID rules |
| [Study-layer validation](study-layer-validation.md) | Understanding mechanical vs. subject-matter validation for a study module |

## Templates

| Template | Destination |
|---|---|
| [Course metadata](../templates/course.md) | `private/courses/<course-code>/course.md` by default |
| [Syllabus](../templates/syllabus.md) | `private/courses/<course-code>/syllabus.md` by default |
| [Raw lecture](../templates/lecture.md) | `private/courses/<course-code>/lectures/yyyy-mm-dd-topic.md` by default |
| [Concept note](../TEMPLATE.md) | `private/courses/<course-code>/concepts/concept-name.md` by default |

## Study Workflows

Reusable LLM prompts live under [prompts/README.md](../prompts/README.md). Begin with:

- [Import a lecture](../prompts/import-lecture.md)
- [Daily study](../prompts/daily-study.md)
- [Log a mistake](../prompts/log-a-mistake.md)
- [Sanitize a private repository for public release](../prompts/sanitize-for-public-release.md)
- [Evidence-based status update](../prompts/update-status.md)
- [Weekly review](../prompts/weekly-review.md)

## Maintenance

Run the non-mutating check after editing notes, documentation, templates, prompts, or scripts:

```bash
make check
```

Use `make refresh` when generated public views should be updated. Generated files are committed
for convenient GitHub and LLM access, but they must be rebuilt rather than edited manually.

## Optional pre-commit hook

To install a local pre-commit hook that runs `make public-safety`
before every commit:

```bash
make install-hooks
```

The hook is entirely optional; see [operating-checklist.md](operating-checklist.md) for details.

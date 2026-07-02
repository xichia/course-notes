# Documentation Index

This directory contains the operational guides for the course-notes system. Course knowledge remains in Markdown under `courses/`; these files explain how to add and maintain it.

## Guides

| Guide | Use it when |
|---|---|
| [Course onboarding](course-onboarding.md) | Adding a real module, its syllabus, lectures, concepts, problem sheets, and exam material |
| [Course import friction test](friction-test.md) | Checking whether a newly imported course is quick to navigate, study, and update |
| [LLM guide](../LLM_GUIDE.md) | Giving an LLM the repository's retrieval, evidence, and editing rules |
| [Publication policy](publication-policy.md) | Deciding what belongs in the tracked `courses/` tree and what stays under `private/` |
| [Repository layout](repository-layout.md) | One-folder workflow: tracked `courses/` plus the Git-ignored `private/` directory |
| [Operating checklist](operating-checklist.md) | Quick reference for the daily study and pre-commit workflow |
| [Public release checklist](public-release-checklist.md) | Manually sanitizing and reviewing material before it enters `courses/` |

## Templates

| Template | Destination |
|---|---|
| [Course metadata](../templates/course.md) | `courses/<course-code>/course.md` |
| [Syllabus](../templates/syllabus.md) | `courses/<course-code>/syllabus.md` |
| [Raw lecture](../templates/lecture.md) | `courses/<course-code>/lectures/yyyy-mm-dd-topic.md` |
| [Concept note](../TEMPLATE.md) | `courses/<course-code>/concepts/concept-name.md` |

## Study Workflows

Reusable LLM prompts live under [prompts/README.md](../prompts/README.md). Begin with:

- [Import a lecture](../prompts/import-lecture.md)
- [Daily study](../prompts/daily-study.md)
- [Log a mistake](../prompts/log-a-mistake.md)
- [Sanitize a private repository for public release](../prompts/sanitize-for-public-release.md)
- [Evidence-based status update](../prompts/update-status.md)
- [Weekly review](../prompts/weekly-review.md)

## Maintenance

Run the complete check after editing notes, documentation, templates, prompts, or scripts:

```bash
make all
```

Generated files are committed for convenient GitHub and LLM access, but they must be rebuilt rather than edited manually.

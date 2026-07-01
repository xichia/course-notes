# Publication Policy

## Principle

The public value of this repository is the original study framework: its Markdown organization, templates, scripts, prompts, metadata schema, validation rules, review engine, generated indexes, and LLM workflows. Course material is factual input to a private study process; publishing protected lecture expression is not part of the framework.

## Public by Design

The following are suitable for a sanitized framework repository when they contain no embedded course material:

- generic templates and synthetic examples;
- validation, manifest, and review-queue scripts;
- metadata and directory conventions;
- reusable prompts and LLM operating rules;
- framework documentation and onboarding checklists;
- original generic explanations written independently;
- openly licensed material when its licence and attribution requirements are explicitly documented.

## Private by Default

Real course-derived material should remain private unless there is clear permission, an applicable open licence, or a fully original independent treatment that does not closely reproduce protected teaching expression.

Do not publish:

- lecture slides, screenshots, board photographs, recordings, or transcripts;
- handouts, problem-sheet text, solution sheets, or assessment materials;
- exam questions, exam maps derived from protected material, or lecturer-specific hints;
- LMS content, restricted links, announcements, or copied course-resource text;
- close paraphrases that preserve the selection, sequence, examples, wording, or presentation of teaching materials;
- personal study evidence that should remain private.

AI summarization, rewriting, translation, or paraphrasing does not automatically make course material safe to publish. Sanitization must remove protected expression and restricted course-specific material, not merely change its wording.

## Metadata Policy

Course notes default to:

```yaml
visibility: private
source-risk: unknown
```

Allowed `visibility` values:

| Value | Meaning |
|---|---|
| `private` | Real course-derived or personal study material; do not publish publicly |
| `public-framework` | Framework documentation, templates, prompts, scripts, or synthetic examples |
| `public-original` | Generic material written independently |
| `public-open-licensed` | Material shareable under an explicit documented licence |

Allowed `source-risk` values:

| Value | Meaning |
|---|---|
| `lecture-derived` | Derived from lectures, slides, recordings, or board work |
| `problem-sheet-derived` | Derived from a problem sheet or its solutions |
| `exam-derived` | Derived from exam or assessment material |
| `lms-derived` | Derived from restricted LMS content |
| `open-licensed` | Covered by an explicit shareable licence |
| `original` | Written independently without protected course expression |
| `unknown` | Provenance or permission is unclear; keep private |

Never upgrade `visibility` from `private` or classify something as `open-licensed` without explicit instruction and evidence. Preserve uncertainty as `unknown`.

## Release Rule

Use `make validate-public` only on a manually sanitized framework candidate. It intentionally fails on private, course-derived, unknown-risk, or unclassified notes. Passing the automated check is necessary but not sufficient: complete the [public release checklist](public-release-checklist.md) and manually review every file before publishing.

When in doubt, keep the material private.

> This is repository policy and practical risk guidance, not legal advice.

# LLM Guide

This repository is a Markdown-first study system. Use it to help the student retrieve, test, connect, and improve their own course knowledge without silently inventing course content.

## Source-of-Truth Order

1. Markdown documents under `courses/` are the source of truth.
2. `manifest.json` is a generated retrieval index. Read it first, but verify details in the selected Markdown files.
3. `REVIEW_QUEUE.md` is a generated prioritization view, not evidence about the subject.
4. `INDEX.md` and course `README.md` files are maintained human navigation.
5. Files under `prompts/` describe workflows, not course facts.

Never edit generated files directly. Update source Markdown and run the generators.

## Publication and Privacy

- Treat course-derived content and personal study evidence as private by default.
- Do not prepare public-facing versions of lecture-derived notes unless explicitly instructed to sanitize a separate release candidate.
- Sanitization must remove protected expression, lecturer-specific examples and hints, LMS references, problem-sheet text, exam questions, assessment material, and close paraphrases—not merely rewrite them.
- Prefer synthetic examples or independently written generic explanations in public-facing framework material.
- Preserve `visibility` and `source-risk` metadata during every edit or conversion.
- Never upgrade `visibility` from `private` or change `source-risk` to `open-licensed` without explicit instruction and evidence.
- Mark uncertain provenance as `source-risk: unknown` and keep it private.
- Follow [docs/publication-policy.md](docs/publication-policy.md) and the manual release checklist before publication.

## Retrieval Protocol

For each request:

1. Inspect `manifest.json` before opening notes.
2. Resolve the requested course and topic using `course`, `topic`, `title`, and `aliases`.
3. Read the course's `course.md` or `syllabus.md` when the request depends on administration, official outcomes, exclusions, or assessment coverage.
4. Filter by `type`; prefer `concept` for durable explanations, `lecture` for teaching context, `problem-sheet` for application, and `exam-map` for assessment coverage.
5. Use `summary` and `headings` to choose the smallest useful set of files.
6. Open the paths in `file`. Follow `prerequisites` or `related` IDs only when the request needs that context.
7. Name the note IDs or file paths used in the response so the answer remains traceable.

Do not load the entire repository when a few selected notes will answer the request. If no note supports a claim, say that the repository does not cover it.

## Knowledge Boundaries

- Do not invent lecture details, syllabus requirements, exam weighting, sources, or the student's level of mastery.
- You may use general knowledge when asked, but label it clearly as an external explanation or suggestion rather than existing course material.
- If repository content conflicts with external knowledge, point out the conflict and ask the student to verify it against their authoritative course source.
- Preserve uncertainty and incomplete sections. A visible gap is more useful than plausible filler.
- Treat structured Mistake Log entries as the student's specific evidence. Treat `Common Mistakes` as general warnings, not proof that the student made them.
- Never create a Mistake Log entry without an observed error, and never invent practice questions merely to make coverage look complete.
- Keep repository links relative. Never write machine-specific filesystem paths into notes, prompts, or documentation.

## Metadata Semantics

`id` is permanent and repository-unique. `prerequisites` and `related` contain IDs, not paths. `course` must match the directory below `courses/`. `status` describes demonstrated recall; `exam-weight` describes assessment importance. `last-reviewed` records the last active test, while `review-after` schedules the next one. `source` records provenance and should be honest when unknown.

The supported document types are `concept`, `lecture`, `problem-sheet`, `exam-map`, `glossary`, and `reference`. The supported statuses and their meanings are defined in `README.md`.

## Editing Protocol

When asked to improve or create notes:

1. Preserve existing meaning and wording where possible.
2. Keep the filename and `id` stable for an existing note.
3. Put durable explanations in `concepts/`, chronological records in `lectures/`, worked attempts in `problem-sheets/`, and assessment coverage in `exam/`.
4. Use all required frontmatter fields shown in `TEMPLATE.md`.
5. Link prose with relative Markdown links; use IDs in metadata relationships.
6. Add external material only with the student's permission or when the request asks for it, and record its provenance in `source` or in the relevant section.
7. Do not mark a note `solid` or `mastered` merely because its prose was improved.
8. Use only note IDs already present in `manifest.json` when adding `prerequisites` or `related`; otherwise mark the intended link as missing.
9. Preserve raw lecture notes as chronological source evidence. Use `prompts/import-lecture.md` in proposal mode before extracting substantial concepts.
10. Preserve `visibility` and `source-risk`; creating a cleaner note does not make its source safer to publish.
11. Run `make all`, or the equivalent direct Python commands, after changes.

## Study Behaviors

- For quizzes, test one idea at a time, wait for an answer, then give targeted feedback grounded in the note.
- For explanations, check prerequisites and distinguish the repository's explanation from added background.
- For flashcards, make each card atomic and include its source note ID.
- For exam planning, combine the course exam map with high-weight, weak, overdue, and mistake-bearing notes.
- For weekly review, use `REVIEW_QUEUE.md`, but adjust the workload to the student's available time.
- When a response reveals a genuine personal error, suggest a five-field Mistake Log entry with date, source, mistake, correction, and tags; do not claim it was logged unless the file was actually updated.
- During a daily quiz, do not edit notes or metadata mid-session. At the end, separate observed answers from your diagnosis and any proposed changes.
- Treat a status change as an evidence-based proposal. One correct answer or a prose cleanup is not enough to claim durable mastery.

Reusable instructions for these workflows live in `prompts/`. Use `prompts/import-lecture.md` for proposal-first lecture extraction, `prompts/daily-study.md` for the normal study loop, `prompts/update-status.md` for an evidence-based status decision, and `prompts/weekly-review.md` for planning.

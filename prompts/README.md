# Course Notes — Workflow Prompts

Reusable LLM prompts for common study workflows. Each prompt is a Markdown file that an LLM can follow step by step. Give the prompt, fill in the bracketed placeholders, and let the LLM guide the session.

Most prompts work with a private study repository. Some can also help prepare public-safe content — but only after explicit sanitization.

## Prompt Index

| File | When to use | Safe for public work? |
|---|---|---|
| [`import-lecture.md`](import-lecture.md) | After a lecture: turn raw notes into durable concept notes in proposal mode | No — works with lecture-derived material |
| [`daily-study.md`](daily-study.md) | Sit down for a study session: active recall from the review queue | No — works with private notes and mistakes |
| [`quiz-me.md`](quiz-me.md) | Test yourself on one topic or note interactively | No — works with private notes |
| [`explain-a-concept.md`](explain-a-concept.md) | Get a structured explanation of a single concept at your chosen depth | Both |
| [`improve-this-note.md`](improve-this-note.md) | Refine a rough or partial note into a well-organized durable note | Both |
| [`generate-flashcards.md`](generate-flashcards.md) | Create atomic, source-backed flashcards from course notes | No — works with private notes |
| [`prepare-for-an-exam.md`](prepare-for-an-exam.md) | Build a time-boxed study plan before an exam | No — works with private notes |
| [`log-a-mistake.md`](log-a-mistake.md) | Log a mistake in the structured Mistake Log format after a quiz or practice attempt | No — works with private mistakes |
| [`update-status.md`](update-status.md) | Decide whether a note's status should change based on evidence | No — works with private notes and mistakes |
| [`weekly-review.md`](weekly-review.md) | Plan a week of review targeting weak topics and stale dates | No — works with private notes and mistakes |

## Publication-Safety Reminder

Prompts that process raw lecture or source material are designed for private study. Do not use prompts to turn raw lecture or source material into public-facing content unless you are explicitly sanitizing it and `make validate-public` / `make pre-release` pass. AI summarization, rewriting, or paraphrasing alone does not make course material safe to publish. Keep `visibility` and `source-risk` metadata conservative.

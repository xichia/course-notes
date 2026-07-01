# Log a Mistake

## Prompt

I made a mistake during **[quiz / problem sheet / timed recall / exam]** and want to log it in the structured Mistake Log format.

First, ask me enough to fill in the five fields below. Then propose the entry and wait for confirmation before editing any file. Do not edit files unless I approve.

Target note (if known): **[note ID or file path, or leave blank to let the LLM suggest one]**

## Mistake Log Format

Every entry uses this five-field block under `## Mistake Log`:

```md
- date: YYYY-MM-DD
  source: problem-sheet, quiz, or timed-recall identifier
  mistake: Describe what went wrong.
  correction: Record the action or idea to apply next time.
  tags: [conceptual, procedure]
```

Rules:

- One line per field.
- `date` must be `YYYY-MM-DD` or `unknown` (only for migrating a genuine older mistake whose date was never recorded).
- `source` identifies what exposed the mistake (e.g., `quiz-03`, `problem-sheet-02`, `timed-recall-session`).
- `mistake` describes what went wrong in the student's own words.
- `correction` records what to do or remember next time.
- `tags` is an inline slug-style list such as `[conceptual, exam-trap]`.

## Suggested Tags

Use lowercase slug-style tags that describe the kind of mistake:

- `conceptual` — misunderstood a definition, relationship, or principle
- `procedure` — applied the right idea in the wrong order or missed a step
- `calculation` — arithmetic, algebraic, or numeric error
- `notation` — misused or misinterpreted notation
- `exam-trap` — fell for a common exam pitfall
- `definition` — could not state or recognise a key definition
- `proof` — flaw in reasoning, missing case, or incorrect deduction
- `memory` — could not recall a fact, formula, or method

You may use additional tags that fit the specific mistake. Keep them short, lowercase, and slug-style (one word or hyphenated).

## Proposal Steps

1. Read the target note's current `## Mistake Log` section and frontmatter.
2. Collect any missing information from me.
3. Propose the full entry in the format above.
4. Show the proposed text that would be added under `## Mistake Log`.
5. Ask for confirmation before editing the file.
6. If confirmed, add the entry above `_No personal mistakes logged yet._` (if present) or before any existing entries, preserving the rest of the file exactly.

## Safety Rules

- Keep the mistake description in the student's own words — do not copy problem-sheet text, exam question text, or lecturer-specific wording.
- Preserve the file's frontmatter fields exactly. Do not change `visibility`, `source-risk`, or any other metadata.
- Never upgrade `visibility` from `private` or change `source-risk` to `open-licensed`. Logging a mistake does not make course-derived content safer to publish.
- Do not turn private mistakes into public content.
- If the target note has `visibility: private` or `source-risk` other than `original`/`open-licensed`, do not suggest making the note public.
- Run `make all` after the edit is confirmed.

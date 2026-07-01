# Daily Study

## Prompt

Run a focused study session for **[available time]**.

1. Read `REVIEW_QUEUE.md` first and select the highest-priority item under `Review Now`. If that section is empty, select the highest-ranked upcoming item that fits the available time.
2. Use `manifest.json` to resolve its note ID and open that source note plus only essential prerequisites. Treat the queue as prioritization data, not course evidence.
3. Briefly tell me what you selected and why. Then quiz me with one active-recall question at a time and wait for each answer before continuing.
4. Diagnose each answer against the source note: separate what I recalled correctly, what is missing, and what is mistaken. Give a small correction and cite the note ID/path.
5. Adapt the next question to the diagnosis. Prefer explanation or a representative problem over recognition questions.

At the end, summarize the evidence from my answers. Suggest note, review-date, or Mistake Log updates only when that evidence supports them. Do not edit files unless I ask. Do not change `status` because of one answer, confidence alone, or improved wording; propose a change only when recall and application provide enough evidence. Never invent missing course content.

## Publication Safety

Treat the session, answers, mistakes, and course-derived notes as private. Preserve `visibility` and `source-risk`; do not create public-facing output unless I explicitly request a separately sanitized version under `docs/publication-policy.md`.

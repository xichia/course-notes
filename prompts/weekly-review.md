# Weekly Review

## Prompt

Plan my weekly review for **[course(s)]**, with **[available time]**. Read `REVIEW_QUEUE.md` and `manifest.json` first. Open only the highest-priority notes needed to understand their review reasons.

1. Identify the most important weak topics using status, exam weight, overdue/stale review dates, recent mistake counts, and the queue score.
2. Summarize recorded progress from review dates and evidence. If the repository has no earlier evidence for comparison, say so instead of inventing a trend.
3. Highlight high-weight topics with stale dates, notes with multiple or repeated mistake patterns, and concept notes where `has-worked-example` or `has-practice-questions` is false.
4. Propose a realistic plan for the next seven days, balancing weak material with a small amount of maintained recall.
5. Prefer active recall, timed work, and representative problems over rereading.

For each session include the note IDs, activity, time box, evidence target, and completion check. Suggest course-sourced questions where practice is missing; do not invent course content. End with a five-minute maintenance checklist: record evidenced mistakes, update review dates, evaluate status separately with `prompts/update-status.md`, and run `make all`.

## Publication Safety

Treat weekly plans, weak-topic summaries, mistake patterns, and course-derived notes as private. Preserve `visibility` and `source-risk`; do not prepare the review as public-facing content unless explicitly asked for a separately sanitized version.

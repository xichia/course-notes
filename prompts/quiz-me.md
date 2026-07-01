# Quiz Me

Use this prompt with repository access, or provide `manifest.json` and the note files it selects.

## Prompt

Read `manifest.json` first. Select notes matching **[course/topic]**, prioritizing **[status, exam weight, or specific note IDs]**. Open only those notes and any prerequisites essential to the quiz.

Quiz me for **[number or duration]** using active recall and short problems rather than recognition questions. Ask one question at a time and wait for my answer. After each answer:

1. Judge it against the selected notes.
2. Say what was correct, missing, or mistaken.
3. Give the smallest useful correction and cite the source note ID/path.
4. Adjust the next question to my performance.

Do not introduce unsupported course facts. At the end, summarize demonstrated strengths, weak points, and any candidate five-field Mistake Log entries. Treat any status change as a separate proposal using `prompts/update-status.md`; one quiz alone is normally evidence for re-testing, not an upgrade.

## Publication Safety

Treat questions derived from course notes and all student answers as private. Preserve `visibility` and `source-risk`; do not publish course-derived quiz material or personal study evidence.

# Generate Flashcards

## Prompt

Read `manifest.json` first and select the smallest set of notes matching **[course/topic/note IDs]**. Prioritize **[weak/high-weight/overdue/all]** material and open the selected source notes.

Generate **[number]** atomic flashcards. Test definitions, conditions, connections, procedures, and known mistakes; avoid trivia and ambiguous prompts. Each answer must be supported by the notes.

Return Markdown in this form:

```text
## Card 1
Front: ...
Back: ...
Source: note-id (path)
Tags: course, topic, difficulty
```

Keep one recall target per card. Flag any useful card that would require external information instead of inventing an answer.

## Publication Safety

Flashcards derived from lectures, problem sheets, exams, LMS content, or personal mistakes remain private. Preserve `visibility` and `source-risk`; for an explicitly requested public set, use only independently written generic or synthetic material after manual sanitization.

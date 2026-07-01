# Improve or Convert a Note

## Prompt

Turn **[rough lecture-note path, concept-note path, or note ID]** into durable concept notes for **[course]**. Read `manifest.json`, the source note, and only directly relevant prerequisite/related notes.

Preserve the original meaning and keep the rough lecture note as the chronological source unless I explicitly ask to replace it. First identify the distinct concepts it contains. For each concept, update an existing concept note when the manifest shows a match; otherwise propose a new readable filename and permanent ID.

Organize durable material into clear sections for definition, intuition, procedure or conditions, worked examples, common traps, structured personal mistakes, practice questions, and related ideas. Do not turn a general warning into a personal Mistake Log item without evidence that I made that mistake, and do not invent practice questions when no course-supported question is available.

Update frontmatter carefully:

- preserve an existing filename and `id`;
- preserve `status`, `last-reviewed`, and `review-after` unless study evidence justifies a change;
- preserve `visibility` and `source-risk`; better writing does not reduce publication risk;
- record the rough lecture note in `source` where appropriate;
- add `prerequisites` and `related` only when those IDs already exist in `manifest.json`;
- use relative Markdown links only.

Do not silently add facts. Clearly label external additions with provenance. Mark missing or ambiguous course information as `[TODO: verify from lecture/text/source]` rather than guessing. Show the proposed file changes or edit them only as requested, then run validation and regenerate derived files.

Do not produce a public-facing version unless explicitly asked to sanitize a separate release candidate. Remove protected course expression, problem/exam text, lecturer-specific examples, and LMS references; prefer synthetic examples and never upgrade `visibility` without explicit evidence and instruction.

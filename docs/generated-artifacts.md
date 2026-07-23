# Notes and Generated Artifacts

> **Experimental, pre-1.0 contract.** It exists because the [study-layer
> workflow](study-layer-workflow.md) writes Markdown that is not a note, and note validation
> had no way to tell the difference.

A courses tree contains two kinds of Markdown: **notes**, which a person maintains and which
owe the full frontmatter schema in [`TEMPLATE.md`](../TEMPLATE.md); and **generated artifacts**,
which a builder or capture step writes and which deliberately carry no note frontmatter.

`discover_note_paths()` decides which is which. Everything it returns is validated as a note.

## Why frontmatter cannot be the signal

A generated artifact has no frontmatter. So does a note whose frontmatter a person just broke.
Treating "no frontmatter" as "not a note" would silently drop exactly the notes that most need
to fail validation. The contract therefore decides from **location and declaration**, never from
a file's contents.

## What counts as a note

Every `*.md` under the scanned courses directory, **except**:

- `README.md` at any depth — navigational, never a note;
- anything under a course's `study/` directory (`<courses>/<course>/study/**`), reserved by the
  [study-module contract](study-module-contract.md);
- anything matching a pattern in the tree's [`.generated-artifacts`](#declaring-artifacts) file.

Everything else is a note. A file is never excluded for looking generated — an ALL-CAPS name, a
missing frontmatter block, or a `study` directory nested inside `concepts/` all stay in the note
set until something above says otherwise.

## What counts as a generated artifact

| Artifact | How it is recognised |
|---|---|
| Study-module files (`STUDY_GUIDE.md`, `QUESTION_BANK.md`, `ANSWER_KEY.md`, `COVERAGE_MATRIX.md`) | `<course>/study/<topic>/` — built in |
| Course-level study-layer output (indexes, revision plans, source-issue logs) | `<course>/study/` — built in |
| LMS or source-system captures, sync and import reports | declared |
| Curation, review, correction, verification, and acceptance records | declared |
| A future artifact type not yet imagined | declared |

Study modules are built in because the public study-module contract already reserves `study/`
for them. Everything else is repository-local and must be declared, so no repository inherits
another's exclusions.

## Declaring artifacts

Put a `.generated-artifacts` file in the courses directory being scanned — `courses/` for the
public tree, `private/courses/` for a private study tree. It lives beside the courses it
describes, so a private tree never has to name its paths in a public repository.

```text
# One glob per line, relative to this directory, POSIX separators.
# Blank lines and lines starting with '#' are ignored.

*/lms-import/**        # a whole captured subtree, in every course
*/COVERAGE_AUDIT.md    # one named report at a course root
*/*_VERIFICATION.md    # a recurring family of workflow records
```

- `*` and `?` stay inside one path segment; `**` spans whole segments.
- Patterns are matched against the path relative to the courses directory, so anchoring a
  pattern with a leading `*/` restricts it to a course root and keeps it out of `concepts/`,
  `lectures/`, `problem-sheets/`, and `exam/`.
- Absolute patterns, `..`, `\` separators, and catch-alls (`*`, `**`, `*.md`, `**/*`, `**/*.md`)
  are refused: a declaration that silences a whole tree is a mistake, not a configuration.
- A pattern matching nothing raises a warning, so the file cannot quietly go stale.
- `validate_notes.py` prints the artifact count beside the note count, so a growing exclusion
  set is visible on every run.

## Naming that keeps declarations safe

Notes are kebab-case and live in the typed subdirectories the
[repository layout](repository-layout.md) defines. Generated artifacts use ALL-CAPS names at a
course root or inside a dedicated subtree. Keeping to that split is what lets a declaration use
a family pattern like `*/*_REVIEW.md` without any risk of shadowing a note.

## What the contract deliberately does not do

- It does not validate generated artifacts. Study modules are checked by a study-module
  validator against the [study-layer validation model](study-layer-validation.md); other
  artifacts are checked by whatever produced them. Note validation never checked these files
  beyond rejecting their missing frontmatter, so nothing is lost by excluding them.
- It does not relax any note check. A declared artifact is out of scope; a note in scope is held
  to exactly the same schema as before.
- It does not make a non-Markdown decision. A normalized transcript is still written as `.txt`
  (see [lecture transcripts](lecture-transcripts.md)) because evidence should not be Markdown at
  all, declaration or no declaration.

# Course Onboarding

Real, unsanitized course material belongs under the ignored private workspace. Keep
`visibility: private`, retain a conservative `source-risk`, and leave unknown administrative
facts explicitly unknown.

> The outer public repository does not track or back up private work. Set up an independent
> encrypted backup before adding irreplaceable material.

## Manual onboarding

Choose a conservative lowercase course slug such as `fluid-mechanics`. Confirm that its final
directory does not already exist; never merge this setup into an existing course directory.

The following commands are for a POSIX shell on macOS or Linux. Run them as one block: the `&&`
chain stops on the first failure, so no later command runs. On Windows, create the same directories
and copies with PowerShell or File Explorer while preserving the same refusal of an existing
destination.

```bash
mkdir -p private/courses && \
mkdir private/courses/course-code && \
mkdir private/courses/course-code/concepts private/courses/course-code/lectures && \
mkdir private/courses/course-code/problem-sheets private/courses/course-code/exam && \
cp templates/course.md private/courses/course-code/course.md && \
cp templates/syllabus.md private/courses/course-code/syllabus.md
```

The second command intentionally fails if `private/courses/course-code/` already exists. The
resulting layout is:

```text
private/courses/course-code/
├── concepts/
├── lectures/
├── problem-sheets/
├── exam/
├── course.md
└── syllabus.md
```

Open both copied files in an editor. Replace every `course-code`, `Course Title`, and term or
administrative placeholder consistently. Keep `visibility: private` and a conservative
`source-risk` unless verified evidence supports a more specific value. Once both required note
files exist and their placeholders have been replaced, run:

```bash
make study-all
```

This validates and refreshes lightweight private notes; it does not configure Git, a remote, or
a backup.

## Record authoritative course information

In `course.md`, replace unknowns only when an official source supports the value. Record the
real title, term, lecturer, assessment structure, dates, and resource references without
guessing.

In `syllabus.md`, copy or faithfully summarize official outcomes and coverage. Put uncertain
claims under `Unclear or Unconfirmed`. AI rewriting does not make restricted material public.

## Add private study material

- Preserve rough source records under `lectures/`.
- Extract durable, one-concept notes under `concepts/` using `TEMPLATE.md`.
- Keep attempts and corrections under `problem-sheets/`.
- Put verified exam-format maps or revision summaries under `exam/`.
- Preserve source references, uncertainty, and stable note IDs.

For a non-generating validation check between edits, run:

```bash
make study-validate
```

These targets cover Markdown notes using the lightweight schema. They are not generic validators
for raw attachments, LMS imports, source packs, or experimental five-file study modules.

To create a public candidate later, separately sanitize a derivative into `courses/`, assign an
honest allowed publication classification, and complete the
[public-release checklist](public-release-checklist.md). Keeping a file private is not itself
sanitization.

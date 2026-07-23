# Lecture Transcripts

How to bring a lecture recording transcript into a study repository without letting it
become either a liability or a wall of unusable text.

A transcript is **source evidence**, in the same category as slide decks and handouts.
It is not a note, and turning it into one by pasting it into Markdown is the main
failure this page exists to prevent.

## Publication safety

Transcripts are `lecture-derived`: verbatim recorded expression, usually carrying
identifiable staff, room, and cohort detail. They stay private.

The repository's `.gitignore` already excludes `transcripts/` and `recordings/`
alongside the other source-material directories, so a transcript placed in a
conventionally named directory is ignored by default. In a split public/private
layout it is additionally covered by the ignored private tree.

Never publish a transcript, a passage from one, or a derived file that reproduces one
at length. Notes *about* a transcript are publishable only under the normal
sanitization rules in `docs/publication-policy.md`.

## The four artifacts

Keep these distinct. Collapsing them is what makes transcripts unreviewable.

| Artifact | Role | Hand-edited? |
|---|---|---|
| Raw transcript | Immutable source, exactly as supplied | **Never** |
| Normalized transcript | Readable, timestamp-anchored derivation | **Never** — regenerate |
| Provenance record | Where it came from, what produced what | Yes |
| Lecture note | Study material citing the above | Yes |

**Preserve the raw file.** Move it into place rather than rewriting it, and record a
checksum before and after so byte preservation is provable. A normalization step that
edits its input destroys the only authoritative copy.

## Normalized transcripts are not notes

A caption export is thousands of fragments of a few words each — unreadable as
evidence and useless as a citation target. Normalizing means merging fragments into
timestamp-anchored paragraphs. It must not reword, correct, or complete anything.

Write the normalized file as `.txt`, not `.md`.

`discover_note_paths()` treats every `*.md` under the scanned courses directory as a
note owing full frontmatter unless it is a `README.md`, sits in a course's `study/`
module tree, or is declared in that tree's `.generated-artifacts` file — see
[generated artifacts](generated-artifacts.md). A normalized transcript written as
`.md` matches none of those, so it enters the validation set, fails it, and — because
`build_review_queue.py` and `build_manifest.py` refuse to write when validation fails
— blocks regeneration of the review queue for the whole repository. Choosing `.txt`
keeps evidence out of the note set without any declaration at all, which is the right
answer for a transcript: it is source evidence, not a document the repository authors.

## Provenance to record

Enough to answer, later, without rerunning anything:

- which course, teaching week, lecture, and date it belongs to;
- where it came from and how it was acquired;
- whether each file is raw, cleaned, or derived;
- what transformation produced each derived file, and with what tool and settings;
- whether timestamps and speaker labels were retained;
- which file is authoritative for citation;
- a frank quality assessment.

State plainly whether the transformation was lossy and in what way.

## Speaker labels

Pass them through exactly as supplied. Never invent, resolve, or infer a name that the
export did not contain — some exporters anonymise speakers, and re-identifying them is
a privacy decision no tool should make silently. Record in the provenance file which
convention the source used.

## Transcript quality is not uniform

Automatic speech recognition is reliable for continuous prose and unreliable for
everything a technical lecture cares about most. Expect:

- **code, commands, and filenames rendered as spoken words** — a command's flags
  become separate words, a filename's extension becomes a different word;
- **mangled proper nouns** — library, tool, and person names;
- **dropped or altered digits** in worked numeric examples;
- **low-confidence noise** before the session starts and after it ends;
- **truncation** when the recording stops early.

So, as a standing rule:

> Take **what was said and emphasised** from the transcript. Take **code, syntax, and
> numbers** from the written course materials. Where the two disagree on a technical
> detail, the written material wins.

If the export carries per-cue confidence scores, keep them — they mark which passages
are worth double-checking. Record known defects in the provenance file; the specific
mangled tokens are more useful to a future reader than an average confidence score.

## Deriving the note

The lecture note is where study value lives. It cites the transcript; it does not
reproduce it.

- Cite stable `[HH:MM:SS]` anchors so a claim can be checked against the recording.
- Separate what the lecture **stated** from your **inference** from it, from a **study
  heuristic**. Label each claim so a later reader can tell them apart without rereading
  the transcript.
- Keep anything the transcript cannot settle in the note's **Unclear or Verify**
  section rather than resolving it from a low-confidence passage.
- Mark speculative assessment relevance as speculative. A lecturer's passing emphasis
  is not a statement about what is assessed.
- Where a transcript claim can be checked against material already in the repository,
  check it and record the outcome — agreement is worth recording, and disagreement is
  worth more.

Automated extraction is fine, but present its output as a proposal to review, not as
an authority. Do not invent content the transcript does not contain.

## Checklist

1. Store the raw export in an ignored source-material directory; verify the checksum
   across the move.
2. Normalize it to timestamp-anchored `.txt` with a deterministic, non-destructive tool.
3. Write the provenance record, including known defects.
4. Write or update the lecture note from `templates/lecture.md`, citing anchors.
5. Re-run the repository's validation and regeneration commands.
6. Confirm no transcript file, and no passage from one, has entered public content.

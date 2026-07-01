import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from build_manifest import GENERATED_WARNING as MANIFEST_WARNING, build_manifest
from build_review_queue import GENERATED_WARNING as REVIEW_WARNING, build_queue, is_review_candidate, rank_note
from studylib import (
    ROOT,
    Note,
    format_issue,
    mistake_summary,
    parse_frontmatter,
    parse_mistake_log,
    practice_question_counts,
    validate_repository,
)


VALID_TEXT = """---
id: demo-example
title: Example Concept
course: demo
type: concept
topic: examples
aliases: [sample]
prerequisites: []
related: []
exam-weight: medium
status: learning
last-reviewed: 2026-06-01
review-after: 2026-06-15
source: "Test fixture"
visibility: public-original
source-risk: original
---

# Example Concept

## Definition

A fixture.

## Intuition

An intuition.

## Worked Example

An example.

## Common Mistakes

- A general warning.

## Mistake Log

- date: 2026-06-25
  source: quiz-01
  mistake: Applied the procedure in the wrong order.
  correction: Check the conditions before applying the procedure.
  tags: [exam-trap, procedure]

- date: 2026-04-01
  source: problem-sheet-00
  mistake: Used inconsistent notation.
  correction: Define symbols before beginning the solution.
  tags: [notation]

## Practice Questions

### Easy

- Test question A.

### Medium

_No practice questions recorded yet._

### Exam-style

- Test question B.

## Related

_None._
"""


def make_note(text=VALID_TEXT, filename="example.md"):
    metadata, body, errors = parse_frontmatter(text)
    return Note(ROOT / "courses" / "demo" / "concepts" / filename, metadata, body, text, tuple(errors))


def note_from_template(template_name, destination_name):
    text = (ROOT / "templates" / template_name).read_text(encoding="utf-8")
    metadata, body, errors = parse_frontmatter(text)
    return Note(
        ROOT / "courses" / "course-code" / destination_name,
        metadata,
        body,
        text,
        tuple(errors),
    )


class StudyLibTests(unittest.TestCase):
    def test_course_and_syllabus_templates_validate_together(self):
        course = note_from_template("course.md", "course.md")
        syllabus = note_from_template("syllabus.md", "syllabus.md")
        self.assertEqual([], validate_repository([course, syllabus]))
        for marker in (
            "| Term |",
            "| Lecturer |",
            "| Exam date |",
            "## Assessment Structure",
            "## Key Resources",
            "## Current Weak Areas",
            "## Current Priorities",
        ):
            self.assertIn(marker, course.body)
        for heading in (
            "## Official Learning Outcomes",
            "## Weekly Topics",
            "## Assessment Topics",
            "## Exam-Relevant Sections",
            "## Excluded Topics",
            "## Lecturer Hints",
            "## Source Links or References",
        ):
            self.assertIn(heading, syllabus.body)

    def test_raw_lecture_template_is_valid_reference_material(self):
        lecture = note_from_template("lecture.md", "lectures/yyyy-mm-dd-topic.md")
        self.assertEqual([], validate_repository([lecture]))
        self.assertFalse(is_review_candidate(lecture))

    def test_onboarding_prompt_and_checklists_exist(self):
        required = [
            "docs/course-onboarding.md",
            "docs/friction-test.md",
            "docs/publication-policy.md",
            "docs/public-release-checklist.md",
            "prompts/import-lecture.md",
            "prompts/daily-study.md",
            "prompts/update-status.md",
            "prompts/weekly-review.md",
        ]
        self.assertTrue(all((ROOT / path).is_file() for path in required))

        prompt = (ROOT / "prompts" / "import-lecture.md").read_text(encoding="utf-8")
        self.assertIn("leave it intact", prompt)
        self.assertIn("Do not invent missing definitions", prompt)
        self.assertIn("Stop and ask for approval", prompt)

    def test_allowed_publication_metadata_values(self):
        visibilities = ("private", "public-framework", "public-original", "public-open-licensed")
        source_risks = (
            "lecture-derived",
            "problem-sheet-derived",
            "exam-derived",
            "lms-derived",
            "open-licensed",
            "original",
            "unknown",
        )
        for visibility in visibilities:
            note = make_note(VALID_TEXT.replace("visibility: public-original", f"visibility: {visibility}"))
            self.assertFalse(any("field 'visibility'" in issue.message for issue in validate_repository([note])))
        for source_risk in source_risks:
            note = make_note(VALID_TEXT.replace("source-risk: original", f"source-risk: {source_risk}"))
            self.assertFalse(any("field 'source-risk'" in issue.message for issue in validate_repository([note])))

    def test_invalid_publication_metadata_fails_normal_validation(self):
        text = VALID_TEXT.replace("visibility: public-original", "visibility: public-ish").replace(
            "source-risk: original", "source-risk: assumed-safe"
        )
        messages = [issue.message for issue in validate_repository([make_note(text)])]
        self.assertTrue(any("field 'visibility': invalid value" in message for message in messages))
        self.assertTrue(any("field 'source-risk': invalid value" in message for message in messages))

        list_values = VALID_TEXT.replace("visibility: public-original", "visibility: [private]").replace(
            "source-risk: original", "source-risk: [unknown]"
        )
        list_messages = [issue.message for issue in validate_repository([make_note(list_values)])]
        self.assertTrue(any("field 'visibility': invalid value" in message for message in list_messages))
        self.assertTrue(any("field 'source-risk': invalid value" in message for message in list_messages))

    def test_public_release_rejects_private_lecture_derived_note(self):
        text = VALID_TEXT.replace("visibility: public-original", "visibility: private").replace(
            "source-risk: original", "source-risk: lecture-derived"
        )
        messages = [issue.message for issue in validate_repository([make_note(text)], public_release=True)]
        self.assertTrue(any("visibility is 'private'" in message for message in messages))
        self.assertTrue(any("source-risk 'lecture-derived'" in message for message in messages))

    def test_public_release_accepts_synthetic_framework_note(self):
        text = VALID_TEXT.replace("visibility: public-original", "visibility: public-framework")
        self.assertEqual([], validate_repository([make_note(text)], public_release=True))

    def test_public_release_rejects_unknown_or_missing_provenance(self):
        unknown = make_note(VALID_TEXT.replace("source-risk: original", "source-risk: unknown"))
        self.assertTrue(
            any("source-risk 'unknown'" in issue.message for issue in validate_repository([unknown], public_release=True))
        )

        missing = make_note(VALID_TEXT.replace("source-risk: original\n", ""))
        self.assertTrue(
            any("missing 'source-risk'" in issue.message for issue in validate_repository([missing], public_release=True))
        )

    def test_readme_links_publication_policy_and_release_checklist(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[docs/publication-policy.md](docs/publication-policy.md)", readme)
        self.assertIn("[docs/public-release-checklist.md](docs/public-release-checklist.md)", readme)

    def test_valid_note_passes_and_extracts_mistake_evidence(self):
        note = make_note()
        self.assertEqual([], validate_repository([note]))
        entries, errors = parse_mistake_log(note)
        self.assertEqual([], errors)
        self.assertEqual(2, len(entries))
        self.assertEqual(
            {"count": 2, "recent": 1, "latest-date": "2026-06-25", "tags": ["exam-trap", "notation", "procedure"]},
            mistake_summary(note, date(2026, 6, 30)),
        )

    def test_malformed_mistake_entry_reports_fields_and_fix(self):
        text = VALID_TEXT.replace("date: 2026-06-25", "date: 2026-99-25", 1).replace(
            "  correction: Check the conditions before applying the procedure.\n", "", 1
        ).replace("tags: [exam-trap, procedure]", "tags: procedure", 1)
        messages = [issue.message for issue in validate_repository([make_note(text)])]
        self.assertTrue(any("entry 1, field 'date': invalid value" in message for message in messages))
        self.assertTrue(any("entry 1, field 'correction': missing" in message for message in messages))
        self.assertTrue(any("entry 1, field 'tags': must be an inline list" in message for message in messages))

    def test_practice_question_detection_by_difficulty(self):
        self.assertEqual(
            {"easy": 1, "medium": 0, "exam-style": 1, "total": 2},
            practice_question_counts(make_note()),
        )

    def test_concept_requires_practice_questions_section(self):
        text = VALID_TEXT.replace(
            "## Practice Questions\n\n### Easy\n\n- Test question A.\n\n### Medium\n\n"
            "_No practice questions recorded yet._\n\n### Exam-style\n\n- Test question B.\n\n",
            "",
        )
        issues = validate_repository([make_note(text)])
        self.assertTrue(any("section '## Practice Questions': missing" in issue.message for issue in issues))

    def test_validation_catches_missing_field_bad_date_and_unknown_reference(self):
        text = VALID_TEXT.replace("course: demo\n", "").replace(
            "review-after: 2026-06-15", "review-after: 2026-99-99"
        ).replace("related: []", "related: [missing-id]")
        messages = [issue.message for issue in validate_repository([make_note(text)])]
        self.assertTrue(any("frontmatter field 'course': missing" in message for message in messages))
        self.assertTrue(any("not a real calendar date" in message for message in messages))
        self.assertTrue(any("unknown note id 'missing-id'" in message for message in messages))

    def test_validation_catches_duplicate_ids(self):
        second_text = VALID_TEXT.replace("title: Example Concept", "title: Second Concept").replace(
            "# Example Concept", "# Second Concept"
        )
        issues = validate_repository([make_note(), make_note(second_text, "second.md")])
        self.assertTrue(any('duplicate value "demo-example"' in issue.message for issue in issues))

    def test_absolute_local_markdown_link_is_rejected_with_a_fix(self):
        machine_path = "/" + "Users/example/course-notes/note.md"
        text = VALID_TEXT.replace("_None._", f"[Machine-only note]({machine_path})")
        issues = validate_repository([make_note(text)])
        message = next(issue.message for issue in issues if "absolute local target" in issue.message)
        self.assertIn(f'"{machine_path}"', message)
        self.assertIn("replace it with a path relative to this Markdown file", message)

    def test_invalid_status_message_names_value_and_allowed_values(self):
        text = VALID_TEXT.replace("status: learning", "status: partial")
        issues = validate_repository([make_note(text)])
        issue = next(issue for issue in issues if "field 'status'" in issue.message)
        self.assertEqual(
            "courses/demo/concepts/example.md: ERROR: frontmatter field 'status': invalid value \"partial\"; "
            "expected one of: archived, learning, mastered, new, reference, shaky, solid",
            format_issue(issue),
        )

    def test_review_rank_uses_all_priority_signals(self):
        item = rank_note(make_note(), date(2026, 6, 30))
        factors = "; ".join(item.factors)
        self.assertIn("learning status", factors)
        self.assertIn("medium exam weight", factors)
        self.assertIn("2 logged mistakes", factors)
        self.assertIn("1 mistake in the last 30 days", factors)
        self.assertIn("reviewed 29 days ago", factors)
        self.assertIn("overdue by 15 days", factors)
        self.assertEqual(127, item.score)
        self.assertTrue(item.needs_attention)

    def test_review_rank_adds_missing_practice_and_high_weight_shaky_bonus(self):
        text = VALID_TEXT.replace("status: learning", "status: shaky").replace(
            "exam-weight: medium", "exam-weight: high"
        ).replace("- Test question A.", "_No practice questions recorded yet._").replace(
            "- Test question B.", "_No practice questions recorded yet._"
        )
        item = rank_note(make_note(text), date(2026, 6, 30))
        factors = "; ".join(item.factors)
        self.assertIn("no practice questions (+10)", factors)
        self.assertIn("high-weight + shaky combination (+15)", factors)
        self.assertEqual(177, item.score)

    def test_manifest_generation_and_warning(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            output = Path(temp_dir) / "manifest.json"
            self.assertEqual(0, build_manifest(output))
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(MANIFEST_WARNING, manifest["_generated"])
            self.assertEqual(3, manifest["format-version"])
            self.assertEqual(4, manifest["count"])
            self.assertTrue(all(not Path(note["file"]).is_absolute() for note in manifest["notes"]))
            demo = next(note for note in manifest["notes"] if note["id"] == "demo-layered-recall")
            self.assertEqual(0, demo["mistake-count"])
            self.assertEqual([], demo["mistake-tags"])
            self.assertTrue(demo["has-practice-questions"])
            self.assertEqual("public-original", demo["visibility"])
            self.assertEqual("original", demo["source-risk"])

    def test_review_queue_generation_and_warning(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            output = Path(temp_dir) / "review-queue.md"
            self.assertEqual(0, build_queue(output, date(2026, 6, 30)))
            content = output.read_text(encoding="utf-8")
            self.assertEqual(REVIEW_WARNING, content.splitlines()[0])
            self.assertIn("[Layered Recall](courses/demo-course/concepts/layered-recall.md)", content)
            self.assertIn("## How Priority Is Scored", content)
            self.assertIn("**Mistakes:** +5 per logged mistake", content)
            self.assertIn("**Combined risk:** high exam weight together with shaky status +15", content)

    def test_existing_repository_notes_remain_valid(self):
        errors = [issue for issue in validate_repository() if issue.level == "error"]
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()

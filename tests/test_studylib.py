import json
import os
import re
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from build_manifest import GENERATED_WARNING as MANIFEST_WARNING, build_manifest
from build_review_queue import GENERATED_WARNING as REVIEW_WARNING, build_queue, is_review_candidate, rank_note
from mark_reviewed import mark_reviewed
from studylib import (
    GeneratedArtifactError,
    GenerationDateError,
    ROOT,
    Note,
    discover_generated_artifact_paths,
    discover_note_paths,
    format_issue,
    generation_date,
    has_substantive_section,
    load_blocklist,
    load_generated_artifact_patterns,
    mistake_summary,
    parse_frontmatter,
    parse_mistake_log,
    portability_issues,
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

    def test_lecture_template_carries_transcript_provenance_affordance(self):
        lecture = note_from_template("lecture.md", "lectures/yyyy-mm-dd-topic.md")
        self.assertIn("Recording or transcript:", lecture.body)
        self.assertIn("docs/lecture-transcripts.md", lecture.body)

    def test_transcript_guidance_documents_the_evidence_contract(self):
        doc = (ROOT / "docs" / "lecture-transcripts.md").read_text(encoding="utf-8")
        for marker in (
            "## Publication safety",
            "## The four artifacts",
            "## Normalized transcripts are not notes",
            "## Provenance to record",
            "## Speaker labels",
        ):
            self.assertIn(marker, doc)
        # The .txt rule exists because .md would enter the note-validation set.
        self.assertIn("`.txt`, not `.md`", doc)
        self.assertIn("discover_note_paths()", doc)

    def test_import_lecture_prompt_covers_transcript_sources(self):
        prompt = (ROOT / "prompts" / "import-lecture.md").read_text(encoding="utf-8")
        self.assertIn("If the Source Is a Recording Transcript", prompt)
        self.assertIn("byte-for-byte intact", prompt)
        self.assertIn("Never bulk-copy the transcript into a note", prompt)
        self.assertIn("Never resolve or infer a name the export did not contain", prompt)

    def test_source_material_directories_are_ignored_by_default(self):
        """Transcripts and recordings must be ignored without any per-course setup."""
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for directory in ("transcripts/", "recordings/", "slides/", "handouts/"):
            self.assertIn(directory, gitignore)

    def test_onboarding_prompt_and_checklists_exist(self):
        required = [
            "docs/course-onboarding.md",
            "docs/friction-test.md",
            "docs/lecture-transcripts.md",
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

        onboarding = (ROOT / "docs" / "course-onboarding.md").read_text(encoding="utf-8")
        self.assertIn("## Manual onboarding", onboarding)
        self.assertIn("make study-all", onboarding)

        project_state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
        self.assertIn("Automated course initialization remains deferred", project_state)

    def test_published_onboarding_block_refuses_existing_course_without_later_writes(self):
        onboarding = (ROOT / "docs" / "course-onboarding.md").read_text(encoding="utf-8")
        manual_section = onboarding.split("## Manual onboarding\n", 1)[1].split(
            "\n## Record authoritative course information", 1
        )[0]
        shell_blocks = re.findall(r"```bash\n(.*?)\n```", manual_section, flags=re.DOTALL)
        self.assertEqual(2, len(shell_blocks))
        published_creation_block = shell_blocks[0]

        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            templates = fixture_root / "templates"
            templates.mkdir()
            templates.joinpath("course.md").write_text("template course\n", encoding="utf-8")
            templates.joinpath("syllabus.md").write_text("template syllabus\n", encoding="utf-8")

            course_dir = fixture_root / "private" / "courses" / "course-code"
            course_dir.mkdir(parents=True)
            course_file = course_dir / "course.md"
            sentinel = "existing course sentinel\n"
            course_file.write_text(sentinel, encoding="utf-8")
            course_identity = (course_dir.stat().st_dev, course_dir.stat().st_ino)
            course_file_identity = (course_file.stat().st_dev, course_file.stat().st_ino)

            later_paths = (
                course_dir / "syllabus.md",
                course_dir / "concepts",
                course_dir / "lectures",
                course_dir / "problem-sheets",
                course_dir / "exam",
            )
            self.assertTrue(all(not path.exists() for path in later_paths))

            result = subprocess.run(
                ["/bin/sh", "-c", published_creation_block],
                cwd=fixture_root,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertEqual(course_identity, (course_dir.stat().st_dev, course_dir.stat().st_ino))
            self.assertEqual(
                course_file_identity,
                (course_file.stat().st_dev, course_file.stat().st_ino),
            )
            self.assertEqual(sentinel, course_file.read_text(encoding="utf-8"))
            self.assertTrue(all(not path.exists() for path in later_paths))

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

    def test_https_clone_url_is_not_mistaken_for_windows_path(self):
        self.assertEqual(
            [],
            portability_issues(
                "git clone https://github.com/example/course-notes.git",
                "README.md",
            ),
        )

    def test_http_url_spans_with_local_path_shapes_are_not_reported(self):
        text = " ".join(
            (
                "https://github.com/xichia/course-notes.git",
                "https://example.invalid/docs/C:/Users/name/guide",
                "https://example.invalid/path/Users/name/guide",
                "(https://example.invalid/a:b/c),",
                "(https://example.invalid/a_(b)/Users/name/guide),",
                "[guide](https://example.invalid/C:/Users/name/guide)",
            )
        )
        self.assertEqual([], portability_issues(text, "README.md"))

    def test_real_local_paths_are_reported(self):
        paths = (
            "/Users/name/course-notes",
            "/home/name/course-notes",
            r"C:\Users\name\course-notes",
            "C:/Users/name/course-notes",
            "file:///Users/name/course-notes",
            "file:///C:/Users/name/course-notes",
        )
        for path in paths:
            with self.subTest(path=path):
                issues = portability_issues(f"Open {path} now", "README.md")
                self.assertTrue(issues)
                self.assertIn(path, issues[0].message)

    def test_url_masking_preserves_adjacent_paths_and_line_numbers(self):
        text = (
            "https://example.invalid/docs/C:/Users/name/guide\n"
            r"https://example.invalid/path\C:\Users\name\course-notes"
            " and /Users/other/course-notes"
        )
        issues = portability_issues(text, "README.md")
        self.assertEqual(2, len(issues))
        self.assertTrue(all("line 2" in issue.message for issue in issues))
        self.assertTrue(any(r"C:\Users\name\course-notes" in issue.message for issue in issues))
        self.assertTrue(any("/Users/other/course-notes" in issue.message for issue in issues))

    def test_punctuation_adjacent_drive_roots_end_url_spans(self):
        for delimiter in (",", ";", ".", "!"):
            for separator in ("\\", "/"):
                local_path = f"C:{separator}Users{separator}name{separator}course-notes"
                text = f"https://example.invalid/path{delimiter}{local_path}"
                with self.subTest(delimiter=delimiter, separator=separator):
                    issues = portability_issues(text, "README.md")
                    self.assertEqual(1, len(issues))
                    self.assertIn(local_path, issues[0].message)
                    self.assertIn("line 1", issues[0].message)

    def test_structural_url_drive_shapes_remain_masked(self):
        urls = (
            "https://example.invalid/docs/C:/Users/name/guide",
            "https://example.invalid/path?next=C:/Users/name/guide",
            "https://example.invalid/path?x=1&next=C:/Users/name/guide",
            "https://example.invalid/path#C:/Users/name/guide",
        )
        self.assertEqual([], portability_issues(" ".join(urls), "README.md"))

    def test_url_punctuation_parentheses_and_multiple_paths_on_one_line(self):
        text = (
            "(https://example.invalid/a_(b)/guide). "
            r"https://example.invalid/path,C:\Users\one\course-notes "
            "https://example.invalid/path#C:/Users/url/guide "
            "https://example.invalid/path!D:/Users/two/course-notes"
        )
        issues = portability_issues(text, "README.md")
        self.assertEqual(2, len(issues))
        self.assertTrue(all("line 1" in issue.message for issue in issues))
        self.assertTrue(any(r"C:\Users\one\course-notes" in issue.message for issue in issues))
        self.assertTrue(any("D:/Users/two/course-notes" in issue.message for issue in issues))

    def test_file_url_markdown_destination_is_still_local(self):
        issues = portability_issues(
            "[local](file:///C:/Users/name/course-notes)",
            "README.md",
        )
        self.assertEqual(1, len(issues))
        self.assertIn("absolute local target", issues[0].message)

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

    def test_note_directly_under_courses_is_rejected(self):
        text = "---\nid: bad-placement\ntitle: Bad\ntype: reference\ntopic: bad\ncourse: foo\naliases: []\nprerequisites: []\nrelated: []\nexam-weight: none\nstatus: reference\nlast-reviewed:\nreview-after:\nsource: test\n---\n\n# Bad"
        metadata, body, errors = parse_frontmatter(text)
        note = Note(ROOT / "courses" / "foo.md", metadata, body, text, tuple(errors))
        issues = validate_repository([note])
        self.assertTrue(any("move this note under" in issue.message for issue in issues))

    def test_public_release_rejects_lms_source_in_public_note(self):
        for term in ("lms", "moodle", "lecture slide", "exam question", "problem sheet", "course pack"):
            text = VALID_TEXT.replace("source: \"Test fixture\"", f"source: \"{term} reference\"")
            issues = validate_repository([make_note(text)], public_release=True)
            self.assertTrue(any("suspicious term" in issue.message for issue in issues), f"term '{term}' not caught")

    def test_public_release_allows_clean_source_in_public_note(self):
        text = VALID_TEXT.replace("source: \"Test fixture\"", "source: \"Synthetic example\"")
        issues = validate_repository([make_note(text)], public_release=True)
        self.assertFalse(any("suspicious term" in issue.message for issue in issues))

    def test_placeholder_bullet_not_counted_as_practice_question(self):
        text = VALID_TEXT.replace("- Test question A.", "- _No practice questions recorded yet._")
        counts = practice_question_counts(make_note(text))
        self.assertEqual(0, counts["easy"])
        # Medium is also placeholder, exam-style has a real question
        self.assertEqual(0, counts["medium"])
        self.assertEqual(1, counts["exam-style"])
        self.assertEqual(1, counts["total"])

    def test_not_applicable_not_treated_as_empty(self):
        text = VALID_TEXT.replace("An example.", "Not applicable here.")
        note = make_note(text)
        self.assertTrue(has_substantive_section(note, "Worked Example"))

    def test_broken_markdown_link_in_non_note_file_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_path = Path(temp_dir)
            broken = temp_path / "broken-link.md"
            broken.write_text("[missing](does-not-exist.md)", encoding="utf-8")
            link_issues = validate_repository()
            link_messages = [issue.message for issue in link_issues]
            # The temp file is outside the repo root, so discover_markdown_paths won't find it.
            # Instead test the helper directly
            from studylib import check_md_links
            issues = check_md_links(broken.read_text(encoding="utf-8"), str(broken), broken)
            self.assertTrue(any("does not exist" in issue.message for issue in issues), link_messages)

    def test_generation_date_respects_source_date_epoch(self):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1704067200"}, clear=True):
            self.assertEqual(date(2024, 1, 1), generation_date())

    def test_generation_date_restores_preexisting_environment_value(self):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "pre-existing"}, clear=False):
            with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1704067200"}, clear=False):
                self.assertEqual(date(2024, 1, 1), generation_date())
            self.assertEqual("pre-existing", os.environ["SOURCE_DATE_EPOCH"])

    def test_generation_date_rejects_invalid_epoch(self):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "invalid"}, clear=True):
            with self.assertRaisesRegex(GenerationDateError, "SOURCE_DATE_EPOCH"):
                generation_date()

    def test_generation_date_date_only_in_manifest(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            output = Path(temp_dir) / "manifest.json"
            self.assertEqual(0, build_manifest(output))
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertIsInstance(manifest["generated-at"], str)
            # Should be date-only (YYYY-MM-DD), not full timestamp
            self.assertRegex(manifest["generated-at"], r"^\d{4}-\d{2}-\d{2}$")

    def test_preview_handles_bullet_lists_gracefully(self):
        from studylib import preview
        text = "---\nid: demo-bullet\ntitle: Bullet Test\ntype: concept\ncourse: demo\ntopic: examples\naliases: []\nprerequisites: []\nrelated: []\nexam-weight: none\nstatus: new\nlast-reviewed:\nreview-after:\nsource: test\nvisibility: public-original\nsource-risk: original\n---\n\n# Bullet Test\n\n## Definition\n\n- First item\n- Second item\n- Third item"
        metadata, body, errors = parse_frontmatter(text)
        note = Note(Path("courses/demo/concepts/bullet.md"), metadata, body, text, tuple(errors))
        result = preview(note)
        self.assertIn("First item", result)
        self.assertIn("Second item", result)
        self.assertNotIn("- First", result)

    def test_blocklist_no_file_passes(self):
        self.assertEqual([], load_blocklist(ROOT / "nonexistent-blocklist"))

        note = make_note()
        issues = validate_repository([note], public_release=True, blocklist=[])
        errors = [i for i in issues if i.level == "error"]
        self.assertEqual([], errors)

    def test_blocklist_file_not_found_returns_empty(self):
        self.assertEqual([], load_blocklist(ROOT / "nonexistent-blocklist.file"))

    def test_local_blocklist_is_ignored_by_git(self):
        result = subprocess.run(
            ["git", "check-ignore", "-q", ".public-release-blocklist"],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(0, result.returncode)

    def test_blocklist_comments_and_blanks_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / ".public-release-blocklist"
            path.write_text(
                "# This is a comment\n\n\n  \n# Another comment\nDemo Secret University\n\nPRIVATE101\n",
                encoding="utf-8",
            )
            terms = load_blocklist(path)
            self.assertEqual(["Demo Secret University", "PRIVATE101"], terms)

    def test_blocklist_catches_term_in_note(self):
        text = VALID_TEXT + "\nDemo Secret University reference.\n"
        note = make_note(text)
        blocklist = ["Demo Secret University"]
        issues = validate_repository([note], public_release=True, blocklist=blocklist)
        messages = [i.message for i in issues]
        self.assertTrue(any("blocked term" in msg for msg in messages))
        self.assertTrue(any("Demo Secret University" in msg for msg in messages))

    def test_blocklist_does_not_affect_normal_validation(self):
        text = VALID_TEXT + "\nPRIVATE101 code.\n"
        note = make_note(text)
        blocklist = ["PRIVATE101"]
        issues = validate_repository([note], public_release=False, blocklist=blocklist)
        messages = [i.message for i in issues]
        self.assertFalse(any("blocked term" in msg for msg in messages))

    def test_blocklist_error_includes_file_and_term(self):
        text = VALID_TEXT + "\nSecret term demo-lms.example here.\n"
        note = make_note(text, filename="blocklist-test.md")
        blocklist = ["demo-lms.example"]
        issues = validate_repository([note], public_release=True, blocklist=blocklist)
        matching = [i for i in issues if "blocked term" in i.message]
        self.assertEqual(1, len(matching))
        self.assertIn("blocklist-test.md", matching[0].file)
        self.assertIn("demo-lms.example", matching[0].message)


    # --- mark_reviewed tests ---

    def _make_review_note(self, temp_dir, note_id="test-review-id", status="learning",
                          last_reviewed="", review_after="", course_override=None):
        """Write a valid concept note below *temp_dir* and return its path."""
        course = course_override or Path(temp_dir).name
        path = Path(temp_dir) / "concepts" / f"{note_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        text = f"""---
id: {note_id}
title: Test Review Note
course: {course}
type: concept
topic: testing
aliases: []
prerequisites: []
related: []
exam-weight: medium
status: {status}
last-reviewed: {last_reviewed}
review-after: {review_after}
source: "Test fixture"
visibility: private
source-risk: original
---

# Test Review Note

## Definition

A fixture.

## Intuition

An intuition.

## Worked Example

An example.

## Common Mistakes

- A general warning.

## Mistake Log

_No personal mistakes logged yet._

## Practice Questions

### Easy

- Test question.

### Medium

_No practice questions recorded yet._

### Exam-style

- Test question B.

## Related

_None._
"""
        path.write_text(text, encoding="utf-8")
        return path

    def test_mark_reviewed_updates_dates(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "courses") as td:
            self._make_review_note(td, "review-test-01", status="learning")
            ret = mark_reviewed("review-test-01", date(2026, 7, 2))
            self.assertEqual(0, ret)
            path = Path(td) / "concepts" / "review-test-01.md"
            content = path.read_text(encoding="utf-8")
            self.assertIn("last-reviewed: 2026-07-02", content)
            self.assertIn("review-after: 2026-07-09", content)

    def test_mark_reviewed_no_match(self):
        ret = mark_reviewed("nonexistent-id-that-surely-does-not-exist", date(2026, 7, 2))
        self.assertEqual(1, ret)

    def test_mark_reviewed_duplicate_ids(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "courses") as td1, \
             tempfile.TemporaryDirectory(dir=ROOT / "courses") as td2:
            self._make_review_note(td1, "duplicate-id", course_override=Path(td1).name)
            self._make_review_note(td2, "duplicate-id", course_override=Path(td2).name)
            ret = mark_reviewed("duplicate-id", date(2026, 7, 2))
            self.assertEqual(1, ret)

    def test_mark_reviewed_date_override(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "courses") as td:
            self._make_review_note(td, "date-override-test", status="new")
            ret = mark_reviewed("date-override-test", date(2026, 5, 1))
            self.assertEqual(0, ret)
            path = Path(td) / "concepts" / "date-override-test.md"
            content = path.read_text(encoding="utf-8")
            self.assertIn("last-reviewed: 2026-05-01", content)
            self.assertIn("review-after: 2026-05-02", content)

    def test_mark_reviewed_cadence_by_status(self):
        cases = [("new", 1), ("shaky", 2), ("learning", 7), ("solid", 30), ("mastered", 60)]
        base = date(2026, 6, 1)
        for status, offset in cases:
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory(dir=ROOT / "courses") as td:
                    nid = f"cadence-{status}"
                    self._make_review_note(td, nid, status=status)
                    ret = mark_reviewed(nid, base)
                    self.assertEqual(0, ret)
                    path = Path(td) / "concepts" / f"{nid}.md"
                    content = path.read_text(encoding="utf-8")
                    expected = (base + timedelta(days=offset)).isoformat()
                    self.assertIn(f"review-after: {expected}", content)

    def test_mark_reviewed_status_unchanged(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "courses") as td:
            self._make_review_note(td, "status-check", status="shaky")
            ret = mark_reviewed("status-check", date(2026, 7, 2))
            self.assertEqual(0, ret)
            path = Path(td) / "concepts" / "status-check.md"
            content = path.read_text(encoding="utf-8")
            self.assertIn("status: shaky", content)

    def test_mark_reviewed_visibility_unchanged(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "courses") as td:
            self._make_review_note(td, "vis-check", status="learning")
            ret = mark_reviewed("vis-check", date(2026, 7, 2))
            self.assertEqual(0, ret)
            path = Path(td) / "concepts" / "vis-check.md"
            content = path.read_text(encoding="utf-8")
            self.assertIn("visibility: private", content)
            self.assertIn("source-risk: original", content)


# A generated study-module artifact: real ones carry no note frontmatter, which is
# exactly what a malformed note also looks like, so location and declaration --
# never the absence of frontmatter -- decide what counts as a note.
STUDY_GUIDE_TEXT = """# Fixture Topic

## 1. Overview

[S] A source-supported statement.
[E] An explanatory synthesis.
"""


class GeneratedArtifactDiscoveryTests(unittest.TestCase):
    """Cover the note/generated-artifact boundary in docs/generated-artifacts.md."""

    def _course_tree(self, courses_dir, course="fixture-course"):
        """Create a synthetic course holding one valid note. Returns the course dir."""
        course_dir = Path(courses_dir) / course
        (course_dir / "concepts").mkdir(parents=True)
        text = VALID_TEXT.replace("course: demo", f"course: {course}").replace(
            "id: demo-example", "id: fixture-example"
        )
        (course_dir / "concepts" / "example.md").write_text(text, encoding="utf-8")
        return course_dir

    def _study_module(self, course_dir, topic="fixture-topic"):
        module = course_dir / "study" / topic
        module.mkdir(parents=True)
        for name in ("STUDY_GUIDE.md", "QUESTION_BANK.md", "ANSWER_KEY.md", "COVERAGE_MATRIX.md"):
            (module / name).write_text(STUDY_GUIDE_TEXT, encoding="utf-8")
        return module

    def test_study_module_artifacts_do_not_fail_note_validation(self):
        """The original failure: contract files were validated as frontmatter-less notes."""
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            self._study_module(course_dir)
            courses_dir = Path(courses)

            notes = discover_note_paths(courses_dir=courses_dir)
            artifacts = discover_generated_artifact_paths(courses_dir=courses_dir)
            self.assertEqual(["example.md"], [p.name for p in notes])
            self.assertEqual(4, len(artifacts))

            issues = validate_repository(courses_dir=courses_dir)
            self.assertEqual([], [format_issue(i) for i in issues if i.level == "error"])

    def test_course_level_study_layer_output_is_an_artifact(self):
        """Files directly in <course>/study/ are study-layer output, not notes."""
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            (course_dir / "study").mkdir()
            (course_dir / "study" / "STUDY_INDEX.md").write_text("# Index\n", encoding="utf-8")

            names = [p.name for p in discover_note_paths(courses_dir=Path(courses))]
            self.assertEqual(["example.md"], names)

    def test_malformed_note_still_fails_validation(self):
        """A human-maintained note with broken frontmatter must stay discoverable."""
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            self._study_module(course_dir)
            broken = course_dir / "concepts" / "broken.md"
            broken.write_text("# Broken\n\nNo frontmatter at all.\n", encoding="utf-8")

            self.assertIn(broken, discover_note_paths(courses_dir=Path(courses)))
            issues = validate_repository(courses_dir=Path(courses))
            errors = [i for i in issues if i.level == "error" and i.file.endswith("broken.md")]
            self.assertTrue(errors, "a malformed note must still produce an error")

    def test_study_directory_must_be_a_direct_child_of_a_course(self):
        """A `study` directory nested inside a note directory is not a module tree."""
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            nested = course_dir / "concepts" / "study"
            nested.mkdir()
            (nested / "misleading.md").write_text("# Misleading\n", encoding="utf-8")

            names = [p.name for p in discover_note_paths(courses_dir=Path(courses))]
            self.assertIn("misleading.md", names)

    def test_a_course_named_study_keeps_its_notes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            self._course_tree(courses, course="study")
            names = [p.name for p in discover_note_paths(courses_dir=Path(courses))]
            self.assertEqual(["example.md"], names)

    def test_declaration_file_excludes_named_artifacts(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            (course_dir / "COVERAGE_AUDIT.md").write_text("# Audit\n", encoding="utf-8")
            (course_dir / "capture").mkdir()
            (course_dir / "capture" / "SYNC_REPORT.md").write_text("# Sync\n", encoding="utf-8")
            (Path(courses) / ".generated-artifacts").write_text(
                "# fixture declaration\n*/COVERAGE_AUDIT.md\n*/capture/**\n", encoding="utf-8"
            )

            names = [p.name for p in discover_note_paths(courses_dir=Path(courses))]
            self.assertEqual(["example.md"], names)
            artifacts = sorted(p.name for p in discover_generated_artifact_paths(courses_dir=Path(courses)))
            self.assertEqual(["COVERAGE_AUDIT.md", "SYNC_REPORT.md"], artifacts)

    def test_declaration_patterns_cannot_reach_into_note_directories(self):
        """A course-root pattern must not shadow a same-named file inside concepts/."""
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            (course_dir / "COVERAGE_AUDIT.md").write_text("# Audit\n", encoding="utf-8")
            (course_dir / "concepts" / "COVERAGE_AUDIT.md").write_text("# Note\n", encoding="utf-8")
            (Path(courses) / ".generated-artifacts").write_text("*/COVERAGE_AUDIT.md\n", encoding="utf-8")

            notes = discover_note_paths(courses_dir=Path(courses))
            self.assertIn("concepts", {p.parent.name for p in notes})
            self.assertEqual(
                ["COVERAGE_AUDIT.md"],
                [p.name for p in discover_generated_artifact_paths(courses_dir=Path(courses))],
            )

    def test_single_star_does_not_cross_a_directory_boundary(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            (course_dir / "reports").mkdir()
            (course_dir / "reports" / "deep.md").write_text("# Deep\n", encoding="utf-8")
            (Path(courses) / ".generated-artifacts").write_text("*/*.md\n", encoding="utf-8")

            names = [p.name for p in discover_note_paths(courses_dir=Path(courses))]
            self.assertIn("deep.md", names)

    def test_readme_files_remain_excluded_without_a_declaration(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            (course_dir / "README.md").write_text("# Navigation\n", encoding="utf-8")

            self.assertEqual(["example.md"], [p.name for p in discover_note_paths(courses_dir=Path(courses))])
            self.assertEqual([], discover_generated_artifact_paths(courses_dir=Path(courses)))

    def test_catch_all_declaration_patterns_are_refused(self):
        for pattern in ("*", "**", "*.md", "**/*.md", "**/*", "**/**"):
            with self.subTest(pattern=pattern):
                with tempfile.TemporaryDirectory(dir=ROOT) as courses:
                    self._course_tree(courses)
                    (Path(courses) / ".generated-artifacts").write_text(pattern + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(GeneratedArtifactError, "too broad"):
                        discover_note_paths(courses_dir=Path(courses))

    def test_absolute_and_escaping_declaration_patterns_are_refused(self):
        cases = {
            "/fixture-course/**": "relative",
            "../**": "escape",
            "fixture-course\\**": r"separators",
        }
        for pattern, expected in cases.items():
            with self.subTest(pattern=pattern):
                with tempfile.TemporaryDirectory(dir=ROOT) as courses:
                    self._course_tree(courses)
                    (Path(courses) / ".generated-artifacts").write_text(pattern + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(GeneratedArtifactError, expected):
                        load_generated_artifact_patterns(Path(courses))

    def test_stale_declaration_pattern_is_reported(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            self._course_tree(courses)
            (Path(courses) / ".generated-artifacts").write_text("*/NEVER_MATCHES.md\n", encoding="utf-8")

            issues = validate_repository(courses_dir=Path(courses))
            warnings = [i for i in issues if i.level == "warning" and "NEVER_MATCHES" in i.message]
            self.assertEqual(1, len(warnings), [format_issue(i) for i in issues])
            self.assertEqual([], [i for i in issues if i.level == "error"])

    def test_comments_and_blank_lines_are_ignored(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            self._course_tree(courses)
            (Path(courses) / ".generated-artifacts").write_text(
                "# a comment\n\n   \n*/COVERAGE_AUDIT.md\n", encoding="utf-8"
            )
            self.assertEqual(["*/COVERAGE_AUDIT.md"], load_generated_artifact_patterns(Path(courses)))

    def test_builders_run_once_artifacts_are_recognised(self):
        """Generated artifacts previously blocked manifest and review-queue writes."""
        with tempfile.TemporaryDirectory(dir=ROOT) as courses:
            course_dir = self._course_tree(courses)
            self._study_module(course_dir)
            with tempfile.TemporaryDirectory() as out:
                manifest = Path(out) / "manifest.json"
                self.assertEqual(0, build_manifest(manifest, courses_dir=Path(courses)))
                self.assertEqual(1, len(json.loads(manifest.read_text(encoding="utf-8"))["notes"]))

                queue = Path(out) / "REVIEW_QUEUE.md"
                self.assertEqual(0, build_queue(queue, date(2026, 6, 20), courses_dir=Path(courses)))
                self.assertTrue(queue.is_file())

    def test_generated_artifact_contract_is_documented(self):
        doc = (ROOT / "docs" / "generated-artifacts.md").read_text(encoding="utf-8")
        for marker in (
            "## What counts as a note",
            "## What counts as a generated artifact",
            "## Declaring artifacts",
            "## What the contract deliberately does not do",
        ):
            self.assertIn(marker, doc)
        self.assertIn(".generated-artifacts", doc)


if __name__ == "__main__":
    unittest.main()

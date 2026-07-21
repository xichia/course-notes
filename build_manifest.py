#!/usr/bin/env python3
"""Build the compact, LLM-first manifest from course note frontmatter."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from studylib import (
    GenerationDateError,
    ROOT,
    STUDY_DIR,
    display_path,
    format_issue,
    generation_date,
    has_substantive_section,
    has_errors,
    load_notes,
    mistake_summary,
    practice_question_counts,
    preview,
    section_headings,
    validate_repository,
)

GENERATED_WARNING_PUBLIC = "GENERATED FILE. DO NOT EDIT. Rebuild with: make manifest (or python3 build_manifest.py)."
GENERATED_WARNING_STUDY = "GENERATED FILE. DO NOT EDIT. Rebuild with: make study-manifest (or python3 build_manifest.py --study)."
GENERATED_WARNING = GENERATED_WARNING_PUBLIC  # backward compat for tests


def build_manifest(output: Path, courses_dir: Path | None = None) -> int:
    is_study = courses_dir is not None
    GENERATED_WARNING = GENERATED_WARNING_STUDY if is_study else GENERATED_WARNING_PUBLIC

    notes = load_notes(courses_dir=courses_dir)
    issues = validate_repository(courses_dir=courses_dir)
    for issue in issues:
        print(format_issue(issue))
    if has_errors(issues):
        print("Manifest not written because validation failed.")
        return 1

    entries = []
    for note in notes:
        metadata = note.metadata
        mistakes = mistake_summary(note)
        practice = practice_question_counts(note)
        entries.append(
            {
                "id": metadata["id"],
                "file": note.file,
                "title": metadata["title"],
                "course": metadata["course"],
                "type": metadata["type"],
                "topic": metadata["topic"],
                "aliases": metadata["aliases"],
                "prerequisites": metadata["prerequisites"],
                "related": metadata["related"],
                "exam-weight": metadata["exam-weight"],
                "status": metadata["status"],
                "last-reviewed": metadata["last-reviewed"],
                "review-after": metadata["review-after"],
                "source": metadata["source"],
                "visibility": metadata.get("visibility", "unclassified"),
                "source-risk": metadata.get("source-risk", "unknown"),
                "mistake-count": mistakes["count"],
                "recent-mistakes-30d": mistakes["recent"],
                "latest-mistake": mistakes["latest-date"],
                "mistake-tags": mistakes["tags"],
                "has-worked-example": has_substantive_section(note, "Worked Example"),
                "has-practice-questions": practice["total"] > 0,
                "practice-questions": practice,
                "summary": preview(note),
                "headings": section_headings(note.body),
            }
        )
    entries.sort(key=lambda entry: (entry["course"], entry["type"], entry["title"].casefold()))

    courses = {}
    for course in sorted({entry["course"] for entry in entries}):
        course_entries = [entry for entry in entries if entry["course"] == course]
        courses[course] = {
            "count": len(course_entries),
            "types": dict(sorted(Counter(entry["type"] for entry in course_entries).items())),
            "topics": sorted({entry["topic"] for entry in course_entries}),
            "note-ids": [entry["id"] for entry in course_entries],
        }

    manifest = {
        "_generated": GENERATED_WARNING,
        "format-version": 3,
        "generated-at": generation_date().isoformat(),
        "how-to-use": [
            "Filter by course, type, topic, status, exam-weight, visibility, source-risk, aliases, mistakes, or practice coverage.",
            "Read summary and headings to choose notes, then open only the listed file paths you need.",
            "Treat Markdown notes as source of truth; this manifest is only a generated index.",
        ],
        "count": len(entries),
        "courses": courses,
        "notes": entries,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {display_path(output)} with {len(entries)} notes across {len(courses)} course(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None, help="output JSON path")
    parser.add_argument(
        "--study",
        action="store_true",
        help="scan private/courses/ and write private/manifest.json",
    )
    args = parser.parse_args(argv)

    courses_dir = STUDY_DIR if args.study else None
    output = args.output if args.output else (ROOT / "private" / "manifest.json" if args.study else ROOT / "manifest.json")
    output = output if output.is_absolute() else ROOT / output
    try:
        return build_manifest(output, courses_dir=courses_dir)
    except GenerationDateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Update review metadata after studying a note."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from studylib import (
    ROOT,
    STUDY_DIR,
    GeneratedArtifactError,
    discover_note_paths,
    format_issue,
    has_errors,
    parse_frontmatter,
    validate_repository,
)

REVIEW_CADENCE: dict[str, int] = {
    "new": 1,
    "shaky": 2,
    "learning": 7,
    "solid": 30,
    "mastered": 60,
    "reference": 0,
    "archived": 0,
}


def _resolve_date(today: date, days: int) -> str:
    if days <= 0:
        return ""
    return (today + timedelta(days=days)).isoformat()


def mark_reviewed(note_id: str, review_date: date, courses_dir: Path | None = None) -> int:
    paths = discover_note_paths(courses_dir=courses_dir)
    matches: list[tuple[Path, dict[str, str], str]] = []

    for path in paths:
        text = path.read_text(encoding="utf-8")
        metadata, body, errors = parse_frontmatter(text)
        if errors:
            continue
        if metadata.get("id") == note_id:
            matches.append((path, metadata, text))

    if not matches:
        print(f"ERROR: no note found with id '{note_id}'", file=sys.stderr)
        return 1

    if len(matches) > 1:
        files = ", ".join(str(m.relative_to(ROOT)) for m, _, _ in matches)
        print(f"ERROR: multiple notes ({len(matches)}) have id '{note_id}': {files}", file=sys.stderr)
        return 1

    path, metadata, text = matches[0]

    status = metadata.get("status", "")
    days = REVIEW_CADENCE.get(status, 0)

    last_reviewed_str = review_date.isoformat()
    review_after_str = _resolve_date(review_date, days) if days > 0 else ""

    orig_lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    updated_last = False
    updated_after = False

    for line in orig_lines:
        stripped = line.lstrip()
        if stripped.startswith("last-reviewed:"):
            indent = line[: len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}last-reviewed: {last_reviewed_str}\n")
            updated_last = True
        elif stripped.startswith("review-after:"):
            indent = line[: len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}review-after: {review_after_str}\n")
            updated_after = True
        else:
            new_lines.append(line)

    if not updated_last:
        print("ERROR: 'last-reviewed' field not found in frontmatter", file=sys.stderr)
        return 1
    if not updated_after:
        print("ERROR: 'review-after' field not found in frontmatter", file=sys.stderr)
        return 1

    new_text = "".join(new_lines)
    path.write_text(new_text, encoding="utf-8")
    rel_path = path.relative_to(ROOT).as_posix()
    print(f"Updated {rel_path}")
    print(f"  last-reviewed: {last_reviewed_str}")
    if review_after_str:
        print(f"  review-after:  {review_after_str}")
    else:
        print(f"  review-after:  (blank — status is {status})")

    issues = validate_repository(courses_dir=courses_dir)
    for issue in issues:
        print(format_issue(issue))

    if has_errors(issues):
        print("ERROR: validation failed after update.", file=sys.stderr)
        return 1

    cmd = "make study-all" if courses_dir else "make all"
    print(f"\nRun `{cmd}` to regenerate manifest and review queue.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note_id", help="frontmatter `id` of the note to mark as reviewed")
    parser.add_argument("--date", "-d", type=date.fromisoformat, default=date.today(), help="review date (default: today)")
    parser.add_argument(
        "--study",
        action="store_true",
        help="scan private/courses/ instead of courses/",
    )
    args = parser.parse_args()
    courses_dir = STUDY_DIR if args.study else None
    try:
        return mark_reviewed(args.note_id, args.date, courses_dir=courses_dir)
    except GeneratedArtifactError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a ranked Markdown review queue from note metadata and mistake logs."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from studylib import (
    REVIEWABLE_TYPES,
    ROOT,
    Note,
    display_path,
    format_issue,
    has_errors,
    load_notes,
    mistake_summary,
    practice_question_counts,
    validate_repository,
)


STATUS_POINTS = {"shaky": 40, "new": 32, "learning": 26, "solid": 8, "mastered": 0}
WEIGHT_POINTS = {"high": 25, "medium": 14, "low": 5, "none": 0}
GENERATED_WARNING = "<!-- GENERATED FILE. DO NOT EDIT. Rebuild with: make review (or python3 build_review_queue.py). -->"


@dataclass(frozen=True)
class ReviewItem:
    note: Note
    score: int
    factors: tuple[str, ...]
    needs_attention: bool
    mistake_count: int
    recent_mistakes: int
    missing_practice: bool


def parse_optional_date(value: str) -> date | None:
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def rank_note(note: Note, today: date) -> ReviewItem:
    metadata = note.metadata
    score = 0
    factors = []

    status = metadata["status"]
    status_points = STATUS_POINTS.get(status, 0)
    score += status_points
    factors.append(f"{status} status (+{status_points})")

    weight = metadata["exam-weight"]
    weight_points = WEIGHT_POINTS[weight]
    score += weight_points
    factors.append(f"{weight} exam weight (+{weight_points})")

    mistakes = mistake_summary(note, today)
    mistake_points = min(mistakes["count"] * 5, 20)
    if mistakes["count"]:
        score += mistake_points
        factors.append(f"{mistakes['count']} logged mistake{'s' if mistakes['count'] != 1 else ''} (+{mistake_points})")

    recent_mistake_points = min(mistakes["recent"] * 12, 36)
    if mistakes["recent"]:
        score += recent_mistake_points
        factors.append(
            f"{mistakes['recent']} mistake{'s' if mistakes['recent'] != 1 else ''} in the last 30 days "
            f"(+{recent_mistake_points})"
        )

    practice = practice_question_counts(note)
    missing_practice = metadata["type"] == "concept" and practice["total"] == 0
    if missing_practice:
        score += 10
        factors.append("no practice questions (+10)")

    high_weight_shaky = weight == "high" and status == "shaky"
    if high_weight_shaky:
        score += 15
        factors.append("high-weight + shaky combination (+15)")

    reviewed = parse_optional_date(metadata["last-reviewed"])
    if reviewed is None:
        score += 20
        factors.append("never reviewed (+20)")
    else:
        age = max((today - reviewed).days, 0)
        stale_points = min(max(age - 7, 0), 20)
        score += stale_points
        factors.append(f"reviewed {age} day{'s' if age != 1 else ''} ago (+{stale_points})")

    review_after = parse_optional_date(metadata["review-after"])
    due = review_after is not None and review_after <= today
    if due:
        overdue_days = (today - review_after).days
        due_points = 30 + min(overdue_days, 30)
        score += due_points
        label = "due today" if overdue_days == 0 else f"overdue by {overdue_days} day{'s' if overdue_days != 1 else ''}"
        factors.append(f"{label} (+{due_points})")
    elif review_after is None:
        score += 10
        factors.append("no review-after date (+10)")
    else:
        days_until = (review_after - today).days
        factors.append(f"scheduled in {days_until} day{'s' if days_until != 1 else ''} (+0)")

    needs_attention = (
        due
        or status in {"new", "learning", "shaky"}
        or mistakes["recent"] > 0
        or reviewed is None
        or (weight == "high" and missing_practice)
    )
    return ReviewItem(
        note,
        score,
        tuple(factors),
        needs_attention,
        mistakes["count"],
        mistakes["recent"],
        missing_practice,
    )


def recommended_action(item: ReviewItem) -> str:
    metadata = item.note.metadata
    if item.recent_mistakes:
        return "Re-test the recent mistake(s) correction with a fresh problem."
    if metadata["status"] == "shaky":
        return "Recall the definition, then solve the worked example unaided."
    if item.missing_practice:
        return "Add one course-sourced practice question, then answer it unaided."
    if item.mistake_count:
        return "Re-test a logged correction and record new evidence if it fails again."
    if metadata["status"] in {"new", "learning"}:
        return "Explain it from memory and test one representative problem."
    return "Use active recall; update the review dates after checking your answer."


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def is_review_candidate(note: Note) -> bool:
    return note.metadata["type"] in REVIEWABLE_TYPES and note.metadata["status"] not in {"archived", "reference"}


def table(items: list[ReviewItem]) -> list[str]:
    if not items:
        return ["_None._"]
    lines = [
        "| Priority | Note | Course / topic | Why it is ranked here | Suggested action |",
        "|---:|---|---|---|---|",
    ]
    for item in items:
        metadata = item.note.metadata
        link = f"[{escape_cell(metadata['title'])}]({item.note.file})"
        why = escape_cell("; ".join(item.factors))
        course_topic = escape_cell(f"{metadata['course']} / {metadata['topic']}")
        action = escape_cell(recommended_action(item))
        lines.append(f"| {item.score} | {link} | {course_topic} | {why} | {action} |")
    return lines


def build_queue(output: Path, today: date) -> int:
    notes = load_notes()
    issues = validate_repository()
    for issue in issues:
        print(format_issue(issue))
    if has_errors(issues):
        print("Review queue not written because validation failed.")
        return 1

    items = [
        rank_note(note, today)
        for note in notes
        if is_review_candidate(note)
    ]
    items.sort(key=lambda item: (-item.score, item.note.metadata["title"].casefold()))
    attention = [item for item in items if item.needs_attention]
    upcoming = [item for item in items if not item.needs_attention]

    lines = [
        GENERATED_WARNING,
        "",
        "# Review Queue",
        "",
        f"Generated for **{today.isoformat()}** from note frontmatter, structured mistake logs, and practice coverage.",
        "",
        "Scores are additive and intentionally simple. They rank study attention; they do not measure ability.",
        "",
        "## How Priority Is Scored",
        "",
        "- **Status:** shaky +40, new +32, learning +26, solid +8, mastered +0.",
        "- **Exam weight:** high +25, medium +14, low +5, none +0.",
        "- **Review timing:** due +30 plus 1 per overdue day (maximum +60); no `review-after` +10.",
        "- **Review age:** never reviewed +20; otherwise 1 point per day beyond 7 days (maximum +20).",
        "- **Mistakes:** +5 per logged mistake (maximum +20), plus +12 per dated mistake from the last 30 days (maximum +36).",
        "- **Practice coverage:** concept note with no recorded practice questions +10.",
        "- **Combined risk:** high exam weight together with shaky status +15.",
        "",
        "## Review Now",
        "",
        *table(attention),
        "",
        "## Upcoming / Maintained",
        "",
        *table(upcoming),
        "",
        "## After a Review",
        "",
        "Update `last-reviewed` and `review-after`. Add a structured Mistake Log entry only for an evidenced error. Propose status changes from repeated quiz, problem-sheet, or timed-recall evidence, then regenerate this file.",
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {display_path(output)} with {len(attention)} current and {len(upcoming)} upcoming item(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "REVIEW_QUEUE.md", help="output Markdown path")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD), useful for reproducible checks")
    args = parser.parse_args()
    date_from_env = os.environ.get("DATE")
    today = (
        datetime.strptime(args.today, "%Y-%m-%d").date()
        if args.today
        else datetime.strptime(date_from_env, "%Y-%m-%d").date()
        if date_from_env
        else date.today()
    )
    output = args.output if args.output.is_absolute() else ROOT / args.output
    return build_queue(output, today)


if __name__ == "__main__":
    raise SystemExit(main())

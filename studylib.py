#!/usr/bin/env python3
"""Shared, dependency-free helpers for the Markdown study system."""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
COURSES_DIR = ROOT / "courses"

REQUIRED_FIELDS = (
    "id",
    "title",
    "course",
    "type",
    "topic",
    "aliases",
    "prerequisites",
    "related",
    "exam-weight",
    "status",
    "last-reviewed",
    "review-after",
    "source",
)
LIST_FIELDS = ("aliases", "prerequisites", "related")
VALID_EXAM_WEIGHTS = {"none", "low", "medium", "high"}
VALID_STATUSES = {"new", "learning", "shaky", "solid", "mastered", "reference", "archived"}
VALID_TYPES = {"concept", "lecture", "problem-sheet", "exam-map", "glossary", "reference"}
VALID_VISIBILITIES = {"private", "public-framework", "public-original", "public-open-licensed"}
VALID_SOURCE_RISKS = {
    "lecture-derived",
    "problem-sheet-derived",
    "exam-derived",
    "lms-derived",
    "open-licensed",
    "original",
    "unknown",
}
PUBLIC_RELEASE_BLOCKED_RISKS = {
    "lecture-derived",
    "problem-sheet-derived",
    "exam-derived",
    "lms-derived",
    "unknown",
}
REVIEWABLE_TYPES = {"concept", "lecture", "problem-sheet"}
MISTAKE_FIELDS = ("date", "source", "mistake", "correction", "tags")
PRACTICE_LEVELS = {"easy": "easy", "medium": "medium", "exam-style": "exam-style"}

PUBLIC_RELEASE_SOURCE_SUSPICIOUS_TERMS = (
    "lms",
    "moodle",
    "canvas",
    "blackboard",
    "brightspace",
    "lecture slide",
    "lecture slides",
    "slides",
    "exam question",
    "problem sheet",
    "course pack",
)

BLOCKLIST_FILENAME = ".public-release-blocklist"


def load_blocklist(path: Path | None = None) -> list[str]:
    """Load the optional public-release blocklist.

    Returns an empty list when the file does not exist.
    Lines starting with ``#`` and blank lines are ignored.
    Each remaining line is a case-insensitive term to block.
    """
    if path is None:
        path = ROOT / BLOCKLIST_FILENAME
    if not path.is_file():
        return []
    terms: list[str] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            terms.append(stripped)
    return terms


FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
RAW_LOCAL_PATH_RE = re.compile(
    r"(?:file:" r"//[^\s)`>]+|/" r"Users/[^\s)`>]+|/home/[^\s)`>]+|/private/[^\s)`>]+|"
    r"~/[^\s)`>]+|[A-Za-z]:[\\/][^\s)`>]+)"
)


@dataclass(frozen=True)
class Note:
    path: Path
    metadata: dict[str, Any]
    body: str
    text: str
    parse_errors: tuple[str, ...]

    @property
    def file(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


@dataclass(frozen=True)
class Issue:
    level: str
    file: str
    message: str


@dataclass(frozen=True)
class MistakeEntry:
    date: date | None
    date_text: str
    source: str
    mistake: str
    correction: str
    tags: tuple[str, ...]


def _parse_list(value: str) -> list[str]:
    if not (value.startswith("[") and value.endswith("]")):
        raise ValueError("must be an inline list such as [one, two] or []")
    inner = value[1:-1].strip()
    if not inner:
        return []
    try:
        row = next(csv.reader([inner], skipinitialspace=True))
    except csv.Error as exc:
        raise ValueError(f"invalid inline list: {exc}") from exc
    items = []
    for item in row:
        item = item.strip()
        if len(item) >= 2 and item[0] == item[-1] == "'":
            item = item[1:-1]
        if item:
            items.append(item)
    return items


def _parse_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """Parse the intentionally small YAML subset used by this repository."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, ["frontmatter: missing or unclosed; add opening and closing '---' lines"]

    metadata: dict[str, Any] = {}
    errors: list[str] = []
    for line_number, line in enumerate(match.group(1).splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1].isspace():
            errors.append(f"frontmatter line {line_number}: nested YAML is not supported")
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {line_number}: expected 'key: value'")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"frontmatter line {line_number}: empty key")
            continue
        if key in metadata:
            errors.append(f"frontmatter line {line_number}: duplicate key '{key}'")
            continue
        try:
            metadata[key] = _parse_list(value) if value.startswith("[") else _parse_scalar(value)
        except ValueError as exc:
            errors.append(f"frontmatter line {line_number}, '{key}': {exc}")

    return metadata, text[match.end():], errors


def discover_markdown_paths() -> list[Path]:
    """Find repository Markdown, excluding internal and cache directories."""
    excluded = {".git", ".codex", ".agents", "__pycache__"}
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if not any(part in excluded for part in path.relative_to(ROOT).parts)
    )


def discover_note_paths() -> list[Path]:
    """Find study documents while excluding navigational README files."""
    if not COURSES_DIR.exists():
        return []
    return sorted(path for path in COURSES_DIR.rglob("*.md") if path.name.lower() != "readme.md")


def load_notes(paths: Iterable[Path] | None = None) -> list[Note]:
    notes = []
    for path in paths if paths is not None else discover_note_paths():
        text = path.read_text(encoding="utf-8")
        metadata, body, errors = parse_frontmatter(text)
        notes.append(Note(path, metadata, body, text, tuple(errors)))
    return notes


def _markdown_target(raw_target: str) -> str:
    raw_target = raw_target.strip()
    if raw_target.startswith("<") and ">" in raw_target:
        return raw_target[1:raw_target.index(">")]
    return raw_target.split(maxsplit=1)[0] if raw_target else ""


def markdown_links(text: str) -> list[tuple[str, int, tuple[int, int]]]:
    links = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = _markdown_target(match.group(1))
        line = text.count("\n", 0, match.start()) + 1
        links.append((target, line, match.span()))
    return links


def is_absolute_local_target(target: str) -> bool:
    lowered = target.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "tel:", "//")):
        return False
    return (
        target.startswith(("/", "~/", "\\\\"))
        or lowered.startswith("file:" "//")
        or bool(re.match(r"^[A-Za-z]:[\\/]", target))
    )


def portability_issues(text: str, file: str) -> list[Issue]:
    """Flag links and raw paths that only work on one machine."""
    issues = []
    link_spans = []
    for target, line, span in markdown_links(text):
        link_spans.append(span)
        if is_absolute_local_target(target):
            issues.append(
                Issue(
                    "error",
                    file,
                    f'Markdown link (line {line}): absolute local target "{target}"; '
                    "replace it with a path relative to this Markdown file",
                )
            )

    for match in RAW_LOCAL_PATH_RE.finditer(text):
        if any(start <= match.start() < end for start, end in link_spans):
            continue
        value = match.group(0)
        line = text.count("\n", 0, match.start()) + 1
        issues.append(
            Issue(
                "error",
                file,
                f'text (line {line}): machine-specific path "{value}"; replace it with a repository-relative path',
            )
        )
    return issues


def _date_value(value: Any) -> date | None:
    if value == "" or value is None:
        return None
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError("must be blank or use YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("is not a real calendar date") from exc


def section_headings(body: str, level: int = 2) -> list[str]:
    marker = "#" * level
    return re.findall(rf"^{re.escape(marker)}\s+(.+?)\s*$", body, re.MULTILINE)


def section_text(body: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _without_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _summarize_text(text: str, limit: int) -> str:
    """Convert a Markdown block to a compact plain-text preview."""
    if re.search(r"^\s*-\s+\S", text, re.MULTILINE):
        items = re.findall(r"^\s*-\s+(.*)", text, re.MULTILINE)
        if items:
            items = [re.sub(r"\s+", " ", item).strip() for item in items]
            return "; ".join(items)[:limit]
    return re.sub(r"\s+", " ", text).strip()[:limit]


def preview(note: Note, limit: int = 240) -> str:
    for heading in ("Summary", "Definition", "Overview", "Purpose"):
        content = section_text(note.body, heading)
        if content:
            paragraph = content.split("\n\n", 1)[0]
            return _summarize_text(paragraph, limit)
    for paragraph in note.body.split("\n\n"):
        if re.fullmatch(r"\s*#{1,6}\s+.+", paragraph):
            continue
        if re.search(r"^\s*-\s+\S", paragraph, re.MULTILINE):
            items = re.findall(r"^\s*-\s+(.*)", paragraph, re.MULTILINE)
            if items:
                items = [re.sub(r"\s+", " ", item).strip() for item in items]
                plain = "; ".join(items)
                return plain[:limit]
        plain = re.sub(r"[#*_`>\s]+", " ", paragraph).strip()
        if plain:
            return plain[:limit]
    return ""


def parse_mistake_log(note: Note) -> tuple[list[MistakeEntry], list[str]]:
    """Parse the small Markdown field convention used by ## Mistake Log."""
    content = _without_html_comments(section_text(note.body, "Mistake Log"))
    if not content:
        return [], []

    raw_entries: list[dict[str, str]] = []
    errors: list[str] = []
    current: dict[str, str] | None = None
    current_number = 0

    for section_line, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped == "_No personal mistakes logged yet._":
            continue

        start = re.match(r"^-\s+date:\s*(.*)$", line)
        if start:
            if current is not None:
                raw_entries.append(current)
            current_number += 1
            current = {"date": start.group(1).strip()}
            continue

        field = re.match(r"^\s{2,}([a-z-]+):\s*(.*)$", line)
        if field and current is not None:
            key, value = field.group(1), field.group(2).strip()
            if key not in MISTAKE_FIELDS:
                errors.append(
                    f"section '## Mistake Log', entry {current_number}: unknown field '{key}'; "
                    f"expected: {', '.join(MISTAKE_FIELDS)}"
                )
            elif key in current:
                errors.append(f"section '## Mistake Log', entry {current_number}, field '{key}': duplicated; keep one value")
            else:
                current[key] = value
            continue

        if field and current is None:
            errors.append(
                f"section '## Mistake Log' line {section_line}: entry must begin with '- date: YYYY-MM-DD' or '- date: unknown'"
            )
        else:
            errors.append(
                f"section '## Mistake Log' line {section_line}: malformed entry; use the five-field structure from TEMPLATE.md"
            )

    if current is not None:
        raw_entries.append(current)

    entries: list[MistakeEntry] = []
    for number, raw in enumerate(raw_entries, start=1):
        missing = [field for field in MISTAKE_FIELDS if field not in raw]
        for field in missing:
            errors.append(
                f"section '## Mistake Log', entry {number}, field '{field}': missing; add '{field}: ...'"
            )

        date_text = raw.get("date", "")
        parsed_date = None
        if "date" in raw and date_text != "unknown":
            try:
                parsed_date = _date_value(date_text)
                if parsed_date is None:
                    raise ValueError("must use YYYY-MM-DD or 'unknown'")
            except ValueError as exc:
                errors.append(
                    f"section '## Mistake Log', entry {number}, field 'date': invalid value \"{date_text}\"; {exc}"
                )

        for field in ("source", "mistake", "correction"):
            if field in raw and not raw[field]:
                errors.append(
                    f"section '## Mistake Log', entry {number}, field '{field}': empty; record the evidence explicitly"
                )

        tags: list[str] = []
        if "tags" in raw:
            try:
                tags = _parse_list(raw["tags"])
                invalid_tags = [tag for tag in tags if not ID_RE.fullmatch(tag)]
                if invalid_tags:
                    errors.append(
                        f"section '## Mistake Log', entry {number}, field 'tags': invalid tag(s) "
                        f"{', '.join(invalid_tags)}; use lowercase slug-style tags"
                    )
            except ValueError as exc:
                errors.append(
                    f"section '## Mistake Log', entry {number}, field 'tags': {exc}"
                )

        if not missing and (parsed_date is not None or date_text == "unknown"):
            if raw["source"] and raw["mistake"] and raw["correction"] and not any(
                message.startswith(f"section '## Mistake Log', entry {number}, field 'tags'")
                for message in errors
            ):
                entries.append(
                    MistakeEntry(
                        parsed_date,
                        date_text,
                        raw["source"],
                        raw["mistake"],
                        raw["correction"],
                        tuple(tags),
                    )
                )

    return entries, errors


def mistake_summary(note: Note, today: date | None = None, recent_days: int = 30) -> dict[str, Any]:
    entries, _ = parse_mistake_log(note)
    today = today or date.today()
    dated = [entry.date for entry in entries if entry.date is not None]
    recent = sum(0 <= (today - entry.date).days <= recent_days for entry in entries if entry.date is not None)
    return {
        "count": len(entries),
        "recent": recent,
        "latest-date": max(dated).isoformat() if dated else "",
        "tags": sorted({tag for entry in entries for tag in entry.tags}),
    }


def practice_question_counts(note: Note) -> dict[str, int]:
    content = _without_html_comments(section_text(note.body, "Practice Questions"))
    counts = {level: 0 for level in PRACTICE_LEVELS.values()}
    current_level = None
    for line in content.splitlines():
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            current_level = PRACTICE_LEVELS.get(heading.group(1).strip().lower())
            continue
        if current_level and re.match(r"^\s*-\s+\S", line):
            stripped = re.sub(r"[*_`]", "", line.lstrip()).strip().lower()
            if stripped.startswith("- no ") and "recorded yet" in stripped:
                continue
            counts[current_level] += 1
    counts["total"] = sum(counts.values())
    return counts


def has_substantive_section(note: Note, heading: str) -> bool:
    content = _without_html_comments(section_text(note.body, heading)).strip()
    if not content:
        return False
    normalized = re.sub(r"[*_`]", "", content).strip().lower()
    if normalized.startswith("no ") and "recorded yet" in normalized:
        return False
    if normalized.startswith(("todo:", "[todo:")):
        return False
    return True


def validate_repository(notes: list[Note] | None = None, public_release: bool = False, blocklist: list[str] | None = None) -> list[Issue]:
    supplied_notes = notes is not None
    notes = notes if supplied_notes else load_notes()
    issues: list[Issue] = []
    ids: dict[str, str] = {}

    if not notes:
        return [Issue("error", "courses/", "no note files found")]

    for note in notes:
        for message in note.parse_errors:
            issues.append(Issue("error", note.file, message))
        if note.parse_errors:
            continue

        metadata = note.metadata
        for field in REQUIRED_FIELDS:
            if field not in metadata:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f"frontmatter field '{field}': missing; add it using TEMPLATE.md as the reference",
                    )
                )

        for field in ("id", "title", "course", "topic", "source"):
            if field in metadata and (not isinstance(metadata[field], str) or not metadata[field].strip()):
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f"frontmatter field '{field}': value is empty; provide a non-empty string",
                    )
                )

        note_id = metadata.get("id")
        if isinstance(note_id, str) and note_id:
            if not ID_RE.fullmatch(note_id):
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f'frontmatter field \'id\': invalid value "{note_id}"; use lowercase letters, numbers, dots, or hyphens',
                    )
                )
            if note_id in ids:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f'frontmatter field \'id\': duplicate value "{note_id}"; already used in {ids[note_id]}',
                    )
                )
            else:
                ids[note_id] = note.file

        for field in LIST_FIELDS:
            if field in metadata and not isinstance(metadata[field], list):
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f"frontmatter field '{field}': expected an inline list such as [one, two] or []",
                    )
                )
            elif isinstance(metadata.get(field), list) and any(not isinstance(item, str) or not item for item in metadata[field]):
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f"frontmatter field '{field}': contains an empty or non-string item; remove or quote that item",
                    )
                )

        if metadata.get("exam-weight") not in VALID_EXAM_WEIGHTS:
            issues.append(
                Issue(
                    "error",
                    note.file,
                    f'frontmatter field \'exam-weight\': invalid value "{metadata.get("exam-weight")}"; '
                    f"expected one of: {', '.join(sorted(VALID_EXAM_WEIGHTS))}",
                )
            )
        if metadata.get("status") not in VALID_STATUSES:
            issues.append(
                Issue(
                    "error",
                    note.file,
                    f'frontmatter field \'status\': invalid value "{metadata.get("status")}"; '
                    f"expected one of: {', '.join(sorted(VALID_STATUSES))}",
                )
            )
        if metadata.get("type") not in VALID_TYPES:
            issues.append(
                Issue(
                    "error",
                    note.file,
                    f'frontmatter field \'type\': invalid value "{metadata.get("type")}"; '
                    f"expected one of: {', '.join(sorted(VALID_TYPES))}",
                )
            )

        visibility = metadata.get("visibility")
        valid_visibility = isinstance(visibility, str) and visibility in VALID_VISIBILITIES
        if visibility is not None and not valid_visibility:
            issues.append(
                Issue(
                    "error",
                    note.file,
                    f'frontmatter field \'visibility\': invalid value "{visibility}"; '
                    f"expected one of: {', '.join(sorted(VALID_VISIBILITIES))}",
                )
            )

        source_risk = metadata.get("source-risk")
        valid_source_risk = isinstance(source_risk, str) and source_risk in VALID_SOURCE_RISKS
        if source_risk is not None and not valid_source_risk:
            issues.append(
                Issue(
                    "error",
                    note.file,
                    f'frontmatter field \'source-risk\': invalid value "{source_risk}"; '
                    f"expected one of: {', '.join(sorted(VALID_SOURCE_RISKS))}",
                )
            )

        if public_release:
            if visibility is None:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        "public release: missing 'visibility'; classify the note before publication",
                    )
                )
            elif valid_visibility and visibility == "private":
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        "public release: visibility is 'private'; remove this note from the public release or keep the repository private",
                    )
                )

            if source_risk is None:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        "public release: missing 'source-risk'; classify provenance before publication",
                    )
                )
            elif valid_source_risk and source_risk in PUBLIC_RELEASE_BLOCKED_RISKS:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f"public release: source-risk '{source_risk}' is not publishable by default; "
                        "remove/sanitize the note or document an allowed original/open licence basis",
                    )
                )

            if valid_visibility and visibility in {"public-framework", "public-original", "public-open-licensed"}:
                source = metadata.get("source", "")
                if source:
                    source_lower = source.lower()
                    matched = [term for term in PUBLIC_RELEASE_SOURCE_SUSPICIOUS_TERMS if term in source_lower]
                    if matched:
                        issues.append(
                            Issue(
                                "error" if visibility != "public-open-licensed" else "warning",
                                note.file,
                                f"public release: source field contains suspicious term(s) {matched}; "
                                "verify provenance before publishing or document the open licence",
                            )
                        )

        parsed_dates: dict[str, date | None] = {}
        for field in ("last-reviewed", "review-after"):
            if field not in metadata:
                continue
            try:
                parsed_dates[field] = _date_value(metadata[field])
            except ValueError as exc:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f'frontmatter field \'{field}\': invalid value "{metadata[field]}"; {exc}',
                    )
                )
        if parsed_dates.get("last-reviewed") and parsed_dates.get("review-after"):
            if parsed_dates["review-after"] <= parsed_dates["last-reviewed"]:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        "frontmatter field 'review-after': must be later than 'last-reviewed'; choose the next future review date",
                    )
                )

        try:
            course_parts = note.path.relative_to(COURSES_DIR).parts
            if len(course_parts) < 2:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        "file location: move this note under courses/<course-code>/ rather than directly in courses/",
                    )
                )
                continue
            path_course = course_parts[0]
            if metadata.get("course") != path_course:
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f'frontmatter field \'course\': value "{metadata.get("course")}" does not match directory "{path_course}"; '
                        f'set it to "{path_course}"',
                    )
                )

            expected_directory = {
                "concept": "concepts",
                "lecture": "lectures",
                "problem-sheet": "problem-sheets",
                "exam-map": "exam",
            }.get(metadata.get("type"))
            if expected_directory and (len(course_parts) < 3 or course_parts[1] != expected_directory):
                issues.append(
                    Issue(
                        "error",
                        note.file,
                        f'frontmatter field \'type\': value "{metadata.get("type")}" requires directory "{expected_directory}/"; move the file there',
                    )
                )
            if metadata.get("type") == "glossary" and (len(course_parts) != 2 or note.path.name != "glossary.md"):
                issues.append(Issue("error", note.file, "frontmatter field 'type': glossary files must be named <course>/glossary.md"))
        except (ValueError, IndexError):
            issues.append(Issue("error", note.file, "file location: move this note under courses/<course>/"))

        h1 = re.search(r"^#\s+(.+?)\s*$", note.body, re.MULTILINE)
        if not h1:
            issues.append(Issue("error", note.file, "section '# title': missing; add one level-one heading matching frontmatter 'title'"))
        elif isinstance(metadata.get("title"), str) and h1.group(1) != metadata["title"]:
            issues.append(
                Issue(
                    "error",
                    note.file,
                    f'section "# {h1.group(1)}": does not match frontmatter title "{metadata["title"]}"; make them identical',
                )
            )

        if metadata.get("type") == "concept":
            headings = set(section_headings(note.body))
            for heading in (
                "Definition",
                "Intuition",
                "Worked Example",
                "Common Mistakes",
                "Mistake Log",
                "Practice Questions",
                "Related",
            ):
                if heading not in headings:
                    issues.append(Issue("error", note.file, f"section '## {heading}': missing; add it using TEMPLATE.md as the reference"))

        if "Mistake Log" in set(section_headings(note.body)):
            _, mistake_errors = parse_mistake_log(note)
            issues.extend(Issue("error", note.file, message) for message in mistake_errors)

        if metadata.get("type") in REVIEWABLE_TYPES and metadata.get("status") not in {"archived", "reference"}:
            if metadata.get("review-after") == "":
                issues.append(
                    Issue(
                        "warning",
                        note.file,
                        "frontmatter field 'review-after': blank on an active note; set YYYY-MM-DD to schedule it",
                    )
                )

        issues.extend(portability_issues(note.text, note.file))
        issues.extend(check_md_links(note.body, note.file, note.path))

    if not supplied_notes:
        note_paths = {note.path.resolve() for note in notes}
        for path in discover_markdown_paths():
            if path.resolve() in note_paths:
                continue
            text = path.read_text(encoding="utf-8")
            rel_path = path.relative_to(ROOT).as_posix()
            issues.extend(portability_issues(text, rel_path))
            issues.extend(check_md_links(text, rel_path, path))

    known_ids = set(ids)
    for note in notes:
        if note.parse_errors:
            continue
        note_id = note.metadata.get("id")
        for field in ("prerequisites", "related"):
            values = note.metadata.get(field)
            if not isinstance(values, list):
                continue
            for target in values:
                if target == note_id:
                    issues.append(
                        Issue(
                            "error",
                            note.file,
                            f"frontmatter field '{field}': contains its own id '{target}'; remove the self-reference",
                        )
                    )
                elif target not in known_ids:
                    issues.append(
                        Issue(
                            "error",
                            note.file,
                            f"frontmatter field '{field}': unknown note id '{target}'; create that note or remove/correct the id",
                        )
                    )

    if public_release and blocklist:
        scanned: set[Path] = set()
        for note in notes:
            if note.path.resolve() not in scanned:
                scanned.add(note.path.resolve())
                issues.extend(_scan_blocklist_term(note.text, note.file, blocklist))
        for path in discover_markdown_paths():
            if path.resolve() in scanned:
                continue
            scanned.add(path.resolve())
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT).as_posix()
            issues.extend(_scan_blocklist_term(text, rel, blocklist))

    return sorted(issues, key=lambda issue: (issue.file, issue.level != "error", issue.message))


def _scan_blocklist_term(text: str, file: str, blocklist: list[str]) -> list[Issue]:
    """Check *text* for every term in *blocklist* and return matching Issues."""
    issues: list[Issue] = []
    lower = text.lower()
    for term in blocklist:
        term_lower = term.lower()
        pos = lower.find(term_lower)
        if pos == -1:
            continue
        line_num = text[:pos].count("\n") + 1
        issues.append(
            Issue(
                "error",
                file,
                f"public release: blocked term '{term}' found (line {line_num}); remove or replace this term before publishing",
            )
        )
    return issues


def has_errors(issues: Iterable[Issue]) -> bool:
    return any(issue.level == "error" for issue in issues)


def format_issue(issue: Issue) -> str:
    return f"{issue.file}: {issue.level.upper()}: {issue.message}"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def generation_date() -> date:
    """Return the preferred generation date, respecting SOURCE_DATE_EPOCH for reproducibility."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is not None:
        try:
            return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date()
        except (ValueError, OSError):
            pass
    return date.today()


def check_md_links(text: str, file: str, source_path: Path) -> list[Issue]:
    """Check relative Markdown links resolve to an existing file."""
    issues: list[Issue] = []
    for target, line, _ in markdown_links(text):
        target_path = target.split("#", 1)[0]
        if not target_path.endswith(".md") or "://" in target_path or is_absolute_local_target(target_path):
            continue
        if not (source_path.parent / target_path).resolve().is_file():
            issues.append(
                Issue(
                    "error",
                    file,
                    f'Markdown link (line {line}): target "{target_path}" does not exist; correct the relative path or create the file',
                )
            )
    return issues

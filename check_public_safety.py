#!/usr/bin/env python3
"""Check public safety before releasing.

Serves as a hardening gate for ``make public-safety``.  Private notes may
live permanently under ``private/`` (the one-folder workflow), so the gate
does not fail merely because private content exists.  It fails only when
private material has leaked beyond the Git-ignored boundary.

Checks in order:

1. ``git ls-files private/`` — any tracked file under ``private/`` is a leak.
2. ``git diff --cached --name-only -- private/`` — any staged addition under
   ``private/`` would introduce private material into the next commit.
3. Scan every tracked and staged non-private text file for leak patterns,
   with two narrowly defined exclusion categories: this script's own source
   (``check_public_safety.py``) and its test file (``tests/test_public_safety.py``)
   are excluded from all pattern scanning, and ``studylib.py`` plus
   ``tests/test_studylib.py`` are additionally excluded from the local-path
   scan specifically — all four files legitimately contain the blocked
   patterns as literal string fixtures for defining or testing the checks
   themselves, not as real leaks. The scan list is otherwise built
   dynamically from Git rather than hardcoded, so newly added files are
   automatically covered.
4. Run ``validate_notes.py --public-release`` on the public ``courses/`` tree.
5. Run the full test suite.

This is pattern-based moderate protection against accidental publication,
not a semantic, legal, copyright, or default-deny approval system. Exit
code 0 only when all checks pass.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
import re

from studylib import ROOT, RAW_LOCAL_PATH_RE, mask_http_urls

# Self-referential files that legitimately contain the blocked patterns as
# literal string fixtures (this checker's own implementation and its tests).
# These are the only files excluded from candidate scanning; nothing else is.
SELF_TEST_EXCLUSIONS: tuple[str, ...] = (
    "check_public_safety.py",
    "tests/test_public_safety.py",
)

# Generic "private/" mentions are blocked only in non-framework files (see
# FRAMEWORK_PREFIXES / FRAMEWORK_EXACT below). This single pattern subsumes
# any more specific "private/<subdir>/" variant, so only one entry is needed.
PRIVATE_TEXT_PATTERNS: list[str] = ["private/"]

# Files whose own source or tests legitimately define or exercise the
# local-path regex itself, and therefore contain path-shaped strings as
# pattern literals or test fixtures rather than as real leaks. Excluded only
# from the local-path scan (not from the private/ or course-path checks),
# mirroring SELF_TEST_EXCLUSIONS' narrower purpose for this one check.
LOCAL_PATH_PATTERN_EXCLUSIONS: tuple[str, ...] = (
    "studylib.py",
    "tests/test_studylib.py",
)

# A real private-course directory name almost always contains a digit (e.g.
# a unit code like "ABCD1234"), while every documented placeholder token in
# this repository's own docs (`course-code`, `<course-code>`,
# `<ignored-course-root>`, `topic-slug`, ...) never does. This lets us catch
# a specific leaked private-course path even inside a framework file that is
# otherwise allowed to mention "private/" and "private/courses/" generically.
PRIVATE_COURSE_PATH_RE = re.compile(r"private/courses/[^/\s]*\d[^/\s]*/")

# Framework paths that legitimately reference private/ in documentation,
# help strings, or layout descriptions.  They are excluded from the
# PRIVATE_TEXT_PATTERNS check.  PRIVATE_COURSE_PATH_RE and RAW_LOCAL_PATH_RE
# still apply to them regardless, since a specific private-course path or a
# machine-local path is an unequivocal leak wherever it appears.
FRAMEWORK_PREFIXES: tuple[str, ...] = (
    "docs/",
    "prompts/",
    "templates/",
    ".github/",
    "handoffs/",
)
FRAMEWORK_EXACT: tuple[str, ...] = (
    ".gitignore",
    "LICENSE",
    "Makefile",
    "TEMPLATE.md",
    "README.md",
    "LLM_GUIDE.md",
    "PROJECT_STATE.md",
    "studylib.py",
    "build_manifest.py",
    "build_review_queue.py",
    "check_public_safety.py",
    "mark_reviewed.py",
    "scripts/pre-commit",
    "scripts/pre-push",
    "validate_notes.py",
)


class GitCommandError(RuntimeError):
    """Raised when a required Git command fails outright (e.g. not a repo)."""


def _run_git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _is_private(path_str: str) -> bool:
    """Return True if *path_str* is under the ignored ``private/`` tree."""
    return path_str.startswith("private/") or path_str == "private"


def _is_framework(path_str: str) -> bool:
    """Return True if *path_str* is a framework file that legitimately references ``private/``."""
    if any(path_str.startswith(p) for p in FRAMEWORK_PREFIXES):
        return True
    if path_str in FRAMEWORK_EXACT:
        return True
    return False


def _candidate_paths() -> list[str]:
    """Return the union of tracked and staged paths, excluding ``private/`` and the self-test files.

    Raises GitCommandError if a required Git command fails outright, so the
    caller can report it alongside the gate's other structured failures
    rather than the process exiting mid-helper.
    """
    seen: set[str] = set()

    r = _run_git(["ls-files"])
    if r.returncode != 0:
        raise GitCommandError(f"git ls-files failed:\n  {r.stderr.strip()}")
    for line in r.stdout.splitlines():
        line = line.strip()
        if line and not _is_private(line) and line not in SELF_TEST_EXCLUSIONS:
            seen.add(line)

    r = _run_git(["diff", "--cached", "--name-only"])
    if r.returncode != 0:
        raise GitCommandError(f"git diff --cached failed:\n  {r.stderr.strip()}")
    for line in r.stdout.splitlines():
        line = line.strip()
        if line and not _is_private(line) and line not in SELF_TEST_EXCLUSIONS:
            seen.add(line)

    return sorted(seen)


def _sources_for(path_str: str) -> list[tuple[str, str]]:
    """Return [(origin, text), ...] for *path_str*'s working-tree and staged content.

    Collapses to a single untagged entry when both sources exist and are
    identical (the ordinary case), so a hit is reported once, not twice.
    Only diverging content is tagged, so a diagnostic can tell a user
    precisely whether a leak is only staged (already fixed in the working
    tree) or only in an uncommitted working-tree edit.
    """
    wt_text: str | None = None
    abspath = ROOT / path_str
    if abspath.exists() and not abspath.is_dir():
        try:
            wt_text = abspath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            wt_text = None

    staged_text: str | None = None
    try:
        r = _run_git(["show", f":{path_str}"])
        if r.returncode == 0:
            staged_text = r.stdout
    except UnicodeDecodeError:
        staged_text = None

    if wt_text is not None and staged_text is not None:
        if wt_text == staged_text:
            return [("", wt_text)]
        return [("working tree", wt_text), ("staged", staged_text)]
    if wt_text is not None:
        return [("", wt_text)]
    if staged_text is not None:
        return [("", staged_text)]
    return []


def _scan_content(text: str, path_str: str, patterns: list[str], origin: str = "") -> list[str]:
    """Scan *text* for *patterns* (case-insensitive substring match).

    Returns a list of formatted hit strings.
    """
    hits = []
    tag = f" [{origin}]" if origin else ""
    for lineno, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        for pat in patterns:
            if pat.lower() in lower:
                hits.append(f"    {path_str}:{lineno}{tag}: {line.strip()}")
                break
    return hits


def _scan_regex(
    text: str,
    path_str: str,
    pattern: re.Pattern[str],
    origin: str = "",
    *,
    scan_text: str | None = None,
) -> list[str]:
    """Scan *text* line by line for *pattern*. Returns formatted hit strings."""
    hits = []
    tag = f" [{origin}]" if origin else ""
    source_lines = text.splitlines()
    scanned_lines = (scan_text if scan_text is not None else text).splitlines()
    for lineno, (line, scanned_line) in enumerate(zip(source_lines, scanned_lines), start=1):
        if pattern.search(scanned_line):
            hits.append(f"    {path_str}:{lineno}{tag}: {line.strip()}")
    return hits


def main() -> int:
    fails: list[str] = []

    # ── 1. No tracked files under private/ ────────────────────────────────
    r = _run_git(["ls-files", "private/"])
    if r.returncode != 0:
        fails.append(f"FAILED: git ls-files failed:\n  {r.stderr.strip()}")
    elif r.stdout.strip():
        fails.append(
            "FAILED: private/ files are tracked by Git.\n"
            "  These must be removed from tracking before a public release:\n"
            + "".join(f"    git rm --cached {shlex.quote(f)}\n" for f in r.stdout.splitlines())
        )

    # ── 2. No staged changes under private/ ───────────────────────────────
    r = _run_git(["diff", "--cached", "--name-only", "--", "private/"])
    if r.returncode != 0:
        fails.append(f"FAILED: git diff --cached failed:\n  {r.stderr.strip()}")
    elif r.stdout.strip():
        fails.append(
            "FAILED: staged changes would introduce private/ files.\n"
            "  Unstage them before a public release:\n"
            + "".join(f"    git restore --staged {shlex.quote(f)}\n" for f in r.stdout.splitlines())
        )

    # ── 3. No leak patterns in tracked/staged non-private files ───────────
    try:
        candidates = _candidate_paths()
    except GitCommandError as exc:
        fails.append(f"FAILED: {exc}")
        candidates = []

    private_hits: list[str] = []
    course_path_hits: list[str] = []
    local_hits: list[str] = []

    for path_str in candidates:
        is_fw = _is_framework(path_str)
        substring_patterns = [] if is_fw else PRIVATE_TEXT_PATTERNS

        for origin, text in _sources_for(path_str):
            if substring_patterns:
                for hit_str in _scan_content(text, path_str, substring_patterns, origin):
                    if hit_str not in private_hits:
                        private_hits.append(hit_str)

            # Always applied, even to framework files: a specific leaked
            # private-course path is a leak regardless of where it appears.
            for hit_str in _scan_regex(text, path_str, PRIVATE_COURSE_PATH_RE, origin):
                if hit_str not in course_path_hits:
                    course_path_hits.append(hit_str)

            # Always applied, except for the small set of files that
            # legitimately define/test this exact pattern: a machine-local
            # path is a leak wherever else it appears.
            if path_str not in LOCAL_PATH_PATTERN_EXCLUSIONS:
                for hit_str in _scan_regex(
                    text,
                    path_str,
                    RAW_LOCAL_PATH_RE,
                    origin,
                    scan_text=mask_http_urls(text),
                ):
                    if hit_str not in local_hits:
                        local_hits.append(hit_str)

    if private_hits:
        fails.append(
            "FAILED: public non-framework files reference private/ paths.\n"
            "  Tracked notes and generated files must not mention private material:\n"
            + "\n".join(private_hits)
        )

    if course_path_hits:
        fails.append(
            "FAILED: tracked/staged files reference a specific private-course path.\n"
            "  A path shaped like a real course directory (private/courses/<code>/...)\n"
            "  leaked into public-facing content, even though generic private/ mentions\n"
            "  are otherwise allowed in framework documentation:\n"
            + "\n".join(course_path_hits)
        )

    if local_hits:
        fails.append(
            "FAILED: tracked/staged files contain absolute local paths.\n"
            "  These must be removed before a public release:\n"
            + "\n".join(local_hits)
        )

    if fails:
        for msg in fails:
            print(msg, file=sys.stderr)
        return 1

    # ── 4. Public release gate ───────────────────────────────────────────
    print("private/ boundary is intact.  Running public release gate...")
    ret = subprocess.call(
        [sys.executable, "validate_notes.py", "--public-release"],
        cwd=ROOT,
    )
    if ret != 0:
        return ret

    # ── 5. Tests ─────────────────────────────────────────────────────────
    print("Public release gate passed.  Running tests...")
    ret = subprocess.call(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
    )
    if ret != 0:
        return ret

    print("public-safety: all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

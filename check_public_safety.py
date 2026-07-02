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
3. Scan every tracked and staged non-private text file for leak patterns.
   The scan list is built dynamically from Git rather than hardcoded, so
   newly added files are automatically covered.
4. Run ``validate_notes.py --public-release`` on the public ``courses/`` tree.
5. Run the full test suite.

Exit code 0 only when all checks pass.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from studylib import ROOT

BLOCKED_PATTERNS: list[str] = [
    "private/",
    "private/courses/",
    "/Users/ianchia",
    "file://",
]

# Framework paths that legitimately reference private/ in documentation,
# help strings, or layout descriptions.  They are excluded from the
# private/ and private/courses/ pattern checks.  The /Users/ianchia and
# file:// patterns still apply to them since those are unequivocal leaks.
FRAMEWORK_PREFIXES: tuple[str, ...] = (
    "docs/",
    "prompts/",
    "templates/",
    ".github/",
)
FRAMEWORK_EXACT: tuple[str, ...] = (
    ".gitignore",
    "LICENSE",
    "Makefile",
    "TEMPLATE.md",
    "README.md",
    "LLM_GUIDE.md",
    "studylib.py",
    "build_manifest.py",
    "build_review_queue.py",
    "check_public_safety.py",
    "mark_reviewed.py",
    "validate_notes.py",
)


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
    """Return the union of tracked and staged paths, excluding ``private/`` and the gate itself."""
    seen: set[str] = set()

    r = _run_git(["ls-files"])
    if r.returncode != 0:
        print(f"FAILED: git ls-files failed:\n  {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    for line in r.stdout.splitlines():
        line = line.strip()
        if line and not _is_private(line) and line != "check_public_safety.py":
            seen.add(line)

    r = _run_git(["diff", "--cached", "--name-only"])
    if r.returncode != 0:
        print(f"FAILED: git diff --cached failed:\n  {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    for line in r.stdout.splitlines():
        line = line.strip()
        if line and not _is_private(line) and line != "check_public_safety.py":
            seen.add(line)

    return sorted(seen)


def _scan_path(path_str: str, patterns: list[str]) -> list[str]:
    """Scan *path_str* for *patterns*.

    Returns a list of formatted ``file:line:match`` strings.
    File is skipped cleanly if it is missing, a directory, binary, or
    cannot be decoded as UTF-8 text.
    """
    abspath = ROOT / path_str
    if not abspath.exists():
        return []
    if abspath.is_dir():
        return []

    try:
        text = abspath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        for pat in patterns:
            if pat.lower() in lower or pat in line:
                hits.append(f"    {path_str}:{lineno}: {line.strip()}")
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
            + "".join(f"    {f}\n" for f in r.stdout.splitlines())
        )

    # ── 2. No staged changes under private/ ───────────────────────────────
    r = _run_git(["diff", "--cached", "--name-only", "--", "private/"])
    if r.returncode != 0:
        fails.append(f"FAILED: git diff --cached failed:\n  {r.stderr.strip()}")
    elif r.stdout.strip():
        fails.append(
            "FAILED: staged changes would introduce private/ files.\n"
            "  Unstage them before a public release:\n"
            + "".join(f"    git restore --staged {f}\n" for f in r.stdout.splitlines())
        )

    # ── 3. No leak patterns in tracked/staged non-private files ───────────
    candidates = _candidate_paths()

    private_hits: list[str] = []
    local_hits: list[str] = []

    for path_str in candidates:
        if _is_framework(path_str):
            # Framework files: only scan for absolute-local-path patterns.
            hits = _scan_path(path_str, ["/Users/ianchia", "file://"])
            local_hits.extend(hits)
        else:
            # Non-framework files: scan for all blocked patterns.
            hits = _scan_path(path_str, BLOCKED_PATTERNS)
            for h in hits:
                pat = h.split(": ")[-1] if ": " in h else ""
                if pat in ("/Users/ianchia", "file://") or pat.startswith("/Users/") or pat.startswith("file:"):
                    local_hits.append(h)
                else:
                    private_hits.append(h)

    if private_hits:
        fails.append(
            "FAILED: public non-framework files reference private/ paths.\n"
            "  Tracked notes and generated files must not mention private material:\n"
            + "\n".join(private_hits)
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

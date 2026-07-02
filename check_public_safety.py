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
3. ``git grep`` for ``private/`` references in the public surface — leaked
   path references in ``courses/`` notes or generated files (``manifest.json``,
   ``REVIEW_QUEUE.md``) would reveal private structure.
4. Run ``validate_notes.py --public-release`` on the public ``courses/`` tree.
5. Run the full test suite.

Exit code 0 only when all checks pass.
"""

from __future__ import annotations

import subprocess
import sys

from studylib import ROOT

# Tracked files that must never reference private/ paths.
# Docs/ and prompts/ legitimately describe the one-folder layout, so they
# are excluded from the private/ scan; only the note surface and generated
# indexes are checked.
PUBLIC_SURFACE: list[str] = [
    "courses/",
    "manifest.json",
    "REVIEW_QUEUE.md",
    "INDEX.md",
    "LLM_GUIDE.md",
]


def _run_git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _git_grep(patterns: list[str], paths: list[str]) -> subprocess.CompletedProcess:
    """Call ``git grep`` with one or more *patterns* restricted to *paths*."""
    cmd = ["git", "grep", "-n", "--no-color"]
    for p in patterns:
        cmd.extend(["-e", p])
    cmd.append("--")
    cmd.extend(paths)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


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

    # ── 3. No private/ path references in the public surface ──────────────
    # Check the note-and-index surface for leaked references to the private
    # directory.  Docs and prompts are excluded because they legitimately
    # describe the one-folder layout.  The patterns ``private/`` and
    # ``private/courses/`` catch relative path references that would reveal
    # the private directory structure (e.g. in a note's body linking to a
    # private file, or a generated manifest entry pointing under private/).

    r = _git_grep(["private/", "private/courses/"], PUBLIC_SURFACE)
    if r.returncode == 0 and r.stdout.strip():
        fails.append(
            "FAILED: public-surface files reference private/ paths.\n"
            "  Tracked notes and generated files must not mention private material:\n"
            + "".join(f"    {l}\n" for l in r.stdout.splitlines())
        )
    elif r.returncode not in (0, 1):
        fails.append(f"FAILED: git grep on public surface failed:\n  {r.stderr.strip()}")

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

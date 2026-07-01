#!/usr/bin/env python3
"""Validate notes normally or apply the conservative public-release gate."""

import argparse

from studylib import discover_note_paths, format_issue, has_errors, validate_repository


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-release",
        action="store_true",
        help="fail on private, course-derived, unknown-risk, or unclassified notes",
    )
    args = parser.parse_args()

    paths = discover_note_paths()
    issues = validate_repository(public_release=args.public_release)
    for issue in issues:
        print(format_issue(issue))

    errors = sum(issue.level == "error" for issue in issues)
    warnings = sum(issue.level == "warning" for issue in issues)
    if has_errors(issues):
        mode = " public-release" if args.public_release else ""
        print(f"FAILED{mode}: {len(paths)} note(s), {errors} error(s), {warnings} warning(s).")
        return 1
    mode = " public-release" if args.public_release else ""
    print(f"OK{mode}: {len(paths)} note(s), no errors, {warnings} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

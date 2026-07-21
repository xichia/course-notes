import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_public_safety import main


REPO_ROOT = Path(__file__).parent.parent
TEST_TMP = REPO_ROOT / ".test_tmp"


def setUpModule():
    # Keep synthetic repositories inside the disposable public-repository test
    # boundary, never under the real ignored course-data tree. This module
    # exclusively owns the shared parent for the duration of its tests.
    TEST_TMP.mkdir()


def tearDownModule():
    TEST_TMP.rmdir()
    if TEST_TMP.exists():
        raise AssertionError(f"temporary test root still exists: {TEST_TMP}")


class TestPublicSafety(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as the repo root
        self.temp_dir = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.root = Path(self.temp_dir.name)
        
        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)

        # We need an initial commit so we can stage things without git complaining about no HEAD
        self._add_file("README.md", "Hello")
        self._git_add("README.md")
        self._git_commit()

        # Patch ROOT in check_public_safety
        self.patch_root = patch('check_public_safety.ROOT', self.root)
        self.patch_root.start()
        
        # Patch subprocess.call to skip the actual validation and test suite execution
        self.patch_call = patch('check_public_safety.subprocess.call', return_value=0)
        self.mock_call = self.patch_call.start()

        # Intercept stderr to check failure messages
        self.patch_stderr = patch('sys.stderr', new_callable=io.StringIO)
        self.mock_stderr = self.patch_stderr.start()
        
        # Intercept stdout to avoid spamming the test output
        self.patch_stdout = patch('sys.stdout', new_callable=io.StringIO)
        self.mock_stdout = self.patch_stdout.start()

    def tearDown(self):
        self.patch_root.stop()
        self.patch_call.stop()
        self.patch_stderr.stop()
        self.patch_stdout.stop()
        self.temp_dir.cleanup()

    def _add_file(self, path_str, content=""):
        p = self.root / path_str
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
        return p

    def _git_add(self, path_str):
        subprocess.run(["git", "add", path_str], cwd=self.root, check=True, capture_output=True)
        
    def _git_commit(self):
        subprocess.run(["git", "commit", "-m", "msg"], cwd=self.root, check=True, capture_output=True)

    def test_tracked_private_file_fails(self):
        self._add_file("private/leak.txt", "secret")
        self._git_add("private/leak.txt")
        self._git_commit()
        
        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: private/ files are tracked by Git", self.mock_stderr.getvalue())

    def test_staged_private_file_fails(self):
        self._add_file("private/leak.txt", "secret")
        self._git_add("private/leak.txt")
        # Do not commit, it's just staged
        
        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: staged changes would introduce private/ files", self.mock_stderr.getvalue())

    def test_ignored_private_files_not_scanned(self):
        self._add_file("private/ignored.txt", "secret leak")
        # Neither added nor committed, so it's untracked/ignored
        
        ret = main()
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")
        self.assertEqual(self.mock_call.call_count, 2)

    def test_private_reference_in_public_content(self):
        self._add_file("courses/public.md", "Check out private/notes.md")
        self._git_add("courses/public.md")
        self._git_commit()
        
        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: public non-framework files reference private/ paths", self.mock_stderr.getvalue())
        self.assertIn("courses/public.md:1", self.mock_stderr.getvalue())

    def test_unrecognised_root_file_with_private_reference_fails(self):
        self._add_file("STATUS.md", "See private/notes.md")
        self._git_add("STATUS.md")

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: public non-framework files reference private/ paths", self.mock_stderr.getvalue())
        self.assertIn("STATUS.md:1", self.mock_stderr.getvalue())

    def test_private_courses_reference_in_public_content(self):
        self._add_file("courses/public.md", "Check out private/courses/notes.md")
        self._git_add("courses/public.md")
        
        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: public non-framework files reference private/ paths", self.mock_stderr.getvalue())
        self.assertIn("private/courses/", self.mock_stderr.getvalue())

    def test_absolute_paths_blocked_everywhere(self):
        # 1. In content
        self._add_file("courses/public.md", "My path is /Users/ianchia/stuff")
        self._git_add("courses/public.md")

        # 2. In framework file
        self._add_file("Makefile", "Local dev file://foo")
        self._git_add("Makefile")

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        self.assertIn("FAILED: tracked/staged files contain absolute local paths", stderr)
        self.assertIn("/Users/ianchia", stderr)
        self.assertIn("file://", stderr)
        # Should not fail on private reference because these are just absolute paths
        self.assertNotIn("FAILED: public non-framework files reference private/ paths", stderr)

    def test_absolute_paths_blocked_for_any_username_not_just_configured_one(self):
        # The detector must not be hardcoded to one specific local username —
        # any /Users/<name>, /home/<name>, or Windows drive-letter path is a leak.
        self._add_file("courses/a.md", "See /Users/someoneelse/notes for details")
        self._add_file("courses/b.md", "See /home/otherperson/notes for details")
        self._add_file("courses/c.md", r"See C:\Users\someone\Documents for details")
        for f in ("courses/a.md", "courses/b.md", "courses/c.md"):
            self._git_add(f)

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        self.assertIn("FAILED: tracked/staged files contain absolute local paths", stderr)
        self.assertIn("/Users/someoneelse", stderr)
        self.assertIn("/home/otherperson", stderr)
        self.assertIn(r"C:\Users\someone", stderr)

    def test_specific_private_course_path_blocked_even_in_framework_file(self):
        # Generic "private/" and "private/courses/" mentions are allowed in
        # framework docs, but a path shaped like a real course directory
        # (containing a digit, unlike the documented "course-code" placeholder)
        # must still be caught, even inside an otherwise-exempt framework file.
        self._add_file(
            "docs/example.md",
            "See private/courses/ABCD1234-2026-S1/materials/lecture.pdf for the leak.",
        )
        self._git_add("docs/example.md")

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        self.assertIn("FAILED: tracked/staged files reference a specific private-course path", stderr)
        self.assertIn("ABCD1234-2026-S1", stderr)

    def test_generic_course_code_placeholder_in_framework_file_is_allowed(self):
        # The documented placeholder shape ("course-code", no digits) must
        # not be mistaken for a real leaked course path.
        self._add_file(
            "docs/example.md",
            "mkdir -p private/courses/course-code/concepts",
        )
        self._git_add("docs/example.md")

        ret = main()
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")

    def test_private_file_staged_then_edited_in_working_tree_still_fails(self):
        # A private/ file staged for addition, then further edited (but not
        # unstaged) in the working tree, must still be caught by the
        # staged-private-file check regardless of the working-tree content.
        self._add_file("private/leak.txt", "secret v1")
        self._git_add("private/leak.txt")
        self._add_file("private/leak.txt", "secret v2, edited after staging")

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: staged changes would introduce private/ files", self.mock_stderr.getvalue())

    def test_private_file_staged_then_deleted_in_working_tree_still_fails(self):
        # A private/ file staged for addition, then deleted from the working
        # tree without unstaging, must still be caught — the staged blob
        # would still leak on commit.
        self._add_file("private/leak.txt", "secret")
        self._git_add("private/leak.txt")
        (self.root / "private" / "leak.txt").unlink()

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: staged changes would introduce private/ files", self.mock_stderr.getvalue())

    def test_working_tree_only_leak_is_caught_and_tagged(self):
        # An uncommitted, unstaged working-tree edit that introduces a leak
        # must be caught even though nothing was staged.
        self._add_file("courses/public.md", "Reference to private/notes here")
        self._git_add("courses/public.md")
        self._git_commit()
        # Now edit in the working tree only (not staged).
        self._add_file("courses/public.md", "Reference to private/other-notes here")

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: public non-framework files reference private/ paths", self.mock_stderr.getvalue())

    def test_checker_and_its_own_test_file_are_excluded_from_scanning(self):
        # check_public_safety.py and tests/test_public_safety.py legitimately
        # contain the blocked pattern strings as literal fixtures; they must
        # never be flagged against themselves.
        self._add_file("check_public_safety.py", 'BLOCKED = ["private/", "/Users/ianchia"]\n')
        self._add_file(
            "tests/test_public_safety.py",
            'self.assertIn("private/", "a fixture containing private/ literally")\n',
        )
        self._git_add("check_public_safety.py")
        self._git_add("tests/test_public_safety.py")

        ret = main()
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")

    def test_remediation_command_shell_quotes_filenames_with_spaces(self):
        self._add_file("private/leak with spaces.txt", "secret")
        self._git_add("private/leak with spaces.txt")

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        # A filename containing a space must be quoted in the suggested
        # remediation command so it is safe to copy-paste into a shell.
        self.assertIn("'private/leak with spaces.txt'", stderr)

    def test_studylib_pattern_definitions_excluded_from_local_path_scan_only(self):
        # studylib.py and its test file legitimately define/exercise the
        # local-path regex as literal fixtures — excluded from that one
        # check, but still subject to the private/ substring check.
        self._add_file("studylib.py", 'RAW_LOCAL_PATH_RE = re.compile(r"/Users/[^\\s]+")\n')
        self._add_file(
            "tests/test_studylib.py",
            'self.assertTrue(is_absolute_local_target("/Users/example/file.md"))\n',
        )
        self._git_add("studylib.py")
        self._git_add("tests/test_studylib.py")

        ret = main()
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")

    def test_studylib_still_checked_for_specific_course_path_leaks(self):
        # studylib.py is a framework file (generic "private/" mentions are
        # allowed there deliberately — see its own docstrings), and its
        # local-path exclusion is narrower still. Neither exemption should
        # become a blanket exemption from every check: a specific leaked
        # course path must still be caught even here.
        self._add_file(
            "studylib.py",
            "# example: private/courses/ABCD1234-2026-S1/materials/lecture.pdf\n",
        )
        self._git_add("studylib.py")

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: tracked/staged files reference a specific private-course path", self.mock_stderr.getvalue())

    def test_public_release_validator_failure_propagates(self):
        self.mock_call.return_value = 1
        ret = main()
        self.assertEqual(ret, 1)
        # Only the public-release validator should have been invoked; the
        # test suite must not run once an earlier stage has already failed.
        self.assertEqual(self.mock_call.call_count, 1)

    def test_test_suite_failure_propagates(self):
        # First call (validate_notes.py --public-release) succeeds, second
        # call (the test suite) fails.
        self.mock_call.side_effect = [0, 1]
        ret = main()
        self.assertEqual(ret, 1)
        self.assertEqual(self.mock_call.call_count, 2)

    def test_staged_leak_with_clean_worktree_fails(self):
        # 1. Stage a leak
        self._add_file("courses/public.md", "Check out private/leak")
        self._git_add("courses/public.md")
        # 2. Fix it in the worktree
        self._add_file("courses/public.md", "Clean content")
        
        # The gate must catch the staged leak despite the clean worktree
        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("FAILED: public non-framework files reference private/ paths", self.mock_stderr.getvalue())

    def test_scripts_pre_commit_allowed_as_framework(self):
        # This file is allowed to mention private/
        self._add_file("scripts/pre-commit", "check private/ for leaks")
        self._git_add("scripts/pre-commit")
        
        ret = main()
        # Should pass
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")

    def test_different_staged_tool_is_not_a_framework_exemption(self):
        self._add_file("tools/future.py", 'print("private/notes/")\n')
        self._git_add("tools/future.py")

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("tools/future.py:1", self.mock_stderr.getvalue())
        self.assertIn("public non-framework files reference private/ paths", self.mock_stderr.getvalue())

    def test_different_tool_working_tree_edit_remains_scanned(self):
        self._add_file("tools/future.py", 'print("public helper")\n')
        self._git_add("tools/future.py")
        self._git_commit()
        self._add_file("tools/future.py", 'print("private/working-tree-leak")\n')

        ret = main()
        self.assertEqual(ret, 1)
        self.assertIn("tools/future.py:1", self.mock_stderr.getvalue())
        self.assertIn("working tree", self.mock_stderr.getvalue())

    def test_staged_http_urls_with_path_shaped_segments_are_allowed(self):
        self._add_file(
            "courses/urls.md",
            "\n".join(
                (
                    "https://github.com/xichia/course-notes.git",
                    "[guide](https://example.invalid/docs/C:/Users/name/guide)",
                    "https://example.invalid/path/Users/name/guide",
                    "https://example.invalid/path?next=C:/Users/name/guide",
                    "https://example.invalid/path?x=1&next=C:/Users/name/guide",
                    "https://example.invalid/path#C:/Users/name/guide",
                    "(https://example.invalid/a_(b)/guide).",
                )
            ),
        )
        self._git_add("courses/urls.md")

        ret = main()
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")

    def test_staged_real_local_paths_and_url_adjacent_windows_path_fail(self):
        self._add_file(
            "courses/local-paths.md",
            "\n".join(
                (
                    "/Users/name/course-notes",
                    "/home/name/course-notes",
                    r"C:\Users\name\course-notes",
                    "C:/Users/name/course-notes",
                    "file:///Users/name/course-notes",
                    "file:///C:/Users/name/course-notes",
                    r"https://example.invalid/path\C:\Users\name\course-notes",
                )
            ),
        )
        self._git_add("courses/local-paths.md")

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        self.assertIn("tracked/staged files contain absolute local paths", stderr)
        self.assertIn("/Users/name/course-notes", stderr)
        self.assertIn(r"C:\Users\name\course-notes", stderr)
        self.assertIn("file:///C:/Users/name/course-notes", stderr)

    def test_staged_punctuation_adjacent_drive_roots_fail_for_all_delimiters(self):
        lines = []
        for delimiter in (",", ";", ".", "!"):
            lines.append(
                f"https://example.invalid/path{delimiter}C:\\Users\\name\\course-notes"
            )
            lines.append(
                f"https://example.invalid/path{delimiter}D:/Users/name/course-notes"
            )
        self._add_file("courses/punctuation-paths.md", "\n".join(lines))
        self._git_add("courses/punctuation-paths.md")

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        self.assertIn("tracked/staged files contain absolute local paths", stderr)
        for delimiter in (",", ";", ".", "!"):
            self.assertIn(f"{delimiter}C:\\Users\\name\\course-notes", stderr)
            self.assertIn(f"{delimiter}D:/Users/name/course-notes", stderr)

    def test_working_tree_punctuation_adjacent_drive_roots_are_caught(self):
        self._add_file("courses/punctuation-working.md", "clean content\n")
        self._git_add("courses/punctuation-working.md")
        self._git_commit()
        self._add_file(
            "courses/punctuation-working.md",
            r"https://example.invalid/path,C:\Users\name\course-notes" "\n"
            "https://example.invalid/path;D:/Users/name/course-notes\n",
        )

        ret = main()
        self.assertEqual(ret, 1)
        stderr = self.mock_stderr.getvalue()
        self.assertIn("working tree", stderr)
        self.assertIn(r"C:\Users\name\course-notes", stderr)
        self.assertIn("D:/Users/name/course-notes", stderr)

    def test_binary_files_skipped_safely(self):
        # Write a binary file
        self._add_file("courses/image.png", b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        self._git_add("courses/image.png")
        
        ret = main()
        self.assertEqual(ret, 0)
        self.assertEqual(self.mock_stderr.getvalue(), "")

    def test_public_release_gate_and_tests_are_called(self):
        ret = main()
        self.assertEqual(ret, 0)
        # Expect two calls to subprocess.call:
        # 1. validate_notes.py --public-release
        # 2. unittest discover
        self.assertEqual(self.mock_call.call_count, 2)
        call_args_list = self.mock_call.call_args_list
        self.assertIn("validate_notes.py", call_args_list[0][0][0])
        self.assertIn("unittest", call_args_list[1][0][0])

if __name__ == "__main__":
    unittest.main()

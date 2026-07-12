import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_public_safety import main

class TestPublicSafety(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as the repo root
        # Sandbox compliance: use a local .test_tmp directory rather than the system /tmp
        test_tmp = Path(__file__).parent.parent / ".test_tmp"
        test_tmp.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=test_tmp)
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
        try:
            self.temp_dir.cleanup()
        except OSError:
            pass  # Windows sometimes has issues with cleanup, but this is mac

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

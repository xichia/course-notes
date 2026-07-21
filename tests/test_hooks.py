"""Tests for `make install-hooks` / `make uninstall-hooks`.

These exercise the actual Makefile targets in an isolated temporary Git
repository (never the developer's real .git/hooks), by copying only the
public framework files the targets need: Makefile, scripts/pre-commit, and
scripts/pre-push.
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEST_TMP = REPO_ROOT / ".test_tmp"


def setUpModule():
    # Keep synthetic Git repositories inside the disposable public-repository
    # test boundary, never under the real ignored course-data tree. This module
    # exclusively owns the shared parent for the duration of its tests.
    TEST_TMP.mkdir()


def tearDownModule():
    TEST_TMP.rmdir()
    if TEST_TMP.exists():
        raise AssertionError(f"temporary test root still exists: {TEST_TMP}")


class TestHooks(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.root = Path(self.temp_dir.name)

        subprocess.run(["git", "init", "-b", "main"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)

        shutil.copy(REPO_ROOT / "Makefile", self.root / "Makefile")
        (self.root / "scripts").mkdir()
        shutil.copy(REPO_ROOT / "scripts" / "pre-commit", self.root / "scripts" / "pre-commit")
        shutil.copy(REPO_ROOT / "scripts" / "pre-push", self.root / "scripts" / "pre-push")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make(self, *targets):
        return subprocess.run(
            ["make", *targets],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_install_hooks_installs_both_pre_commit_and_pre_push(self):
        result = self._make("install-hooks")
        self.assertEqual(result.returncode, 0, result.stderr)

        pre_commit_dst = self.root / ".git" / "hooks" / "pre-commit"
        pre_push_dst = self.root / ".git" / "hooks" / "pre-push"
        self.assertTrue(pre_commit_dst.is_file())
        self.assertTrue(pre_push_dst.is_file())
        self.assertEqual(pre_commit_dst.read_text(), (self.root / "scripts" / "pre-commit").read_text())
        self.assertEqual(pre_push_dst.read_text(), (self.root / "scripts" / "pre-push").read_text())
        # Installed hooks must be executable.
        self.assertTrue(pre_commit_dst.stat().st_mode & 0o111)
        self.assertTrue(pre_push_dst.stat().st_mode & 0o111)

    def test_install_hooks_is_idempotent(self):
        first = self._make("install-hooks")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self._make("install-hooks")
        self.assertEqual(second.returncode, 0, second.stderr)

    def test_install_hooks_refuses_to_overwrite_unrelated_pre_commit_hook(self):
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        unrelated = hooks_dir / "pre-commit"
        unrelated.write_text("#!/bin/sh\necho 'unrelated hook, not ours'\n")

        result = self._make("install-hooks")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists and differs", result.stdout + result.stderr)
        # The unrelated hook must be left completely untouched.
        self.assertEqual(unrelated.read_text(), "#!/bin/sh\necho 'unrelated hook, not ours'\n")

    def test_install_hooks_refuses_to_overwrite_unrelated_pre_push_hook(self):
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        unrelated = hooks_dir / "pre-push"
        unrelated.write_text("#!/bin/sh\necho 'also unrelated'\n")

        result = self._make("install-hooks")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists and differs", result.stdout + result.stderr)
        self.assertEqual(unrelated.read_text(), "#!/bin/sh\necho 'also unrelated'\n")

    def test_uninstall_hooks_removes_only_project_owned_hooks(self):
        self._make("install-hooks")
        result = self._make("uninstall-hooks")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertFalse((self.root / ".git" / "hooks" / "pre-commit").exists())
        self.assertFalse((self.root / ".git" / "hooks" / "pre-push").exists())

    def test_uninstall_hooks_leaves_unrelated_hook_in_place(self):
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        unrelated = hooks_dir / "pre-commit"
        unrelated.write_text("#!/bin/sh\necho 'not managed by course notes'\n")

        result = self._make("uninstall-hooks")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not managed by this project", result.stdout + result.stderr)
        self.assertTrue(unrelated.exists())
        self.assertEqual(unrelated.read_text(), "#!/bin/sh\necho 'not managed by course notes'\n")

    def test_uninstall_hooks_with_nothing_installed_is_a_safe_no_op(self):
        result = self._make("uninstall-hooks")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nothing to remove", result.stdout + result.stderr)

    def test_hook_scripts_document_bypass_truthfully(self):
        # The bypass instructions in each hook's own comment must match the
        # real Git bypass flag for that hook type — this is a truthfulness
        # check on the shipped documentation, not just behavior.
        pre_commit_text = (self.root / "scripts" / "pre-commit").read_text()
        pre_push_text = (self.root / "scripts" / "pre-push").read_text()
        self.assertIn("git commit --no-verify", pre_commit_text)
        self.assertIn("git push --no-verify", pre_push_text)
        # Both hooks must also state they are optional, not automatically
        # installed — matching PROJECT_STATE.md's claim about hook status.
        self.assertIn("optional", pre_commit_text.lower())
        self.assertIn("optional", pre_push_text.lower())


if __name__ == "__main__":
    unittest.main()

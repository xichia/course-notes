# Operating Checklist

Quick reference for the one-working-copy Course Notes workflow.

See:

- [Repository layout](repository-layout.md) for the directory model;
- [Publication policy](publication-policy.md) for classification rules;
- [Public-release checklist](public-release-checklist.md) before promoting private material.

---

## 1. Private schema-based notes

Private Markdown notes following the normal note schema may live under `private/courses/`.

Validate them and rebuild their generated views with:

```bash
make study-all
```

This runs the private-note equivalents of validation, manifest generation, and review-queue generation.

`make study-all` is for schema-based private notes. It is not a general validator for raw source packs, LMS imports, attachments, or five-file study-layer modules. Those artifacts use their own documented workflows and validators.

---

## 2. Public notes and framework changes

For a non-mutating validation and test pass, run:

```bash
make check
```

This validates public notes and runs the regression suite without rebuilding files. When source
notes have changed and generated public views should be refreshed, run:

```bash
make refresh
```

`make refresh` is intentionally mutating. `make all` remains the backward-compatible combined
refresh-and-test command. Generated files should be rebuilt through supported commands, not
edited manually.

---

## 3. Canonical safety gate

Before a public commit or push, run:

```bash
make public-safety
```

The gate verifies that:

- nothing under `private/` is tracked;
- nothing under `private/` is staged;
- relevant tracked and staged public text does not contain configured leak patterns;
- public-release validation passes;
- all tests pass.

The gate checks both staged and working-tree content where necessary, so a staged leak cannot be hidden by a later working-tree edit.

This is moderate accidental-publication protection. It does not establish copyright clearance, confidentiality clearance, institutional permission, or legal authority to publish.

---

## 4. Before a public commit

A useful pre-commit sequence is:

```bash
make check
make refresh
make public-safety
make verify-generated
git diff --check
git status --short
git diff --cached --name-status
git ls-files -- private/
git diff --cached --name-only -- private/
```

The final two commands must return no private paths.

`make study-all` may also be useful when schema-based private notes changed, but it is not required for unrelated public framework work.

Stop if:

- a command fails;
- an unexpected path is staged;
- a generated file changes unexpectedly;
- a private path appears;
- the diff contains material you have not reviewed.

---

## 5. Before a push

Before pushing:

```bash
make public-safety
git status --branch --short
git log --oneline --decorate -3
```

Confirm that:

- the intended commits are present;
- the working tree is clean or contains only understood changes;
- the branch and remote are correct;
- no private file is tracked or staged.

Remote CI can ratify the pushed state only after the push occurs.

---

## 6. Promoting a private note

Unsanitized or uncleared material must remain under `private/`.

A derivative may be copied or rewritten into tracked `courses/` only after a separate sanitization and review process.

Allowed public metadata includes:

```yaml
visibility: public-original
source-risk: original
```

or, when the source has a documented compatible licence:

```yaml
visibility: public-open-licensed
source-risk: open-licensed
```

Do not change metadata merely to make validation pass. The content itself must support the classification.

After promotion:

```bash
make refresh
make check
make public-safety
```

Then complete the [Public-release checklist](public-release-checklist.md).

---

## 7. Private workspace

Common ignored locations include:

```text
private/courses/
private/raw/
private/drafts/
private/manifest.json
private/REVIEW_QUEUE.md
private/framework-feedback.md
```

Other workflow-specific private directories may also exist.

Never use `git add -f` to force private material into Git.

If a private path appears in `git status`, determine whether it is genuinely ignored, staged, or tracked before taking action.

Useful checks:

```bash
git check-ignore -v private/
git status --short --ignored
git ls-files -- private/
git diff --cached --name-only -- private/
```

Private material is deliberately absent from Git history and therefore needs an independent backup strategy.

---

## 8. Responding to a safety failure

Read the complete diagnostic before changing anything.

### Tracked private file

Remove it from Git’s index without deleting the working copy:

```bash
git rm --cached -- <file>
```

### Staged private file

Unstage it without discarding the working copy:

```bash
git restore --staged -- <file>
```

### Leak in a public file

Remove or replace the sensitive reference, then rerun:

```bash
make public-safety
```

Do not weaken a legitimate check merely to obtain a passing result.

---

## 9. Optional local hooks

The repository provides two optional managed hooks:

```text
scripts/pre-commit
scripts/pre-push
```

Both run the canonical:

```bash
make public-safety
```

### Install

```bash
make install-hooks
```

This manages:

```text
.git/hooks/pre-commit
.git/hooks/pre-push
```

Installation is safe and idempotent:

- an already matching Course Notes hook is left in place;
- an unrelated existing hook is not overwritten;
- a conflict produces a diagnostic instead.

Hooks are local to the working copy. Installing them does not commit them to another user’s `.git/hooks/` directory.

### Uninstall

```bash
make uninstall-hooks
```

Removal is ownership-aware:

- a byte-identical Course Notes hook is removed;
- an unrelated or manually modified hook is left untouched;
- missing hooks are a safe no-op.

### Bypass

Either hook can be deliberately bypassed:

```bash
git commit --no-verify
git push --no-verify
```

Bypass only when the consequences are understood. A routine failure should be corrected rather than habitually bypassed.

### Limits

Hooks are:

- optional;
- local;
- bypassable;
- not a substitute for reviewing the staged diff;
- not proof that content is authorised for publication.

The pre-push hook runs before data leaves the local repository, but GitHub Actions remains the remote source of post-push ratification.

---

## 10. CI and generated-file freshness

CI runs on pushes and pull requests.

It:

1. runs the canonical public-safety gate;
2. regenerates both public views from the HEAD commit timestamp;
3. checks that the committed generated files were current.

A local passing result does not mean CI has already passed. After pushing, inspect the remote workflow before describing the release as green.

---

## 11. Local release blocklist

An optional `.public-release-blocklist` may contain additional terms that should fail public-release validation.

Example:

```text
# Comments and blank lines are ignored.
Example Institution
example.internal
COURSE-PLACEHOLDER
```

The file is:

- local only;
- ignored by Git;
- case-insensitive;
- a smoke alarm rather than semantic review.

Do not commit it.

---

## 12. Minimal daily sequence

For schema-based private-note study:

```bash
make study-review
```

For public-note maintenance:

```bash
make review
```

After editing tracked notes:

```bash
make refresh
make check
```

Before committing or pushing:

```bash
make public-safety
```

When in doubt, stop and inspect:

```bash
git status --short
git diff
git diff --cached
```

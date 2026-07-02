# Operating Checklist

Quick reference for the one-folder Course Notes workflow.  See
[repository-layout.md](repository-layout.md) for the full directory map and
[publication-policy.md](publication-policy.md) for the metadata rules.

---

## 1. Daily / private study

Study your private notes under `private/courses/`, review them, and keep the
private generated views up to date:

```bash
make study-all
```

This validates the private notes, rebuilds `private/manifest.json`, and
regenerates `private/REVIEW_QUEUE.md`.

---

## 2. Public framework / public notes

Before any public commit, make sure the tracked `courses/` tree and framework
files are consistent:

```bash
make all
```

This validates public notes, rebuilds `manifest.json`, regenerates
`REVIEW_QUEUE.md`, and runs all tests.

---

## 3. Safety gate

The hardening gate checks that no private material has leaked into the public
surface:

```bash
make public-safety
```

It verifies:

- No files under `private/` are tracked by Git.
- No files under `private/` are staged.
- No public notes or generated files contain `private/` path references.
- The public release gate (`validate_notes.py --public-release`) passes.
- All tests pass.

---

## 4. Before every public commit or push

Run the full pre-flight sequence:

```bash
make all                          # public consistency check
make study-all                    # private consistency (optional but recommended)
make public-safety                # leak barrier
git status --short                # confirm only intended files are staged
git ls-files private              # must return nothing
git diff --cached --name-only -- private/   # must return nothing
```

If any command fails or reveals unexpected files, stop and investigate before
committing.

---

## 5. Promoting a private note to public

A note under `private/courses/<course>/` may be promoted to
`courses/<course>/` only after sanitization.  The promoted note must use
public-safe metadata:

```yaml
visibility: public-original
source-risk: original
```

Or, if the source has a documented open licence:

```yaml
visibility: public-open-licensed
source-risk: open-licensed
```

After promoting a note, run:

```bash
make all
make public-safety
```

See [publication-policy.md](publication-policy.md) and
[public-release-checklist.md](public-release-checklist.md) before promoting any
material.

---

## 6. Private material — allowed paths

The following paths are Git-ignored.  Keep all raw, source-risky, or
unpublished material here:

```text
private/courses/
private/raw/
private/drafts/
private/manifest.json
private/REVIEW_QUEUE.md
private/framework-feedback.md
```

Never commit or force-add anything under `private/`.  If `git status` ever
shows a file under `private/`, investigate and unstage or untrack it
immediately.

---

## 7. What to do when something leaks

If `make public-safety` fails:

1. Read the error message — it names the file and the problem.
2. If a `private/` file is **tracked**, remove it from Git:

   ```bash
   git rm --cached <file>
   ```

3. If a `private/` file is **staged**, unstage it:

   ```bash
   git restore --staged <file>
   ```

4. If a public file references `private/`, edit the file to remove the leak.
5. Re-run `make public-safety` to confirm the fix.

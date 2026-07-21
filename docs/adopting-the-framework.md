# Adopting the Framework

Course Notes is experimental and pre-1.0. Evaluate it with the fictional demo before placing
important private work beside it.

## Evaluate

```bash
git clone https://github.com/xichia/course-notes.git
cd course-notes
make check
```

The clone contains only tracked public framework files and fictional public notes. Ignored
private files from another working copy are never included.

## Choose an ownership model

For personal use, fork the repository, create your own repository from a copy, or keep a local
clone. The public repository does not itself prove that GitHub's “template repository” setting
is enabled, so do not depend on that feature without checking the live setting separately.

If you want framework updates, retain the original repository as an `upstream` remote and use
your own repository as `origin`. Review upstream diffs before merging: pre-1.0 changes are not
assumed to be backward-compatible with local templates, conventions, or automation.

## Understand the two storage boundaries

The outer Git repository records the public framework and tracked `courses/` content. Its
ignored `private/` directory may share the workspace, but it does **not** share the outer
repository's commits, remote, history, or clone behavior.

The simplest safe approach is an independent encrypted backup of private work. Test restoration,
not only backup creation.

Advanced users may initialize a separate nested Git repository inside `private/`. That creates
an independent history; it does not become part of the outer repository. Do not attach a public
or otherwise unsuitable remote, and verify ignore/tracking boundaries before every first push.

## Start and maintain a course

Follow the manual sequence in [Course onboarding](course-onboarding.md). Keep administrative facts
unknown until verified, retain conservative provenance classifications, and run the private-note
validation commands after changes.

When pulling framework updates:

1. inspect the upstream changes and release notes, if any;
2. run `make check` before merging;
3. resolve changes to templates or conventions deliberately;
4. run `make public-safety` and `make verify-generated` afterward;
5. confirm the private backup remains restorable.

## Report problems safely

Use fictional or synthetic fixtures. Do not attach restricted course content, assessment
material, source packs, LMS exports, credentials, session data, personal results, grades, or
study evidence. Describe the public command, expected behavior, actual behavior, and a sanitized
diagnostic instead.

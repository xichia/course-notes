# Public Release Checklist

Use this checklist before promoting any private material into `courses/` (the tracked tree the GitHub remote publishes). The Git-ignored `private/` directory is working storage, not a release; an automated pass on `courses/` is not permission to publish everything still living under `private/`.

## Remove Private Course Material

- [ ] Remove or replace real courses with clearly synthetic/demo courses.
- [ ] Remove lecture-derived notes, slides, screenshots, recordings, transcripts, and close paraphrases.
- [ ] Remove problem-sheet questions, solutions, attempts containing protected text, and derived examples.
- [ ] Remove exam questions, assessment material, and course-derived exam maps.
- [ ] Remove lecturer-specific hints, examples, anecdotes, and teaching sequences.
- [ ] Remove LMS material, restricted links, announcements, and copied handbook text.
- [ ] Remove personal study evidence that should remain private.
- [ ] Remove every file marked `visibility: private`.

## Verify What Remains

- [ ] Use synthetic examples or independently written generic explanations.
- [ ] Confirm every `public-open-licensed` item has an explicit licence and required attribution.
- [ ] Confirm every public note has an allowed `visibility` and `source-risk` classification.
- [ ] Confirm no copyrighted or access-restricted course material remains.
- [ ] Confirm AI-generated paraphrases do not preserve protected course expression.
- [ ] Search for absolute local paths, home-directory paths, drive-letter paths, and file URIs.
- [ ] Search for sensitive terms, credentials, private links, student identifiers, and personal data.
- [ ] (Optional) Create a `.public-release-blocklist` file with private terms (university names, course codes, lecturer names, LMS hostnames) before running checks.

## Run Checks

```bash
make pre-release
```

Or step by step:

```bash
make validate-public
make manifest
make review
make test
```

- [ ] Public-release validation passes with no private, course-derived, unknown-risk, unclassified notes, or suspicious source references.
- [ ] Generated files were rebuilt from the sanitized Markdown sources.
- [ ] Relative Markdown links resolve in the release candidate.
- [ ] Running `make pre-release` twice produces no diff.

## Manual Approval

- [ ] Review the complete Git diff and staged file list manually.
- [ ] Open representative rendered Markdown files on GitHub or a previewer.
- [ ] Confirm the repository communicates that its value is the study system, not course-material publication.
- [ ] Push only after this manual review is complete.

Passing this checklist is a release decision, not legal clearance. See [publication policy](publication-policy.md).

# Project State: Course Notes

Course Notes is experimental and pre-1.0. Interfaces and conventions may change while adopter
feedback and pilot workflows are incorporated.

## Implementation matrix

| Capability | Status | Operational evidence or boundary |
|---|---|---|
| Lightweight public notes | Implemented | `courses/`, `TEMPLATE.md`, and normal/public validation |
| Lightweight private notes | Implemented | Ignored private workspace and `study-*` targets |
| Manifest generation | Implemented | `build_manifest.py`; shared deterministic generation date |
| Review queue | Implemented | `build_review_queue.py`; shared date behavior with explicit overrides |
| Public-safety gate | Implemented | Git-boundary, leak-pattern, public-release, and test checks |
| Local hooks | Implemented, optional | Ownership-aware pre-commit and pre-push scripts; not auto-installed |
| CI | Implemented | Safety and deterministic-generation checks on Python 3.9 and current 3.x |
| Course scaffolding | Manual; automated initializer not bundled | Manual onboarding is supported; no initializer ships in this release |
| Study-module contract and prompts | Experimental | Pilot specifications; not a turnkey workflow |
| Generic study-module validator | Not bundled; deferred | Do not claim mechanical validation without a configured validator |
| Formal versioned study-module schema | Deferred | Current prose contract remains experimental |
| Synthetic end-to-end study-module example | Deferred | No complete public demonstration currently ships |
| LMS/source import | Not bundled | Project-specific importing is outside the reusable public framework |
| Private-work backup | User-managed | The outer repository ignores private work and provides no backup |

## Operational safeguards

`make public-safety` is the canonical publication-safety gate. It checks the Git boundary,
scans applicable public text for configured leak patterns, runs public-release validation, and
runs the test suite. Optional hooks invoke the same gate; CI ratifies pushed commits and also
checks deterministic generated files.

These checks reduce accidental disclosure but do not establish copyright clearance,
confidentiality clearance, institutional permission, or legal authority to publish. Local hooks
are optional and bypassable. Human review remains necessary.

`.public-release-blocklist` is an optional ignored extension to the local safety scan. It must
not be committed.

## Deferred work

The next advanced-study milestones are a generic validator, a formal versioned schema, and a
fully synthetic end-to-end module example. They are deliberately deferred from the adopter-
readiness pass; the existing contract and prompts must first be piloted with independent
subject-matter review.

GitHub repository-setting changes, releases, tags, and remote configuration are also outside
the repository implementation represented here.

Automated course initialization remains deferred pending a simpler design with clearly bounded
filesystem guarantees.

## Persistent risks

- Passing automation does not prove material is lawful or appropriate to publish.
- Pre-1.0 framework changes may require manual review when pulled into an adopter's copy.
- Ignored private material is absent from the public repository's history and clones and needs
  independent encrypted backup.

Historical implementation snapshots remain under `handoffs/`; they are evidence of past state,
not current operating instructions.

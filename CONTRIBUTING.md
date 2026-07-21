# Contributing

Contributions should improve the reusable public framework: code, tests, fictional examples,
templates, prompts, or documentation.

Never submit private or restricted course material, assessment content, LMS exports, credentials,
personal study evidence, or identifying information. When reporting a problem, reduce it to a
fictional fixture and include only the minimum public-safe diagnostic needed to reproduce it.

Before requesting review, run:

```bash
make check
make public-safety
make verify-generated
git diff --check
```

Rebuild `manifest.json` and `REVIEW_QUEUE.md` through the supported generation targets; do not
edit them by hand. Fix genuine validation defects in the content or implementation. Never
weaken, bypass, or remove a check merely to obtain a pass.

Review the complete diff and keep changes bounded. Automated checks reduce mistakes but do not
establish publication rights, copyright clearance, institutional permission, or subject-matter
correctness.

See the [publication policy](docs/publication-policy.md), [operating checklist](docs/operating-checklist.md),
and [project state](PROJECT_STATE.md) for the current boundaries.

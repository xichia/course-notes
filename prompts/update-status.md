# Update Status

## Prompt

Evaluate whether **[note ID or path]** should keep, upgrade, or downgrade its current `status` after **[quiz/problem sheet/timed recall]**.

Read `manifest.json`, the source note, its structured Mistake Log, and only the evidence I provide or that is recorded in repository practice material. Do not infer attempts or success that are not documented.

First produce a compact evidence table with date, evidence source, task type, observed result, and recurring pattern. Then make a separate recommendation:

- **keep** when evidence is too thin or mixed;
- **upgrade** only after at least two successful attempts separated by time or using different task types, with application evidence for `solid` or `mastered`;
- **downgrade** when repeated mistakes, failed transfer, or repeated inability to recall the core idea demonstrates a genuine gap;
- **re-test** when there is only one unusually good or bad answer.

State the proposed status, confidence, supporting evidence, counter-evidence, and the next test that would change the decision. A polished note or one good answer is not mastery.

Do not edit metadata while evaluating. Ask me before changing `status` unless I explicitly instructed you to apply the decision. If approved, update only the justified fields, preserve the note ID, and run `make all`.

Preserve `visibility` and `source-risk` exactly. A successful quiz or status upgrade is not evidence that course-derived content is safe to publish; never change publication metadata without separate explicit instruction and provenance evidence.

# Course Import Friction Test

Run `make all`, then try this checklist with the newly imported course. The goal is to expose workflow friction early, not to make every checkbox green through invented metadata.

## Ten-Minute Test

- [ ] **Weak-topic lookup:** Can I find the most important weak topic in `REVIEW_QUEUE.md` in under one minute and explain why it is ranked there?
- [ ] **Manifest-first retrieval:** Can an LLM answer a course question by reading `manifest.json` first, opening only relevant source notes, and naming the files it used?
- [ ] **Today's work:** Can I tell what to study today without manually scanning every note?
- [ ] **Source trace:** Can I trace a concept's `source` back to a lecture, slide, reading, or problem sheet?
- [ ] **Syllabus trace:** Can I distinguish confirmed learning outcomes and exam coverage from unclear or unconfirmed material?
- [ ] **Mistake capture:** Can I add one evidenced five-field Mistake Log entry in under two minutes and pass `make validate`?
- [ ] **Practice gap:** Can I see which concepts lack worked examples or practice questions from the manifest or weekly-review prompt?
- [ ] **Evidence-based status:** Can I use `prompts/update-status.md` to propose a status change without making it automatically?
- [ ] **Lecture import:** Can `prompts/import-lecture.md` propose existing-note updates and new concept candidates while leaving the raw lecture unchanged?
- [ ] **Portable links:** Do course files use repository-relative paths, with no machine-specific links?
- [ ] **Publication boundary:** Are real course files still `visibility: private`, with conservative `source-risk` values and no assumption that AI paraphrasing makes them public?

## If Something Fails

Record the smallest source-of-friction fix below. Prefer clearer filenames, source fields, course navigation, or prompt wording before adding new scripts.

| Friction | Smallest useful fix | Done |
|---|---|---|

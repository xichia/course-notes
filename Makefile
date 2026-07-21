PYTHON ?= python3

.PHONY: help check refresh verify-generated validate validate-public manifest review test all pre-release reviewed \
        study-validate study-manifest study-review study-all study-reviewed public-safety \
        install-hooks uninstall-hooks

help:
	@echo "Course Notes targets:"
	@echo "  check             Validate public notes and run tests (non-mutating)"
	@echo "  refresh           Validate and rebuild manifest.json and REVIEW_QUEUE.md"
	@echo "  verify-generated  Rebuild public views from the HEAD timestamp and check for drift"
	@echo "  all               Refresh public views and run tests"
	@echo "  public-safety     Run publication-safety checks and tests"
	@echo "  study-all         Validate and refresh schema-based private notes"
	@echo "  install-hooks     Install the optional managed Git hooks"
	@echo "  uninstall-hooks   Remove only hooks managed by this project"

check:
	$(PYTHON) validate_notes.py
	$(PYTHON) -m unittest discover -s tests -v

refresh:
	$(PYTHON) validate_notes.py
	$(PYTHON) build_manifest.py
	$(PYTHON) build_review_queue.py

verify-generated:
	@SOURCE_DATE_EPOCH="$$(git log -1 --format=%ct HEAD)" $(PYTHON) build_manifest.py
	@SOURCE_DATE_EPOCH="$$(git log -1 --format=%ct HEAD)" $(PYTHON) build_review_queue.py
	@git diff --exit-code -- manifest.json REVIEW_QUEUE.md

validate:
	$(PYTHON) validate_notes.py

validate-public:
	$(PYTHON) validate_notes.py --public-release

manifest:
	$(PYTHON) build_manifest.py

review:
	$(PYTHON) build_review_queue.py

test:
	$(PYTHON) -m unittest discover -s tests -v

pre-release:
	$(MAKE) public-safety
	$(PYTHON) build_manifest.py
	$(PYTHON) build_review_queue.py

reviewed:
	$(PYTHON) mark_reviewed.py $(NOTE) $(DATE:%=--date %)

all:
	$(MAKE) refresh
	$(PYTHON) -m unittest discover -s tests -v

study-validate:
	$(PYTHON) validate_notes.py --study

study-manifest:
	$(PYTHON) build_manifest.py --study

study-review:
	$(PYTHON) build_review_queue.py --study

study-all:
	$(PYTHON) validate_notes.py --study
	$(PYTHON) build_manifest.py --study
	$(PYTHON) build_review_queue.py --study

study-reviewed:
	$(PYTHON) mark_reviewed.py --study $(NOTE) $(DATE:%=--date %)

public-safety:
	$(PYTHON) check_public_safety.py

HOOK_PRE_COMMIT_SRC = scripts/pre-commit
HOOK_PRE_COMMIT_DST = .git/hooks/pre-commit
HOOK_PRE_PUSH_SRC = scripts/pre-push
HOOK_PRE_PUSH_DST = .git/hooks/pre-push

install-hooks:
	@mkdir -p .git/hooks
	@if [ -f "$(HOOK_PRE_COMMIT_DST)" ] && ! cmp -s "$(HOOK_PRE_COMMIT_SRC)" "$(HOOK_PRE_COMMIT_DST)"; then \
		echo "ERROR: $(HOOK_PRE_COMMIT_DST) already exists and differs from $(HOOK_PRE_COMMIT_SRC)."; \
		echo "  Remove or back up the existing hook manually, then re-run."; \
		exit 1; \
	fi
	@if [ -f "$(HOOK_PRE_PUSH_DST)" ] && ! cmp -s "$(HOOK_PRE_PUSH_SRC)" "$(HOOK_PRE_PUSH_DST)"; then \
		echo "ERROR: $(HOOK_PRE_PUSH_DST) already exists and differs from $(HOOK_PRE_PUSH_SRC)."; \
		echo "  Remove or back up the existing hook manually, then re-run."; \
		exit 1; \
	fi
	@cp "$(HOOK_PRE_COMMIT_SRC)" "$(HOOK_PRE_COMMIT_DST)"
	@chmod +x "$(HOOK_PRE_COMMIT_DST)"
	@echo "Installed $(HOOK_PRE_COMMIT_DST)"
	@cp "$(HOOK_PRE_PUSH_SRC)" "$(HOOK_PRE_PUSH_DST)"
	@chmod +x "$(HOOK_PRE_PUSH_DST)"
	@echo "Installed $(HOOK_PRE_PUSH_DST)"

uninstall-hooks:
	@if [ -f "$(HOOK_PRE_COMMIT_DST)" ] && cmp -s "$(HOOK_PRE_COMMIT_SRC)" "$(HOOK_PRE_COMMIT_DST)"; then \
		rm "$(HOOK_PRE_COMMIT_DST)"; \
		echo "Removed $(HOOK_PRE_COMMIT_DST)"; \
	elif [ -f "$(HOOK_PRE_COMMIT_DST)" ]; then \
		echo "WARNING: $(HOOK_PRE_COMMIT_DST) is not managed by this project — leaving it in place."; \
	else \
		echo "No $(HOOK_PRE_COMMIT_DST) found — nothing to remove."; \
	fi
	@if [ -f "$(HOOK_PRE_PUSH_DST)" ] && cmp -s "$(HOOK_PRE_PUSH_SRC)" "$(HOOK_PRE_PUSH_DST)"; then \
		rm "$(HOOK_PRE_PUSH_DST)"; \
		echo "Removed $(HOOK_PRE_PUSH_DST)"; \
	elif [ -f "$(HOOK_PRE_PUSH_DST)" ]; then \
		echo "WARNING: $(HOOK_PRE_PUSH_DST) is not managed by this project — leaving it in place."; \
	else \
		echo "No $(HOOK_PRE_PUSH_DST) found — nothing to remove."; \
	fi

PYTHON ?= python3

.PHONY: validate validate-public manifest review test all pre-release reviewed \
        study-validate study-manifest study-review study-all study-reviewed public-safety

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
	$(PYTHON) validate_notes.py --public-release
	$(PYTHON) build_manifest.py
	$(PYTHON) build_review_queue.py
	$(PYTHON) -m unittest discover -s tests -v

reviewed:
	$(PYTHON) mark_reviewed.py $(NOTE) $(DATE:%=--date %)

all:
	$(PYTHON) validate_notes.py
	$(PYTHON) build_manifest.py
	$(PYTHON) build_review_queue.py
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

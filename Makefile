PYTHON ?= python3

.PHONY: validate validate-public manifest review test all pre-release

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

all:
	$(PYTHON) validate_notes.py
	$(PYTHON) build_manifest.py
	$(PYTHON) build_review_queue.py
	$(PYTHON) -m unittest discover -s tests -v

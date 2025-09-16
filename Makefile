PACKAGE=aws_cleaner
PYTHON=$(shell which python 2>/dev/null || which python3 2>/dev/null)

.PHONY: all install develop clean test

all:
	@echo "Makefile commands:"
	@echo "  make install   - Install the package"
	@echo "  make develop   - Install in editable/development mode"
	@echo "  make clean     - Remove build, cache, and artifacts"
	@echo "  make test      - Run unit tests with pytest"
	@echo "  make reformat  - Reformat the sources with black/isort

install:
	@pip install .

develop:
	@pip install -e ".[dev]"

clean:
	@rm -rf build dist *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +

check:
	@pytest -vvv
	$(PYTHON) -m black --check -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m isort --check-only -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m pytest

reformat:
	$(PYTHON) -m black -- $(shell git ls-files -- "*.py")
	$(PYTHON) -m isort -- $(shell git ls-files -- "*.py")

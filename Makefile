help:
	@echo "Tasks in \033[1;32mpsql_vcs\033[0m:"
	@cat Makefile

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
ACTIVATE = . $(VENV)/bin/activate

venv:
	python3.13 -m venv $(VENV)

prepare: venv
	$(PIP) install pytest bandit

dev:
	$(PIP) install -e .

test: dev
	$(ACTIVATE); pytest --doctest-modules --junitxml=junit/test-results.xml
	$(ACTIVATE); bandit -r src -f xml -o junit/security.xml || true

build: clean
	$(PIP) install wheel
	$(PYTHON) setup.py bdist_wheel

clean:
	@rm -rf .pytest_cache/ .mypy_cache/ junit/ build/ dist/
	@find . \( -path './.venv' -o -path $(VENV) \) -prune -o -type d -name '__pycache__' -delete
	@find . \( -path './.venv' -o -path $(VENV) \) -prune -o -type d -name '*/*.egg-info*' -delete

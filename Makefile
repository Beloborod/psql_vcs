help:
	@echo "Tasks in \033[1;32mpsql_vcs\033[0m:"
	@cat Makefile

prepare:
	pip install mypy flake8 pytest bandit pydocstyle isort black

lint:
	mypy src --ignore-missing-imports
	flake8 src --ignore=$(shell cat .flakeignore)

format:
	black src/ tests/
	isort src/ tests/

dev:
	pip install -e .

test: dev
	pytest --doctest-modules --junitxml=junit/test-results.xml
	bandit -r src -f xml -o junit/security.xml || true

build: clean
	pip install wheel
	python setup.py bdist_wheel

clean:
	@rm -rf .pytest_cache/ .mypy_cache/ junit/ build/ dist/
	@find . -not -path './.venv*' -path '*/__pycache__*' -delete
	@find . -not -path './.venv*' -path '*/*.egg-info*' -delete

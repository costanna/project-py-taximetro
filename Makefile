.PHONY: install precommit-install test lint format run-cli run-api docker-up

install:
	pip install -r requirements-dev.txt

precommit-install: install
	pre-commit install

test:
	pytest

lint:
	black --check .
	isort --check-only .
	flake8 .

format:
	black .
	isort .

run-cli:
	python taximeter.py

run-api:
	python run_api.py

docker-up:
	docker compose up --build

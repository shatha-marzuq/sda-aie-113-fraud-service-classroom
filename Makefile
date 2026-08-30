.PHONY: install run-batch lint

install:
	pip install -e .

run-batch:
	python -m fraud_service.batch

lint:
	ruff check src tests
.PHONY: install test run eval lint docker
install:
	pip install -e ".[dev]"

test:
	pytest -q

run:
	uvicorn pet_report.main:app --host 0.0.0.0 --port 8000 --reload

eval:
	python -m pet_report.cli eval

docker:
	docker compose up --build

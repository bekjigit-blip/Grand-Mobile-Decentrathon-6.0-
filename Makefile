.PHONY: build_index predict test run_server dev

PYTHON ?= python3
IN ?= data/sample_tickets.jsonl
OUT ?= pred.jsonl

build_index:
	$(PYTHON) -m app.build_index

predict:
	$(PYTHON) -m app.predict --input $(IN) --output $(OUT)

test:
	$(PYTHON) -m pytest -v tests/

run_server:
	$(PYTHON) -m app.server

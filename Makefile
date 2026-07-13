PYTHON ?= python3

.PHONY: dev doctor test smoke visual inspect render

dev:
	$(PYTHON) app.py

doctor:
	$(PYTHON) scripts/doctor.py

test:
	$(PYTHON) tests/run_tests.py

smoke:
	$(PYTHON) scripts/smoke_test.py

visual:
	$(PYTHON) scripts/check_visual_tokens.py

inspect:
	$(PYTHON) scripts/inspect_document.py $(FILE)

render:
	$(PYTHON) scripts/render_document.py $(FILE)

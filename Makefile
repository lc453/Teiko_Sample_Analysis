PYTHON=python

.PHONY: setup pipeline dashboard

setup:
	$(PYTHON) -m pip install -r requirements.txt

pipeline:
	$(PYTHON) load_data.py
	$(PYTHON) text_based_tests.py

dashboard:
	$(PYTHON) main.py
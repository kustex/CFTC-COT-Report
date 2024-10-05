install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

format:
	black *.py

lint:
	pylint --errors-only app_cftc.py cftc_analyser.py 

test:
	python -m pytest -vv --cov=hello app_cftc.py

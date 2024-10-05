install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

format:
	black *.py

test:
	python -m pytest -vv --cov=hello app_cftc.py

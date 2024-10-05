install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

install-aws:
	pip install --upgrade pip &&\
		pip install -r requirements_aws.txt

format:
	black *.py

lint:
	pylint --disable=R,C app_cftc.py

test:
	python -m pytest -vv --cov=hello app_cftc.py
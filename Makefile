.PHONY: all fmt install test clean publish

all:
	python setup.py bdist

fmt:
	git ls-files *.py **/*.py | xargs black

install:
	python setup.py install

test:
	tox

clean:
	rm -rf build/ dist/ httpie_asap_auth.egg-info/

# Publish to PyPi - obtain a token and place it in ~/.pypirc
publish:
	python setup.py sdist
	twine upload dist/*

.PHONY: all fmt install test clean publish

all:
	python setup.py bdist

fmt:
	git ls-files **/*.py | xargs black

install:
	python setup.py install

test:
	tox

clean:
	rm -rf build/ dist/ httpie_asap_auth.egg-info/

publish:
	python setup.py sdist
	twine upload dist/*

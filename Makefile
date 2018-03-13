.PHONY: all install test clean publish

all:
	python setup.py bdist

install:
	python setup.py install

test:
	tox

clean:
	rm -rf build/ dist/ httpie_asap_auth.egg-info/

publish: clean
	python setup.py sdist
	twine upload dist/*

.PHONY: all install test clean

all:
	python setup.py bdist

install:
	python setup.py install

test:
	tox

clean:
	rm -rf build/ dist/ httpie_asap_auth.egg-info/

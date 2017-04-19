# Makefile

all:
	python setup.py bdist

install:
	python setup.py install

test:
	tox

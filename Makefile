# Makefile
.PHONY: all install clean

all:
	python setup.py bdist

install:
	python setup.py install

test:
	tox

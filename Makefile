.PHONY: all sync install lock upgrade test fmt build clean publish

all: build

sync install:
	uv sync --locked --group test

lock:
	uv lock --check

upgrade:
	uv lock --upgrade

fmt:
	uv run --locked --python 3.14 --group format black .

test:
	uv run --locked --group test pytest -v -s --doctest-modules --cov httpie_asap_auth --cov-report html:build/coverage --cov-report term httpie_asap_auth.py tests/

build:
	uv build

clean:
	rm -rf build/ dist/ httpie_asap_auth.egg-info/

# Publish to PyPI with UV_PUBLISH_TOKEN or credentials configured for uv.
publish: build
	uv publish dist/*

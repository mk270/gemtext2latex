# Makefile for maintainer tasks

PACKAGE=$(shell toml get --toml-path pyproject.toml "tool.setuptools.packages[0]")

build:
	python -m build

dist:
	git diff --exit-code && \
	rm -rf ./dist && \
	mkdir dist && \
	$(MAKE) build

release:
	$(MAKE) dist && \
	twine upload dist/* && \
	git tag v$$(grep version pyproject.toml | grep -o "[0-9.]\+") && \
	git push --tags

loc:
	cloc $(PACKAGE)

.PHONY: dist build

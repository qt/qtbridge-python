# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only
# Minimal GNU Makefile for Sphinx

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
EXAMPLESDIR   = ../examples

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile copy-examples clean-examples

copy-examples:
	@echo "Copying example READMEs..."
	@mkdir -p examples
	@for d in $(EXAMPLESDIR)/*; do \
		if [ -d "$$d" ] && [ -f "$$d/README.md" ]; then \
			name=$$(basename "$$d"); \
			mkdir -p examples/"$$name"; \
			cp -f "$$d/README.md" examples/"$$name"/ 2>/dev/null || true; \
		fi; \
	done

clean-examples:
	@echo "Cleaning copied example READMEs..."
	@rm -rf examples/*

# Override default targets to copy examples first
html: copy-examples
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean: clean-examples
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

%: Makefile copy-examples
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

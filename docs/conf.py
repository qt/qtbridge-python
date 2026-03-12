# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only

import sys
import os
import types
from unittest.mock import MagicMock

# needed for autodoc stuff
# Mock Qt/shiboken dependencies that are not installed in the docs build env
_MOCKED_MODULES = [
    "shiboken6",
    "shiboken6.Shiboken",
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtQml",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtQuick",
]
for _mod in _MOCKED_MODULES:
    sys.modules[_mod] = MagicMock()

# Make src/ importable as a fallback for any submodule autodoc traversal
sys.path.insert(0, os.path.abspath("../src"))

# Load __init__.pyi as the authoritative QtBridge documentation module.
_pyi_path = os.path.abspath("../src/QtBridge/__init__.pyi")
_docs_mod = types.ModuleType("QtBridge")
_docs_mod.__file__ = _pyi_path
_docs_mod.__package__ = "QtBridge"
_docs_mod.__path__ = []
# if this is updated, update QtBridge.__init__.py's __all__ as well
_docs_mod.__all__ = [
    "Signal", "DataProvider", "bridge_instance", "bridge_type",
    "insert", "remove", "move", "edit", "reset", "complete",
    "qtbridge", "load_qml_component", "QmlObject", "QmlComponentFactory",
    "watch", "effect", "Change",
]
with open(_pyi_path) as _f:
    exec(compile(_f.read(), _pyi_path, "exec"), _docs_mod.__dict__)
sys.modules["QtBridge"] = _docs_mod

# Project information
project = "Qt Bridge - Python"
# copied form PySide. Might need change
copyright = u'2026 The Qt Company Ltd. Documentation contributions included herein are the copyrights of their respective owners. The documentation provided herein is licensed under the terms of the GNU Free Documentation License version 1.3 (https://www.gnu.org/licenses/fdl.html) as published by the Free Software Foundation. Qt and respective logos are trademarks of The Qt Company Ltd. in Finland and/or other countries worldwide. All other trademarks are property of their respective owners.'
author = "QtBridge Python Team"
release = "0.2.0-beta"

# General configuration
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
    "deflist",
    "tasklist",
    "attrs_inline",
]

# Allow direct markdown includes across the repo (e.g. example READMEs)
myst_all_links_external = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#41cd52",   # Qt green
        "color-brand-content": "#41cd52",
    },
    "dark_css_variables": {
        "color-brand-primary": "#41cd52",
        "color-brand-content": "#41cd52",
    },
}

html_title = "Qt Bridge — Python"

# Autodoc options
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
always_document_param_types = True

# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
# Napoleon (Google/NumPy docstrings)
napoleon_google_docstring = False
napoleon_numpy_docstring = True

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pyside": ("https://doc.qt.io/qtforpython-6/", None),
}

# copy-button
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# MyST
source_suffix = {
    ".md": "myst",
}

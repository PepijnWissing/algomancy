# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Algomancy"
copyright = "2026, Pepijn Wissing"
author = "Pepijn Wissing"
release = "0.3.16"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",  # optional but useful
]

myst_heading_anchors = 3

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

templates_path = ["_templates"]
exclude_patterns = []

napoleon_google_docstring = True
napoleon_numpy_docstring = False

napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

autodoc_class_signature = "mixed"
autodoc_typehints = "description"
autodoc_member_order = "bysource"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_favicon = "_static/icon.png"

html_theme = "furo"

html_theme_options = {
    "announcement": "You are looking at a beta version of the docs - work is in progress!",
    "sidebar_hide_name": True,
    "light_logo": "algomancy_logo_light.png",
    "dark_logo": "algomancy_logo_dark.png",
}

html_static_path = ["_static"]

# html_logo = "_static/algomancy_logo_light.png"

# html_css_files = [
#     "custom.css",
# ]

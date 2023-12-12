# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PROJECT NAME HERE'
copyright = '2023, Aquaveo'
author = 'aquaveo'

version = '99.99.99'
release = ''
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
import numpy
import PySide2
import xarray
import sys
import os
import shutil

sys.path.insert(0, os.path.abspath('../../'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

# html_theme_options = {
#     'display_version': True,
#     'prev_next_buttons_location': 'bottom',
#     'style_nav_header_background': 'white',
#     # Toc options
#     'collapse_navigation': True,
#     'sticky_navigation': True,
#     'navigation_depth': 4,
#     'includehidden': True,
#     'titles_only': False
# }

html_static_path = ['_static']

autodoc_mock_imports = [
    'xms.constraint', 'xms.adh.data.sediment_materials_io', 'Matplotlib', 'shiboken2', 'xms.api', 'xms.guipy',
    'xms.core', 'xms.components', 'xms.data_objects', 'xms.grid', 'xms.adcirc'
]
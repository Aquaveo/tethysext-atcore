# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

# Add source code directory to path
docs_dir = os.path.abspath(os.path.dirname(__file__))
package_dir = os.path.dirname(docs_dir)
# sys.path.insert(0, os.path.join(package_dir))
print(f'PYTHON PATH: {sys.path}')

project = 'atcore'
copyright = '2023, Aquaveo'
author = 'Aquaveo'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
]

# Autodoc config
autodoc_typehints = 'both'
autodoc_mock_imports = [
    'bokeh',
    'django',
    'django_select2',
    'datetimewidget',
    'panel',
    'plotly',
    'taggit',
    'tethys_dataset_services',
    'tethys_gizmos',
    'tethys_apps',
    'tethys_compute',
    'tethys_portal',
    'tethys_sdk',
    'tethysext.atcore.tests',
]
autosummary_generate = True

# Template config
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

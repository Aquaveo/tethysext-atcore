# Documentation for ATCore

This directory contains the Sphinx documentation project for ATCore. Use these instructions to create a Conda environment and build the documentation.

## Create Conda Environment

Create a conda environment with the dependencies installed using the `docs_environment.yml`:

```
cd docs
conda env create -f docs_environment.yml
```

## Install ATCore into Docs Environment

Install ATCore into the docs environment by running the following command from the **root directory** of the repository:

```
pip install -e .
```

## Build Docs

Activate the conda environment and build the documentation using these commands:

```
conda activate atcore-docs
cd docs
make html
```

## Autobuild

Alternatively, use autobuild to build the docs, host them with a dev server, and automatically rebuild when changes are made:

```
cd docs
sphinx-autobuild --host 127.0.0.1 --port 8001 ./source ./build/html
```
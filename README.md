# Status

| Job                       | Status                                                                                                                                                                                             | Coverage           |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Build Status              | [![Build Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=build)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                            | [![Total Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=coverage)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |
| Lint Status               | [![Lint Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=lint)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                              |                    |
| Unit Tests                | [![Unit Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                   | [![Unit Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |
| Integration Tests         | [![Integration Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)     | [![Integration Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) | 

# Installs

### OS Dependencies

```bash
$ sudo apt update
$ sudo apt install gcc libgdal-dev g++ libhdf5-dev
```
### Activate tethys environment

```bash
conda activate tethys
```
### Install for Development:

Run the following command from the same directory as the setup.py

```bash
$ tethys install -d
```

### Install for Production:

Run the following command from the same directory as the setup.py

```bash
$ tethys install
```

### settings.py

Add the following to `INSTALLED_APPS` in your `settings.py` (tethys/tethys_portal/settings.py):

```python
'datetimewidget',
'django_select2',
'taggit',
```

# Testing

This extension has two types of tests: unit tests and integrated tests.

## Setup

Some of the tests require a test database. The database must be a PostgreSQL 9.6 or higher with the postgis extension intalled. Create an empty database before hand. The default database connection string is:

```bash
'postgresql://tethys_super:pass@172.17.0.1:5435/atcore_tests'
```

To specify a custom database connection string, define the `ATCORE_TEST_DATABASE` environment variable:

```bash
export ATCORE_TEST_DATABASE="postgresql://<username>:<password>@<ipaddress>:<port>/<dbname>"
```

## Running the Tests

To run unit tests:

```bash
$ coverage run --rcfile=coverage.ini -m unittest -v tethysext.atcore.tests.unit_tests 
$ coverage report
```

To run integrated tests, install extension in existing installation of Tethys and run:

```bash
$ t
$ coverage run --rcfile=coverage.ini <TETHYS_HOME>/src/manage.py test tethysext.atcore.tests.integrated_tests
$ coverage report
```

## Linting

We are using flake8 to enforce the pep 8 standard. Any change to the rules can be made in the tox.ini file.

```bash
$ flake8 [dir]
```

## Run All Tests

To run all of the test and linting with cumulative coverage:

```bash
. test.sh </path/to/tethys/manage.py>
```

## Minify Scripts

The minified scripts were minified using the harmony branch of uglify-js. For example:

```bash
sudo apt install npm
sudo npm install -g mishoo/UglifyJS2#harmony
uglifyjs --compress --mangle -- input.js > input.min.js
```
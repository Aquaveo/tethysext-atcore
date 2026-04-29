# Status

| Job                       | Status                                                                                                                                                                                             | Coverage           |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Build Status              | [![Build Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=build)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                            | [![Total Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=coverage)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |
| Lint Status               | [![Lint Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=lint)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                              |                    |
| Unit Tests                | [![Unit Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                   | [![Unit Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |
| Integration Tests         | [![Integration Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)     | [![Integration Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |

# Installs

### OS Dependencies

On Debian/Ubuntu:

```bash
$ sudo apt update
$ sudo apt install gcc g++ libgdal-dev libhdf5-dev
```

On macOS (Homebrew):

```bash
$ brew install gdal hdf5
```

### Create a Python virtual environment

ATCore is a Tethys Platform extension. The supported way to develop and test it is in a Python venv with `tethys-platform` installed via pip. Python 3.10–3.13 are supported.

```bash
$ python3.12 -m venv .venv
$ source .venv/bin/activate
$ pip install --upgrade pip wheel setuptools
```

### Install Tethys Platform and ATCore dependencies

Install Tethys Platform itself, then the rest of ATCore's runtime/test dependencies (mirroring `install.yml`):

```bash
$ pip install tethys-platform
$ pip install \
    "sqlalchemy>=2" \
    "geoalchemy2>=0.13" \
    "django-select2<8.3.0" \
    django-taggit \
    django-datetime-widget2 \
    condorpy \
    coverage \
    factory_boy \
    filelock \
    flake8 \
    geojson \
    pandas \
    panel \
    param \
    plotly \
    "pyshp>=3.0.0" \
    psycopg2-binary \
    "geoserver-restconfig>=2.0.10" \
    tethys-dataset-services
```

### Install ATCore for development

From the repo root (the directory containing `pyproject.toml`):

```bash
$ pip install -e .
```

# Testing

This extension has two types of tests: unit tests and integrated tests. Integrated tests need a PostgreSQL+PostGIS database; unit tests do not.

## Provision the test database

Easiest path is a local PostGIS Docker container that mirrors CI. The default connection string in `tethysext/atcore/tests/__init__.py` is `postgresql://tethys_super:pass@172.17.0.1:5438/atcore_tests`; on macOS use `127.0.0.1` instead of `172.17.0.1`.

```bash
$ docker run -d \
    --name atcore-postgis \
    -e POSTGRES_USER=tethys_super \
    -e POSTGRES_PASSWORD=pass \
    -e POSTGRES_DB=atcore_tests \
    -p 5438:5432 \
    --platform linux/amd64 \
    postgis/postgis:17-3.5
```

`--platform linux/amd64` is needed on Apple Silicon — the postgis image does not publish a native arm64 manifest.

To point the tests at a different database, define `ATCORE_TEST_DATABASE`:

```bash
$ export ATCORE_TEST_DATABASE="postgresql://<username>:<password>@<host>:<port>/<dbname>"
```

The user given must be a PostgreSQL superuser so the test runner can create/destroy the test database.

## Run the tests

Run each phase individually so failures are easy to attribute:

```bash
# Unit tests (no database needed)
$ coverage run --rcfile=coverage.ini -m unittest -v tethysext.atcore.tests.unit_tests

# Integrated tests (require ATCORE_TEST_DATABASE)
$ TETHYS_MANAGE=$(python -c "import tethys_portal, os; print(os.path.join(os.path.dirname(tethys_portal.__file__), 'manage.py'))")
$ coverage run -a --rcfile=coverage.ini "$TETHYS_MANAGE" test -v 2 tethysext.atcore.tests.integrated_tests

# Coverage report
$ coverage report --rcfile=coverage.ini --skip-covered

# Lint
$ flake8
```

`test.sh` wraps all four phases:

```bash
$ . test.sh "$TETHYS_MANAGE"
```

## Minify Scripts

The minified scripts were minified using the harmony branch of uglify-js. For example:

```bash
sudo apt install npm
sudo npm install -g mishoo/UglifyJS2#harmony
uglifyjs --compress --mangle -- input.js > input.min.js
```
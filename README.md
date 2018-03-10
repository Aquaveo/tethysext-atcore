# Status

| Job                       | Status                                                                                                                                                                                             | Coverage           |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| Build Status              | [![Build Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=build)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                            | [![Total Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=coverage)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |
| Lint Status               | [![Lint Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=lint)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                              |                    |
| Unit Tests                | [![Unit Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                   | [![Unit Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) |
| Integration Tests         | [![Integration Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)     | [![Integration Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master) | 

# Installs

### Development:

```bash
$ python setup.py develop
```

### Production:

```bash
$ python setup.py install
```

# Testing

This extension has two types of tests: unit tests and integrated tests. To run unit tests:

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

# Linting

We are using flake8 to enforce the pep 8 standard. Any change to the rules can be made in the tox.ini file.

```bash
$ flake8 [dir]
```
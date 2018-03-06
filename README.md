# Status

| Job                        | Status                                                                                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Build Status:              | [![Build Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=build)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                              |
| Unit Test Status:          | [![Unit Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                   |
| Unit Test Coverage:        | [![Unit Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=unit_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                 |
| Integration Test Status:   | [![Integration Test Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)     |
| Integration Test Coverage: | [![Integration Test Coverage](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/coverage.svg?job=integration_tests)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)   |
| Lint Status:               | [![Lint Status](https://git.aquaveo.com/tethys/tethysext-atcore/badges/master/pipeline.svg?job=lint)](https://git.aquaveo.com/tethys/tethysext-atcore/commits/master)                              |

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
$ coverage run --source=./tethysext/atcore setup.py test
$ coverage report
```

To run integrated tests, install extension in existing installation of Tethys and run:

```bash
$ t
$ tethys test -c -f tethysext.atcore.tests.integrated_tests
```

# Linting

We are using flake8 to enforce the pep 8 standard. Any change to the rules can be made in the tox.ini file.

```bash
$ flake8 [dir]
```
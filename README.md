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
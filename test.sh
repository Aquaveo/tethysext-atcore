#!/usr/bin/env bash
if [ ! -f "$1" ]; then
    echo "Usage: . test.sh [/path/to/manage.py]";
    return 1;
fi
rm -f .coverage
echo "Running Unit Tests..."
coverage run -a --rcfile=coverage.ini "$1" test -v 1 tethysext.atcore.tests.unit_tests
echo "Running Intermediate Tests..."
coverage run -a --rcfile=coverage.ini "$1" test -v 1 tethysext.atcore.tests.integrated_tests
echo "Combined Coverage Report..."
coverage report -m --rcfile=coverage.ini
echo "Linting..."
flake8
echo "Testing Complete"
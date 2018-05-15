#!/usr/bin/env bash
if [ ! -f "$1" ]; then
    echo "Usage: . test.sh [/path/to/manage.py]";
    return 1;
fi
mkdir -p coverage
rm -f .coverage
echo "Running Unit Tests..."
coverage run -a --rcfile=coverage.ini -m unittest -v tethysext.atcore.tests.unit_tests
echo "Running Intermediate Tests..."
coverage run -a --rcfile=coverage.ini $1 test tethysext.atcore.tests.integrated_tests
echo "Combined Coverage Report..."
coverage report -m
echo "Linting..."
flake8
echo "Testing Complete"
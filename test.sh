#!/usr/bin/env bash
if [ ! -f "$1" ]; then
    echo "Usage: . test.sh [/path/to/manage.py]";
    return 1;
fi
rm -f .coverage
echo "Running Intermediate Tests..."
coverage run -a --rcfile=coverage.ini $1 test -v 2 tethysext.atcore.tests.integrated_tests
echo "Combined Coverage Report..."
coverage report -m --rcfile=coverage.ini
echo "Testing Complete"
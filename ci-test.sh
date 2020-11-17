#!/usr/bin/env bash
if [ ! -f "$1" ]; then
    echo "Usage: . test.sh [/path/to/manage.py]";
    return 1;
fi

# Cleanup Previous Runs
rm -f .coverage

echo "Running Unit Tests..."
coverage run -a --rcfile=ci-coverage.ini -m unittest -v tethysext.atcore.tests.unit_tests
unittest_ret_val=$?

echo "Running Intermediate Tests..."
coverage run -a --rcfile=ci-coverage.ini "$1" test -v 2 tethysext.atcore.tests.integrated_tests
intermediate_ret_val=$?

# Minimum Required Coverage
minimum_required_coverage=80
coverage report -m --skip-covered --fail-under $minimum_required_coverage
coverage_ret_val=$?

#echo "Linting..."
flake8
echo "Testing Complete"

if [ "$unittest_ret_val" -ne "0" ] || [ "$intermediate_ret_val" -ne "0" ] || [ "$coverage_ret_val" -ne "0" ]; then
    if [ "$unittest_ret_val" -ne "0" ]; then
        echo "Unit Tests Failed!!!"
    fi

    if [ "$intermediate_ret_val" -ne "0" ]; then
        echo "Intermediate Tests Failed!!!"
    fi

    if [ "$coverage_ret_val" -ne "0" ]; then
        echo "Below Minimum Coverage of $minimum_required_coverage!!!"
    fi

    return 1
fi

return 0

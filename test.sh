#!/usr/bin/env bash
mkdir -p coverage
rm -f .coverage
coverage run -a --rcfile=coverage.ini -m unittest -v tethysext.atcore.tests.unit_tests
coverage run -a --rcfile=coverage.ini $1 test tethysext.atcore.tests.integrated_tests
coverage report
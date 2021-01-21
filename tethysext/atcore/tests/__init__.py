import os
# NOTE: database user given must be a superuser to successfully execute all tests.
default_connection = 'postgresql://tethys_super:pass@172.17.0.1:5436/atcore_tests'
TEST_DB_URL = os.environ.get('ATCORE_TEST_DATABASE', default_connection)

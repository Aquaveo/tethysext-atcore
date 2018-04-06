import os
default_connection = 'postgresql://tethys_super:pass@172.17.0.1:5435/appusertests'
TEST_DB_URL = os.environ.get('ATCORE_TEST_DATABASE', default_connection)

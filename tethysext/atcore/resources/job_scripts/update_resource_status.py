#!/opt/tethys-python
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tethysext.atcore.models.app_users import Resource


def run(resource_db_url: str, resource_id: str, status_keys: list):
    """
    Update the status of a Resource

    Args:
        resource_db_url (str): The url to the resource in the database.
        resource_id (str): The resource ID.
        status_keys (list): A list of status keys to check.
    """
    resource_db_session = None

    try:
        # Get resource
        resource_db_engine = create_engine(resource_db_url)
        make_resource_db_session = sessionmaker(bind=resource_db_engine)
        resource_db_session = make_resource_db_session()
        resource = resource_db_session.query(Resource).get(resource_id)

        # Check Status List
        if len(status_keys) <= 0:
            raise ValueError('Argument "status" keys must have at least one status.')

        # Get status for upload keys
        status_success = True
        for status_key in status_keys:
            status = resource.get_status(status_key, None)
            status_success = status in Resource.OK_STATUSES and status_success

        # Set root status accordingly
        if status_success:
            resource.set_status(Resource.ROOT_STATUS_KEY, Resource.STATUS_SUCCESS)
        else:
            resource.set_status(Resource.ROOT_STATUS_KEY, Resource.STATUS_FAILED)

        resource_db_session.commit()
    except Exception as e:
        sys.stderr.write('Error processing {0}'.format(resource_id))
        sys.stderr.write(str(e))
        traceback.print_exc(file=sys.stderr)
    finally:
        resource_db_session and resource_db_session.close()


if __name__ == '__main__':
    args = sys.argv
    args.pop(0)
    run(*args)

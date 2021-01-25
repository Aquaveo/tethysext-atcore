#!/opt/tethys-python
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tethysext.atcore.models.app_users import Resource


def run(resource_db_url: str, resource_id: str, resource_class_path: str, status_keys: list):
    """
    Update the root status of a resource based ont he status of one or more other statuses of the same resource.

    Args:
        resource_db_url (str): The SQLAlchemy to the resource database.
        resource_id (str): The resource ID.
        resource_class_path (str): Path to the class module.
        status_keys (list): One or more keys of statuses to check to determine resource status. The other jobs must update these statuses to one of the Resource.OK_STATUSES for the resource to be marked as SUCCESS.
    """  # noqa: E501
    resource_db_session = None
    resource_module_path = resource_class_path.rsplit('.', 1)[0]
    resource_class_name = resource_class_path.rsplit('.', 1)[1]

    resource_module = __import__(resource_module_path, fromlist=[resource_class_name])
    resource_class = getattr(resource_module, resource_class_name)

    try:
        # Get resource
        resource_db_engine = create_engine(resource_db_url)
        make_resource_db_session = sessionmaker(bind=resource_db_engine)
        resource_db_session = make_resource_db_session()
        resource = resource_db_session.query(resource_class).get(resource_id)

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
    run(args[0], args[1], args[2], args[3].split(','))

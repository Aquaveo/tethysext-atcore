from sqlalchemy.orm import sessionmaker
from .base import AppUsersBase
from .app_user import AppUser


def initialize_app_users_db(engine, first_time=False, app_user_model=AppUser):
    """
    Initialize database with app_users tables and initial data.
    Args:
        engine(sqlalchemy.engine): connection to database.
        first_time(bool): is first time initializing.
        app_user_model(atcore.models.app_user.AppUser): subclass of AppUser data model.

    Returns:
    """
    # Create tables
    AppUsersBase.metadata.create_all(engine)

    Session = sessionmaker(engine)
    session = Session()

    staff_user = session.query(app_user_model).\
        filter(app_user_model.username == app_user_model.STAFF_USERNAME).\
        one_or_none()

    if not staff_user:
        new_user = app_user_model(
            username=app_user_model.STAFF_USERNAME,
            role=app_user_model.ROLES.DEVELOPER
        )
        session.add(new_user)
        session.commit()

    session.close()

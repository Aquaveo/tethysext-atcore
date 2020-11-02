from .base import FileDatabaseBase


def initialize_file_database_db(engine):
    """
    Initialize database with files_databases and file_collections tables and initial data.
    Args:
        engine(sqlalchemy.engine): connection to database.

    Returns:
    """
    # Create tables
    FileDatabaseBase.metadata.create_all(engine)

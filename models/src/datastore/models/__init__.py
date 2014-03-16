from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Base = declarative_base()


def _create_engine(database, database_options):
    return create_engine(URL(**database), **database_options)


def session_maker(database, database_options):
    """Initialize a new database connection."""
    engine = _create_engine(database, database_options)
    Base.metadata.bind = engine
    Base.metadata.create_all()
    return scoped_session(sessionmaker(bind=engine))


from datastore.models.blob import Blob
from datastore.models.blob_ref import BlobRef
from datastore.models.blob_trees import BlobLink, TreeLink
from datastore.models.chunked_upload import ChunkedUpload
from datastore.models.commit import Commit
from datastore.models.tree import Tree
from datastore.models.user import Node, User


def create_database(database):  # pragma: no cover
    engine = _create_engine(database, {})
    Base.metadata.create_all(engine)

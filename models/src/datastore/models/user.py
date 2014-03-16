from sqlalchemy import Column, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import UniqueConstraint

from datastore.models import Base


class User(Base):
    __tablename__ = "fd_users"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)

    email = Column(String(256), unique=True)

    salt = Column(LargeBinary)
    password = Column(LargeBinary)

    country = Column(String(2))
    display_name = Column(String(256))

    def __repr__(self):
        return "<User(%r, %r, %r)>" % (self.id, self.email, self.password)


class Node(Base):
    __tablename__ = "fd_nodes"
    __table_args__ = (
        UniqueConstraint('path', 'owner_id', name='_path_owner_id_uc'),
        {'mysql_engine': 'InnoDB'},
    )

    id = Column(Integer, primary_key=True)
    path = Column(String(256))

    # Each node has a unary link with the head of the commits.
    head_id = Column(Integer, ForeignKey('fd_commit.id'))
    head = relationship(
        'Commit',
        uselist=False,
        backref='node'
    )

    # Each user has a collection of nodes which maps to the root commit for
    # each storage node (i.e.: 'main', 'test', ...). This way, each node has
    # its own history and commit log.
    owner_id = Column(Integer, ForeignKey('fd_users.id'))
    owner = relationship(
        User,
        backref=backref(
            'nodes',
            collection_class=attribute_mapped_collection('path')
        )
    )

    def __repr__(self):
        return "<Node(%r, %r, %r, %r)>" % (self.id, self.path, self.head_id,
                                           self.owner_id)

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from datastore.models import Base


class Commit(Base):
    """A commit models a version of a given user drive. Unless it is the very
    first revision, it has a parent Commit which corresponds to its previous
    version.
    """

    __tablename__ = "fd_commit"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    root_id = Column(Integer, ForeignKey('fd_tree.id'))
    parent_id = Column(Integer, ForeignKey('fd_commit.id'))

    # Each commit object holds a link to its root tree, and to an optional
    # parent commit (modeling the revision graph).
    root = relationship('Tree', backref='commit', uselist=False)
    parent = relationship('Commit', uselist=False)

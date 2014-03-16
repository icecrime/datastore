from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from datastore.models import Base


class BlobRef(Base):
    __tablename__ = "fd_blob_ref"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    key = Column(String(64), index=True)
    expires = Column(DateTime)

    root = Column(String(64))
    path = Column(String(1024))

    blob_id = Column(Integer, ForeignKey('fd_blob_trees.id'))
    blob = relationship('BlobLink')

    owner_id = Column(Integer, ForeignKey('fd_users.id'))
    owner = relationship('User', backref='links')

    def __repr__(self):
        return "<BlobRef('%r, %r, %r, %r, %r, %r')>" % \
            (self.id, self.key, self.root, self.blob, self.expires, self.owner)

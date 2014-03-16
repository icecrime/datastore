from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


from datastore.models import Base


class ChunkedUpload(Base):
    __tablename__ = "fd_chunkedupload"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    upload_id = Column(String(40), index=True)

    # A ChunkedUpload belongs to a specific user (we don't want several users
    # to contribute to a given upload).
    owner = relationship('User')
    owner_id = Column(Integer, ForeignKey('fd_users.id'))

    # Store the current received bytes count and the upload expire date.
    offset = Column(Integer)
    expires = Column(DateTime)

    def __repr__(self):
        return "<ChunkedUpload(%r, %r, %r)>" % \
            (self.id, self.owner_id, self.expires)

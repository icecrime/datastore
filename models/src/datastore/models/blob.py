from sqlalchemy import Column, Integer, String

from datastore.models import Base


class Blob(Base):
    __tablename__ = "fd_blob"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    iv = Column(Integer, index=False)
    hash = Column(String(40), index=True)

    def __repr__(self):
        return "<Blob('%r, %r')>" % (self.id, self.hash)

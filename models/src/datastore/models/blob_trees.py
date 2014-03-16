from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from datastore.models import Base
from datastore.models.tree import Tree


class BlobLink(Base):
    __tablename__ = 'fd_blob_trees'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)

    path = Column(String(256))
    is_deleted = Column(Boolean, default=False)

    blob_id = Column(Integer, ForeignKey('fd_blob.id'))
    parent_tree_id = Column(Integer, ForeignKey('fd_tree.id'))
    parent_blob_id = Column(Integer, ForeignKey('fd_blob_trees.id'))

    # Relationships
    blob = relationship('Blob', lazy=False)
    tree = relationship(
        Tree,
        backref=backref(
            'sub_files',
            lazy=False,
            collection_class=attribute_mapped_collection('path')
        )
    )
    parent = relationship('BlobLink', uselist=False, remote_side=[id])

    @property
    def hash(self):
        return self.blob.hash

    @property
    def iv(self):
        return self.blob.iv

    def copy(self):  # pragma: no cover
        # When creating a new tree, we want to copy the previous tree content
        # without copying the whole mapped object relationships.
        return BlobLink(
            path=self.path,
            blob=self.blob,
            blob_id=self.blob_id,
            is_deleted=self.is_deleted,
            parent_blob_id=self.parent_blob_id,
            parent_tree_id=self.parent_tree_id
        )


class TreeLink(Base):
    __tablename__ = 'fd_tree_trees'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)

    path = Column(String(256))
    is_deleted = Column(Boolean, default=False)

    tree_id = Column(Integer, ForeignKey('fd_tree.id'))
    parent_id = Column(Integer, ForeignKey('fd_tree.id'))

    # Relationships. Note that the parent relationship uses a lazy=False on
    # its sub_trees backref in order for the tree retrieval to automatically
    # retrieve all of its children (there is no point in loading a Tree by
    # itself as the object holds no information).
    tree = relationship(
        Tree,
        primaryjoin=Tree.id == tree_id
    )
    parent = relationship(
        Tree,
        backref=backref(
            'sub_trees',
            lazy=False,
            collection_class=attribute_mapped_collection('path')
        ),
        primaryjoin=Tree.id == parent_id
    )

    def copy(self):  # pragma: no cover
        # When creating a new tree, we want to copy the previous tree content
        # without copying the whole mapped object relationships.
        new_link = TreeLink(
            tree=Tree(created=self.tree.created),
            path=self.path,
            tree_id=self.tree_id,
            parent_id=self.parent_id,
            is_deleted=self.is_deleted
        )
        self.tree.copy_to(new_link.tree)
        return new_link

    def debug(self, indent=0):
        self.tree.debug(self.path)  # pragma: no cover

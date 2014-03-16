from datetime import datetime

from sqlalchemy import Column, DateTime, Integer

from datastore.models import Base


class Tree(Base):
    __tablename__ = "fd_tree"
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow())

    def copy_to(self, dest):  # pragma: no cover
        value_copy = lambda d: dict((k, v.copy()) for k, v in d.items())
        dest.sub_files = value_copy(self.sub_files)
        dest.sub_trees = value_copy(self.sub_trees)

    def debug(self, name='', indent=0):  # pragma: no cover
        indent_str = '  ' * indent
        print '%s+ %s/ [0x%x]' % (indent_str, name, id(self))
        for subd in sorted(self.sub_trees.values()):
            if not subd.is_deleted:
                subd.tree.debug(subd.path, indent + 1)
        for subf in sorted(self.sub_files.values()):
            if not subf.is_deleted:
                print '%s  - %s [0x%x]' % (indent_str, subf.path, id(subf))

"""Various database utilities.

"""

from flask import g

from datastore.api import config, tools
from datastore.models import Commit, Node, Tree, TreeLink


class MissingNodeException(Exception):
    """Raised whenever an operation because of a missing node in our database
    representation of the filesystem.
    """
    pass


def _as_tree_link(node, path=''):
    if type(node) is Tree:
        node = TreeLink(path=path, tree=node)
    return node


def _get_default_search_node(root):
    # If the search_node is unspecified, we start from the head of the user
    # which, if non existing, we use a dummy empty node.
    root_node = g.user.dbuser.nodes.get(root)
    return root_node.head.root if root_node and root_node.head else Tree()


def copy_hierarchy(root, path, destination, source=None):
    # If source node is not specifed, use latest logged user's head.
    if not source:
        r_node = g.user.dbuser.nodes.get(root)
        source = r_node.head.root

    # Create current and reference nodes and successively clone as required. We
    # try to preserve as much hierarchy as possible.
    path_elements = tools.split_path(path)
    for directory in path_elements[:-1]:
        # The impacted path is always composed of new tree objects. We don't
        # create nodes which didn't exist previously (requires create_folder).
        if not source or (directory not in source.sub_trees):
            raise MissingNodeException()

        if not config.enable_full_history:
            destination = source.sub_trees[directory].tree
        else:  # pragma: no cover
            # Copy the previous node's content to a newly created one.
            new_node = TreeLink(tree=Tree(), path=directory)
            source.sub_trees[directory].tree.copy_to(new_node.tree)
            destination.sub_trees[directory] = new_node
            destination = new_node.tree

        # Move on to the next nodes.
        source = source.sub_trees[directory].tree

    # Return both the reference node and its new instance.
    return source, destination


def create_commit(root):
    latest = g.db_session.query(Node).with_lockmode('update') \
              .filter(Node.path==root, Node.owner_id==g.user.dbuser.id).first()
    if not latest or not latest.head:  # pragma: no cover
        raise MissingNodeException()

    # Copy the previous node content if it existed.
    if not config.enable_full_history:
        commit = latest.head
    else:  # pragma: no cover
        commit = Commit(root=Tree(), parent=latest.head)
        if latest.head.root:
            latest.head.root.copy_to(commit.root)
    return commit


def get_stored_object(root, path, search_node=None):
    """Retrieve a database stored object.

    Args:
        root: the storage node
        path: the storage path (down the provided root)
        search_node: the starting point for the search (defaults to the user's
            root if not provided)

    Returns:
        The requested node as a BlobLink, or a TreeLink for a directory.

    Raises:
        HTTP 404 if either the starting point for the search or the requested
            node are not found.
    """
    # Retrieve the search node (either as specified, or the user's head).
    search_node = search_node or _get_default_search_node(root)

    # Retrieving the root is a special case as the path is empty. However, the
    # root is a Tree rather than a TreeLink.
    path_elements = tools.split_path(path)
    if not path_elements:
        return _as_tree_link(search_node)

    # Walk the user commit tree to find the requested path. We assume that any
    # part of the path but the last is necessarily a directory.
    for directory in path_elements[:-1]:
        if not directory in search_node.sub_trees:
            raise MissingNodeException()
        search_node = search_node.sub_trees[directory].tree

    # The last path element can either be a directory or a file.
    output = None
    path_end = path_elements[-1].rstrip('/')

    # If the path has a trailing slash, we only allow it to identify a
    # directory. If it doesn't, it may identify either a file (in prioriry) or
    # a directory (if not matching file is found).
    if path.endswith('/'):
        output = search_node.sub_trees.get(path_end)
    else:
        output = (search_node.sub_files.get(path_end) or
                  search_node.sub_trees.get(path_end))

    # If it is neither found as a directory nor a file, raise a MissingNode.
    # Note that we return the BlobLink rather than the Blob itself in order to
    # retrieve the revision (which is an attribute of the link).
    if not output:
        raise MissingNodeException()
    return output


def store_commit(root, commit):
    if root not in g.user.dbuser.nodes:  # pragma: no cover
        raise MissingNodeException()
    g.user.dbuser.nodes[root].head = commit
    g.db_session.commit()

# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.uri import Path
from itools.handlers import Node as TreeNode
from access import AccessControl


class Node(TreeNode):
    """A Node is a base object supporting the HTTP protocol and the access
    control API.
    """

    def _get_object(self, name):
        raise NotImplementedError, 'the method "_get_object" is missing'


    def _get_names(self):
        raise NotImplementedError, 'the method "_get_names" is missing'


    ########################################################################
    # Publishing
    ########################################################################
    def get_object(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            here = self.get_root()
        else:
            here = self

        if len(path) == 0:
            return here

        while path[0] == '..':
            here = here.parent
            path = path[1:]

        for name in path:
            here = here._get_object(name)

        return here


    def get_names(self, path='.'):
        object = self.get_object(path)
        return object._get_names()


    def get_method(self, name):
        try:
            method = getattr(self, name)
        except AttributeError:
            return None
        return method


    def GET(self, context):
        raise NotImplementedError


    def HEAD(self, context):
        """Note that "HEAD" is tweaked by the default Web server to call "GET"
        and return the length of the body, and None as the body.
        """
        pass


    def POST(self, context):
        raise NotImplementedError


    def PUT(self, context):
        raise NotImplementedError


    def LOCK(self, context):
        raise NotImplementedError


    def UNLOCK(self, context):
        raise NotImplementedError


    ########################################################################
    # Security
    ########################################################################
    def get_access_control(self):
        node = self
        while node is not None:
            if isinstance(node, AccessControl):
                return node
            node = node.parent

        return None



class Root(AccessControl, Node):
    """The Root is the main entry point of the Web application. Responsible for
    traversal, user retrieval, and error pages.
    It is a handler of type Foldern so check out the Handler and Folder API.
    """

    def init(self, context):
        """Initialize the root for the new context.
        Useful for resetting attributes, etc."""
        pass


    def get_user(self, username):
        """Return an object representing the user named after the username, or
        None.
        The nature of the object, the location of the storage and the retrieval
        of the data remain at your discretion. The only requirements are the
        "name" attribute, and the "authenticate" method with a "password"
        parameter.
        """
        return None


    ########################################################################
    # Publishing
    ########################################################################
    def before_traverse(self, context):
        """Pre-publishing process.
        Possible actions are language negotiation, etc.
        """
        pass

    
    def after_traverse(self, context, body):
        """Post-publishing process.
        Possible actions are wrapping the body into a template, etc."""
        return body


    ########################################################################
    # Error Pages
    ########################################################################
    def unauthorized(self, context):
        """Called on status 401 for replacing the body by an error page."""
        return '401 Unauthorized'


    def forbidden(self, context):
        """Called on status 403 for replacing the body by an error page."""
        return '403 Forbidden'


    def not_found(self, context):
        """Called on status 404 for replacing the body by an error page."""
        return '404 Not Found'


    def internal_server_error(self, context):
        """Called on status 500 for replacing the body by an error page."""
        return '500 Internal Server Error'

# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2006 Juan David Ib��ez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
This module provides the abstract class which is the root in the
handler class hierarchy.
"""

# Import from the Standard Library
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.resources import base
from itools.handlers.transactions import get_transaction
from base import Node



class Handler(Node):
    """
    This class represents a resource handler, where a resource can be
    a file, a directory or a link. It is used as a base class for any
    other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # All handlers have a resource and a timestamp, plus the state.
    # The variable class "__slots__" is to be overriden.
    __slots__ = ['resource', 'timestamp']


    def __init__(self, resource=None, **kw):
        self.resource = resource
        self.timestamp = None
        # If the resources is None, this is a fresh new handler
        if resource is None:
            self.new(**kw)


    def __getattr__(self, name):
        if name not in self.__slots__:
            message = "'%s' object has no attribute '%s'"
            raise AttributeError, message % (self.__class.__name__, name)

        self.load_state()
        return getattr(self, name)


    # By default the handler is a free node (does not belong to a tree, or
    # is the root of a tree).
    parent = None
    name = ''
    real_handler = None


    ########################################################################
    # API
    ########################################################################
    def copy_handler(self):
        # Deep load
        self._deep_load()
        # Create and initialize the instance
        cls = self.__class__
        copy = object.__new__(cls)
        copy.resource = None
        copy.timestamp = None
        # Copy the state
        for name in cls.__slots__:
            if name == 'resource' or name == 'timestamp':
                continue
            value = getattr(self, name)
            value = deepcopy(value)
            setattr(copy, name, value)
        # Return the copy
        return copy


    def _deep_load(self):
        self.load_state()


    def load_state(self):
        resource = self.resource
        resource.open()
        try:
            self._load_state(resource)
        finally:
            resource.close()
        self.timestamp = resource.get_mtime()


    def load_state_from(self, resource):
        resource.open()
        get_transaction().add(self)
        try:
            self._load_state(resource)
        finally:
            resource.close()
        self.timestamp = datetime.now()


    def save_state(self):
        resource = self.resource

        transaction = get_transaction()
        transaction.lock()
        resource.open()
        try:
            self._save_state(resource)
        finally:
            resource.close()
            transaction.release()


    def save_state_to(self, resource):
        transaction = get_transaction()
        transaction.lock()
        resource.open()
        try:
            self._save_state_to(resource)
        finally:
            resource.close()
            transaction.release()


    def _save_state(self, resource):
        self._save_state_to(resource)


    def is_outdated(self):
        timestamp = self.timestamp
        # It cannot be out-of-date if it has not been loaded yet
        if timestamp is None:
            return False

        mtime = self.resource.get_mtime()
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return True

        return mtime > timestamp


    def has_changed(self):
        timestamp = self.timestamp
        # Not yet loaded, even
        if timestamp is None:
            return False

        mtime = self.resource.get_mtime()
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return False

        return self.timestamp > mtime


    def set_changed(self):
        if self.resource is not None:
            self.timestamp = datetime.now()
            get_transaction().add(self)


    ########################################################################
    # XXX Obsolete.
    # To be removed by 0.5, use instead "self.resource.get_mimetype".
    def get_mimetype(self):
        return self.resource.get_mimetype()

    mimetype = property(get_mimetype, None, None, '')

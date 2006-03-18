# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ib��ez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import datetime

# Import from itools
from itools.handlers.File import File
from itools.handlers.Folder import Folder
import IO



class IndexedField(File):

    def get_skeleton(self):
        return IO.encode_uint32(0)


    def _load_state(self, resource):
        state = self.state

        state.number_of_terms = IO.decode_uint32(resource.read(4))
        state.terms = []

        data = resource.read()
        for i in range(state.number_of_terms):
            term, data = IO.decode_string(data)
            state.terms.append(term)


    def add_term(self, term):
        state = self.state

        state.number_of_terms += 1
        state.terms.append(term)
        # Update the resource
        self.resource.write(IO.encode_uint32(state.number_of_terms))
        self.resource.append(IO.encode_string(term))
        # Set timestamp
        self.timestamp = self.resource.get_mtime()


    def to_str(self):
        state = self.state
        return IO.encode_uint32(state.number_of_terms) \
               + ''.join([ IO.encode_string(x) for x in state.terms ])



class StoredField(File):

    def get_skeleton(self, data=u''):
        return IO.encode_string(data)


    def _load_state(self, resource):
        data = resource.read()
        self.state.value = IO.decode_string(data)[0]


    def to_str(self):
        return IO.encode_string(self.state.value)



class IDocument(Folder):

    def _get_handler(self, segment, resource):
        name = segment.name
        if name.startswith('i'):
            return IndexedField(resource)
        elif name.startswith('s'):
            return StoredField(resource)
        return Folder._get_handler(self, segment, resource)


    def _load_state(self, resource):
        Folder._load_state(self, resource)
        self.document = None


    # Used by Catalog.index_document, may be removed (XXX).
    def _set_handler(self, name, handler):
        self.resource.set_resource(name, handler.resource)
        self.state.cache[name] = None
        self.timestamp = self.resource.get_mtime()



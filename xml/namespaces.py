# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from warnings import warn

# Import from itools
from itools.datatypes import String, Unicode
from parser import XMLError


"""
This module keeps a registry for namespaces and namespace handlers.

Namespace handlers are used through the parsing process, they are
responsible to deal with the elements and attributes associated to
them.

This module provides an API to register namespace uris and handlers,
and to ask this registry.

It also provides a registry from namespace prefixes to namespace uris.
While namespace prefixes are local to an XML document, it is sometimes
useful to refer to a namespace through its prefix. This feature must
be used carefully, collisions
"""



xml_uri = 'http://www.w3.org/XML/1998/namespace'
xmlns_uri = 'http://www.w3.org/2000/xmlns/'


###########################################################################
# The registry
###########################################################################
namespaces = {}
prefixes = {}


def register_namespace(namespace, *args):
    """Associates a namespace handler to a namespace uri. It a prefix is
    given it also associates that that prefix to the given namespace.
    """
    # Register the URI
    namespaces[namespace.uri] = namespace

    # Register the prefix
    prefix = namespace.prefix
    if prefix is not None:
        if prefix in prefixes:
            warn('The prefix "%s" is already registered.' % prefix)
        prefixes[prefix] = namespace.uri

    # Register additional URIs
    for uri in args:
        namespaces[uri] = namespace


def get_namespace(namespace_uri):
    """Returns the namespace handler associated to the given uri. If there
    is none the default namespace handler will be returned, and a warning
    message will be issued.
    """
    if namespace_uri in namespaces:
        return namespaces[namespace_uri]

    # Use default
    warn('Unknown namespace "%s" (using default)' % namespace_uri)
    return namespaces[None]


def has_namespace(namespace_uri):
    """Returns true if there is namespace handler associated to the given uri.
    """
    return namespace_uri in namespaces


def get_namespace_by_prefix(prefix):
    """Returns the namespace handler associated to the given prefix. If there
    is none the default namespace handler is returned, and a warning message
    is issued.
    """
    if prefix in prefixes:
        namespace_uri = prefixes[prefix]
        return get_namespace(namespace_uri)

    # Use default
    warn('Unknown namespace prefix "%s" (using default)' % prefix)
    return namespaces[None]


def get_element_schema(namespace, name):
    return get_namespace(namespace).get_element(name)


def is_empty(namespace, name):
    schema = get_namespace(namespace).get_element(name)
    return getattr(schema, 'is_empty', False)


###########################################################################
# Namespaces
###########################################################################

class ElementSchema(object):

    class_uri = None
    attributes = {}

    # Default Values
    is_empty = False
    translate_content = True


    def __init__(self, name, **kw):
        self.name = name
        for key in kw:
            setattr(self, key, kw[key])


    def _get_attr_datatype(self, name):
        datatype = self.attributes.get(name)
        if datatype is None:
            message = 'unexpected "%s" attribute for "%s" element'
            raise XMLError, message % (name, self.name)

        return datatype


    def get_attr_datatype(self, attr_uri, attr_name):
        if attr_uri is None:
            if attr_name == 'xmlns':
                return String

        if attr_uri is None or attr_uri == self.class_uri:
            return self._get_attr_datatype(attr_name)

        # Foreign attribute
        return get_namespace(attr_uri).get_free_attribute(attr_name)


    #######################################################################
    # Internationalization
    def is_translatable(self, attributes, attribute_name):
        """Some elements may contain text addressed to users, that is, text
        that could be translated in different human languages, for example
        the 'p' element of XHTML. This method should return 'True' in that
        cases, False (the default) otherwise.

        If the parameter 'attribute_name' is given, then we are being asked
        wether that attribute is or not translatable. An example is the 'alt'
        attribute of the 'img' elements of XHTML.
        """
        return False



class XMLNamespace(object):

    def __init__(self, uri, prefix, elements=None, free_attributes=None):
        self.uri = uri
        self.prefix = prefix
        # Elements
        self.elements = {}
        if elements is not None:
            for element in elements:
                name = element.name
                if name in self.elements:
                    raise ValueError, 'element "%s" is defined twice' % name
                self.elements[name] = element
        # Free Attributes
        if free_attributes is None:
            self.free_attributes = {}
        else:
            self.free_attributes = free_attributes


    def get_element(self, name):
        """Returns a dictionary that defines the schema for the given element.
        """
        element = self.elements.get(name)
        if element is None:
            raise XMLError, 'unexpected element "%s"' % name

        return element


    def get_free_attribute(self, name):
        datatype = self.free_attributes.get(name)
        if datatype is None:
            raise XMLError, 'unexpected attribute "%s"' % name

        return datatype



# The default namespace is used for free elements.

class DefaultNamespace(XMLNamespace):
    """Default namespace handler for elements and attributes that are not
    bound to a particular namespace.
    """

    def get_element(self, name):
        return ElementSchema(name)


default_namespace = DefaultNamespace(None, None)



# The builtin "xml:" namespace
xml_namespace = XMLNamespace(
    xml_uri, 'xml',
    free_attributes={
        'lang': String,
        'space': String,
        'base': String,
        'id': String})


# The builtin "xmlns:" namespace, for namespace declarations
class XMLNSNamespace(XMLNamespace):

    def get_free_datatype(self, name):
        return String


xmlns_namespace = XMLNSNamespace(xmlns_uri, 'xmlns')



###########################################################################
# Register
###########################################################################
register_namespace(xml_namespace)
register_namespace(xmlns_namespace)
register_namespace(default_namespace)


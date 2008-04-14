# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.xml import (XMLFile, XMLParser, XMLError, XML_DECL, DOCUMENT_TYPE,
    START_ELEMENT, END_ELEMENT, TEXT, COMMENT, PI, CDATA, stream_to_str)
from itools.xml.i18n import get_messages



class ParserTestCase(TestCase):

    def test_xml_decl(self):
        data = '<?xml version="1.0" encoding="UTF-8"?>'
        token = XML_DECL
        value = '1.0', 'UTF-8', None
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_doctype_public(self):
        data = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                '  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
        token = DOCUMENT_TYPE
        value = ('html', 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd',
                 '-//W3C//DTD XHTML 1.0 Strict//EN', None)
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_doctype_system(self):
        data = ('<!DOCTYPE html SYSTEM'
                ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
        token = DOCUMENT_TYPE
        value = ('html', 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd',
                 None, None)
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    #######################################################################
    # Character References
    def test_char_ref(self):
        data = '&#241;'
        token = TEXT
        value = "ñ"
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_char_ref_hex(self):
        data = '&#xf1;'
        token = TEXT
        value = "ñ"
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_char_ref_empty(self):
        data = '&#;'
        self.assertRaises(XMLError, XMLParser(data).next)


    #######################################################################
    # Character References
    def test_entity_references(self):
        self.assertEqual(XMLParser("&fnof;").next()[1], "ƒ")
        self.assertEqual(XMLParser("&Xi;").next()[1], "Ξ")
        self.assertEqual(XMLParser("&psi;").next()[1], "ψ")
        self.assertEqual(XMLParser("&permil;").next()[1], "‰")
        self.assertEqual(XMLParser("&real;").next()[1], "ℜ")
        self.assertEqual(XMLParser("&infin;").next()[1], "∞")
        self.assertEqual(XMLParser("&there4;").next()[1], "∴")
        self.assertEqual(XMLParser("&clubs;").next()[1], "♣")


    #######################################################################
    # Start Element
    def test_element(self):
        data = '<a>'
        token = START_ELEMENT
        value = None, 'a', {}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_attributes(self):
        data = '<a href="http://www.ikaaro.org">'
        token = START_ELEMENT
        value = None, 'a', {(None, 'href'): 'http://www.ikaaro.org'}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_attributes_single_quote(self):
        data = "<a href='http://www.ikaaro.org'>"
        token = START_ELEMENT
        value = None, 'a', {(None, 'href'): 'http://www.ikaaro.org'}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_attributes_no_quote(self):
        data = "<a href=http://www.ikaaro.org>"
        self.assertRaises(XMLError, XMLParser(data).next)


    def test_attributes_forbidden_char(self):
        data = '<img title="Black & White">'
        self.assertRaises(XMLError, XMLParser(data).next)


    def test_attributes_entity_reference(self):
        data = '<img title="Black &amp; White">'
        token = START_ELEMENT
        value = None, 'img', {(None, 'title'): 'Black & White'}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    #######################################################################
    # CDATA
    def test_cdata(self):
        data = '<![CDATA[Black & White]]>'
        token = CDATA
        value = 'Black & White'
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    #######################################################################
    # Broken XML
    #######################################################################
    def test_missing_end_element(self):
        data = '<div><span></div>'
        parser = XMLParser(data)
        self.assertRaises(XMLError, list, parser)


    def test_missing_end_element2(self):
        data = '<div>'
        parser = XMLParser(data)
        self.assertRaises(XMLError, list, parser)



class XMLTestCase(TestCase):

    def test_identity(self):
        """
        Tests wether the input and the output match.
        """
        data = ('<html>\n'
                '<head></head>\n'
                '<body>\n'
                ' this is a <span style="color: red">test</span>\n'
                '</body>\n'
                '</html>')
        h1 = XMLFile(string=data)
        h2 = XMLFile(string=data)

        self.assertEqual(h1, h2)


    def test_doctype_public(self):
        data = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                '  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
        stream = XMLParser(data)
        self.assertEqual(stream_to_str(stream), data)


    def test_doctype_system(self):
        data = ('<!DOCTYPE html SYSTEM'
                ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">')
        stream = XMLParser(data)
        self.assertEqual(stream_to_str(stream), data)



class TranslatableTestCase(TestCase):

    def test_surrounding(self):
        text = '<em>Hello World</em>'
        parser = XMLParser(text)
        messages = get_messages(parser)
        messages = list(messages)

        self.assertEqual(messages, [(u'Hello World', 0)])



if __name__ == '__main__':
    unittest.main()

# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from operator import attrgetter
from string import Template

# Import from itools
from itools.uri import Path
from itools.datatypes import XMLAttribute
from itools.handlers import Folder
from itools.xml import Parser
from itools.stl import stl
from itools.web import get_context

# Import from itools.cms
from utils import get_parameters
from base import Handler



###########################################################################
# Table
###########################################################################

def batch(uri, start, size, total, gettext=Handler.gettext,
          msgs=(u"There is 1 object.", u"There are ${n} objects.")):
    """
    Outputs an HTML snippet with navigation links to move through a set
    of objects.

    Input data:
        
        uri -- The base URI to use to build the navigation links.

        start -- The start of the batch (from 0).

        size -- The size of the batch.

        total -- The total number of objects.
    """
    # Plural forms (XXX do it the gettext way)
    if total == 1:
        msg1 = gettext(msgs[0])
    else:
        msg1 = gettext(msgs[1])
        msg1 = Template(msg1).substitute(n=total)
    msg1 = msg1.encode('utf-8')

    # Calculate end
    end = min(start + size, total)

    # Previous
    previous = None
    if start > 0:
        previous = max(start - size, 0)
        previous = str(previous)
        previous = uri.replace(batchstart=previous)
        previous = str(previous)
        previous = XMLAttribute.encode(previous)
        previous = '<a href="%s" title="%s">&lt;&lt;</a>' \
                   % (previous, gettext(u'Previous'))
    # Next
    next = None
    if end < total:
        next = str(end)
        next = uri.replace(batchstart=next)
        next = str(next)
        next = XMLAttribute.encode(next)
        next = '<a href="%s" title="%s">&gt;&gt;</a>' \
               % (next, gettext(u'Next'))

    # Output
    if previous is None and next is None:
        msg = msg1
    else:
        # View more
        if previous is None:
            link = next
        elif next is None:
            link = previous
        else:
            link = '%s %s' % (previous, next)

        msg2 = gettext(u"View from ${start} to ${end} (${link}):")
        msg2 = Template(msg2)
        msg2 = msg2.substitute(start=(start+1), end=end, link=link)
        msg2 = msg2.encode('utf-8')

        msg = '%s %s' % (msg1, msg2)

    # Wrap around a paragraph
    return Parser('<p class="batchcontrol">%s</p>' % msg)



def table_sortcontrol(column, sortby, sortorder):
    """
    Returns an html snippet with a link that lets to order a column
    in a table.
    """
    # Process column
    if isinstance(column, (str, unicode)):
        column = [column]

    # Calculate the href
    data = {}
    data['sortby'] = column

    if sortby == column:
        value = sortorder
        if sortorder == 'up':
            data['sortorder'] = 'down'
        else:
            data['sortorder'] = 'up'
    else:
        value = 'none'
        data['sortorder'] = 'up'

    href = get_context().uri.replace(**data)
    return href, value


def table_head(columns, sortby, sortorder, gettext=lambda x: x):
    # Build the namespace
    columns_ = []
    for name, title in columns:
        if title is None:
            column = None
        else:
            column = {'title': gettext(title)}
            href, sort = table_sortcontrol(name, sortby, sortorder)
            column['href'] = href
            column['order'] = sort
        columns_.append(column)
    # Go
    return columns_


table_template = list(Parser("""
<stl:block xmlns="http://www.w3.org/1999/xhtml"
  xmlns:stl="http://xml.itools.org/namespaces/stl">

  <!-- Content -->
  <form action="." method="post" id="browse_list" name="browse_list">
    <table xmlns="http://www.w3.org/1999/xhtml"
      xmlns:stl="http://xml.itools.org/namespaces/stl">
      <thead stl:if="columns">
        <tr>
          <th stl:if="column_checkbox"></th>
          <th stl:if="column_image"></th>
          <th stl:repeat="column columns" valign="bottom">
            <a stl:if="column" href="${column/href}"
              class="sort_${column/order}">${column/title}</a>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr stl:repeat="row rows" class="${repeat/row/even} ${row/class}">
          <td stl:if="column_checkbox">
            <input class="checkbox" type="checkbox" name="ids" stl:if="row/id"
              value="${row/id}" checked="${row/checked}" />
          </td>
          <td stl:if="column_image">
            <img border="0" src="${row/img}" stl:if="row/img" />
          </td>
          <td stl:repeat="column row/columns">
            <a stl:if="column/href" href="${column/href}">${column/value}</a>
            <stl:block if="not column/href">${column/value}</stl:block>
          </td>
        </tr>
      </tbody>
    </table> 
    <p stl:if="actions">
      <stl:block repeat="action actions">
        <input type="submit" name=";${action/name}" value="${action/value}"
          class="${action/class}" onclick="${action/onclick}" />
      </stl:block>
    </p>
  </form>
</stl:block>
"""))


def table(columns, rows, sortby, sortorder, actions=[], gettext=lambda x: x):
    """
    The parameters are:

      columns --
        [(name, title), (name, title), ...]

      rows --
        [{'checkbox': , 'img': }, ...]

      sortby --
        The column to sort.

      sortorder --
        The order the column must be sorted by.

      actions --
        [{'name': , 'value': , 'class': , 'onclick': }, ...]

      gettext --
        The translation function.
    """
    namespace = {}
    namespace['column_checkbox'] = False
    namespace['column_image'] = False
    # The columns
    namespace['columns'] = table_head(columns, sortby, sortorder, gettext)
    # The rows
    aux = []
    for row in rows:
        x = {}
        # The checkbox column
        # TODO Instead of the parameter 'checked', use only 'checkbox', but
        # with three possible values: None, False, True
        id = None
        if actions and row['checkbox'] is True:
            id = row['id']
            if isinstance(id, int):
                id = str(id)
            namespace['column_checkbox'] = True
            # Checked by default?
            x['checked'] = row.get('checked', False)
        x['id'] = id
        # The image column
        x['img'] = row.get('img')
        if x['img'] is not None:
            namespace['column_image'] = True
        # A CSS class on the TR
        x['class'] = row.get('class')
        # Other columns
        x['columns'] = []
        for column, kk in columns:
            value = row.get(column)
            if isinstance(value, tuple):
                value, href = value
            else:
                href = None
            x['columns'].append({'value': value, 'href': href})
        aux.append(x)

    namespace['rows'] = aux
    # The actions
    namespace['actions'] = [
        {'name': name, 'value': value, 'class': cls, 'onclick': onclick}
        for name, value, cls, onclick in actions ]

    return stl(events=table_template, namespace=namespace)



###########################################################################
# Breadcrumb
###########################################################################
class Breadcrumb(object):
    """
    Instances of this class will be used as namespaces for STL templates.
    The built namespace contains the breadcrumb, that is to say, the path
    from the tree root to another tree node, and the content of that node.
    """

    def __init__(self, filter_type=Handler, root=None, start=None):
        """
        The 'start' must be a handler, 'filter_type' must be a handler class.
        """
        context = get_context()
        request, response = context.request, context.response

        if root is None:
            root = context.root
        if start is None:
            start = root

        here = context.handler

        # Get the query parameters
        parameters = get_parameters('bc', id=None, target=None)
        id = parameters['id']
        # Get the target folder
        target_path = parameters['target']
        if target_path is None:
            if isinstance(start, Folder):
                target = start
            else:
                target = start.parent
        else:
            target = root.get_handler(target_path)

        # XXX Obsolete code
        self.style = 'style'
##        self.style = '../' * len(start.get_abspath().split('/')) + 'style'

        # Object to link
        object = request.form.get('object')
        if object == '':
            object = '.'
        self.object = object

        # The breadcrumb
        breadcrumb = []
        node = target
        while node is not root.parent:
            url = context.uri.replace(bc_target=str(root.get_pathto(node)))
            breadcrumb.insert(0, {'name': node.name, 'url': url})
            node = node.parent
        self.path = breadcrumb

        # Content
        objects = []
        self.is_submit = False
        user = context.user
        filter = (Folder, filter_type)
        for handler in target.search_handlers(handler_class=filter):
            ac = handler.get_access_control()
            if not ac.is_allowed_to_view(user, handler):
                continue

            path = here.get_pathto(handler)
            bc_target = str(root.get_pathto(handler))
            url = context.uri.replace(bc_target=bc_target)

            self.is_submit = True
            # Calculate path
            path_to_icon = handler.get_path_to_icon(16)
            if path:
                path_to_handler = Path(str(path) + '/')
                path_to_icon = path_to_handler.resolve(path_to_icon)
            objects.append({'name': handler.name,
                            'is_folder': isinstance(handler, Folder),
                            'is_selectable': True,
                            'path': path,
                            'url': url,
                            'icon': path_to_icon,
                            'object_type': handler.get_mimetype()})

        self.objects = objects

        # Avoid general template
        response.set_header('Content-Type', 'text/html; charset=UTF-8')



###########################################################################
# Menu
###########################################################################
menu_template = list(Parser("""
<dl xmlns="http://www.w3.org/1999/xhtml"
  xmlns:stl="http://xml.itools.org/namespaces/stl">
  <stl:block repeat="item items">
    <dt class="${item/class}">
      <img stl:if="item/src" src="${item/src}" alt="" width="16" height="16" />
      <stl:block if="not item/href">${item/title}</stl:block>
      <a stl:if="item/href" href="${item/href}">${item/title}</a>
    </dt>
    <dd>${item/items}</dd>
  </stl:block>
</dl>
"""))



def build_menu(options):
    """
    The input (options) is a tree:

      [{'href': ...,
        'class': ...,
        'src': ...,
        'title': ...,
        'items': [....]}
       ...
       ]
       
    """
    for option in options:
        if option['items']:
            option['items'] = build_menu(option['items'])
        else:
            option['items'] = None

    namespace = {'items': options}
    return stl(events=menu_template, namespace=namespace)



def _tree(node, root, depth, active_node, filter, user, width):
    # Build the namespace
    namespace = {}
    namespace['src'] = node.get_path_to_icon(size=16, from_handler=active_node)
    namespace['title'] = node.get_title()

    # The href
    firstview = node.get_firstview()
    if firstview is None:
        namespace['href'] = None
    else:
        path = active_node.get_pathto(node)
        namespace['href'] = '%s/;%s' % (path, firstview)

    # The CSS style
    namespace['class'] = ''
    if node is active_node:
        namespace['class'] = 'nav_active'

    # Expand only if in path
    aux = active_node
    while True:
        # Match
        if aux is node:
            break
        # Reach the root, do not expand
        if aux is root:
            namespace['items'] = []
            return namespace, False
        # Next
        aux = aux.parent

    # Expand till a given depth
    if depth <= 0:
        namespace['items'] = []
        return namespace, True

    # Expand the children
    depth = depth - 1

    # Filter the handlers by the given class (don't filter by default)
    if filter is None:
        search = node.search_handlers()
    else:
        search = node.search_handlers(handler_class=filter)

    children = []
    counter = 0
    for child in search:
        ac = child.get_access_control()
        if ac.is_allowed_to_view(user, child):
            ns, in_path = _tree(child, root, depth, active_node, filter, user,
                                width)
            if in_path:
                children.append(ns)
            elif counter < width:
                children.append(ns)
            counter += 1
    if counter > width:
        children.append({'href': None,
                         'class': '',
                         'src': None, 
                         'title': '...',
                         'items': []})
    namespace['items'] = children
 
    return namespace, True



def tree(root, depth=6, active_node=None, filter=None, user=None, width=10):
    ns, in_path = _tree(root, root, depth, active_node, filter, user, width)
    return build_menu([ns])


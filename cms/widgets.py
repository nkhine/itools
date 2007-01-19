# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from operator import attrgetter
from string import Template

# Import from itools
from itools.uri import Path
from itools.handlers.Folder import Folder
from itools.xhtml import XHTML
from itools.stl import stl
from itools.web import get_context

# Import from itools.cms
from utils import get_parameters
from Handler import Handler



###########################################################################
# Table
###########################################################################
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
            if name is None:
                column['href'] = None
            else:
                href, sort = table_sortcontrol(name, sortby, sortorder)
                column['href'] = href
                column['order'] = sort
        columns_.append(column)
    # Go
    return columns_


table_template_string = """
<table xmlns="http://www.w3.org/1999/xhtml"
  xmlns:stl="http://xml.itools.org/namespaces/stl">
  <thead stl:if="columns">
    <tr>
      <th stl:repeat="column columns" valign="bottom">
        <stl:block if="column">
          <stl:block if="not column/href">${column/title}</stl:block>
          <a stl:if="column/href" href="${column/href}"
            class="sort_${column/order}">${column/title}</a>
        </stl:block>
      </th>
    </tr>
  </thead>
  <tbody>
    <tr stl:repeat="row rows" class="${repeat/row/even}">
      <td>
        <input class="checkbox" type="checkbox" name="ids" stl:if="row/id"
          value="${row/id}" />
      </td>
      <td>
        <img border="0" src="${row/img}" stl:if="row/img" />
      </td>
      <td stl:repeat="column row/columns" class="${column/class}">
        <a href="${column/href}" stl:if="column/href">${column/title}</a>
        <stl:block if="not column/href">${column/title}</stl:block>
      </td>
    </tr>
  </tbody>
</table>
"""

table_template = XHTML.Document()
table_template.load_state_from_string(table_template_string)


def table(rows, columns, sortby, sortorder, gettext=lambda x: x):
    """
    The parameters are:
        
      rows --
        [{'id': ..., 'img': ...,
          'columns': [{'href': ..., 'title': ..., 'class': ...}, ...]}
         ...]

      columns --
        [None, None, (name, title), (name, title), ...]

      sortby --
        The column to sort.

      sortorder --
        The order the column must be sorted by.

      gettext --
        The translation function.
    """
    namespace = {}
    namespace['rows'] = rows
    namespace['columns'] = table_head(columns, sortby, sortorder, gettext)

    return stl(table_template, namespace)



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
    output = '<dl>\n'

    for option in options:
        cls = option['class']
        href = option['href']
        src = option['src']
        # The option
        output += '<dt class="%s">' % cls
        # The image
        if option['src'] is not None:
            output += '<img src="%s" alt="" width="16" height="16" /> ' % src
        # The link
        if option['href'] is None:
            output += option['title']
        else:
            output += '<a href="%s">' % href
            output += option['title']
            output += '</a>'
        output += '</dt>\n'

        # Sub-options
        output += '<dd>'
        if option['items']:
            output += build_menu(option['items'])
        output += '</dd>'

    output += '</dl>\n'
    return output



def _tree(context, handler, depth, filter):
    # Define local variables
    here = context.handler
    handler_path = handler.abspath

    # Build the namespace
    namespace = {}
    namespace['src'] = handler.get_path_to_icon(size=16, from_handler=here)
    namespace['title'] = handler.get_title_or_name()

    # The href
    firstview = handler.get_firstview()
    if firstview is None:
        namespace['href'] = None
    else:
        if handler_path == '/':
            namespace['href'] = '/;%s' % firstview
        else:
            namespace['href'] = '%s/;%s' % (handler_path, firstview)

    # The CSS style
    namespace['class'] = ''
    if handler_path == str(context.path):
        namespace['class'] = 'nav_active'

    # Expand only if in path
    here_path = str(context.path)
    if not here_path.startswith(handler_path):
        namespace['items'] = []
        return namespace

    # Expand till a given depth
    if depth <= 0:
        namespace['items'] = []
        return namespace

    # Expand the children
    depth = depth - 1
    user = context.user

    # Filter the handlers by the given class (don't filter by default)
    if filter is None:
        search = handler.search_handlers()
    else:
        search = handler.search_handlers(handler_class=filter)

    children = []
    for child in search:
        ac = child.get_access_control()
        if ac.is_allowed_to_view(user, child):
            children.append(_tree(context, child, depth, filter))
    namespace['items'] = children
 
    return namespace



def tree(context, root=None, depth=6, filter=None):
    if root is None:
        root = context.root

    options = [_tree(context, root, depth, filter)]
    return build_menu(options)


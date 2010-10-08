# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from cStringIO import StringIO

# Import from the Python Image Library
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

# Import from rsvg
try:
    from cairo import Context, ImageSurface, FORMAT_ARGB32
    from rsvg import Handle as rsvg_handle
except ImportError:
    rsvg_handle = None

# Import from itools
from file import File
from registry import register_handler_class


class Image(File):

    class_mimetypes = ['image']

    def _load_state_from_file(self, file):
        self.data = file.read()

        # Size
        handle = self._get_handle()
        if handle:
            self.size = self._get_size(handle)
        else:
            self.size = (0, 0)

        # A cache for thumbnails, where the key is the size and the format,
        # and the value is the thumbnail.
        self.thumbnails = {}


    def _get_handle(self):
        if PILImage is None:
            return None

        #data = self.to_str()
        data = self.data
        f = StringIO(data)
        try:
            return PILImage.open(f)
        except (IOError, OverflowError):
            return None


    def _get_size(self, handle):
        return handle.size


    #########################################################################
    # API
    #########################################################################
    def get_size(self):
        return self.size


    def get_thumbnail(self, width, height, format="jpeg"):
        format = format.lower()

        # Get the handle
        handle = self._get_handle()
        if handle is None:
            return None, None

        # Cache hit
        thumbnails = self.thumbnails
        key = (width, height, format)
        if key in thumbnails:
            return thumbnails[key]

        # Cache miss
        value = self._get_thumbnail(handle, width, height, format)
        thumbnails[key] = value
        return value


    def _get_thumbnail(self, handle, width, height, format):
        # Do not create the thumbnail if not needed
        image_width, image_height = self.size
        if width >= image_width or height >= image_height:
            return self.to_str(), format

        # Convert to RGBA
        try:
            im = handle.convert("RGBA")
        except IOError:
            return None, None

        # Make the thumbnail
        # TODO Improve the quality of the thumbnails by cropping?
        try:
            im.thumbnail((width, height), PILImage.ANTIALIAS)
        except IOError:
            # PIL does not support interlaced PNG files, raises IOError
            return None, None

        thumbnail = StringIO()
        im.save(thumbnail, format.upper(), quality=80)
        data = thumbnail.getvalue()
        thumbnail.close()

        # Store in the cache and return
        return data, format



class SVGFile(Image):

    class_mimetypes = ['image/svg+xml']


    def _get_handle(self):
        if rsvg_handle is None:
            return None

        data = self.to_str()
        svg = rsvg_handle()
        svg.write(data)
        svg.close()
        return svg


    def _get_size(self, handle):
        return handle.get_property('width'), handle.get_property('height')


    def _get_thumbnail(self, handle, width, height, format):
        image_width, image_height = self.size
        if width >= image_width or height >= image_height:
            # Case 1: convert
            surface = ImageSurface(FORMAT_ARGB32, image_width, image_height)
            ctx = Context(surface)
        else:
            # Case 2: scale
            surface = ImageSurface(FORMAT_ARGB32, width, height)
            ctx = Context(surface)

            image_width = float(image_width)
            image_height = float(image_height)
            ratio = image_width/image_height
            if ratio > 1.0:
                height = height/ratio
            elif ratio < 1.0:
                width = width * ratio

            ctx.scale(width/image_width, height/image_height)

        # Render
        handle.render_cairo(ctx)
        output = StringIO()
        surface.write_to_png(output)
        surface.finish()

        # FIXME We do not use the 'format' parameter
        return output.getvalue(), 'png'



register_handler_class(Image)
register_handler_class(SVGFile)

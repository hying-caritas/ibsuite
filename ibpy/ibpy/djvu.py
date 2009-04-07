#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

from image import PageImageRef
from util import *

class DJVUToPPM(object):
    def __init__(self, config):
        object.__init__(self)
        self.djvu_fn = config.input_fn
        self.tmpd = '%s/djvutopgm' % (config.tmp_dir,)
        makedirs(self.tmpd)
        self.output_prefix = '%s/out' % (self.tmpd,)
    def get_image(self, page_num):
        spage_num = '%d' % (page_num,)
        out_fn = self.output_prefix + '-' + spage_num
        check_call(['ddjvu', '-format=pgm', '-page=' + spage_num,
                    self.djvu_fn, out_fn])
        return PageImageRef(page_num, file_name = out_fn)

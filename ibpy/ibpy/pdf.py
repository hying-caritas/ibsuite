#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import os.path
import re

from image import PageImageRef
from util import *

class PDFToPPM(object):
    def __init__(self, config):
        object.__init__(self)
        self.pdf_fn = config.input_fn
        self.tmpd = '%s/pdftoppm' % (config.tmp_dir,)
        makedirs(self.tmpd)
        self.output_prefix = '%s/out' % (self.tmpd,)
        self.dpi = config.rendering_dpi
    def get_image(self, page_num):
        spage_num = '%d' % (page_num,)
        sdpi = '%d' % (self.dpi,)
        check_call(['pdftoppm', '-r', sdpi, '-f', spage_num,
                    '-l', spage_num, '-gray', self.pdf_fn,
                    self.output_prefix])
        fns = os.listdir(self.tmpd)
        fns = [os.path.join(self.tmpd, fn) for fn in fns]
        re_img_fn = re.compile('%s-0*%d.pgm' % (self.output_prefix, page_num))
        img_fns = [fn for fn in fns if re_img_fn.match(fn)]
        assert(len(img_fns) == 1)
        return PageImageRef(page_num, file_name = img_fns[0])

class PDFImage(object):
    def __init__(self, config):
        object.__init__(self)
        self.pdf_fn = config.input_fn
        self.output_prefix = config.output_prefix
        self.tmpd = '%s/pdfimage' % (config.tmp_dir,)
        makedirs(self.tmpd)
        self.output_prefix = '%s/out' % (self.tmpd,)
        self.re_out_fn = re.compile('%s-0*\\.(ppm|pbm)' % (self.output_prefix,))
    def get_image(self, page_num):
        spage_num = '%d' % (page_num,)
        check_call(['pdfimages', '-f', spage_num, '-l', spage_num,
                    self.pdf_fn, self.output_prefix])
        img_fn = '%s-%06d.pgm' % (self.output_prefix, page_num)
        fns = os.listdir(self.tmpd)
        fns = [os.path.join(self.tmpd, fn) for fn in fns]
        out_fns = [fn for fn in fns if self.re_out_fn.match(fn)]
        assert(len(out_fns) == 1)
        out_fn = out_fns[0]
        cmdline = ['convert', '-depth', '8']
        if out_fn.endswith('pbm'):
            cmdline.append('-negate')
        cmdline.extend([out_fns[0], img_fn])
        check_call(cmdline)
        os.unlink(out_fns[0])
        return PageImageRef(page_num, file_name = img_fn)

def create_pdf_to_ppm(config):
    if config.input_type == 'image':
        return PDFImage(config)
    else:
        return PDFToPPM(config)

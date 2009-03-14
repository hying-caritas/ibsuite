#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

from subprocess import Popen, PIPE, call
import os.path

from image import PageImageRef

class PDFToPPM(object):
    def __init__(self, config):
        object.__init__(self)
        self.pdf_fn = config.input_fn
        self.output_prefix = config.output_prefix
        self.dpi = config.rendering_dpi
        self.pfw = config.pfw
    def get_image(self, page_num):
        spage_num = '%d' % (page_num,)
        sdpi = '%d' % (self.dpi,)
        ret = call(['pdftoppm', '-r', sdpi, '-f', spage_num, '-l', spage_num,
                    '-gray', self.pdf_fn, self.output_prefix])
        assert(ret == 0)
        img_fn = '%s-%0*d.pgm' % (self.output_prefix, self.pfw, page_num)
        return PageImageRef(page_num, file_name = img_fn)

class PDFImage(object):
    def __init__(self, config):
        object.__init__(self)
        self.pdf_fn = config.input_fn
        self.output_prefix = config.output_prefix
        self.pfw = config.pfw
    def get_image(self, page_num):
        spage_num = '%d' % (page_num,)
        ret = call(['pdfimages', '-f', spage_num, '-l', spage_num,
                    self.pdf_fn, self.output_prefix])
        assert(ret == 0)
        fn_stem = '%s-%0*d' % (self.output_prefix, self.pfw, 0)
        img_fn = '%s-%0*d.pgm' % (self.output_prefix, self.pfw, page_num)
        fn_ppm = fn_stem + '.ppm'
        fn_pbm = fn_stem + '.pbm'
        if os.path.exists(fn_ppm):
            ret = call(['convert', '-depth', '8', fn_ppm, img_fn])
            assert(ret == 0)
            os.unlink(fn_ppm)
        else:
            ret = call(['convert', '-depth', '8', '-negate', fn_pbm, img_fn])
            assert(ret == 0)
            os.unlink(fn_pbm)
        return PageImageRef(page_num, file_name = img_fn)

def create_pdf_to_ppm(config):
    if config.input_type == 'image':
        return PDFImage(config)
    else:
        return PDFToPPM(config)

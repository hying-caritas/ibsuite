#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import os
import tempfile
import Image, ImageFilter
import config

from util import *

class PageImageRef(object):
    def __init__(self, page_num, sub_page_num = 0,
                 image = None, file_name = None):
        object.__init__(self)
        self.page_num = page_num
        self.sub_page_num = sub_page_num
        self.image = image
        self.file_name = file_name
    def __del__(self):
        if self.file_name and not config.debug:
            os.unlink(self.file_name)
    def clear(self):
        self.file_name = None
        self.image = None
    def derive(self, image = None, file_name = None):
        return PageImageRef(self.page_num, self.sub_page_num,
                            image, file_name)
    def get_image(self):
        if self.image:
            return self.image
        elif self.file_name:
            self.image = Image.open(self.file_name)
            return self.image
    def get_file_name(self, ext = 'pgm'):
        if self.file_name:
            return self.file_name
        self.file_name = temp_file_name('.'+ext)
        if self.image:
            self.image.save(self.file_name)
            return self.file_name

class NullConv(object):
    def __init__(self, config):
        object.__init__(self)
    def convert(self, pimg_ref, out_file_name = None):
        return pimg_ref

class PreCrop(object):
    def __init__(self, config):
        object.__init__(self)
        self.trim_left = config.trim_left
        self.trim_top = config.trim_top
        self.trim_right = config.trim_right
        self.trim_bottom = config.trim_bottom
    def convert(self, pimg_ref, out_file_name = None):
        if self.trim_left < 0.01 and self.trim_top < 0.01 and \
                self.trim_right < 0.01 and self.trim_bottom < 0.01:
            return pimg_ref
        img = pimg_ref.get_image()
        iw, ih = img.size
        left = nround(self.trim_left * iw)
        right = iw - nround(self.trim_right * iw)
        top = nround(self.trim_top * ih)
        bottom = ih - nround(self.trim_bottom * ih)
        img = img.crop((left, top, right, bottom))
        return pimg_ref.derive(img)

class Dilate(object):
    def __init__(self, config):
        object.__init__(self)
    def convert(self, pimg_ref, out_file_name = None):
        img = pimg_ref.get_image()
        img = img.filter(ImageFilter.MinFilter(3))
        return pimg_ref.derive(img)

def create_dilate(config):
    if config.dilate:
        return Dilate(config)
    else:
        return NullConv(config)

class Unpaper(object):
    def __init__(self, config):
        object.__init__(self)
    def convert(self, pimg_ref, out_file_name = None):
        if out_file_name is None:
            out_file_name = temp_file_name('.pgm')
        check_call(['unpaper', '-q', '--no-deskew',
                    pimg_ref.get_file_name(), out_file_name])
        return pimg_ref.derive(file_name = out_file_name)

class RowCondense(object):
    def __init__(self, config):
        object.__init__(self)
        self.unpaper_keep_size = config.unpaper_keep_size
    def convert(self, pimg_ref, out_file_name = None):
        img = pimg_ref.get_image()
        iw, ih = img.size
        ethr = max(ih/500, 1)

        def not_empty(h):
            return sum(h[:-32]) > ethr

        top = 0
        bottom = ih
        left = -1
        right = iw

        for x in range(1, iw+1):
            ir = img.crop((x - 1, 0, x, ih))
            if not_empty(ir.histogram()):
                left = x - 1
                break
        if left == -1:
            if self.unpaper_keep_size:
                nimg = img
            else:
                nimg = img.crop((0, 0, 2, ih))
            return pimg_ref.derive(nimg)

        for x in range(left, iw-1, -1):
            ir = img.crop((x, 0, x+1, ih))
            if not_empty(ir.histogram()):
                right = x+1
                break

        rows = []
        pe = True
        for y in range(1, ih+1):
            ic = img.crop((left, y-1, right, y))
            ce = not not_empty(ic.histogram())
            if pe != ce:
                rows.append(y-1)
                pe = ce
        if not pe:
            rows.append(ih)
        if len(rows) == 0:
            if self.unpaper_keep_size:
                nimg = img
            else:
                nimg = img.crop((0, 0, 2, ih))
            return pimg_ref.derive(nimg)

        minh_empty = max(ih / 100, 5)
        for i in range(len(rows)-3, 1, -2):
            if rows[i+1] - rows[i] < minh_empty:
                del rows[i+1]
                del rows[i]
        minh_ink = max(ih / 100, 5)
        nh = 0
        for i in range(0, len(rows) - 2, 2):
            inkh = rows[i+1] - rows[i]
            ninkh = rows[i+3] - rows[i+2]
            nh = nh + inkh
            if inkh < minh_ink or ninkh < minh_ink:
                nh = nh + minh_empty
            else:
                nh = nh + rows[i+2] - rows[i+1]
        nh += rows[-1] - rows[-2]
        nw = right - left
        if self.unpaper_keep_size:
            nw, nh = iw, ih
            nimg = Image.new("L", (nw, nh))
            nimg.paste(255, [0, 0, nw, nh])
        else:
            nimg = Image.new("L", (nw, nh))
        cy = 0
        for i in range(0, len(rows) - 2, 2):
            inkh = rows[i+1] - rows[i]
            ninkh = rows[i+3] - rows[i+2]
            nimg.paste(img.crop((left, rows[i], right, rows[i+1])), (0, cy))
            cy = cy + inkh
            if inkh < minh_ink or ninkh < minh_ink:
                eh = minh_empty
            else:
                eh = rows[i+2] - rows[i+1]
            nimg.paste(255, (0, cy, nw, cy + eh))
            cy = cy + eh
        nimg.paste(img.crop((left, rows[-2], right, rows[-1])), (0, cy))
        return pimg_ref.derive(nimg)

class ColumnCondense(object):
    def __init__(self, config):
        object.__init__(self)
        self.unpaper_keep_size = config.unpaper_keep_size
    def convert(self, pimg_ref, out_file_name = None):
        img = pimg_ref.get_image()
        iw, ih = img.size
        ethr = max(iw/500, 1)

        def not_empty(h):
            return sum(h[:-32]) > ethr

        top = -1
        bottom = ih
        left = 0
        right = iw

        for y in range(1, ih+1):
            ir = img.crop((0, y - 1, iw, y))
            if not_empty(ir.histogram()):
                top = y - 1
                break
        if top == -1:
            if self.unpaper_keep_size:
                nimg = img
            else:
                nimg = img.crop((0, 0, iw, 2))
            return pimg_ref.derive(nimg)

        for y in range(ih-1, top, -1):
            ir = img.crop((0, y, iw, y+1))
            if not_empty(ir.histogram()):
                bottom = y+1
                break

        cols = []
        pe = True
        for x in range(1, iw+1):
            ic = img.crop((x-1, top, x, bottom))
            ce = not not_empty(ic.histogram())
            if pe != ce:
                cols.append(x-1)
                pe = ce
        if not pe:
            cols.append(iw)
        if len(cols) == 0:
            if self.unpaper_keep_size:
                nimg = img
            else:
                nimg = img.crop((0, 0, iw, 2))
            return pimg_ref.derive(nimg)

        minw_empty = max(iw / 100, 5)
        for i in range(len(cols)-3, 1, -2):
            if cols[i+1] - cols[i] < minw_empty:
                del cols[i+1]
                del cols[i]
        minw_ink = max(iw / 100, 5)
        nw = 0
        for i in range(0, len(cols) - 2, 2):
            inkw = cols[i+1] - cols[i]
            ninkw = cols[i+3] - cols[i+2]
            nw = nw + inkw
            if inkw < minw_ink or ninkw < minw_ink:
                nw = nw + minw_empty
            else:
                nw = nw + cols[i+2] - cols[i+1]
        nw += cols[-1] - cols[-2]
        nh = bottom - top
        if self.unpaper_keep_size:
            nw, nh = iw, ih
            nimg = Image.new("L", (nw, nh))
            nimg.paste(255, [0, 0, nw, nh])
        else:
            nimg = Image.new("L", (nw, nh))
        cx = 0
        for i in range(0, len(cols) - 2, 2):
            inkw = cols[i+1] - cols[i]
            ninkw = cols[i+3] - cols[i+2]
            nimg.paste(img.crop((cols[i], top, cols[i+1], bottom)),
                       (cx, 0))
            cx = cx + inkw
            if inkw < minw_ink or ninkw < minw_ink:
                ew = minw_empty
            else:
                ew = cols[i+2] - cols[i+1]
            nimg.paste(255, (cx, 0, cx + ew, nh))
            cx = cx + ew
        nimg.paste(img.crop((cols[-2], top, cols[-1], bottom)),
                   (cx, 0))
        return pimg_ref.derive(nimg)

class RowColumnCondense(object):
    def __init__(self, config):
        object.__init__(self)
        self.rc = RowCondense(config)
        self.cc = ColumnCondense(config)
    def convert(self, pimg_ref, out_file_name = None):
        pimg_ref = self.cc.convert(pimg_ref)
        return self.rc.convert(pimg_ref)

def create_unpaper(config):
    if config.unpaper == 'cc':
        return ColumnCondense(config)
    elif config.unpaper == 'rc':
        return RowCondense(config)
    elif config.unpaper == 'rcc':
        return RowColumnCondense(config)
    elif config.unpaper == 'up':
        return Unpaper(config)
    else:
        return NullConv(config)

class PostProc(object):
    def __init__(self, config):
        object.__init__(self)
        self.colors = config.colors
        self.rotate = config.rotate
        self.gamma = config.gamma
    def convert(self, pimg_ref, out_file_name = None):
        def do_gamma(infn):
            gmfn = temp_file_name('.png')
            cmd = ['convert', '-gamma', '%.2f' % (self.gamma,),
                   '-depth', '8', infn, gmfn]
            check_call(cmd)
            return gmfn

        if self.gamma > 0.001:
            gmfn = do_gamma(pimg_ref.get_file_name())
            pimg_ref = pimg_ref.derive(file_name = gmfn)

        if out_file_name is None:
            out_file_name = temp_file_name('.png')
        proc = False
        cmd = ['convert']
        if self.colors < 256:
            scolors = '%d' % (self.colors,)
            cmd.extend(['-colors', scolors])
            proc = True
        if self.rotate:
            cmd.extend(['-rotate', '-90'])
            proc = True
        if not proc:
            return pimg_ref
        cmd.extend(['-depth', '8', pimg_ref.get_file_name(), out_file_name])
        check_call(cmd)
        return pimg_ref.derive(file_name = out_file_name)

class FixBlackWhite(object):
    def __init__(self, config):
        object.__init__(self)
    def convert(self, pimg_ref, out_file_name = None):
        def fix(p):
            if p < 10:
                return 0
            if p > 245:
                return 255
            return p
        if out_file_name is None:
            out_file_name = temp_file_name('.png')
        img = pimg_ref.get_image()
        img = img.point(fix)
        return pimg_ref.derive(img)

class Collector(object):
    def __init__(self, config):
        object.__init__(self)
        self.page_map = {}
        self.out_files = []
        self.output_prefix = "%s/out" % (config.tmp_dir,)
        self.first_page = config.first_page
        self.last_page = config.last_page
    def collect(self, pimg_ref):
        in_file_name = pimg_ref.get_file_name('png')
        ext = in_file_name[-3:]
        pn = pimg_ref.page_num
        out_file_name = '%s-%06d-%02d.%s' % (self.output_prefix,
                                             pn, pimg_ref.sub_page_num, ext)
        os.rename(in_file_name, out_file_name)
        pimg_ref.clear()
        self.out_files.append(out_file_name)
        if not self.page_map.has_key(pn):
            self.page_map[pn] = len(self.out_files)
    def end(self):
        pm = self.page_map
        nopn = len(self.out_files)
        for pn in range(self.last_page, self.first_page, -1):
            if pm.has_key(pn):
                nopn = pm[pn]
            else:
                pm[pn] = nopn

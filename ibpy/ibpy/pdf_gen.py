#
# Copyright 2009 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

from reportlab.pdfgen import canvas

class PDFGenerator(object):
    def __init__(self, config):
        object.__init__(self)
        self.out_file_name = config.out_file_name
        self.rotate = config.rotate
        self.out_size = config.out_size
        self.title = config.title
        self.author = config.author
        self.bookmarks = config.bookmarks
    def generate(self, img_files, page_map):
        def gen_page_to_bm_map(bms, pm):
            p2bm = {}
            for bm in bms:
                if page_map.has_key(bm.page):
                    opn = page_map[bm.page] - 1
                    if not p2bm.has_key(opn):
                        p2bm[opn] = []
                    p2bm[opn].append(bm.title)
            return p2bm
        if self.rotate:
            oh, ow = self.out_size
        else:
            ow, oh = self.out_size
        c = canvas.Canvas(self.out_file_name, pagesize=(ow,oh))
        c.setTitle(self.title)
        c.setAuthor(self.author)
        p2bm = gen_page_to_bm_map(self.bookmarks, page_map)
        for opn, fn in enumerate(img_files):
            c.drawImage(fn, 0, 0)
            if p2bm.has_key(opn):
                for n, t in enumerate(p2bm[opn]):
                    key = '%d-%d' % (opn, n)
                    c.bookmarkPage(key)
                    c.addOutlineEntry(t, key, 0, 0)
            c.showPage()
        c.save()

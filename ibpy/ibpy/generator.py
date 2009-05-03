#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

from pylrs import pylrs
import imb

class NullGenerator(object):
    def __init__(self, config):
        object.__init__(self)
    def generate(self, img_files, page_map):
        pass

class LRFGenerator(object):
    def __init__(self, config):
        object.__init__(self)
        self.rotate = config.rotate
        self.out_size = config.out_size
        self.out_file_name = config.out_file_name
        self.title = config.title
        self.author = config.author
        self.bookmarks = config.bookmarks
    def generate(self, img_files, page_map):
        if self.rotate:
            oh, ow = self.out_size
        else:
            ow, oh = self.out_size
        book_setting = pylrs.BookSetting(screenwidth=ow,
                                         screenheight=oh)
        book = pylrs.Book(title=self.title, author=self.author,
                          booksetting=book_setting)
        page_style = pylrs.PageStyle(topmargin=0, oddsidemargin=0,
                                     evensidemargin=0, textwidth=ow,
                                     textheight=oh)
        block_style = pylrs.BlockStyle(blockwidth=ow, blockheight=oh)
        images = []
        for fn in img_files:
            stream = pylrs.ImageStream(fn)
            page = book.Page(page_style)
            page.BlockSpace()
            image = page.ImageBlock(refstream=stream, xsize=ow, ysize=oh,
                                    blockwidth=ow, blockheight=oh,
                                    x1=ow, y1=oh,
                                    blockStyle=block_style)
            images.append(image)
        page_map = page_map
        for bm in self.bookmarks:
            if page_map.has_key(bm.page):
                opn = page_map[bm.page]
                book.addTocEntry(bm.title, images[opn-1])
        book.renderLrf(self.out_file_name)

class IMBGenerator(object):
    def __init__(self, config):
        object.__init__(self)
        self.out_file_name = config.out_file_name
        self.title = config.title
        self.author = config.author
        self.bookmarks = config.bookmarks
    def generate(self, img_files, page_map):
        book = imb.Book(title=self.title, author=self.author)
        pages = []
        for fn in img_files:
            page = book.add_page(fn)
            pages.append(page)
        for bm in self.bookmarks:
            if page_map.has_key(bm.page):
                opn = page_map[bm.page]
                book.add_toc_entry(bm.title, pages[opn-1])
        book.save(self.out_file_name)

def create_generator(config):
    if config.out_format == 'lrf':
        return LRFGenerator(config)
    elif config.out_format == 'imb':
        return IMBGenerator(config)
    elif config.out_format == 'pdf':
        import pdf_gen
        return pdf_gen.PDFGenerator(config)
    else:
        return NullGenerator(config)

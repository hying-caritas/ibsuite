#
# Copyright 2009-2010 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import poppler

from util import *

class Bookmark(object):
    def __init__(self, title = None, page = None):
        object.__init__(self)
        self.title = title
        self.page = page

class PDFMeta(object):
    def __init__(self, doc_title, author, pages):
        object.__init__(self)
        self.doc_title = doc_title
        self.author = author
        self.pages = pages

class PDFInfoParser(object):
    def __init__(self, config):
        object.__init__(self)
        self.input_fn = config.input_fn
    def get_bookmarks(self, doc):
        def collect(idx):
            has_next = True
            while has_next:
                act = idx.get_action()
                if type(act) is poppler.ActionGotoDest:
                    dest =  act.dest
                    bookmarks.append(Bookmark(act.title, dest.page_num))
                    cidx = idx.get_child()
                    if cidx:
                        collect(cidx)
                has_next = idx.next()
        bookmarks = []
        try:
            idx = poppler.IndexIter(doc)
        except:
            idx = None
        if idx:
            collect(idx)
        return bookmarks
    def parse(self):
        doc = poppler.document_new_from_file('file://' +
                                             os.path.abspath(self.input_fn),
                                             None);
        title = doc.get_property('title')
        author = doc.get_property('author')
        if title is None:
            title = ''
        if author is None:
            author = ''
        meta = PDFMeta(title, author, doc.get_n_pages())
        bookmarks = self.get_bookmarks(doc)
        return (meta, bookmarks)

def print_bookmarks(bms):
    for bm in bms:
        print bm.title.encode('utf-8'), bm.page

if __name__ == '__main__':
    import sys
    config = Bookmark()
    config.input_fn = sys.argv[1]
    parser = PDFInfoParser(config)
    doc_info = parser.parse()
    info = doc_info[0]
    bms = doc_info[1]
    print info.doc_title.encode('utf-8')
    print info.author.encode('utf-8')
    print info.pages
    print_bookmarks(bms)

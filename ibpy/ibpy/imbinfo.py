#!/usr/bin/python

import os.path
from util import *
import imb

class ImbInfo(object):
    def __init__(self, doc_title, author, pages):
        object.__init__(self)
        self.doc_title = doc_title
        self.author = author
        self.pages = pages

class ImbInfoParser(object):
    def __init__(self, config):
        object.__init__(self)
        self.imb_fn = config.input_fn
    def parse(self):
        book = imb.Book()
        book.load(self.imb_fn)
        info = ImbInfo(book.title, book.author, len(book.pages))
        return (info, book.toc_entries)

def print_bookmarks(bms):
    for bm in bms:
        print bm.title.encode('utf-8'), bm.page

if __name__ == '__main__':
    import sys
    info = get_info(sys.argv[1])
    print 'title:', info.doc_title.encode('utf-8')
    print 'author:', info.author.encode('utf-8')
    print 'pages:', info.pages
    print_bookmarks(info.bookmarks)

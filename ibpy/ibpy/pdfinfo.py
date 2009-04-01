#!/usr/bin/python

from xml.sax import saxutils
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces, ContentHandler

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

class PDFMInfoHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.bookmarks = []
        self.bm_stack = []
        self.doc_title = ''
        self.author = ''
        self.pages = 0
    def startElement(self, name, attrs):
        if name == 'bookmark':
            bm = Bookmark()
            self.bookmarks.append(bm)
            self.bm_stack.append(bm)
        else:
            self.curr_elem = name
    def endElement(self, name):
        if name == 'bookmark':
            del self.bm_stack[-1]
        self.curr_elem = None
    def characters(self, ch):
        if len(self.bm_stack) != 0:
            bm = self.bm_stack[-1]
            if self.curr_elem == 'title':
                bm.title = ch
            elif self.curr_elem == 'page':
                bm.page = int(ch)
        else:
            if self.curr_elem == 'doc_title':
                self.doc_title = ch
            elif self.curr_elem == 'author':
                self.author = ch
            elif self.curr_elem == 'pages':
                self.pages = int(ch)
    def get_info(self):
        return (PDFMeta(self.doc_title, self.author, self.pages),
                self.bookmarks)

def parse(f):
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)

    dh = PDFMInfoHandler()
    parser.setContentHandler(dh)

    parser.parse(f)

    return dh.get_info()

def get_info(pdf_fn):
    p = Popen(['ibpdfinfo', pdf_fn], stdout = PIPE)
    info = parse(p.stdout)
    return info

class PDFInfoParser(object):
    def __init__(self, config):
        object.__init__(self)
        self.input_fn = config.input_fn
    def parse(self):
        return get_info(self.input_fn)

def print_bookmarks(bms):
    for bm in bms:
        print bm.title.encode('utf-8'), bm.page

if __name__ == '__main__':
    import sys
    info = get_info(sys.argv[1])
    print info.doc_title.encode('utf-8')
    print info.author.encode('utf-8')
    print info.pages
    print_bookmarks(info.bookmarks)

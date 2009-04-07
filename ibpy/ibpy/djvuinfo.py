#
# Copyright 2009 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

from util import *

class DJVUInfo(object):
    def __init__(self, doc_title, author, pages):
        object.__init__(self)
        self.doc_title = doc_title
        self.author = author
        self.pages = pages

class DJVUInfoParser(object):
    def __init__(self, config):
        object.__init__(self)
        self.djvu_fn = config.input_fn
    def parse(self):
        p = Popen(['djvused', '-e', 'n', self.djvu_fn], stdout = PIPE)
        pages = int(p.stdout.read())
        info = DJVUInfo('', '', pages)
        return (info, [])

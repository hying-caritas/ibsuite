#
# Copyright 2009 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import re
import types

from util import *

class Bookmark(object):
    def __init__(self, title = None, page = None):
        object.__init__(self)
        self.title = title
        self.page = page

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
    def get_outline(self):
        def parse_ol_list(lst):
            for i in lst:
                t = i[0]
                u = i[1]
                pn = 0
                if u.startswith('#'):
                    pn = int(u[1:])
                ol.append(Bookmark(t, pn))
                if len(i) > 2:
                    parse_ol_list(i[2:])
        p = Popen(['djvused', '-e', 'print-outline', self.djvu_fn],
                  stdout = PIPE)
        parser = Parser(p.stdout)
        ol_lst_p = parser.parse()
        if len(ol_lst_p) == 0:
            return []
        ol_lst = ol_lst_p[0]
        if len(ol_lst) == 0:
            return []
        assert(ol_lst[0][1] == 'bookmarks')

        ol = []
        parse_ol_list(ol_lst)
        return ol
    def get_pages(self):
        p = Popen(['djvused', '-e', 'n', self.djvu_fn], stdout = PIPE)
        return int(p.stdout.read())
    def get_meta(self):
        p = Popen(['djvused', '-e', 'print-meta', self.djvu_fn], stdout = PIPE)
        parser = Parser(p.stdout)
        m_lst = parser.parse()
        m_dic = {}
        for i, key in enumerate(m_lst):
            if i % 2 == 0:
                m_dic[key[1]] = m_lst[i+1]
        title = ''
        author = ''
        if m_dic.has_key('Title'):
            title = m_dic['Title']
        if m_dic.has_key('Author'):
            author = m_dic['Author']
        pages = self.get_pages()
        info = DJVUInfo(title, author, pages)
        return info
    def parse(self):
        return (self.get_meta(), self.get_outline())

class Lex(object):
    T_none = 0
    T_int = 1
    T_sym = 2
    T_str = 3
    T_bbrace = 4
    T_ebrace = 5
    T_end = 6
    re_int = re.compile(r'^[1-9][0-9]*')
    re_sym = re.compile(r'^[a-zA-Z_#][a-zA-Z_#\-0-9]*')
    re_spc = re.compile(r'^[\t\r\n ]')
    re_str = re.compile(r'^"([ -^a-~]+)"')
    re_str_esc1 = re.compile(r'\\([0-7]{1,3})')
    re_str_esc2 = re.compile(r'\\([abtnvfr\\])')
    esc2_dic = {
        'a' : '\a',
        'b' : '\b',
        't' : '\t',
        'n' : '\n',
        'v' : '\v',
        'f' : '\f',
        'r' : '\r',
        '\\' : '\\',
        }
    def __init__(self, inf):
        object.__init__(self)
        self.lineno = 0
        self.inf = inf
        self.line = ''
    def lex(self):
        def unesc_str(esc_str):
            def repl1(m):
                return chr(int(m.group(1), 8))
            def repl2(m):
                return Lex.esc2_dic[m.group(1)]
            esc_str2 = Lex.re_str_esc1.sub(repl1, esc_str)
            str = Lex.re_str_esc2.sub(repl2, esc_str2)
            return str

        while True:
            if self.line == '':
                self.lineno = self.lineno + 1
                self.line = self.inf.readline()
                if not self.line:
                    return (Lex.T_end, None)
            c = self.line[0]
            if c == '(':
                self.line = self.line[1:]
                return (Lex.T_bbrace, None)
            elif c == ')':
                self.line = self.line[1:]
                return (Lex.T_ebrace, None)
            m = Lex.re_int.search(self.line)
            if m:
                sval = m.group(0)
                self.line = self.line[m.end(0):]
                return (Lex.T_int, int(sval));
            m = Lex.re_sym.search(self.line)
            if m:
                self.line = self.line[m.end(0):]
                return (Lex.T_sym, m.group(0))
            m = Lex.re_str.search(self.line)
            if m:
                self.line = self.line[m.end(0):]
                esc_str = m.group(1)
                str = unesc_str(esc_str)
                ustr = str.decode('utf-8')
                return (Lex.T_str, ustr)
            m = Lex.re_spc.search(self.line)
            if m:
                self.line = self.line[m.end(0):]
                continue
            assert(0)

class Parser(object):
    def __init__(self, inf):
        object.__init__(self)
        self.lex = Lex(inf)
    def list(self, tstop):
        t, v = self.lex.lex()
        lst = []
        while t != tstop:
            if t == Lex.T_str:
                item = v
            elif t == Lex.T_int:
                item = v
            elif t == Lex.T_bbrace:
                item = self.list(Lex.T_ebrace)
            elif t == Lex.T_sym:
                item = (t, v)
            else:
                assert(0)
            lst.append(item)
            t, v = self.lex.lex()
        return lst
    def parse(self):
        return self.list(Lex.T_end)

if __name__ == '__main__':
    import sys
    p = Parser(sys.stdin)
    l = p.parse()
    print l

#!/usr/bin/python

import sys
import struct
import Image, ImageDraw

def mid(lst):
    return lst[len(lst) / 2]

def utf16n_to_utf8(n):
    s = struct.pack('H', n)
    return s.decode('utf16')

class Font(object):
    math_fonts = ['cmmi', 'cmsy', 'cmex']
    def __init__(self, name, height, asc, dsc):
        object.__init__(self)
        self.name = name
        self.height = height
        self.ascent = asc
        self.descent = dsc
        self.is_math_ = self.get_is_math()
    def get_ascent(self):
        b = abs(self.ascent) + abs(self.descent)
        return self.height * self.ascent / b
    def get_descent(self):
        b = abs(self.ascent) + abs(self.descent)
        return self.height * self.descent / b
    def get_is_math(self):
        for fn in Font.math_fonts:
            if self.name.startswith(fn):
                return True
        return False
    def is_math(self):
        return self.is_math_

class Char(object):
    def __init__(self, x, y, w, c, font):
        object.__init__(self)
        self.x = x
        self.y = y
        self.w = w
        self.c = c
        self.font = font
        self.is_math_symbol_ = self.get_is_math_symbol()
    def __cmp__(self, ach):
        return self.x - ach.x
    def bbox(self):
        return (self.x, self.y + self.font.get_ascent(),
                self.x + self.w, self.y + self.font.get_descent())
    def get_is_math_symbol(self):
        if self.c >= '0' and self.c <= '9':
            return True
        if self.c in '+-*/=().%#':
            return True
        return False
    def is_math(self):
        return self.font.is_math()
    def is_math_symbol(self):
        return self.is_math_symbol_

class Line(object):
    def __init__(self, base):
        object.__init__(self)
        self.chars = []
        self.base = base
    def __cmp__(self, aln):
        return self.base - aln.base
    def append_char(self, ch):
        self.chars.append(ch)
    def set_height(self):
        ascs = [ch.font.get_ascent() for ch in self.chars]
        dscs = [ch.font.get_descent() for ch in self.chars]
        ascs.sort()
        dscs.sort()
        self.ascent = mid(ascs)
        self.descent = mid(dscs)
        self.top = min(self.base + self.ascent, self.base + self.descent)
        self.bottom = max(self.base + self.ascent, self.base + self.descent)
    def overlap(self, aln):
        if self.top > aln.bottom or aln.top > self.bottom:
            return False
        return True
    def merge(self, aln):
        self.base = max(self.base, aln.base)
        self.top = min(self.top, aln.top)
        self.bottom = max(self.bottom, aln.bottom)
        self.chars.extend(aln.chars)
    def bbox(self):
        self.chars.sort()
        lft = self.chars[0].x
        lch = self.chars[-1]
        rt = lch.x + lch.w
        return (lft, self.top, rt, self.bottom)
    def is_math(self):
        ms = [int(ch.is_math()) for ch in self.chars]
        return sum(ms) / float(len(ms)) > 0.5

class Page(object):
    def __init__(self, doc, s):
        object.__init__(self)
        self.doc = doc
        self.lines = []
        self.parse(s)
    def find_line(self, ch):
        for ln in self.lines:
            if abs(ln.base - ch.y) < 0.1:
                return ln
        return None
    def add_line(self, ch):
        ln = Line(ch.y)
        self.lines.append(ln)
        return ln
    def parse(self, s):
        self.chars = []
        doc = self.doc
        font = None
        for l in s:
            ws = l.split(':')
            if ws[0] == 'char':
                x, y, w = [float(f)/self.width for f in ws[1:4]]
                nc = int(ws[-1])
                ch = Char(x, y, w, utf16n_to_utf8(nc), font)
                self.chars.append(ch)
            elif ws[0] == 'font':
                nm = ws[1]
                ht = float(ws[5]) / self.width
                asc, dsc = map(float, ws[6:8])
                font = doc.find_font(nm, ht)
                if font is None:
                    font = Font(nm, ht, asc, dsc)
                    doc.add_font(font)
            elif ws[0] == 'page':
                self.width = float(ws[1])
                self.height = float(ws[2])
        for ch in self.chars:
            ln = self.find_line(ch)
            if ln is None:
                ln = self.add_line(ch)
            ln.append_char(ch)
        self.lines.sort()
        for ln in self.lines:
            ln.set_height()
        eaten = []
        prev = None
        for i, ln in enumerate(self.lines):
            if prev and prev.overlap(ln):
                prev.merge(ln)
                eaten.append(i)
            else:
                prev = ln
        eaten.reverse()
        for i in eaten:
            del self.lines[i]
    def test1(self, fn):
        img = Image.open(fn)
        draw = ImageDraw.Draw(img)
        width = img.size[0]
        for ch in self.chars:
            chbox = [f * width for f in ch.bbox()]
            draw.rectangle(chbox, outline=128, fill=None)
        img.save('result_ch.png')
    def test2(self, fn):
        img = Image.open(fn)
        draw = ImageDraw.Draw(img)
        width = img.size[0]
        for ln in self.lines:
            lbox = [f * width for f in ln.bbox()]
            draw.rectangle(lbox, outline=128, fill=None)
        img.save('result_ln.png')
    def test3(self, fn):
        img = Image.open(fn)
        draw = ImageDraw.Draw(img)
        width = img.size[0]
        for ln in self.lines:
            if ln.is_math():
                lbox = [f * width for f in ln.bbox()]
                draw.rectangle(lbox, outline=128, fill=None)
        img.save('result_eqn.png')
    def test4(self, fn):
        img = Image.open(fn)
        draw = ImageDraw.Draw(img)
        width = img.size[0]
        for ch in self.chars:
            if ch.is_math() or ch.is_math_symbol():
                chbox = [f * width for f in ch.bbox()]
                draw.rectangle(chbox, outline=128, fill=None)
        img.save('result_eqn_ch.png')

class Doc(object):
    def __init__(self):
        object.__init__(self)
        self.fonts = []
    def find_font(self, font_name, font_height):
        for ft in self.fonts:
            if ft.name == font_name and \
                    abs(ft.height - font_height) < 0.1 * abs(ft.height):
                return ft
        return None
    def add_font(self, font):
        self.fonts.append(font)

if __name__ == '__main__':
    doc = Doc()
    page = Page(doc)
    page.parse(sys.stdin)
    fn = 'chap6-04.ppm'
    page.test1(fn)
    page.test2(fn)
    page.test3(fn)
    page.test4(fn)

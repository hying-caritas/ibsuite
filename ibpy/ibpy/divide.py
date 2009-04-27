#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import sys
import os
import copy
import Image, ImageDraw
from bisect import bisect_left

from util import *

class Char(object):
    def __init__(self, pair):
        object.__init__(self)
        self.pair = pair
        self.is_word_end_ = False
    def width(self):
        return self.pair[1] - self.pair[0]
    def set_space(self, prev, next):
        if prev:
            self.bc = self.pair[0] - prev.pair[1]
        else:
            self.bc = 0
        if next:
            self.ac = next.pair[0] - self.pair[1]
        else:
            self.ac = 0
    def set_word_end(self):
        self.is_word_end_ = True
    def is_word_end(self):
        return self.is_word_end_
    def __cmp__(self, ach):
        if self.pair[1] < ach.pair[1]:
            return -1
        else:
            return 1

class Seg(object):
    def __init__(self, line, bbox, bl, al, bh, ah):
        object.__init__(self)
        self.line = line
        self.bbox = bbox
        self.bl = bl
        self.al = al
        self.bh = bh
        self.ah = ah
        self.img = None
        self.porg_ = [0, 0]
        self.out_x = 0
        self.is_line_end_ = False
    def set_line_end(self):
        self.is_line_end_ = True
    def is_line_end(self):
        return self.is_line_end_
    def scale(self):
        page = self.line.page
        doc = page.doc
        opedge_ex = doc.opedge_ex
        edge_ex = page.opxl2norm(opedge_ex)

        ebbox = self.bbox[:]
        ebbox[0] = max(ebbox[0] - edge_ex, 0)
        ebbox[1] = max(ebbox[1] - edge_ex, 0)
        ebbox[2] = min(ebbox[2] + edge_ex, page.image_width())
        ebbox[3] = min(ebbox[3] + edge_ex, page.image_height())

        ow_norm = page.width_after_divide()
        oh_norm = page.opxl2norm(doc.out_size[1] - 2*doc.margin - \
                                     2*opedge_ex - 1)
        cw = ebbox[2] - ebbox[0]
        ch = ebbox[3] - ebbox[1]

        scale_factor_org = (cw - ow_norm) / cw
        rotate = False
        expand = False
        rbbox = ebbox[:]
        if scale_factor_org > 0.1 and self.height() > 2 * doc.avg_lh:
            if ow_norm / ch > oh_norm / cw:
                expand = True
                scale_factor_rot = (cw - oh_norm) / cw
                rw = oh_norm / cw * ch
                rh = oh_norm
                che = (cw / rh) * ow_norm
                rbbox[1] = max(rbbox[1] - (che - ch)/2, 0)
                rbbox[3] = min(rbbox[3] + (che - ch)/2, page.image_height())
                che = rbbox[3] - rbbox[1]
                rwe = oh_norm / cw * che
                etop = oh_norm / cw * (self.bbox[1] - rbbox[1] - self.line.bl/2)
                ebtm = oh_norm / cw * (self.bbox[3] - rbbox[1] + self.line.al/2)
                etop = max(etop, 0)
                ebtm = min(ebtm, rwe)
            else:
                scale_factor_rot = (ch - ow_norm) / ch
                rw = ow_norm
                rh = ow_norm / ch * cw
                rwe = rw
            if (rh - ow_norm) / ow_norm > 0.1:
                rotate = True
        rimg = page.rcrop(rbbox)
        if rotate:
            sw = rwe
            sh = rh
            rimg = rimg.rotate(90)
            self.scale_factor = scale_factor_rot
        else:
            sw = ow_norm
            sh = ow_norm / cw * ch
            self.scale_factor = scale_factor_org
        psw = nround(page.norm2opxl(sw))
        psh = nround(page.norm2opxl(sh))
        self.img = rimg.resize((psw, psh), Image.ANTIALIAS)
        if expand:
            draw = ImageDraw.Draw(self.img)
            petop = nround(page.norm2opxl(etop))
            pebtm = nround(page.norm2opxl(ebtm))
            draw.line(((petop, 0), (petop, psh)), fill = 0)
            draw.line(((pebtm, 0), (pebtm, psh)), fill = 0)
        self.bbox[0] = page.opxl2norm(doc.margin)
        self.bbox[2] = self.bbox[0] + sw
        self.bbox[3] = self.bbox[1] + sh
    def width(self):
        return self.bbox[2] - self.bbox[0]
    def height(self):
        return self.bbox[3] - self.bbox[1]
    def pwidth(self):
        return self.line.page.norm2opxl(self.bbox[2] - self.bbox[0])
    def pheight(self):
        return self.line.page.norm2opxl(self.bbox[3] - self.bbox[1])
    def get_page(self):
        return self.line.page
    def porg(self):
        return self.porg_
    def get_img(self, ry, h):
        page = self.line.page
        doc = page.doc
        if self.img is None:
            edge_ex = page.edge_ex()
            ebbox = self.bbox[:]
            bl = min(self.bl/2, edge_ex)
            al = min(self.al/2, edge_ex)
            ebbox[1] = max(ebbox[1] - bl, 0)
            ebbox[3] = min(ebbox[3] + al, page.image_height())
            bh = min(self.bh/2, edge_ex)
            ah = min(self.ah/2, edge_ex)
            ebbox[0] = max(ebbox[0] - bh, 0)
            ebbox[2] = min(ebbox[2] + ah, page.image_width())
            self.porg_[0] = nround(page.norm2opxl(self.bbox[0] - ebbox[0]))
            self.porg_[1] = nround(page.norm2opxl(self.bbox[1] - ebbox[1]))
            self.img = self.line.page.ocrop(ebbox)
        ph = self.pheight()
        iw, ih = self.img.size
        yo = self.porg_[1]
        if ry == 0:
            if h >= ph:
                return self.img
            else:
                return self.img.crop([0, 0, iw, h + yo])
        else:
            if ry + yo + h >= ph:
                y2 = ih
            else:
                y2 = ry + yo + h
            return self.img.crop([0, ry + yo, iw, y2])

class SegPart(object):
    def __init__(self, seg, sy):
        self.seg = seg
        self.sy = sy
        self.pout_bl = self.seg.pout_bl
        self.pout_x = self.seg.pout_x
    def is_line_end(self):
        return self.seg.is_line_end()
    def pwidth(self):
        return self.seg.pwidth()
    def pheight(self):
        return self.seg.pheight() - self.sy
    def get_page(self):
        return self.seg.get_page()
    def porg(self):
        return self.seg.porg()
    def get_img(self, ry, h):
        return self.seg.get_img(self.sy + ry, h)

HALIGN_LEFT = 0
HALIGN_RIGHT = 1
HALIGN_BOTH = 2
HALIGN_INDENT = 3
HALIGN_NORMAL = 3
HALIGN_CENTER = 4
HALIGN_STRICT_CENTER = 5
HALIGN_NUM_EQN = 6

class TextFormat(object):
    def __init__(self, ln):
        object.__init__(self)
        self.left = max(ln.bbox[0], 0.001)
        self.height = ln.height()
        self.acw = ln.avg_char_width()
    def conform(self, ln):
        ln_lft = ln.bbox[0]
        lh = ln.height()
        ln_acw = ln.avg_char_width()
        if abs(ln_lft - self.left) / self.left > 0.1:
            return False
        if abs(lh - self.height) / self.height > 0.5:
            return False
        if abs(ln_acw - self.acw) / self.acw > 0.8:
            return False
        return True
    def dump(self):
        print self.left, self.height, self.acw

class Line(object):
    def __init__(self, page, bbox):
        object.__init__(self)
        self.page = page
        self.bbox = bbox
        self.chars = []
        self.bl = 0
        self.al = 0
        self.is_figure_ = False
        self.sub_lines = []
        self.is_expand_ = False
        self.segs = []
        self.halign_ = HALIGN_LEFT
        self.blur_chars = []
    def __deepcopy__(self, memo):
        ln = copy.copy(self)
        ln.bbox = self.bbox[:]
        ln.chars = copy.deepcopy(self.chars, memo)
        ln.sub_lines = copy.deepcopy(self.sub_lines, memo)
        ln.segs = copy.deepcopy(self.segs, memo)
        ln.blur_chars = copy.deepcopy(self.blur_chars, memo)
        return ln
    def height(self):
        return self.bbox[3] - self.bbox[1]
    def width(self):
        return self.bbox[2] - self.bbox[0]
    def halign(self):
        return self.halign_
    def count_chars(self):
        return len(self.chars)
    def is_eqn(self):
        if self.halign_ == HALIGN_NUM_EQN:
            return True
        else:
            return False
    def is_center(self):
        if self.halign_ == HALIGN_CENTER or \
                self.halign_ == HALIGN_STRICT_CENTER:
            return self.halign_
        else:
            return False
    def is_thin(self):
        lh = self.page.doc.avg_lh
        if self.height() < 0.6 * lh:
            return True
        else:
            return False
    def is_compound(self):
        return len(self.sub_lines) != 0
    def merge_width(self, aln):
        return max(self.bbox[2], aln.bbox[2]) - min(self.bbox[0], aln.bbox[0])
    def prepare_merge(self):
        if len(self.sub_lines) == 0:
            ln = copy.deepcopy(self)
            self.sub_lines = [ln]
    def merge(self, aln):
        self.prepare_merge()
        if self.bbox[1] > aln.bbox[1]:
            self.sub_lines.insert(0, aln)
            self.bl = aln.bl
            self.bbox[1] = aln.bbox[1]
        else:
            self.sub_lines.append(aln)
            self.al = aln.al
            self.bbox[3] = aln.bbox[3]
        self.bbox[0] = min(self.bbox[0], aln.bbox[0])
        self.bbox[2] = max(self.bbox[2], aln.bbox[2])
        self.merge_chars(aln)
        self.set_chars_space()
    def merge_chars(self, aln):
        chars = []
        schars = self.chars
        achars = aln.chars
        snch = len(schars)
        anch = len(achars)
        i = 0
        j = 0
        lft = schars[0].pair[0]
        while i < snch and j < anch:
            sch = schars[i]
            ach = achars[j]
            lft = min(lft, sch.pair[0], ach.pair[0])
            if sch.pair[1] < ach.pair[0]:
                rt = sch.pair[1]
                ch = Char([lft, rt])
                chars.append(ch)
                lft = ach.pair[0]
                i = i + 1
            elif ach.pair[1] < sch.pair[0]:
                rt = ach.pair[1]
                ch = Char([lft, rt])
                chars.append(ch)
                lft = sch.pair[0]
                j = j + 1
            elif sch.pair[1] == ach.pair[1]:
                rt = sch.pair[1]
                ch = Char([lft, rt])
                chars.append(ch)
                i = i + 1
                j = j + 1
                lft = self.bbox[2]
            elif sch.pair[1] > ach.pair[1]:
                rt = sch.pair[1]
                j = j + 1
            elif ach.pair[1] > sch.pair[1]:
                rt = ach.pair[1]
                i = i + 1
        if lft < rt:
            ch = Char([lft, rt])
            chars.append(ch)
            if i < snch and schars[i].pair[1] == rt:
                i = i + 1
            elif j < anch and achars[j].pair[1] == rt:
                j = j + 1
        while i < snch:
            chars.append(schars[i])
            i = i + 1
        while j < anch:
            chars.append(achars[j])
            j = j + 1
        self.chars = chars
    def get_sparse_char(self):
        schars = sorted(self.chars, None, lambda c: c.ac, True)
        ch = schars[0]
        if ch.ac > self.page.doc.avg_lh:
            return ch
        else:
            return None
    def is_sparse(self):
        return not (self.get_sparse_char() is None)
    def get_ink_width(self):
        cws = [c.width() for c in self.chars]
        return sum(cws)
    def avg_char_width(self):
        return self.get_ink_width() / float(len(self.chars))
    def is_intense(self):
        if self.get_ink_width() / float(self.width()) > 0.95 and \
                len(self.chars) < 3:
            return True
        else:
            return False
    def is_short(self):
        if self.width() / float(self.page.width()) < 0.4:
            return True
        else:
            return False
    def get_halign(self):
        page = self.page
        pg_lft = page.bbox[0]
        pg_rt = page.bbox[2]
        avg_ln_lft = pg_lft + page.doc.avg_rln_lft
        avg_lh = page.doc.avg_lh
        thr_inl = avg_lh * 3 / 2 # threshhold indent low
        thr_inh = avg_lh * 5 / 2 # threshhold indent high
        rspc = pg_rt - self.bbox[2]
        lspc = min(abs(self.bbox[0] - pg_lft), abs(self.bbox[0] - avg_ln_lft))
        ch = self.get_sparse_char()
        if not ch is None:
            arspc = ch.ac
        else:
            arspc = rspc
        if lspc < thr_inl:
            if rspc < thr_inl:
                return HALIGN_BOTH
            else:
                return HALIGN_LEFT
        if rspc < thr_inl and arspc < thr_inl:
            if lspc < thr_inh:
                return HALIGN_INDENT
            else:
                return HALIGN_RIGHT
        if abs(lspc - rspc) / float(lspc) < 0.25:
            return HALIGN_STRICT_CENTER
        if rspc != arspc and abs(lspc - arspc) / float(lspc) < 0.25:
            return HALIGN_NUM_EQN
        if lspc > thr_inh and rspc > thr_inh:
            return HALIGN_CENTER
        return HALIGN_LEFT
    def fix_halign(self, text_format):
        self.halign_ = HALIGN_INDENT
    def blur(self):
        bf = self.page.doc.avg_lh
        self.blur_chars = []
        ch = self.chars[0]
        cl = ch.pair[0]
        cr = ch.pair[1]
        for ch in self.chars[1:]:
            if ch.pair[0] - cr < bf:
                cr = ch.pair[1]
                continue
            else:
                bch = Char([cl, cr])
                self.append_blur_char(bch)
                cl = ch.pair[0]
                cr = ch.pair[1]
        bch = Char([cl, cr])
        self.append_blur_char(bch)
        bchars = self.blur_chars[:]
        bchars.insert(0, None)
        bchars.append(None)
        for i, bch in enumerate(bchars[1:-1]):
            bch.set_space(bchars[i], bchars[i+2])
    def cover(self, aln):
        bf = self.page.doc.avg_lh
        bchars = self.blur_chars
        nch = len(bchars)
        i = 0
        for ach in aln.chars:
            while i < nch:
                bch = bchars[i]
                if bch.pair[1] + bf > ach.pair[0]:
                    break
                i = i + 1
            if i == nch:
                return False
            if bch.pair[0] - bf > ach.pair[0] or bch.pair[1] + bf < ach.pair[1]:
                return False
        return True
    def set_figure(self):
        self.is_figure_ = True
    def is_figure(self):
        return self.is_figure_
    def set_expand(self):
        self.is_expand_ = True
    def is_expand(self):
        return self.is_expand_
    def is_center_figure(self):
        return self.is_figure_ and (self.is_center() or \
                                        self.halign_ == HALIGN_BOTH)
    def to_seg(self):
        seg = Seg(self, self.bbox[:], self.bl, self.al, self.bbox[0], \
                      self.page.image_width() - self.bbox[2])
        seg.set_line_end()
        return seg
    def set_space(self, prev, next):
        if prev:
            self.bl = self.bbox[1] - prev.bbox[3]
        else:
            self.bl = self.bbox[1]
        if next:
            self.al = next.bbox[1] - self.bbox[3]
        else:
            self.al = self.page.image_height() - self.page.bbox[3]
        self.set_chars_space()
        self.halign_ = self.get_halign()
        self.set_word_end()
    def set_word_end(self):
        pchars = self.chars[:-1]
        npch = len(pchars)
        if npch <= 5:
            return
        pchars = sorted(pchars, None, lambda c: c.ac, True)
        acs = [c.ac for c in pchars]
        avg_ac = sum(acs) / float(npch)
        wchars = pchars[:(npch+2)/3]
        thr = avg_ac * 1.2
        wchars = [ch.ac > thr and ch for ch in wchars]
        for ch in wchars:
            if ch:
                ch.set_word_end()
    def print_word_end(self):
        for ch in self.chars:
            if ch.is_word_end():
                print ch.pair[1],
    def set_chars_space(self):
        chars = self.chars[:]
        chars.insert(0, None)
        chars.append(None)
        for i, ch in enumerate(chars[1:-1]):
            ch.set_space(chars[i], chars[i+2])
        self.blur()
    def append_char(self, ch):
        self.chars.append(ch)
    def append_blur_char(self, bch):
        self.blur_chars.append(bch)
    def append_seg(self, seg):
        self.segs.append(seg)
    def divide(self):
        doc = self.page.doc
        npw = self.page.width_after_divide()
        self.segs = []
        if self.is_figure():
            is_scale = self.width() > npw
            scale_much = False
            is_expand = self.is_expand()
            sub_lines = self.sub_lines

            seg = self.to_seg()
            if is_scale:
                seg.scale()
                if seg.scale_factor > 0.2:
                    scale_much = True
            self.append_seg(seg)

            if not is_expand and scale_much and len(sub_lines) > 1:
                fl = sub_lines[0]
                if not fl.is_figure() and not fl.is_sparse() and \
                        not fl.is_short():
                    fl.real_divide()
            if not is_expand and scale_much and len(sub_lines) > 1:
                ll = sub_lines[-1]
                if not ll.is_figure() and not ll.is_sparse() and \
                        not ll.is_short():
                    ll.real_divide()

            if scale_much and is_expand:
                for l in sub_lines:
                    l.real_divide()
            return
        self.real_divide()
    def real_divide(self):
        doc = self.page.doc
        flex = doc.flex_coeff
        divide = doc.divide
        pg_width = self.page.width()

        ln_lft = self.bbox[0]
        ln_rt = self.bbox[2]
        ln_width = ln_rt - ln_lft;
        lh = self.height()
        pg_lft = self.page.bbox[0]
        nrln_lft = (ln_lft - pg_lft) / divide
        npw = self.page.width_after_divide()

        if nrln_lft + ln_width < npw:
            seg = self.to_seg()
            self.append_seg(seg)
            return
        if self.is_center() and self.is_compound() and ln_width < npw:
            seg = self.to_seg()
            self.append_seg(seg)
            return
        sy = self.bbox[1]
        ey = self.bbox[3]
        pdx = ln_lft
        ach = Char([0, 0]) # anchor char
        il = min(self.al, self.bl, lh / 2)
        bl = self.bl
        pdw = ln_lft
        dw = 0
        for n in range(1, divide):
            m = ln_lft
            ha = self.halign()
            if ha == HALIGN_LEFT or ha == HALIGN_BOTH or ha == HALIGN_INDENT:
                # (pg_width / divide - nrln_lft) * n
                m = m + pg_width * n / divide - nrln_lft * n
            else:
                m = m + ln_width * n / divide
            if m <= pdx:
                continue
            elif m >= ln_rt:
                break
            sx = max(m - flex, ln_lft)
            ex = min(m + flex, ln_rt)
            ach.pair = [sx, sx]
            ics = bisect_left(self.chars, ach)
            ach.pair = [ex, ex]
            ice = bisect_left(self.chars, ach)
            dx = m
            dw = 0
            wch = None
            for ch in self.chars[ics: ice]:
                cdx = ch.pair[1] + ch.ac / 2
                if wch:
                    if ch.is_word_end() and abs(cdx - m) < abs(dx - m):
                        wch = ch
                        dx = cdx
                        dw = ch.ac
                elif ch.is_word_end():
                    wch = ch
                    dx = cdx
                    dw = ch.ac
                elif (ch.ac > dw or (ch.ac == dw and \
                                         abs(cdx - m) < abs(dx - m))):
                    dx = cdx
                    dw = ch.ac
            seg = Seg(self, [pdx, sy, dx - dw/2, ey], bl, il, pdw, dw)
            self.append_seg(seg)
            bl = il
            pdx = dx + dw / 2
            pdw = dw
        if pdx < ln_rt:
            seg = Seg(self, [pdx, sy, ln_rt, ey], il, self.al, pdw,
                      self.page.image_width() - ln_rt)
            self.append_seg(seg)
    def has_sub_seg(self):
        for sl in self.sub_lines:
            if len(sl.segs) != 0:
                return True
        return False
    def draw_words_outline(self, draw):
        wb = self.bbox[:]
        left = -1
        for ch in self.chars:
            if left == -1:
                left = ch.pair[0]
            if ch.is_word_end():
                wb[0] = left
                wb[2] = ch.pair[1]
                draw.rectangle(wb, outline=128, fill=None)
                left = -1
        if left != -1:
            wb[0] = left
            wb[2] = self.chars[-1].pair[1]
            draw.rectangle(wb, outline=128, fill=None)
    def save(self, fn):
        img = self.page.img.crop(self.bbox)
        img.save(fn)
    def print_chars(self):
        for ch in self.chars:
            print ch.pair,
        print 'blur:',
        for bch in self.blur_chars:
            print bch.pair,
        print

class PageStat(object):
    def __init__(self, avg_lh, avg_il, avg_cpl, avg_rln_lft):
        object.__init__(self)
        self.avg_lh = avg_lh
        self.avg_il = avg_il
        self.avg_cpl = avg_cpl
        self.avg_rln_lft = avg_rln_lft

class BasicPage(object):
    def __init__(self, doc, page_no):
        object.__init__(self)
        self.doc = doc
        self.page_no = page_no
        self.opxl2norm_coeff = None
        self.norm2opxl_coeff = None
    def width(self):
        return max(self.bbox[2] - self.bbox[0], 0.333)
    def height(self):
        return self.bbox[3] - self.bbox[1]
    def image_width(self):
        return 1.
    def image_height(self):
        return self.image_height_
    def width_after_divide(self):
        doc = self.doc
        divide = doc.divide
        flex = doc.flex_coeff
        if divide == 1:
            npw = self.width()
        elif divide == 2:
            npw = self.width() / divide + flex
        else:
            npw = self.width() / divide + 2 * flex
        return npw
    def opxl2norm(self, op):
        if self.opxl2norm_coeff is None:
            npw = self.width_after_divide()
            doc = self.doc
            ow = doc.out_size[0] - 2 * doc.margin - 2 * doc.opedge_ex
            if hasattr(self, "img"):
                iw = self.norm2rpxl(npw)
            else:
                iw = 0
            if ow >= iw:
                ow = iw
            self.opxl2norm_coeff = npw / ow
        return op * self.opxl2norm_coeff
    def norm2opxl(self, norm):
        if self.norm2opxl_coeff is None:
            npw = self.width_after_divide()
            doc = self.doc
            ow = doc.out_size[0] - 2 * doc.margin - 2 * doc.opedge_ex
            if hasattr(self, "img"):
                iw = self.norm2rpxl(npw)
            else:
                iw = 0
            if ow >= iw:
                ow = iw
            self.norm2opxl_coeff = ow / npw
        return norm * self.norm2opxl_coeff
    def edge_ex(self):
        opedge_ex = self.doc.opedge_ex
        return self.opxl2norm(opedge_ex)
    def norm2rpxl(self, norm):
        return norm * self.img.size[0]
    def render(self, pimg_ref):
        self.img = pimg_ref.get_image()
        iw, ih = self.img.size
        sw = self.norm2opxl(self.image_width())
        sh = self.norm2opxl(self.image_height())
        if abs(iw - sw) < 0.1 and abs(ih - sh) < 0.1:
            self.scaled_img = self.img
        else:
            sw = nround(sw)
            sh = nround(sh)
            self.scaled_img = self.img.resize((sw, sh), Image.ANTIALIAS)
    def rcrop(self, bbox):
        pbbox = map(lambda x: nround(self.norm2rpxl(x)), bbox)
        return self.img.crop(pbbox)
    def ocrop(self, bbox):
        pbbox = map(lambda x: nround(self.norm2opxl(x)), bbox)
        return self.scaled_img.crop(pbbox)
    def parse(self, pimg_ref):
        def append_line(ln):
            self.lines.append(ln)
        def ipxl2norm(pxl):
            return float(pxl) / iw
        p = Popen(['iblineparser', pimg_ref.get_file_name()], stdout = PIPE)
        img = pimg_ref.get_image()
        iw, ih = img.size
        self.image_height_ = float(ih) / iw
        self.lines = []
        for l in p.stdout:
            ws = l.split()
            if  ws[0] == 'char':
                pair = map(ipxl2norm, ws[1:])
                ch = Char(pair)
                ln.append_char(ch)
            elif ws[0] == 'line':
                bbox = map(ipxl2norm, ws[1:])
                ln = Line(self, bbox)
                append_line(ln)
            else:
                self.bbox = map(ipxl2norm, ws[1:])
        self.set_space()
    def add_text_formats(self):
        doc = self.doc
        for ln in self.lines:
            if ln.is_intense() or ln.is_sparse():
                continue
            halign = ln.halign()
            if (halign == HALIGN_BOTH or halign == HALIGN_RIGHT \
                    or halign == HALIGN_INDENT):
                tf = doc.find_text_format(ln)
                if tf is None:
                    ntf = TextFormat(ln)
                    doc.add_text_format(ntf)
    def fix_lines_halign(self):
        doc = self.doc
        for ln in self.lines:
            ha = ln.halign()
            if ha == HALIGN_CENTER:
                tf = doc.find_text_format(ln)
                if tf:
                    ln.fix_halign(tf)
    def set_space(self):
        lines = self.lines[:]
        lines.insert(0, None)
        lines.append(None)
        for i, ln in enumerate(lines[1:-1]):
            ln.set_space(lines[i], lines[i+2])
    def bound_line(self, y1, y2):
        bl = None
        for ln in self.lines:
            if ln.bbox[3] > y1 and ln.bbox[1] < y2:
                if bl:
                    bl.merge(ln)
                else:
                    bl = ln
        if bl is None:
            d = self.height()
            ym = (y1 + y2) / 2
            for ln in self.lines:
                yl = (ln.bbox[1] + ln.bbox[3]) / 2
                if abs(yl - ym) < d:
                    d = abs(yl - ym)
                    bl = ln
        return bl
    def get_stat(self):
        if len(self.lines) == 0:
            return None
        lhs = map(lambda l: l.height(), self.lines)
        ils = map(lambda l: l.al, self.lines)
        cpls = map(lambda l: l.count_chars(), self.lines)
        rln_lfts = [l.bbox[0] - self.bbox[0] for l in self.lines]
        avg_lh = middle(lhs)
        avg_il = middle(ils)
        avg_cpl = middle(cpls)
        avg_rln_lft = middle(rln_lfts)
        return PageStat(avg_lh, avg_il, avg_cpl, avg_rln_lft)
    def save_words_outline(self):
        cimg = self.img.copy()
        draw = ImageDraw.Draw(cimg)
        for ln in self.lines:
            ln.draw_words_outline(draw)
        cimg.save('out/words_outline.png')
    def save_lines_outline(self):
        cimg = self.img.copy()
        draw = ImageDraw.Draw(cimg)
        for ln in self.lines:
            draw.rectangle(ln.bbox, outline=128, fill=None)
        cimg.save('out/lines_outline.png')
    def save_lines(self):
        for i, ln in enumerate(self.lines):
            print i,
            print ln.print_word_end()
            print
            ln.save('out/line-%d.png' % (i,))

class Page(BasicPage):
    def __init__(self, doc, page_no):
        BasicPage.__init__(self, doc, page_no)
    def hl_parse(self):
        doc = self.doc
        self.mark_figure_by_height()
        if doc.fix_figure_by_vspace:
            self.fix_figure_by_vspace()
        if doc.fix_figure_by_halign:
            self.fix_figure_by_halign()
        self.fix_ij()
        self.fix_underscore()
        self.fix_equation()
        if doc.merge_center:
            self.merge_center()
        if doc.merge_sparse:
            self.merge_sparse()
        self.mark_figure_by_intense()
    def merge_center(self):
        lines = self.lines
        n = 0
        nln = len(lines)
        npw = self.width_after_divide()
        eaten = []
        while n < nln:
            ln = lines[n]
            if (ln.is_center() or ln.is_eqn()) and not ln.is_figure():
                ln.prepare_merge()
                n = n + 1
                while n < nln:
                    aln = lines[n]
                    if (aln.is_center() or aln.is_eqn()) and \
                            not aln.is_figure():
                        ln.merge(aln)
                        eaten.append(n)
                        n = n + 1
                    else:
                        break
                ln.set_figure()
                ln.set_expand()
            else:
                n = n + 1
        eaten.reverse()
        for n in eaten:
            del lines[n]
    def merge_sparse(self):
        lines = self.lines
        n = 0
        nln = len(lines)
        eaten = []
        while n < nln:
            ln = lines[n]
            if ln.is_sparse() and not ln.is_figure():
                n = n + 1
                multi_ln = False
                while n < nln:
                    aln = lines[n]
                    if aln.is_sparse() and not aln.is_figure():
                        ln.merge(aln)
                        eaten.append(n)
                        multi_ln = True
                        n = n + 1
                    else:
                        break
                if multi_ln:
                    ln.set_figure()
                    ln.set_expand()
            else:
                n = n + 1
        eaten.reverse()
        for n in eaten:
            del lines[n]
    def fix_ij(self):
        while self.fix_ij_one() != 0:
            pass
    def fix_ij_one(self):
        nlh = self.doc.avg_lh
        ilh = nlh / 3
        lines = self.lines
        nln = len(lines)

        eaten = []
        for i, ln in enumerate(lines):
            if ln.height() < ilh:
                aln = None
                if ln.al <= ilh and i < nln - 1:
                    aln = lines[i + 1]
                elif ln.bl <= ilh and i > 0:
                    aln = lines[i - 1]
                if aln and aln.cover(ln) and \
                        ln.get_ink_width() < 0.5 * aln.get_ink_width():
                    aln.merge(ln)
                    eaten.append(i)
        eaten.reverse()
        for i in eaten:
            del lines[i]
        return len(eaten)
    def fix_underscore(self):
        while self.fix_underscore_one() != 0:
            pass
    def fix_underscore_one(self):
        ulh = self.doc.avg_lh / 2
        lines = self.lines
        nln = len(lines)

        eaten = []
        for i, ln in enumerate(lines):
            if ln.height() <= ulh:
                aln = None
                if ln.bl * 5 <= ln.al * 4 and i > 0 and \
                        ln.bl < lines[i-1].height() * 0.5:
                    aln = lines[i - 1]
                elif ln.al * 5 <= ln.bl * 4 and i < nln - 1 and \
                        ln.al < lines[i+1].height() * 0.5:
                    aln = lines[i + 1]
                if aln and aln.cover(ln) and ln.width() < aln.width():
                    aln.merge(ln)
                    eaten.append(i)
        eaten.reverse()
        for i in eaten:
            del lines[i]
        return len(eaten)
    def fix_equation(self):
        while self.fix_equation_one() != 0:
            pass
    def fix_equation_one(self):
        nlh = self.doc.avg_lh
        sil = self.doc.avg_il / 2
        elh = nlh * 5 / 4
        lines = self.lines
        nln = len(lines)

        eaten = []
        for i, ln in enumerate(lines):
            if ln.height() <= nlh:
                aln = None
                if i > 0 and (ln.bl * 5 <= ln.al * 4 or ln.bl <= sil):
                    aln = lines[i - 1]
                if aln is None and i < nln - 1 and \
                        (ln.al * 5 <= ln.bl * 4 or ln.al <= sil):
                    aln = lines[i + 1]
                if aln and aln.height() > elh and aln.cover(ln) and \
                        ln.get_ink_width() < 0.5 * aln.get_ink_width():
                    aln.merge(ln)
                    eaten.append(i)
        eaten.reverse()
        for i in eaten:
            del lines[i]
        return len(eaten)
    def mark_figure_by_height(self):
        doc = self.doc
        hfig = 3 * (doc.avg_lh + doc.avg_il)
        # line which is too high is considered figure
        for ln in self.lines:
            if ln.height() > hfig:
                ln.set_figure()
    def mark_figure_by_intense(self):
        doc = self.doc
        # line which is too high is considered figure
        for ln in self.lines:
            if not ln.is_figure() and ln.is_intense() and not ln.is_thin():
                ln.set_figure()
                ln.prepare_merge()
                ln.set_expand()
    def fix_figure_by_halign(self):
        lines = self.lines

        nln = len(lines)
        n = 0
        eaten = []
        while n < nln:
            ln = lines[n]
            if ln.is_center_figure():
                eatent = []
                for i in range(n-1, -1, -1):
                    aln = lines[i]
                    if (aln.is_short() or aln.is_sparse()) and \
                            (aln.is_center() or aln.is_center_figure()):
                        ln.merge(lines[i])
                        eatent.append(i)
                    else:
                        break
                eatent.reverse()
                eaten.extend(eatent)
                n = n + 1
                while n < nln:
                    aln = lines[n]
                    if (aln.is_short() or aln.is_sparse()) and \
                            (aln.is_center() or aln.is_center_figure()):
                        ln.merge(lines[n])
                        eaten.append(n)
                        n = n + 1
                    else:
                        n = n + 1
                        break
            else:
                n = n + 1
        eaten.reverse()
        for i in eaten:
            del lines[i]
    def fix_figure_by_vspace(self):
        il = self.doc.avg_il
        ilf = 1.8 * il  # vspace for figure
        lines = self.lines
        nln = len(lines)
        n = 0
        eaten = []
        while n < nln:
            ln = lines[n]
            if ln.is_figure():
                eatent = []
                for i in range(n-1, -1, -1):
                    aln = lines[i]
                    if aln.al < ilf:
                        ln.merge(lines[i])
                        eatent.append(i)
                    else:
                        break
                eatent.reverse()
                eaten.extend(eatent)
                n = n + 1
                while n < nln:
                    aln = lines[n]
                    if aln.bl < ilf:
                        ln.merge(lines[n])
                        eaten.append(n)
                        n = n + 1
                    else:
                        n = n + 1
                        break
            else:
                n = n + 1
        eaten.reverse()
        for i in eaten:
            del lines[i]
    def divide(self):
        def set_segs_line_end():
            for ln in self.lines:
                ln.segs[-1].set_line_end()
                if ln.has_sub_seg():
                    for sl in ln.sub_lines:
                        if len(sl.segs) >= 1:
                            sl.segs[-1].set_line_end()

        for ln in self.lines:
            ln.divide()
        set_segs_line_end()
    def set_output_left(self):
        ph = self.image_height()
        divide = self.doc.divide
        npw = self.width_after_divide()
        pg_lft = self.bbox[0]
        pg_rt = self.bbox[2]
        lines = self.lines

        def set_line_left(ln):
            ln_lft = ln.bbox[0]
            nln_lft = (ln_lft - pg_lft) / divide
            for seg in ln.segs:
                sw = seg.width()
                if nln_lft + sw > npw:
                    if ln.is_center():
                        nln_lft = max((npw - sw) / 2, 0)
                    else:
                        nln_lft = max(npw - sw, 0)
                seg.out_x = nln_lft

        def fix_indent_first_line():
            avg_lh = self.doc.avg_lh
            avg_il = self.doc.avg_il
            nln = len(lines)
            i = 0
            while i < nln - 1:
                ln = lines[i]
                next = lines[i+1]
                nalg = next.halign()
                alg = ln.halign()
                lh = ln.height()
                nh = next.height()
                ln_lft = ln.bbox[0]
                n_lft = next.bbox[0]
                ln_rt = ln.bbox[2]
                if abs(ln_lft - n_lft) > avg_lh / 2 and \
                        abs(ln_lft - n_lft) < avg_lh * 7 / 2 and \
                        alg <= HALIGN_NORMAL and nalg <= HALIGN_NORMAL and \
                        abs(pg_rt - ln_rt) < avg_lh / 2 and \
                        abs(nh - lh) < 0.4 * min(lh, ph) and \
                        ln.al <= 1.3 * avg_il:
                    i = i + 1
                    nx = next.segs[0].out_x
                    for seg in ln.segs[1:]:
                        sw = seg.width()
                        if nx + sw > npw:
                            break
                        seg.out_x = nx
                i = i + 1

        for ln in lines:
            set_line_left(ln)
            if ln.has_sub_seg():
                for sl in ln.sub_lines:
                    set_line_left(sl)

        fix_indent_first_line()
    def output(self):
        def output_line(ln, il):
            if len(ln.segs) == 0:
                return
            seg = ln.segs[0]
            seg.out_bl = il
            out_segs.append(seg)
            is_il = min(il, ln.bl, ln.al)
            for seg in ln.segs[1:]:
                seg.out_bl = is_il
                out_segs.append(seg)
        def output_hline(il):
            out_segs.append(HLine(self, il))

        out_segs = []
        ph = self.image_height()
        max_il = ph * self.doc.max_il_coeff
        alh = self.doc.avg_lh
        self.set_output_left()
        il = 0
        for ln in self.lines:
            has_sub_seg = ln.has_sub_seg()
            if has_sub_seg:
                output_hline(il)

            in_il = min(alh, il)
            output_line(ln, in_il)
            il = min(ln.al, max_il)

            in_il = min(alh, il)
            if has_sub_seg:
                output_hline(in_il)
                sub_lines = ln.sub_lines
                for sl in sub_lines:
                    output_line(sl, in_il)
                output_hline(in_il)
        return out_segs

class HLine(object):
    def __init__(self, page, pout_bl):
        object.__init__(self)
        self.page = page
        self.pout_bl = pout_bl
    def pheight(self):
        return 1
    def get_page(self):
        return self.page
    def is_line_end(self):
        return True

class PageSpace(object):
    def __init__(self, page, pout_bl):
        object.__init__(self)
        self.page = page
        self.pout_bl = pout_bl
    def pheight(self):
        return self.pout_bl + 1
    def get_page(self):
        return self.page
    def is_line_end(self):
        return True

class Doc(object):
    def __init__(self, config):
        object.__init__(self)
        self.text_formats = []
        self.load_config(config)
        self.avg_lh = 0.015
        self.avg_il = 0.005
        self.avg_cpl = 5
        self.flex_coeff = 1./12
        self.avg_rln_lft = 0
        self.stats = []
    def load_config(self, config):
        self.config = config
        self.divide = config.divide
        self.margin = config.margin
        self.out_size = config.out_size
        self.max_il_coeff = config.max_il_coeff
        if config.flex_coeff is not None:
            self.flex_coeff = config.flex_coeff
        self.fix_figure_by_vspace = config.fix_figure_by_vspace
        self.fix_figure_by_halign = config.fix_figure_by_halign
        self.merge_center = config.merge_center
        self.merge_sparse = config.merge_sparse
        self.opedge_ex = config.opedge_ex
    def add_text_format(self, tf):
        self.text_formats.append(tf)
    def find_text_format(self, ln):
        for tf in self.text_formats:
            if tf.conform(ln):
                return tf
        return None
    def dump_text_formats(self):
        for tf in self.text_formats:
            tf.dump()
    def stat_page(self, page):
        stat = page.get_stat()
        if stat:
            self.stats.append(stat)
    def end_stat(self):
        avg_lhs = [stat.avg_lh for stat in self.stats]
        avg_ils = [stat.avg_il for stat in self.stats]
        avg_cpls = [stat.avg_cpl for stat in self.stats]
        avg_rln_lfts = [stat.avg_rln_lft for stat in self.stats]
        self.avg_lh = middle(avg_lhs)
        self.avg_il = middle(avg_ils)
        self.avg_cpl = middle(avg_cpls)
        self.avg_rln_lft = middle(avg_rln_lfts)
        if self.config.flex_coeff is None:
            self.flex_coeff = min(3. / self.avg_cpl, 1.0 / 12)

class PageParser(object):
    def __init__(self, config):
        object.__init__(self)
        self.doc = Doc(config)
    def parse(self, pimg_ref):
        page = Page(self.doc, pimg_ref.page_num)
        page.parse(pimg_ref)
        return page
    def stat_page(self, page):
        self.doc.stat_page(page)
    def end_stat(self):
        self.doc.end_stat()

class PageHLParser(object):
    def __init__(self, config):
        object.__init__(self)
        self.doc = None
    def set_doc(self, page):
        if self.doc is None:
            self.doc = page.doc
    def hl_parse(self, page):
        page.add_text_formats()
        page.fix_lines_halign()
        page.hl_parse()
        return page
    def train(self, page):
        self.set_doc(page)
        self.doc.stat_page(page)
    def end_train(self):
        self.doc.end_stat()

class NullPageHLParser(object):
    def __init__(self, config):
        object.__init__(self)
    def hl_parse(self, page):
        return page
    def train(self, page):
        pass
    def end_train(self):
        pass

def create_page_hl_parser(config):
    if config.divide > 1:
        return PageHLParser(config)
    else:
        return NullPageHLParser(config)

class PageDivider(object):
    def __init__(self, config):
        object.__init__(self)
    def divide(self, page, pimg_ref):
        page.render(pimg_ref)
        page.divide()
        segs = page.output()
        return segs

class SimplePageDivider(object):
    def __init__(self, config):
        object.__init__(self)
    def divide(self, page, pimg_ref):
        page.render(pimg_ref)
        segs = []
        pg_lft = page.bbox[0]
        if len(page.lines):
            page.lines[0].bl = 0
        for ln in page.lines:
            seg = ln.to_seg()
            seg.out_bl = seg.bl
            seg.out_x = seg.bbox[0] - pg_lft
            segs.append(seg)
        return segs

def create_page_divider(config):
    if config.divide > 1:
        return PageDivider(config)
    else:
        return SimplePageDivider(config)

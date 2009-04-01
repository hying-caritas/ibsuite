#
# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import os
import Image, ImageDraw

from image import PageImageRef
from divide import HLine, PageSpace, SegPart
from util import *

class Assembler(object):
    def __init__(self, config):
        object.__init__(self)
        self.config = config
        self.img = Image.new("L", config.out_size)
        self.draw = ImageDraw.Draw(self.img)
        self.fill_img()
        self.segs = []
        self.opimg_refs = []
    def fill_img(self):
        ow, oh = self.img.size
        self.img.paste(255, [0, 0, ow, oh])
    def output_img(self, oi):
        def real_output_img():
            if not config.crop:
                opimg = self.img.copy()
            else:
                rt = max(ow * 3/4, rt_ink) + config.margin
                btm = max(oh * 3/4, btm_ink) + config.margin
                opimg = self.img.crop((0, 0, rt, btm)).copy()
            opimg_ref = PageImageRef(page.page_no, page.out_no, opimg)
            self.opimg_refs.append(opimg_ref)
            page.out_no = page.out_no + 1
            self.fill_img()

        rt_ink = 0
        btm_ink = 0
        config = self.config
        ow, oh = config.out_size
        seg = self.segs[0]
        page = seg.get_page()
        sh = seg.pheight()
        rh = oh - 2 * config.opedge_ex
        if sh >= rh:
            poverlap = nround(config.overlap * rh)
            sy = 0
            remain = sh
            while remain >= rh:
                h = min(remain, rh)
                crop = seg.get_img(sy, nceil(h))
                txo = nround(seg.pout_x)
                self.img.paste(crop, (txo, 0))
                rt_ink = txo + crop.size[0]
                btm_ink = crop.size[1]
                real_output_img()
                if remain == h:
                    remain = 0
                    break
                remain = remain - h + poverlap
                sy = sy + h - poverlap
            del self.segs[0]
            if remain != 0:
                self.segs.insert(0, SegPart(seg, sy))
            return

        y = config.margin
        for i in range(oi):
            seg = self.segs[i]
            page = seg.get_page()
            y = y + seg.pout_bl
            ny = nround(y)
            if isinstance(seg, HLine):
                self.draw.line(((0, ny), (ow, ny)), fill = 0)
                y = y + 1
            elif isinstance(seg, PageSpace):
                self.draw.line(((0, ny), (ow, ny)), fill = 0)
                y = y + 1 + seg.pout_bl
            else:
                sh = seg.pheight()
                crop1 = seg.get_img(0, nceil(sh))
                (porgx, porgy) = seg.porg()
                pxo = min(porgx, seg.pout_x)
                pyo = min(porgy, seg.pout_bl/2.)
                pxo = nround(pxo)
                pyo = nround(pyo)
                szx, szy = crop1.size
                if porgx != pxo or porgy != pyo:
                    crop = crop1.crop((porgx - pxo, porgy - pyo, szx, szy))
                else:
                    crop = crop1
                txo = nround(seg.pout_x) - pxo
                tyo = ny - pyo
                self.img.paste(crop, (txo, tyo))
                rt_ink = max(txo + crop.size[0], rt_ink)
                btm_ink = max(tyo + crop.size[1], btm_ink)
                y = y + sh
        real_output_img()
        del self.segs[0:oi]
    def kick_page(self):
        while len(self.segs) != 0 and \
                isinstance(self.segs[0], PageSpace):
            del self.segs[0]

        if len(self.segs) == 0:
            return

        page = self.segs[0].get_page()
        config = self.config
        self.segs[0].pout_bl = min((self.segs[0].pout_bl+1)/2, config.opedge_ex)

        oh = config.out_size[1]
        oh34 = oh * 3 / 4
        h = config.margin * 2 + config.opedge_ex
        nl = -1
        nh = -1
        for i, seg in enumerate(self.segs):
            t = h + seg.pout_bl + seg.pheight()
            if nl == -1 and t > oh34:
                nl = i
            if t > oh:
                nh = i
                break
            h = t
        if nh == -1:
            return
        if nl == nh:
            if nh == 0:
                nh = nh + 1
            self.output_img(nh)
            return self.kick_page()
        oi = -1
        oal = 0
        for i in range(nl, nh):
            seg = self.segs[i]
            nseg = self.segs[i+1]
            if seg.is_line_end():
                al = nseg.pout_bl
                if al >= oal:
                    oi = i
                    oal = al
        if oi == -1:
            oi = nh - 1
        self.output_img(oi+1)
        self.kick_page()
    def flush_page(self):
        self.kick_page()
        n = len(self.segs)
        if n > 0:
            self.output_img(n)
    def start_page(self, page):
        self.page = page
        self.page.out_no = 0
    def put_hline(self, pil):
        hl = HLine(self.page, pil)
        self.segs.append(hl)
    def put_seg(self, seg, il):
        config = self.config
        page = self.page
        px = self.page.norm2opxl(seg.out_x)
        seg.pout_x = px + self.config.margin + config.opedge_ex
        seg.pout_bl = self.page.norm2opxl(il)
        self.segs.append(seg)
    def end_page(self):
        if self.config.run_pages:
            oh = self.config.out_size[1]
            ps = PageSpace(self.page, oh/20)
            self.segs.append(ps)
            self.kick_page()
        else:
            self.flush_page()
    def assemble(self, segs):
        if len(segs) == 0:
            return []
        page = segs[0].get_page()
        self.start_page(page)
        for seg in segs:
            if isinstance(seg, HLine):
                self.put_hline(seg.pout_bl)
            else:
                self.put_seg(seg, seg.out_bl)
        self.end_page()
        opimg_refs = self.opimg_refs
        self.opimg_refs = []
        return opimg_refs
    def end(self):
        self.flush_page()
        opimg_refs = self.opimg_refs
        self.opimg_refs = []
        return opimg_refs

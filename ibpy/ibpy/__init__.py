# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.


import sys
import os
import os.path
import tempfile
import random
import shutil

import input
import image
import divide
import assembler
import generator
import config
from util import *

def __reformat(args):
    def setup():
        rtmpd = os.path.join(conf.tmp_dir, 'tmp')
        try:
            os.makedirs(rtmpd)
        except:
            pass
        tempfile.tempdir = rtmpd

    def clean():
        if not config.debug:
            shutil.rmtree(conf.tmp_dir);

    def page_hl_parser_train():
        nsample = min(10, (conf.last_page-conf.first_page+1)/2)
        nsample = max(nsample, 1)
        for i in range(nsample):
            pn= random.randint(conf.first_page, conf.last_page)
            pimg_ref = inputtoppm.get_image(pn)
            pimg_ref = precrop.convert(pimg_ref)
            pimg_ref = unpaper.convert(pimg_ref)
            page = page_parser.parse(pimg_ref)
            page_hl_parser.train(page)
        page_hl_parser.end_train()

    random.seed()
    conf = config.Config(args)
    setup()

    inputtoppm = input.create_input_to_ppm(conf)
    precrop = image.PreCrop(conf)
    unpaper = image.create_unpaper(conf)
    dilate = image.create_dilate(conf)
    page_parser = divide.PageParser(conf)
    page_hl_parser = divide.create_page_hl_parser(conf)
    page_divider = divide.create_page_divider(conf)
    asm = assembler.Assembler(conf)
    post_proc = image.PostProc(conf)
    fix_black_white = image.FixBlackWhite(conf)
    collector = image.Collector(conf)
    gen = generator.create_generator(conf)

    if conf.divide > 1:
        page_hl_parser_train()

    for pn in range(conf.first_page, conf.last_page+1):
        print 'page: %d' % (pn,)

        last = (pn == conf.last_page)
        pimg_ref = inputtoppm.get_image(pn)
        pimg_ref = precrop.convert(pimg_ref)
        pimg_ref = unpaper.convert(pimg_ref)
        dilate_pimg_ref = dilate.convert(pimg_ref)
            
        page = page_parser.parse(pimg_ref)
        pimg_ref = None
        page = page_hl_parser.hl_parse(page)
        segs = page_divider.divide(page, dilate_pimg_ref)
        page = None
        dilate_pimg_ref = None
        opimg_refs = asm.assemble(segs)
        segs = None
        if last:
            opimg_refs_rem = asm.end()
            opimg_refs.extend(opimg_refs_rem)
            opimg_refs_rem = None

        for opimg_ref in opimg_refs:
            opimg_ref = post_proc.convert(opimg_ref)
            opimg_ref = fix_black_white.convert(opimg_ref)
            collector.collect(opimg_ref)
        if last:
            collector.end()
        opimg_refs = None

    gen.generate(collector.out_files, collector.page_map)

    clean()

def reformat(args):
    try:
        ret = 0
        ret = __reformat(args)
    except CommandNotFound, e:
        print 'Command not found: %s\n' % (e.cmd,)
    return ret

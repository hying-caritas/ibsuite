# Copyright 2008 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import sys
import os.path
import tempfile
import types
from optparse import OptionParser

import input
from util import *

debug = False

ext_map = {
    '.pdf' : 'pdf',
    '.imb' : 'imb',
    '.lrf' : 'lrf',
    '.djvu' : 'djvu',
}

def file_name_to_format(fn):
    s, ext = os.path.splitext(fn)
    if ext_map.has_key(ext):
        return ext_map[ext]

oprof_prs505p = {
    'out_width' : 584,
    'out_height' : 754,
    'margin' : 0,
    'colors' : 8,
}

oprof_prs505l = {
    'out_width' : 754,
    'out_height' : 584,
    'rotate' : True,
    'margin' : 0,
    'colors' : 8,
}

oprof_x61t = {
    'out_width' : 768,
    'out_height' : 1024,
    'margin' : 2,
    'colors' : 256,
}

oprof_kdx = {
    'out_width' : 824,
    'out_height' : 1200,
    'margin' : 2,
    'colors' : 16,
}

pprof_divide2 = {
    'divide' : 2,
    'fix_figure_by_vspace' : True,
    'fix_figure_by_halign' : True,
    'merge_center' : True,
    'merge_sparse' : True,
}

pprof_resize = {
    'divide' : 1,
    'dilate' : True,
}

pprof_repage = {
    'divide' : 1,
    'dilate' : False,
    'unpaper' : 'null',
}

pprof_crop = {
    'divide' : 1,
    'page_parser' : 'simple',
    'assembler' : 'simple',
    'page_hl_parser' : 'crop',
    'out_center' : True,
}

iprof_img = {
    'divide' : 1,
    'dilate' : True,
    'unpaper' : 'up',
    'input_type' : 'image',
}

profiles = {
    'prs505p' : oprof_prs505p,
    'prs505l' : oprof_prs505l,
    'x61t' : oprof_x61t,
    'kdx' : oprof_kdx,
    'divide2' : pprof_divide2,
    'resize' : pprof_resize,
    'repage' : pprof_repage,
    'crop' : pprof_crop,
    'img' : iprof_img,
}

# type, default value, short option, description
config_options = {
    'config' : (str, None, '-c', 'Configuration file'),
    'input_fn' : (str, None, '-i', 'Input file name'),
    'iprof' : (str, None, None, 'Input profile'),
    'oprof' : (str, None, None, 'Output profile'),
    'pprof' : (str, None, None, 'Processing profile'),
    'input_format' : (str, None, None, 'Input format'),
    'input_type' : (str, 'graph', None, 'Input type'),
    'input_img_negate' : (str2bool, True, None, 'Negate input image'),
    'divide' : (int, 1, '-d', 'How many segment to divide one line'),
    'margin' : (int, 0, None, 'Output margin'),
    'out_width' : (int, 584, '-w', 'Output width'),
    'out_height' : (int, 754, None, 'Output height'),
    'empty_coeff' : (float, 0.95, None, 'Empty coeff'),
    'max_il_coeff' : (float, 1.0/12, None, 'Max inter-line space coeff'),
    'flex_coeff' : (float, None, None, 'flex coeff'),
    'fix_figure_by_vspace' : (str2bool, False, None, 'Fix figure parsing via vertical space'),
    'fix_figure_by_halign' : (str2bool, False, None, 'Fix figure parsing via herizonal alignment'),
    'merge_center' : (str2bool, False, None, 'Merge center'),
    'merge_sparse' : (str2bool, False, None, 'Merge sparse'),
    'run_pages' : (str2bool, True, None, 'Run pages'),
    'unpaper' : (str, 'null', None, 'unpaper algorithm'),
    'dilate' : (str2bool, True, None, 'Dilate'),
    'trim_left' : (str2percent, 0., None, 'Trim left'),
    'trim_top' : (str2percent, 0., None, 'Trim top'),
    'trim_right' : (str2percent, 0., None, 'Trim right'),
    'trim_bottom' : (str2percent, 0., None, 'Trim bottom'),
    'overlap' : (str2percent, 0.1, None, 'Overlap across page for big line (image) in percentage'),
    'parsing_dpi' : (int, 180, None, 'DPI used to parsing image'),
    'rendering_dpi' : (int, 360, None, 'DPI used to render result image'),
    'opedge_ex' : (float, None, None, 'output page edge expanded'),
    'page_parser' : (str, None, None, "Page parser"),
    'page_hl_parser' : (str, None, None, "High-level page parser"),
    'assembler' : (str, None, None, "Assembler"),
    'colors' : (int, 4, None, 'Color number for output image'),
    'rotate' : (str2bool, False, None, 'Rotate output image'),
    'gamma' : (float, 0, None, 'Level of gamma correction'),
    'out_file_name' : (str, None, '-o', 'Output file name'),
    'out_format' : (str, None, None, 'Output format'),
    'out_center' : (str2bool, False, None, 'Put output segment in center'),
    'title' : (str, None, None, 'Book title'),
    'author' : (str, None, None, 'Book author'),
    'first_page' : (int, 1, "-f", 'First page'),
    'last_page' : (int, None, "-l", 'Last page'),
    'crop' : (str2bool, False, None, 'Crop the result'),
    'debug' : (str2bool, False, None, "Debug mode"),
    'dynamic_out_size' : (str2bool, False, None, 'Output size is not fixed'),
}

def setup_option_parser(parser):
    keys = config_options.keys()
    keys.sort()
    for k in keys:
        desc = config_options[k]
        conv, default, short, help = desc
        if short:
            parser.add_option(short, '--' + k, dest=k, help = help)
        else:
            parser.add_option('--' + k, dest=k, help = help)

def cleanup_options(options):
    for k in dir(options):
        if k.startswith('__'):
            continue
        if getattr(options, k) is None:
            delattr(options, k)

def profs_from_options(options):
    profs = {}
    if hasattr(options, 'iprof'):
        profs['iprof'] = options.iprof
    if hasattr(options, 'oprof'):
        profs['oprof'] = options.oprof
    if hasattr(options, 'pprof'):
        profs['pprof'] = options.pprof
    return profs

class Config(object):
    def __init__(self, args):
        object.__init__(self)
        self.load(args)
    def load(self, args):
        usage = 'Usage: %s [options] <input file>' % (os.path.basename(args[0]))
        parser = OptionParser(usage=usage)
        setup_option_parser(parser)
        options, in_fns = parser.parse_args(args[1:])
        if len(in_fns) != 1:
            parser.print_help()
            return
        self.input_fn = in_fns[0]
        cleanup_options(options)

        if hasattr(options, 'config'):
            conf_fn = options.config
            conf_kv = kv(file(conf_fn))
            self.apply_profiles(conf_kv)
            self.apply_dict(conf_kv)

        profs = profs_from_options(options)
        self.apply_profiles(profs)
        self.apply_obj(options)

        self.deduce()
        self.apply_defaults()
        self.check()
    def apply_dict(self, dic):
        for k, v in dic.iteritems():
            desc = config_options[k]
            if type(v) == types.StringType:
                v = desc[0](v)
            setattr(self, k, v)
    def apply_obj(self, obj):
        for k in dir(obj):
            if not config_options.has_key(k):
                continue
            v = getattr(obj, k)
            desc = config_options[k]
            if type(v) == types.StringType:
                v = desc[0](v)
            setattr(self, k, v)
    def apply_profiles(self, profs):
        if profs.has_key('iprof'):
            nm = profs['iprof']
            iprof = profiles[nm]
            self.apply_dict(iprof)
        if profs.has_key('oprof'):
            nm = profs['oprof']
            oprof = profiles[nm]
            self.apply_dict(oprof)
        if profs.has_key('pprof'):
            nm = profs['pprof']
            pprof = profiles[nm]
            self.apply_dict(pprof)
    def apply_defaults(self):
        for k in config_options:
            if not hasattr(self, k):
                desc = config_options[k]
                setattr(self, k, desc[1])
    def deduce(self):
        if hasattr(self, 'input_fn') and not hasattr(self, 'input_format'):
            in_format = file_name_to_format(self.input_fn)
            if in_format:
                self.input_format = in_format
        if hasattr(self, 'out_file_name') and not hasattr(self, 'out_format'):
            out_format = file_name_to_format(self.out_file_name)
            if out_format:
                self.out_format = out_format
        if hasattr(self, 'input_fn'):
            meta, bms = input.get_input_info(self)
            if not hasattr(self, 'title'):
                self.title = meta.doc_title
            if not hasattr(self, 'author'):
                self.author = meta.author
            if not hasattr(self, 'bookmarks'):
                self.bookmarks = bms
            if not hasattr(self, 'last_page'):
                self.last_page = meta.pages
    def check(self):
        self.out_size = (self.out_width, self.out_height)
        if self.input_fn is None:
            print 'Please specify input file name!'
            sys.exit(-1)
        input_fn = os.path.basename(self.input_fn)
        (input_fn_base, input_ext) = os.path.splitext(input_fn)

        self.tmp_dir = tempfile.mkdtemp('ibpy')

        self.output_prefix = self.tmp_dir + '/out'
        if self.out_file_name is None:
            self.out_file_name = '%s.%s' % \
                (input_fn_base, self.out_format)
            if self.out_file_name == self.input_fn:
                self.out_file_name = '%s.%s' % \
                    (self.input_fn, self.out_format)

        if self.title == '':
            self.title = input_fn_base.decode('utf-8')

        if self.opedge_ex is None:
            if self.dilate:
                self.opedge_ex = 2
            else:
                self.opedge_ex = 0

        global debug
        if self.debug:
            debug = self.debug

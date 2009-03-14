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

ext_map = {
    '.pdf' : 'pdf',
    '.imb' : 'imb',
    '.lrf' : 'lrf'
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

iprof_img = {
    'divide' : 1,
    'dilate' : True,
    'unpaper' : 'up',
    'input_type' : 'image',
}

profiles = {
    'prs505p' : oprof_prs505p,
    'prs505l' : oprof_prs505l,
    'divide2' : pprof_divide2,
    'resize' : pprof_resize,
    'repage' : pprof_repage,
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
    'colors' : (int, 4, None, 'Color number for output image'),
    'rotate' : (str2bool, False, None, 'Rotate output image'),
    'output_prefix' : (str, None, None, 'Output image prefix'),
    'out_file_name' : (str, None, '-o', 'Output file name'),
    'out_format' : (str, None, None, 'Output format'),
    'title' : (str, None, None, 'Book title'),
    'author' : (str, None, None, 'Book author'),
    'first_page' : (int, 1, "-f", 'First page'),
    'last_page' : (int, None, "-l", 'Last page'),
    'crop' : (str2bool, False, None, 'Crop the result'),
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
            if sys.platform == 'win32':
                self.pfw = 6  # this is a workaround for the Windows version
            else:
                self.pfw = len('%d' % (meta.pages,))
    def check(self):
        self.out_size = (self.out_width, self.out_height)
        if self.input_fn is None:
            print 'Please specify input file name!'
            sys.exit(-1)
        (self.input_fn_base, input_ext) = os.path.splitext(self.input_fn)

        self.tmp_dir = tempfile.mkdtemp('ibpy')

        if self.out_format == 'image':
            if self.output_prefix is None:
                print 'Please specify output_prefix for image output format!'
                sys.exit(-1)
        else:
            if self.output_prefix is None:
                self.output_prefix = self.tmp_dir + '/out'
            if self.out_file_name is None:
                self.out_file_name = '%s.%s' % \
                    (self.input_fn_base, self.out_format)
                if self.out_file_name == self.input_fn:
                    self.out_file_name = '%s.%s' % \
                        (self.input_fn, self.out_format)

        if self.title == '':
            self.title = self.input_fn_base

        if self.opedge_ex is None:
            if self.dilate:
                self.opedge_ex = 2
            else:
                self.opedge_ex = 0
    def load_old(self, conf_kv):
        self.kv = conf_kv
        self.input_fn = conf_kv.get('input')
        in_fmt = file_name_to_format(self.input_fn, 'pdf')
        self.input_format = conf_kv.get('input_format', inf_fmt)
        self.input_type = conf_kv.get('input_type', 'graph')
        self.divide = conf_kv.get('divide', 2, int)
        self.margin = conf_kv.get('margin', 1, int)
        ow = conf_kv.get('out_width', 600, int)
        oh = conf_kv.get('out_height', 800, int)
        self.out_size = (ow, oh)
        self.empty_coeff = conf_kv.get('empty_coeff', 0.95, float)
        self.max_il_coeff = conf_kv.get('max_il_coeff', 1.0 / 12, float)
        self.flex_coeff = conf_kv.get('flex_coeff', None, float)
        self.fix_figure_by_vspace = conf_kv.get('fix_figure_by_vspace',
                                                True, str2bool)
        self.fix_figure_by_halign = conf_kv.get('fix_figure_by_halign',
                                                True, str2bool)
        self.merge_center = conf_kv.get('merge_center', True, str2bool)
        self.merge_sparse = conf_kv.get('merge_sparse', True, str2bool)
        self.vector_parse = conf_kv.get('vector_parse', False, str2bool)
        self.run_pages = conf_kv.get('run_pages', False, str2bool)
        self.unpaper = conf_kv.get('unpaper', 'null')
        self.dilate = conf_kv.get('dilate', True, str2bool)
        self.trim_left = conf_kv.get('trim_left', 0., float) / 100.
        self.trim_top = conf_kv.get('trim_top', 0., float) / 100.
        self.trim_right = conf_kv.get('trim_right', 0., float) / 100.
        self.trim_bottom = conf_kv.get('trim_bottom', 0., float) / 100.
        self.overlap = conf_kv.get('overlap', 10., float) / 100.
        self.parsing_dpi = conf_kv.get('parsing_dpi', 180, int)
        self.rendering_dpi = conf_kv.get('rendering_dpi', 360, int)
        self.opedge_ex_usr = conf_kv.get('opedge_ex', None, int)

        self.colors = conf_kv.get('colors', 4, int)
        self.rotate = conf_kv.get('rotate', False, str2bool)
        self.output_prefix = conf_kv.get('output_prefix')
        self.out_file_name = conf_kv.get('out_file_name')
        out_fmt = file_name_to_format(self.out_file_name, 'lrf')
        self.out_format = conf_kv.get('out_format', out_fmt)

        meta, bms = input.get_input_info(self)
        self.title = conf_kv.get('title', meta.doc_title)
        self.author = conf_kv.get('author', meta.author)
        self.bookmarks = conf_kv.get('bookmarks', bms)
        self.first_page = conf_kv.get('first_page', 1, int)
        self.last_page = conf_kv.get('last_page', meta.pages, int)
        if sys.platform == 'win32':
            default_pfw = 6      # this is a workaround for the Windows version
        else:
            default_pfw = len('%d' % (meta.pages,))
        self.pfw = conf_kv.get('pfw', default_pfw)

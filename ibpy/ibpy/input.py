#
# Copyright 2009 Huang Ying <huang.ying.caritas@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

import sys

import pdf
import pdfinfo
import imb
import imbinfo
import djvu
import djvuinfo

def get_input_info(config):
    iformat = config.input_format
    if iformat == 'pdf':
        info_parser = pdfinfo.PDFInfoParser(config)
    elif iformat == 'imb':
        info_parser = imbinfo.ImbInfoParser(config)
    elif iformat == 'djvu':
        info_parser = djvuinfo.DJVUInfoParser(config)
    else:
        print 'Invalid input format: %s' % (iformat)
        sys.exit(-1)
    return info_parser.parse()

def create_input_to_ppm(config):
    if config.input_format == 'pdf':
        return pdf.create_pdf_to_ppm(config)
    elif config.input_format == 'imb':
        return imb.IMBToPPM(config)
    elif config.input_format == 'djvu':
        return djvu.DJVUToPPM(config)

import sys

import pdf
import pdfinfo
import imb
import imbinfo

def get_input_info(config):
    iformat = config.input_format
    if iformat == 'pdf':
        info_parser = pdfinfo.PDFInfoParser(config)
    elif iformat == 'imb':
        info_parser = imbinfo.ImbInfoParser(config)
    else:
        print 'Invalid input format: %s' % (iformat)
        sys.exit(-1)
    return info_parser.parse()

def create_input_to_ppm(config):
    if config.input_format == 'pdf':
        return pdf.create_pdf_to_ppm(config)
    elif config.input_format == 'imb':
        return imb.IMBToPPM(config)

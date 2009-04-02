DIR_POPPLER = ../poppler
INC_POPPLER = ${DIR_POPPLER}
LIB_POPPLER = ${DIR_POPPLER}/poppler/libpoppler.la

PREFIX = /usr/local
CXX = g++
CXXLINK = libtool --mode=link ${CXX}
CFLAGS = -I ${INC_POPPLER} -I ${INC_POPPLER}/poppler -DHAVE_CONFIG_H -Wall -Wno-write-strings
CXXFLAGS = ${CFLAGS}
LDFLAGS =
LIBS = ${LIB_POPPLER}
INSTALL = libtool --mode=install install

EXEC_NAME = ibpdf2xml
OBJS = pdftohtml.o HtmlOutputDev.o HtmlFonts.o HtmlLinks.o parseargs.o

${EXEC_NAME}: ${OBJS}
	${CXXLINK} -o $@ ${LDFLAGS} $^ ${LIBS}

clean:
	rm -rf ${EXEC_NAME} *.o

install:
	mkdir -p ${PREFIX}/bin
	${INSTALL} ibpdf2xml ${PREFIX}/bin

uninstall:
	rm -rf ${PREFIX}/bin/ibpdf2xml

distclean: clean
	find . -name '*~' | xargs rm -f

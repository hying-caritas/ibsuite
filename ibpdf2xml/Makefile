DIR_POPPLER = ../poppler
INC_POPPLER = ${DIR_POPPLER}
LIB_POPPLER = ${DIR_POPPLER}/poppler/.libs

PREFIX = /usr/local
CXX = g++
CFLAGS = -I ${INC_POPPLER} -I ${INC_POPPLER}/poppler -DHAVE_CONFIG_H -Wall -Wno-write-strings
CXXFLAGS = ${CFLAGS}
LDFLAGS = -L ${LIB_POPPLER}
LIBS = -lpoppler

EXEC_NAME = ibpdf2xml
OBJS = pdftohtml.o HtmlOutputDev.o HtmlFonts.o HtmlLinks.o parseargs.o

${EXEC_NAME}: ${OBJS}
	${CXX} -o $@ ${LDFLAGS} $^ ${LIBS}

clean:
	rm -rf ${EXEC_NAME} *.o

install:
	install ibpdf2xml ${PREFIX}/bin

uninstall:
	rm -rf ${PREFIX}/bin/ibpdf2xml

distclean: clean
	find . -name '*~' | xargs rm -f

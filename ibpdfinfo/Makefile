DIR_POPPLER = ../poppler
INC_POPPLER = ${DIR_POPPLER}
LIB_POPPLER = ${DIR_POPPLER}/poppler/libpoppler.la

CXX = g++
CXXLINK = libtool --mode=link ${CXX}
CFLAGS = -I ${INC_POPPLER} -I ${INC_POPPLER}/poppler -DHAVE_CONFIG_H \
	-Wall -Wno-write-strings -g
CXXFLAGS = ${CFLAGS}
LDFLAGS = -g
LIBS = ${LIB_POPPLER}
PREFIX = /usr/local
INSTALL = libtool --mode=install install

EXEC_NAME = ibpdfinfo
OBJS = ibpdfinfo.o parseargs.o

${EXEC_NAME}: ${OBJS}
	${CXXLINK} -o $@ ${LDFLAGS} $^ ${LIBS}

clean:
	rm -rf ${EXEC_NAME} *.o

install:
	${INSTALL} ibpdfinfo ${PREFIX}/bin

uninstall:
	rm -rf ${PREFIX}/bin/ibpdfinfo

distclean: clean
	find . -name '*~' | xargs rm -f

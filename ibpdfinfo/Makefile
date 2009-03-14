DIR_POPPLER = ../poppler
INC_POPPLER = ${DIR_POPPLER}
LIB_POPPLER = ${DIR_POPPLER}/poppler/.libs

CXX = g++
CFLAGS = -I ${INC_POPPLER} -I ${INC_POPPLER}/poppler -DHAVE_CONFIG_H \
	-Wall -Wno-write-strings -g
CXXFLAGS = ${CFLAGS}
LDFLAGS = -L ${LIB_POPPLER} -g
LIBS = -lpoppler
PREFIX = /usr/local

EXEC_NAME = ibpdfinfo
OBJS = ibpdfinfo.o parseargs.o

${EXEC_NAME}: ${OBJS}
	${CXX} -o $@ ${LDFLAGS} $^ ${LIBS}

clean:
	rm -rf ${EXEC_NAME} *.o

install:
	install ibpdfinfo ${PREFIX}/bin

uninstall:
	rm -rf ${PREFIX}/bin/ibpdfinfo

distclean: clean
	find . -name '*~' | xargs rm -f

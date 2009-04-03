CC = gcc
CFLAGS = -g
LDFLAGS = -g
LIBS = -lnetpbm
PREFIX = /usr/local

EXEC = iblineparser
OBJS = iblineparser.o

${EXEC}: ${OBJS}
	${CC} -o $@ ${LDFLAGS} $^ ${LIBS}

clean:
	rm -rf ${EXEC} ${OBJS}

install:
	mkdir -p ${DESTDIR}/${PREFIX}/bin
	install iblineparser ${DESTDIR}/${PREFIX}/bin

uninstall:
	rm -rf ${DESTDIR}/${PREFIX}/bin/iblineparser

distclean: clean
	rm -f *~

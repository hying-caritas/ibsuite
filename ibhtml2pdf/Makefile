PREFIX = /usr/local
DESTDIR = /

all:
	./build.sh xulapp

install:
	./install.sh -destdir ${DESTDIR} -prefix ${PREFIX}

uninstall:
	rm -rf ${DESTDIR}/${PREFIX}/lib/ibhtml2pdf
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibhtml2pdf

clean:
	rm -f *.xulapp
	rm -f *.tmp

distclean: clean
	find . -name '*~' | xargs rm -f

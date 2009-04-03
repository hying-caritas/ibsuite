PREFIX = /usr/local

all:
	./build.sh xulapp

install:
	mkdir -p ${DESTDIR}/${PREFIX}
	./install.sh -destdir ${DESTDIR} -prefix ${PREFIX}

uninstall:
	rm -rf ${DESTDIR}/${PREFIX}/lib/ibhtml2img
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibhtml2img

clean:
	rm -f *.xulapp
	rm -f *.tmp

distclean: clean
	find . -name '*~' | xargs rm -f

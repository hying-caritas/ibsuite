
PREFIX=/usr/local

install:
	mkdir -p ${DESTDIR}/${PREFIX}/bin
	install ibchm2pdf ${DESTDIR}/${PREFIX}/bin
	install ibchm2imb ${DESTDIR}/${PREFIX}/bin
	install ibreformat ${DESTDIR}/${PREFIX}/bin
	install ibimb2pdf ${DESTDIR}/${PREFIX}/bin
	install ibimgcat ${DESTDIR}/${PREFIX}/bin

uninstall:
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibchm2pdf
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibchm2imb
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibreformat
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibimb2pdf
	rm -rf ${DESTDIR}/${PREFIX}/bin/ibimgcat

clean:

distclean:
	rm -f *~

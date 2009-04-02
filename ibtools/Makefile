
PREFIX=/usr/local

install:
	mkdir -p ${PREFIX}/bin
	install ibchm2pdf ${PREFIX}/bin
	install ibchm2imb ${PREFIX}/bin
	install ibreformat ${PREFIX}/bin
	install ibimb2pdf ${PREFIX}/bin
	install ibimgcat ${PREFIX}/bin

uninstall:
	rm -rf ${PREFIX}/bin/ibchm2pdf
	rm -rf ${PREFIX}/bin/ibchm2imb
	rm -rf ${PREFIX}/bin/ibreformat
	rm -rf ${PREFIX}/bin/ibimb2pdf
	rm -rf ${PREFIX}/bin/ibimgcat

clean:

distclean:
	rm -f *~

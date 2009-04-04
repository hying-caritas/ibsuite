VER = 0.1

all:
	${MAKE} -C poppler
ifndef NO_XUL
	${MAKE} -C ibhtml2pdf
	${MAKE} -C ibhtml2img
endif
	${MAKE} -C iblineparser
	${MAKE} -C ibpdfinfo
	${MAKE} -C ibpdf2xml

clean:
	${MAKE} -C ibhtml2pdf clean
	${MAKE} -C ibhtml2img clean
	${MAKE} -C iblineparser clean
	${MAKE} -C ibpdfinfo clean
	${MAKE} -C ibpy clean
	${MAKE} -C ibpdf2xml clean

poppler_clean:
	${MAKE} -C poppler clean

cleanall: clean poppler_clean

distclean:
	-[ -f poppler/Makefile ] && ${MAKE} -C poppler distclean
	${MAKE} -C ibhtml2pdf distclean
	${MAKE} -C ibhtml2img distclean
	${MAKE} -C iblineparser distclean
	${MAKE} -C ibpdfinfo distclean
	${MAKE} -C ibpy distclean
	${MAKE} -C ibpdf2xml distclean
	rm -f *~

INSTALL_MOD := iblineparser ibpdfinfo ibpdf2xml ibtools
ifndef NO_XUL
INSTALL_MOD := ${INSTALL_MOD} ibhtml2pdf ibhtml2img
endif
ifndef NO_POPPLER
INSTALL_MOD := ${INSTALL_MOD} poppler
endif

install:
	for m in ${INSTALL_MOD} ibpy; do \
		${MAKE} -C $$m install; \
	done

uninstall:
	for m in ${INSTALL_MOD} ibpy; do \
		${MAKE} -C $$m uninstall; \
	done

dist:
	rm -f ibsuite-src-${VER}.tar.gz
	rm -rf ibsuite-src-${VER}
	mkdir ibsuite-src-${VER}
	for m in ibpy ibhtml2img ibhtml2pdf iblineparser ibpdf2xml \
		ibpdfinfo ibtools poppler; do \
		mkdir ibsuite-src-${VER}/$$m; \
		cp -r $$m/* ibsuite-src-${VER}/$$m; \
	done
	for f in configure Makefile README; do \
		cp $$f ibsuite-src-${VER}; \
	done
	tar -czf ibsuite-src-${VER}.tar.gz ibsuite-src-${VER}
	rm -rf ibsuite-src-${VER}

bdist:
	rm -f ibsuite-${VER}.tar.gz
	rm -rf ibsuite-${VER}
	mkdir ibsuite-${VER}
	for m in ${INSTALL_MOD}; do \
		${MAKE} -C $$m install DESTDIR=`pwd`/ibsuite-${VER}/root; \
	done
	mkdir ibsuite-${VER}/ibpy
	cp -r ibpy/ibpy ibsuite-${VER}/ibpy
	cp ibpy/setup.py ibsuite-${VER}/ibpy
	cp scripts/install.sh ibsuite-${VER}
	tar -czf ibsuite-${VER}.tar.gz ibsuite-${VER}
	rm -rf ibsuite-${VER}

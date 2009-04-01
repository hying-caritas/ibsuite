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

install:
	${MAKE} -C poppler install
ifndef NO_XUL
	${MAKE} -C ibhtml2pdf install
	${MAKE} -C ibhtml2img install
endif
	${MAKE} -C iblineparser install
	${MAKE} -C ibpdfinfo install
	${MAKE} -C ibpdf2xml install
	${MAKE} -C ibtools install
	${MAKE} -C ibpy install

uninstall:
ifndef NO_XUL
	${MAKE} -C ibhtml2pdf uninstall
	${MAKE} -C ibhtml2img uninstall
endif
	${MAKE} -C iblineparser uninstall
	${MAKE} -C ibpdfinfo uninstall
	${MAKE} -C ibpdf2xml uninstall
	${MAKE} -C ibtools uninstall
	${MAKE} -C ibpy uninstall
	${MAKE} -C poppler uninstall

dist:
	rm -f ibsuite-${VER}.tar.gz
	rm -rf ibsuite-${VER}
	mkdir ibsuite-${VER}
	for m in ibpy ibhtml2img ibhtml2pdf iblineparser ibpdf2xml \
		ibpdfinfo ibtools poppler; do \
		mkdir ibsuite-${VER}/$$m; \
		cp -r $$m/* ibsuite-${VER}/$$m; \
	done
	for f in configure Makefile README; do \
		cp $$f ibsuite-${VER}; \
	done
	tar -czf ibsuite-${VER}.tar.gz ibsuite-${VER}
	rm -rf ibsuite-${VER}

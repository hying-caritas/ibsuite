VER = 0.1

OS := $(shell uname -o)
OS := $(subst GNU/Linux, linux, ${OS})
OS := $(shell echo ${OS} | tr / _)
MACH = $(shell uname -m)

all:
	${MAKE} -C poppler
ifndef NO_XUL
	${MAKE} -C ibhtml2pdf
	${MAKE} -C ibhtml2img
endif
	${MAKE} -C iblineparser
	${MAKE} -C ibpdfinfo
	${MAKE} -C ibpdf2xml

doc:
	${MAKE} -C doc

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

DIST_BASE = ibsuite-src-${VER}

dist:
	rm -f ${DIST_BASE}.tar.gz
	rm -rf ${DIST_BASE}
	mkdir ${DIST_BASE}
	for m in ibpy ibhtml2img ibhtml2pdf iblineparser ibpdf2xml \
		ibpdfinfo ibtools poppler scripts doc; do \
		mkdir ${DIST_BASE}/$$m; \
		cp -r $$m/* ${DIST_BASE}/$$m; \
	done
	for f in autogen.sh configure COPYING Makefile README; do \
		cp $$f ${DIST_BASE}; \
	done
	tar -czf ${DIST_BASE}.tar.gz ${DIST_BASE}
	rm -rf ${DIST_BASE}

ifndef NO_POPPLER
BDIST_BASE = ibsuite-poppler-${VER}.${OS}.${MACH}
else
BDIST_BASE = ibsuite-${VER}.${OS}.${MACH}
endif

bdist:
	rm -f ${BDIST_BASE}.tar.gz
	rm -rf ${BDIST_BASE}
	mkdir ${BDIST_BASE}
	for m in ${INSTALL_MOD}; do \
		${MAKE} -C $$m install DESTDIR=`pwd`/${BDIST_BASE}/root; \
	done
	mkdir ${BDIST_BASE}/ibpy
	cp -r ibpy/ibpy ${BDIST_BASE}/ibpy
	cp ibpy/setup.py ${BDIST_BASE}/ibpy
	cp scripts/install.sh ${BDIST_BASE}
	tar -czf ${BDIST_BASE}.tar.gz ${BDIST_BASE}
	rm -rf ${BDIST_BASE}

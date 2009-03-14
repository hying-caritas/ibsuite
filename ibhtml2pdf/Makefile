PREFIX = /usr/local

all:
	./build.sh xulapp

install:
	./install.sh -prefix ${PREFIX}

uninstall:
	rm -rf ${PREFIX}/lib/ibhtml2pdf
	rm -rf ${PREFIX}/bin/ibhtml2pdf

clean:
	rm -f *.xulapp
	rm -f *.tmp

distclean: clean
	find . -name '*~' | xargs rm -f

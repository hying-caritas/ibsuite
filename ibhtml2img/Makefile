PREFIX = /usr/local

all:
	./build.sh xulapp

install:
	mkdir -p ${PREFIX}
	./install.sh -prefix ${PREFIX}

uninstall:
	rm -rf ${PREFIX}/lib/ibhtml2img
	rm -rf ${PREFIX}/bin/ibhtml2img

clean:
	rm -f *.xulapp
	rm -f *.tmp

distclean: clean
	find . -name '*~' | xargs rm -f

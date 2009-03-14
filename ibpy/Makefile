all:
	python setup.py build

install:
	python setup.py install

uninstall:
	echo "Don't know how to uninstall until now!"

clean:
	rm -rf build
	rm -rf ibpy.egg-info
	rm -rf temp

distclean: clean
	find . -name '*~' | xargs rm -f
	fint . -name '*.pyc' | xargs rm -f

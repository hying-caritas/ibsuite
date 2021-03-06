#! /bin/bash

# (C) Copyright 2004-2007 Shawn Betts
# (C) Copyright 2007 John J. Foerch
# (C) Copyright 2008 Huang Ying
#
# Use, modification, and distribution are subject to the terms specified in the
# COPYING file.

## BUILD
##
##   Whether to build the xulapp.  This is just a shortcut for developers and hackers.
##
BUILD=""

## PREFIX
##
##   Install prefix.  Conkeror will be installed to $PREFIX/lib/ibhtml2pdf and a
##   symlink to the stub binary will be placed in $PREFIX/bin/ibhtml2pdf
##
PREFIX=/usr/local

while [[ "$1" = -* ]]; do
    case "$1" in
        -build) BUILD=1 ;;
        -prefix) PREFIX="${2%/}" ; shift ;;
	-destdir) DESTDIR="${2%/}" ; shift ;;
        *)
            echo "Unrecognized option. Please read the source."
            exit 1
    esac
    shift
done

# Find an appropriate xulrunner binary
XULRUNNER=''
for xr in xulrunner-1.9.1 xulrunner-1.9 xulrunner; do
    XRTMP=`which $xr`
    if [ -n "$XRTMP" -a -x "$XRTMP" ]; then
	if expr `$XRTMP --gre-version | cut -d . -f 1,2` '>=' 1.9 > /dev/null; then
	    # xulrunner is version 1.9 or higher, take it
	    XULRUNNER=$XRTMP
	    break
	else
	    # xulrunner is older than version 1.9, forget it
	    XRTMP=/usr/lib/$xr/xulrunner
	    if [ -x $XRTMP ]; then
		if expr `$XRTMP --gre-version | cut -d . -f 1,2` '>=' 1.9 > /dev/null; then
		    # xulrunner is a 1.9 version, take it
		    XULRUNNER=$XRTMP
		    break
		fi
	    fi
	fi
    fi
done

if [ -z "$XULRUNNER" ]; then
    echo "xulrunner version 1.9 required, but not found. Bailing out." 1>&2
    exit 1;
fi

function assert_ibhtml2pdf_src () {
    if  [[ ! -e build.sh ]]; then
        echo "The current directory does not appear to contain the Conkeror source code."
        exit 1
    fi
}

if [[ -n "$BUILD" ]]; then
    ## -build has been requested.
    ## assert we are in the ibhtml2pdf source directory
    assert_ibhtml2pdf_src
    bash build.sh xulapp
fi

### ibhtml2pdf.xulapp should be in the current directory
if [[ ! -e ibhtml2pdf.xulapp ]]; then
    echo "ibhtml2pdf.xulapp not found.  install cannot continue."
    exit 1
fi

echo -n "Installing ibhtml2pdf to $PREFIX/lib/ibhtml2pdf ..."
mkdir -p "$DESTDIR/$PREFIX/lib"
${XULRUNNER} --install-app ibhtml2pdf.xulapp "$DESTDIR/$PREFIX/lib/"
echo ok

if [[ -e "$DESTDIR/$PREFIX/bin/ibhtml2pdf" ]]; then
    rm "$DESTDIR/$PREFIX/bin/ibhtml2pdf"
fi
echo -n "Installing ibhtml2pdf binary in $PREFIX/bin ..."
sed -e 's?PREFIX?'${PREFIX}'?g' ibhtml2pdf > ibhtml2pdf.tmp
mkdir -p "$DESTDIR/$PREFIX/bin"
install ibhtml2pdf.tmp $DESTDIR/$PREFIX/bin/ibhtml2pdf
rm ibhtml2pdf.tmp
echo ok

echo "Done."

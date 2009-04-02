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
##   Install prefix.  Conkeror will be installed to $PREFIX/lib/ibhtml2img and a
##   symlink to the stub binary will be placed in $PREFIX/bin/ibhtml2img
##
PREFIX=/usr/local

while [[ "$1" = -* ]]; do
    case "$1" in
        -build) BUILD=1 ;;
        -prefix) PREFIX="${2%/}" ; shift ;;
        *)
            echo "Unrecognized option. Please read the source."
            exit 1
    esac
    shift
done

# Find an appropriate xulrunner binary
XULRUNNER=''
for xr in xulrunner-1.9 xulrunner; do
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

function assert_ibhtml2img_src () {
    if  [[ ! -e build.sh ]]; then
        echo "The current directory does not appear to contain the Conkeror source code."
        exit 1
    fi
}

if [[ -n "$BUILD" ]]; then
    ## -build has been requested.
    ## assert we are in the ibhtml2img source directory
    assert_ibhtml2img_src
    bash build.sh xulapp
fi

### ibhtml2img.xulapp should be in the current directory
if [[ ! -e ibhtml2img.xulapp ]]; then
    echo "ibhtml2img.xulapp not found.  install cannot continue."
    exit 1
fi

echo -n "Installing ibhtml2img to $PREFIX/lib/ibhtml2img ..."
mkdir -p "$PREFIX/lib"
$XULRUNNER --install-app ibhtml2img.xulapp "$PREFIX/lib/"
echo ok

if [[ -e "$PREFIX/bin/ibhtml2img" ]]; then
    rm "$PREFIX/bin/ibhtml2img"
fi
echo -n "Installing ibhtml2img binary in $PREFIX/bin ..."
sed -e 's?PREFIX?'${PREFIX}'?g' ibhtml2img > ibhtml2img.tmp
mkdir -p "$PREFIX/bin"
install ibhtml2img.tmp $PREFIX/bin/ibhtml2img
rm ibhtml2img.tmp
echo ok

echo "Done."

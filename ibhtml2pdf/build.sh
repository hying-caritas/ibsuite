#! /bin/bash

# (C) Copyright 2004-2007 Shawn Betts
# (C) Copyright 2007-2008 John J. Foerch
# (C) Copyright 2007-2008 Jeremy Maitin-Shepard
# (C) Copyright 2008 Huang Ying
#
# Use, modification, and distribution are subject to the terms specified in the
# COPYING file.

TARGET='help'

## ETAGSDIR
##
##   This variable is for target `etags'.  It specifies the destination
##   directory for the TAGS file.
##
ETAGSDIR=""

case "$1" in
    xulapp)
        TARGET=xulapp ;;
    dist-tar)
        TARGET=dist-tar ;;
    release)
        TARGET=release ;;
    etags)
        TARGET=etags
        ETAGSDIR="$2"
        shift ;;
    notes)
        TARGET=notes ;;
    help|-help|--help)
        TARGET=help ;;
    *)
        echo 'bad usage. please read the source.'
        exit 1
esac
shift

VERSION=$(grep '^Version=' application.ini | cut -d '=' -f 2)

## if this is not an official release, tag on a build date.
##
## if this is an official release, strip the subminor.
##
MILESTONE="${VERSION##*.}"
BUILD_DATE=$(date +%Y%m%d)
SHORT_VERSION="$VERSION"

case "$TARGET" in
    release|announce)
        VERSION="${VERSION%.*}" ;;
    *)
        VERSION="$VERSION.$BUILD_DATE"
esac
echo "build target: $TARGET, $VERSION"

### UTILITIES
###
###

## SCRATCH
##
##   Temporary directory for build process.
##
SCRATCH=""

function get_scratch () {
    if [[ -z "$SCRATCH" ]]; then
        SCRATCH=$(mktemp -d ibhtml2pdf-XXXXXX)
    fi
}

function do_cleanup () {
    if [[ -n "$SCRATCH" ]]; then
        rm -r "$SCRATCH"
        SCRATCH=""
    fi
}

function assert_ibhtml2pdf_src () {
    if  [[ ! -e application.ini ]]; then
        echo "The current directory does not appear to contain the Conkeror source code."
        exit 1
    fi
}

function copy_tree_sans_boring () {
    src="$1"
    dest="$2"
    mkdir -p "$dest"
    O=$IFS
    IFS=$'\n'
    ( cd "$src"; find . -type d -and \! -name '*[~#]' -print0 ) \
        | ( cd "$dest"; xargs -0 mkdir -p )
    files=($( cd "$src"; find . -type f -and \! -name '*[~#]' -print ))
    for file in "${files[@]}" ; do cp "$src/$file" "$dest/$file" ; done
    IFS=$O
}

function do_check_milestone_for_release ()
{
    if [[ "$MILESTONE" = "0" ]]; then
        return
    fi

    dest=VERSION
    proposed="${VERSION%.*}".$(( ${VERSION#*.} + 1 )).0

    echo "The version given in the file $dest does not have 0 as its last component."
    echo -n "Shall I rewrite \`VERSION=$VERSION.$MILESTONE' to \`VERSION=$proposed'? [yN] "
    read
    if [[ "$REPLY" = [Yy]* ]]; then
        perl -pi -e 's/^VERSION='$VERSION'\.'$MILESTONE'$/VERSION='$proposed'/' "$dest"
        echo "Version changed in $dest.  Please run this build program again."
        exit
    else
        echo "Leaving $dest untouched.  Continuing with build."
    fi
}

function diff_wrapper () {
    scratch="$1"
    dest="$2"
    perlexp="$3"

    scratchfile="${scratch}/$dest"
    patchfile="${scratch}/$dest.patch"

    echo -n "Processing $dest ..."
    perl -0777 -p -e "$perlexp" "$dest" > "$scratchfile"
    echo ok

    if cmp "$dest" "$scratchfile" ; then
        echo "$dest does not need to be updated"
    else
        diff -u "$dest" "$scratchfile" | tee "$patchfile"
        echo -n "Apply this patch to $dest? [yN] "
        read
        if [[ "$REPLY" = [Yy]* ]]; then
            patch < "$patchfile"
        else
            echo "Leaving $dest untouched"
        fi
    fi
}

### TARGETS
###
###

function do_target_xulapp () {
    echo -n Building XULRunner Application...

    get_scratch
    mkdir -p "$SCRATCH/chrome"
    cp application.ini "$SCRATCH"
    if [ -n "$IBHTML2PDF_APP_NAME" ]; then
        sed -i -e "s/Name=ibhtml2pdf/Name=${IBHTML2PDF_APP_NAME}/" "${SCRATCH}/application.ini"
    fi
    for x in chrome defaults; do
        copy_tree_sans_boring "$x" "$SCRATCH/$x"
    done
    BUILD_ID=$(git rev-parse HEAD 2> /dev/null)
    if [ "$?" != 0 ]; then
        BUILD_ID="git"
    fi
    pushd "$SCRATCH" > /dev/null
    ## begin preprocessing
    ##
    perl -pi -e 's/BuildID=git/BuildID='${BUILD_ID}'/g' application.ini
    ##
    ## end preprocessing
    zip -r ../ibhtml2pdf.xulapp * > /dev/null
    popd > /dev/null
    do_cleanup
    echo ok
}

function do_target_dist_tar () {
    do_target_xulapp
    get_scratch
    ## now we have ibhtml2pdf.xulapp
    ## package it with install.sh
    ##
    ## some other files should probably go in here.. NEWS, for example
    mkdir "$SCRATCH/ibhtml2pdf-$VERSION"
    mv ibhtml2pdf.xulapp "$SCRATCH/conkeror-$VERSION/"
    cp install.sh "$SCRATCH/ibhtml2pdf-$VERSION/"
    pushd "$SCRATCH" > /dev/null
    tar c ibhtml2pdf-$VERSION | gzip > ibhtml2pdf-$VERSION.tar.gz
    popd > /dev/null
    mv "$SCRATCH/ibhtml2pdf-$VERSION.tar.gz" .
    echo -n "Making ibhtml2pdf-$VERSION.tar.gz ..."
    do_cleanup
    echo ok
}

function do_target_release () {
    do_check_milestone_for_release
    ## Make any and all release archives.
    ##
    ## Right now, we just make a tar.gz archive that includes an install
    ## script.  In the future, we could consider making an OSX App, a Windows
    ## Installer EXE, and a Mozilla XPI Installer.
    ##
    do_target_dist_tar
    echo -n Putting ibhtml2pdf-$VERSION.tar.gz in downloads directory ...
    mv ibhtml2pdf-$VERSION.tar.gz ../downloads
    echo ok
}

function do_target_etags () {
    if [[ -z "$ETAGSDIR" ]]; then
        ETAGSDIR=.
    fi
    ETAGSDIR="${ETAGSDIR%/}/TAGS"
    echo -n "Building $ETAGSDIR ..."
    etags -o "$ETAGSDIR" $(find -name \*.js -and \! -name '*[~#]*')
    echo ok
}

function do_target_notes () {
    FILES=($(find ibhtml2pdf -name \*.js))
    for file in "${FILES[@]}"; do
        fileo="${file//\//\/}"
        perl -0777 -ne 's/## BLOCK COMMENTS
                           (.*\/\*\s*[A-Z][A-Z].*:.*$
                            (\n.*$)*?
                            (\n.*\*\/)
                            (?{ $p = pos(); })) |
                          ## LINE COMMENTS
                           (.*\/\/\s*[A-Z][A-Z].*:.*$
                            ((\n.*\/\/.*$)*)
                            (?{ $p = pos(); }))
                         /print "'$fileo':$p\n" . $& . "\n\n"/mexg' < "$file"
    done
}

function do_target_help () {
    echo "For this script to work, your current working directory must"
    echo "be \`<IBHTML2PDF>/src' where <IBHTML2PDF> is the project root."
    echo "This script expects to find the subdirectory structure,"
    echo "\`ibhtml2pdf/content', and VERSION in the current directory,"
    echo "\`downloads' and \`www' in the parent directory, and possibly"
    echo "other files."
    echo
    echo 'Usage:  bash build.sh <TARGET>'
    echo 'where <TARGET> is one of:'
    echo
    echo ' xulapp'
    echo
    echo ' dist-tar'
    echo
    echo ' release                Builds a release xpi and puts it in ../downloads.'
    echo
    echo ' etags [DIR]            Build TAGS file in etags format.  If a'
    echo '                        directory is given, TAGS will be made in'
    echo '                        that directory.'
    echo
    echo ' notes                  Shows specially formatted comments in'
    echo "                        \`ibhtml2pdf/content/*.js'  Modifies no files."
    echo
    echo ' help                   Shows this help message.  Modifies no files.'
    echo
}

### MAIN
###
###

assert_ibhtml2pdf_src

case "$TARGET" in
    xulapp) do_target_xulapp ;;
    dist-tar) do_target_dist_tar ;;
    release) do_target_release ;;
    etags) do_target_etags ;;
    notes) do_target_notes ;;
    help) do_target_help ;;
esac

do_cleanup

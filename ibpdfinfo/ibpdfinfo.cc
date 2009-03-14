//========================================================================
//
// pdfminfo.cc
//
// Copyright 1999-2000 G. Ovtcharov
// Copyright 2008-2009 Huang Ying <huang.ying.caritas@gmail.com>
//
// Based on pdftohtml
//
//========================================================================

#include "config.h"
#include <poppler-config.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#ifdef HAVE_DIRENT_H
#include <dirent.h>
#endif
#include <time.h>
#include "parseargs.h"
#include "goo/GooString.h"
#include "goo/gmem.h"
#include "Object.h"
#include "Stream.h"
#include "Array.h"
#include "Dict.h"
#include "XRef.h"
#include "Catalog.h"
#include "Page.h"
#include "PDFDoc.h"
#include "Link.h"
#include "GlobalParams.h"
#include "Error.h"
#include "Outline.h"
#include "goo/gfile.h"
#include "goo/GooList.h"
#include "UnicodeMap.h"
#include "PDFDocEncoding.h"

static int firstPage = 1;
static int lastPage = 0;
static GBool printHelp = gFalse;
GBool ignore=gFalse;
GBool stout=gFalse;
GBool errQuiet=gFalse;
GBool noDrm=gFalse;

GBool showHidden = gFalse;
GBool noMerge = gFalse;
static char ownerPassword[33] = "";
static char userPassword[33] = "";
static GBool printVersion = gFalse;

static char textEncName[128] = "";

static ArgDesc argDesc[] = {
	{"-f",      argInt,      &firstPage,     0,
	 "first page to convert"},
	{"-l",      argInt,      &lastPage,      0,
	 "last page to convert"},
	{"-q",      argFlag,     &errQuiet,      0,
	 "don't print any messages or errors"},
	{"-h",      argFlag,     &printHelp,     0,
	 "print usage information"},
	{"-help",   argFlag,     &printHelp,     0,
	 "print usage information"},
	{"-i",      argFlag,     &ignore,        0,
	 "ignore images"},
	{"-stdout"  ,argFlag,    &stout,         0,
	 "use standard output"},
	{"-hidden", argFlag,   &showHidden,   0,
	 "output hidden text"},
	{"-nomerge", argFlag, &noMerge, 0,
	 "do not merge paragraphs"},   
	{"-enc",    argString,   textEncName,    sizeof(textEncName),
	 "output text encoding name"},
	{"-v",      argFlag,     &printVersion,  0,
	 "print copyright and version info"},
	{"-opw",    argString,   ownerPassword,  sizeof(ownerPassword),
	 "owner password (for encrypted files)"},
	{"-upw",    argString,   userPassword,   sizeof(userPassword),
	 "user password (for encrypted files)"},
	{"-nodrm", argFlag, &noDrm, 0,
	 "override document DRM settings"},
	{NULL}
};

static void fputs_quote(char *s, FILE *f)
{
	char *p;

	for (p = s; *p != '\0'; p++) {
		switch (*p) {
		case '<':
			fputs("&lt;", f);
			break;
		case '>':
			fputs("&gt;", f);
			break;
		default:
			fputc(*p, f);
			break;
		}
	}
}

static void fputs_simple_mark(char *mark, char *text, FILE *f)
{
	fprintf(f, "<%s>", mark);
	fputs_quote(text, f);
	fprintf(f, "</%s>\n", mark);
}

static Unicode *gooStringToUnicode(GooString *s, int *length)
{
	unsigned char *uni_str = NULL;
	Unicode *uni;
	int len, i;

	if (!s->hasUnicodeMarker()) {
		printf("no unicode");
		if (s->getLength() > 0)
			uni_str = (unsigned char *)
				pdfDocEncodingToUTF16(s, &len);
		else
			len = 0;
	} else {
		uni_str = (unsigned char *)s->getCString();
		len = s->getLength();
	}

	if (len < 2)
		len = 0;
	else
		len = len/2 - 1;
	uni = new Unicode[len];
	for (i = 0; i < len; i++)
		uni[i] = (uni_str[2 + i*2]<<8) + uni_str[2+i*2+1];
	*length = len;
	if (!s->hasUnicodeMarker())
		delete[] uni_str;

	return uni;
}

static char *unicodeToChar (Unicode *unicode, int len)
{
	static UnicodeMap *uMap = NULL;
	if (uMap == NULL) {
		GooString *enc = new GooString("UTF-8");
		uMap = globalParams->getUnicodeMap(enc);
		uMap->incRefCnt ();
		delete enc;
	}
		
	GooString gstr;
	char buf[8]; /* 8 is enough for mapping an unicode char to a string */
	int i, n;
	char *result;

	for (i = 0; i < len; ++i) {
		n = uMap->mapUnicode(unicode[i], buf, sizeof(buf));
		gstr.append(buf, n);
	}

	result = new char[gstr.getLength() + 1];
	strcpy(result, gstr.getCString());

	return result;
}

static char *gooStringToChar(GooString *s)
{
	Unicode *uni;
	int len;
	char *result;

	uni = gooStringToUnicode(s, &len);
	result = unicodeToChar(uni, len);
	delete[] uni;
	return result;
}


static char* getInfoString(Dict *dict, char *key)
{
	Object obj;
	GooString *goo_str;
	char *result;

	if (!dict->lookup(key, &obj)->isString()) {
		obj.free();
		return NULL;
	}
	goo_str = obj.getString();
	result = gooStringToChar(goo_str);
	obj.free();
	return result;
}

void dumpOutlineItems(GooList *items, Catalog *catalog, FILE *output);

void dumpOutlineItem(OutlineItem *item, Catalog *catalog, FILE *output)
{
	char *title = NULL;
	LinkAction *action;
	LinkGoTo *link_goto;
	LinkDest *dest;
	GooString *namedDest;
	int page_num;
	GooList *kids;

	item->open();
	title = unicodeToChar(item->getTitle(),
			      item->getTitleLength());
	action = item->getAction();
	if (!action || !action->isOk() || action->getKind() != actionGoTo)
		goto out;
	link_goto = dynamic_cast<LinkGoTo *>(action);
	namedDest = link_goto->getNamedDest();
	dest = link_goto->getDest();
	if (namedDest && !dest)
		dest = catalog->findDest(namedDest);
	if (!dest)
		goto out;
	if (dest->isPageRef()) {
		Ref ref = dest->getPageRef();
		page_num = catalog->findPage(ref.num, ref.gen);
	} else
		page_num = dest->getPageNum();
	fputs("<bookmark>\n", output);

	fputs_simple_mark("title", title, output);

	fprintf(output, "<page>%d</page>\n", page_num);

	if (item->hasKids()) {
		kids = item->getKids();
		dumpOutlineItems(kids, catalog, output);
	}
	fputs("</bookmark>\n", output);

out:
	if (title)
		delete[] title;
	item->close();
	return;
}

void dumpOutlineItems(GooList *items, Catalog *catalog, FILE *output)
{
	int i, len;
	OutlineItem *item;

	len = items->getLength();

	fputs("<bookmarks>\n", output);
	for (i = 0; i < len; i++) {
		item = (OutlineItem *)items->get(i);
		dumpOutlineItem(item, catalog, output);
	}
	fputs("</bookmarks>\n", output);
}

void dumpDocOutline(PDFDoc *doc, FILE *output)
{
	Outline *outline;
	GooList *items;

	outline = doc->getOutline();
	if (!outline)
		goto empty;
	items = outline->getItems();
	if (!items)
		goto empty;

	dumpOutlineItems(items, doc->getCatalog(), output);
	return;
empty:
	fputs("<bookmarks></bookmarks>\n", output);
	
}

int main(int argc, char *argv[])
{
	PDFDoc *doc = NULL;
	GooString *fileName = NULL;
	GBool ok;
	GooString *ownerPW, *userPW;
	Object info;
	FILE *output = stdout;

	// parse args
	ok = parseArgs(argDesc, &argc, argv);
	if (!ok || argc < 2 || argc > 3 || printHelp || printVersion) {
		fprintf(stderr, "pdfminfo version %s, based on "
			"Xpdf version %s\n", "0.36", xpdfVersion);
		fprintf(stderr, "%s\n\n", xpdfCopyright);
		if (!printVersion) {
			printUsage("pdfminfo", "<PDF-file>", argDesc);
		}
		exit(1);
	}
 
	// read config file
	globalParams = new GlobalParams();

	if (errQuiet)
		globalParams->setErrQuiet(errQuiet);

	if (textEncName[0]) {
		globalParams->setTextEncoding(textEncName);
		if( !globalParams->getTextEncoding() )
			goto error;    
	}

	// open PDF file
	if (ownerPassword[0]) {
		ownerPW = new GooString(ownerPassword);
	} else {
		ownerPW = NULL;
	}
	if (userPassword[0]) {
		userPW = new GooString(userPassword);
	} else {
		userPW = NULL;
	}

	fileName = new GooString(argv[1]);

	doc = new PDFDoc(fileName, ownerPW, userPW);
	if (userPW) {
		delete userPW;
	}
	if (ownerPW) {
		delete ownerPW;
	}
	if (!doc->isOk()) {
		goto error;
	}

	// check for copy permission
	if (!doc->okToCopy()) {
		if (!noDrm) {
			error(-1, "Copying of text from this "
			      "document is not allowed.");
			goto error;
		}
		fprintf(stderr, "Document has copy-protection bit set.\n");
	}

	printf("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
	printf("<pdfminfo>\n");

	doc->getDocInfo(&info);
	if (info.isDict()) {
		Dict *dict = info.getDict();
		char *s;
		s = getInfoString(dict, "Title");
		if (s)
			fputs_simple_mark("doc_title", s, output);
		s = getInfoString(dict, "Author");
		if (s)
			fputs_simple_mark("author", s, output);
		s = getInfoString(dict, "Keywords");
		if (s)
			fputs_simple_mark("keywords", s, output);
		s = getInfoString(dict, "Subject");
		if (s)
			fputs_simple_mark("subject", s, output);
	}
	info.free();

	fprintf(output, "<pages>%d</pages>\n", doc->getNumPages());

	dumpDocOutline(doc, output);

	printf("</pdfminfo>\n");

	// clean up
error:
	if(doc) delete doc;
	if(globalParams) delete globalParams;

	// check for memory leaks
	Object::memCheck(stderr);
	gMemReport(stderr);

	return 0;
}

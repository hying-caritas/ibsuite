/*
  Convert HTML to image using mozilla render engine.
  
  Copyright: Huang Ying <huang.ying.caritas@gmail.com> 2008

  Some code is copied from Mozilla2PS of Michele Baldessari
  <michele@pupazzo.org>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; version 2 of the License.

  This program is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301
  USA
*/

function WebProgressListener() {
    var self = this;
    self.onDone = function() { dump("onDone\n"); };
}

WebProgressListener.prototype.
QueryInterface = function(iid) {
    var self = this;
    if (iid.equals(Components.interfaces.nsIWebProgressListener) ||
	iid.equals(Components.interfaces.nsISupportsWeakReference) ||
	iid.equals(Components.interfaces.nsISupports))
	return self;

    throw Components.results.NS_ERROR_NO_INTERFACE;
};

WebProgressListener.prototype.
onStateChange = function(webProgress, request, stateFlags, status) {
    var self = this;
    const WPL = Components.interfaces.nsIWebProgressListener;

    if (stateFlags & WPL.STATE_IS_NETWORK) {
	if (stateFlags & WPL.STATE_STOP) {
	    self.onDone();
	}
    }
};

WebProgressListener.prototype.
onProgressChange = function(webProgress, request, curSelf, maxSelf,
			    curTotal, maxTotal) { };

WebProgressListener.prototype.
onLocationChange = function(webProgress, request, location) { };

WebProgressListener.prototype.
onStatusChange = function(webProgress, request, status, message) { };

WebProgressListener.prototype.
onSecurityChange = function(webProgress, request, state) { };

function HtmlCanvas() {
    var self = this;
    self.browser = document.getElementById("browser");
    self.onPageLoaded = function() { dump("onPageLoaded\n"); };
    self.onSaved = function() { dump("onSaved\n"); };
};

HtmlCanvas.prototype.setTextZoom = function(factor) {
    var self = this;
    var cview = self.browser.docShell.contentViewer;
    var dview = cview.QueryInterface(Components.interfaces.
				     nsIMarkupDocumentViewer);
    dview.textZoom = factor;
};

HtmlCanvas.prototype.setWidth = function(width) {
    var self = this;
    self.browser.style.width = width + "px";
    self.browser.width = width;
};

HtmlCanvas.prototype.loadPage = function(url) {
    var self = this;
    var listener = new WebProgressListener();
    listener.onDone = function () { self._onPageLoaded(); };
    self.browser.addProgressListener(listener, Components.interfaces.
				     nsIWebProgress.NOTIFY_STATUS);
    self.browser.loadURI(url, null, null);
};

HtmlCanvas.prototype._onPageLoaded = function() {
    var self = this;
    var cwin = self.browser.contentWindow;
    var cdoc = self.browser.contentDocument;

    //Draw canvas
    var doc_root = cdoc.documentElement;
    var w = doc_root.scrollWidth;
    var h = doc_root.scrollHeight;
    if ("body" in cdoc) {
	w = Math.max(w, cdoc.body.scrollWidth);
	h = Math.max(h, cdoc.body.scrollHeight);
    }
    var trunk = 10240;
    self.canvases = [];
    var canvas;
    var ctx;
    var y = 0;
    var remain = h;
    var th;
    while (remain) {
	if (remain < trunk)
	    th = remain;
	else
	    th = trunk;
	canvas = cdoc.createElement("canvas");
	canvas.style.width = w + "px";
	canvas.style.height = h + "px";
	canvas.width = w;
	canvas.height = th;
	ctx = canvas.getContext("2d");
	ctx.clearRect(0, 0, w, trunk);
	ctx.save();
	ctx.drawWindow(cwin, 0, y, w, th, "rgb(0,0,0)");
	remain -= th;
	y += th;
	ctx.restore();
	self.canvases.push(canvas)
    }
    self.savedCount = 0;
    self.onPageLoaded();
};

HtmlCanvas.prototype.saveCanvas = function(canvas, fileName) {
    var self = this;
    // convert string filepath to an nsIFile
    var file = Components.classes["@mozilla.org/file/local;1"].
	createInstance(Components.interfaces.nsILocalFile);
    file.initWithPath(fileName);

    // create a data url from the canvas and then create URIs of the
    // source and targets
    var io = Components.classes["@mozilla.org/network/io-service;1"].
	getService(Components.interfaces.nsIIOService);
    var source = io.newURI(canvas.toDataURL("image/png", ""),
			   "UTF8", null);
    var target = io.newFileURI(file);

    // prepare to save the canvas data
    var persist = Components.classes["@mozilla.org/embedding/browser/nsWebBrowserPersist;1"].createInstance(Components.interfaces.nsIWebBrowserPersist);

    persist.persistFlags = Components.interfaces.nsIWebBrowserPersist.
	PERSIST_FLAGS_REPLACE_EXISTING_FILES;
    persist.persistFlags |= Components.interfaces.nsIWebBrowserPersist.
	PERSIST_FLAGS_AUTODETECT_APPLY_CONVERSION;

    // save the canvas data to the file
    var listener = new WebProgressListener();
    listener.onDone = function() { self.onCanvasSaved(); }
    persist.progressListener = listener;
    persist.saveURI(source, null, null, null, null, file);
};

HtmlCanvas.prototype.onCanvasSaved = function() {
    var self = this;
    self.savedCount++;
    if (self.savedCount == self.canvases.length)
	self.onSaved();
};

HtmlCanvas.prototype.save = function(fileName) {
    function formatNumber(num) {
	var b = "000000";
	var snum = num.toString();
	return b.substr(0, b.length - snum.length) + snum;
    }
    var self = this;
    var i;
    for (i = 0; i < self.canvases.length; i++) {
	var ename = fileName.replace('%d', formatNumber(i));
	self.saveCanvas(self.canvases[i], ename);
    }
};

function Html2Img(url, imgFile, options) {
    var hc = new HtmlCanvas();
    hc.onPageLoaded = function() { hc.save(imgFile); };
    hc.onSaved = function () { window.close(); };
    hc.setWidth(options.width);
    hc.setTextZoom(options.zoom);
    hc.loadPage(url);
}

function onLoad() {
    try {
	var wCmdLn = window.arguments[0];
	nsCmdLn = wCmdLn.QueryInterface(Components.interfaces.nsICommandLine);
	var options = { zoom : 1.2, width : 754 };
	var param;
	param = nsCmdLn.handleFlagWithParam("zoom", false);
	if (param)
	    options.zoom = param;
	param = nsCmdLn.handleFlagWithParam("width", false);
	if (param)
	    options.width = param;
	if (nsCmdLn.length != 2) {
	    dump("Wrong number of arguments. Expected <source> <destination>\n");
	    window.close();
	}
	var url = nsCmdLn.getArgument(0);
	var imgFile = nsCmdLn.getArgument(1);
	Html2Img(url, imgFile, options);
    }
    catch(e) {
	dump(e + "\n");
	window.close();
    }
}

function init() {
    window.addEventListener("load", onLoad, false);
}

init();

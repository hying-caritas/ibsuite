/*
  Convert HTML to PDF with mozilla rendering engine.

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

  Michele Baldessari <michele@pupazzo.org> 2006
  Huang Ying <huang.ying.caritas@gmail.com> 2008
*/

function WebProgressListener() {
    var self = this;
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

    if (stateFlags & WPL.STATE_STOP) {
	if ("onDone" in self)
	    self.onDone();
	if (stateFlags & WPL.STATE_IS_NETWORK)
	    if ("onNetworkDone" in self)
		self.onNetworkDone();
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

function HtmlPrinter() {
    var self = this;
    self.browser = document.getElementById("browser");
    self.onPageLoaded = function() { dump("onPageLoaded\n"); };
    self.onPrinted = function() { dump("onPrinted\n"); };
};

HtmlPrinter.prototype.loadPage = function(url) {
    var self = this;
    var listener = new WebProgressListener();
    listener.onNetworkDone = function() { self.onPageLoaded(); };
    self.browser.addProgressListener(listener, Components.interfaces.
				     nsIWebProgress.NOTIFY_STATUS);
    self.browser.loadURI(url, null, null);
};

HtmlPrinter.prototype.print = function(fileName, options) {
    var self = this;
    var ifreq = content.QueryInterface(Components.interfaces.
				       nsIInterfaceRequestor);
    var webBrowserPrint = ifreq.getInterface(Components.interfaces.
					     nsIWebBrowserPrint);
    var gPrintSettings = webBrowserPrint.globalPrintSettings;

    gPrintSettings.marginTop = -0.24;
    gPrintSettings.marginBottom = -0.24;
    gPrintSettings.marginLeft = -0.24;
    gPrintSettings.marginRight = -0.24;
    gPrintSettings.edgeLeft = 0;
    gPrintSettings.edgeTop = 0;
    gPrintSettings.edgeRight = 0;
    gPrintSettings.edgeBottom = 0;
    gPrintSettings.footerStrLeft = "";
    gPrintSettings.footerStrCenter = "";
    gPrintSettings.footerStrRight = "";
    gPrintSettings.headerStrLeft = "";
    gPrintSettings.headerStrCenter = "";
    gPrintSettings.headerStrRight = "";
    gPrintSettings.printToFile = true;
    gPrintSettings.printSilent = true;
    gPrintSettings.toFileName = fileName;
    gPrintSettings.paperWidth = options.width;
    gPrintSettings.paperHeight = options.height;
    //gPrintSettings.paperName = "Letter";
    gPrintSettings.showPrintProgress = false;
    // Adobe Postscript Drivers are expected (together with a FILE:
    // printer called "Generic PostScript Printer". Drivers can be
    // found here:
    // http://www.adobe.com/support/downloads/product.jsp?product=44&platform=Windows
    var runtime = Components.classes["@mozilla.org/xre/app-info;1"].
    getService(Components.interfaces.nsIXULRuntime);
    var OS = runtime.OS;
    if (OS == "WINNT")
	gPrintSettings.printerName = "Generic PostScript Printer";
    else
	gPrintSettings.printerName = "PostScript/default";

    var listener = new WebProgressListener();
    listener.onDone = function() { self.onPrinted(); };
    webBrowserPrint.print(gPrintSettings, listener);
};

function Html2Pdf(url, pdfFile, options) {
    var hp = new HtmlPrinter();
    hp.onPageLoaded = function() {
	var printit = function() {
	    try {
		hp.print(pdfFile, options);
	    } catch (e) {
		dump(e + "\n");
		window.close();
	    }
	};
	window.setTimeout(printit, 0);
    };
    hp.onPrinted = function() {
	var quit = function() { window.close(); };
	window.setTimeout(quit, 0);
    };
    hp.loadPage(url);
}

function onLoad() {
    try {
	var wCmdLn = window.arguments[0];
	nsCmdLn = wCmdLn.QueryInterface(Components.interfaces.nsICommandLine);
	var options = { width : 6.4, height : 4.8 };
	var param;
	param = nsCmdLn.handleFlagWithParam("pw", false);
	if (param)
	    options.width = param;
	param = nsCmdLn.handleFlagWithParam("ph", false);
	if (param)
	    options.height = param;
	if (nsCmdLn.length != 2) {
	    dump("Wrong number of arguments. Expected <source> <destination>\n");
	    window.close();
	    return;
	}
	var url = nsCmdLn.getArgument(0);
	var pdfFile = nsCmdLn.getArgument(1);
	Html2Pdf(url, pdfFile, options);
    }
    catch(e) {
	dump(e + "\n");
	window.close();
    }
}

function init() {
    addEventListener("load", onLoad, false);
}

init();

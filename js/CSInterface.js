/**
 * CSInterface.js - Minimal CEP API wrapper
 * Based on Adobe CEP SDK (simplified for this extension)
 */

var SystemPath = {
    HOST_APPLICATION: "hostApplication",
    COMMON:           "common",
    MY_DOCUMENTS:     "myDocuments",
    APPLICATION:      "application",
    EXTENSION:        "extension",
    DESKTOP:          "desktop",
    TEMPORARY:        "temporary",
    OS_EXTENSION:     "OSExtension",
};

function CSInterface() {}

CSInterface.prototype.evalScript = function (script, callback) {
    if (window.__adobe_cep__) {
        if (typeof callback === "function") {
            window.__adobe_cep__.evalScript(script, callback);
        } else {
            window.__adobe_cep__.evalScript(script);
        }
    }
};

CSInterface.prototype.getSystemPath = function (pathType) {
    if (window.__adobe_cep__) {
        var result = window.__adobe_cep__.getSystemPath(pathType);
        // CEP returns a file:// URL — strip the protocol and decode %20 etc.
        result = result.replace(/^file:\/\/\//, "/")   // file:///Users/... → /Users/...
                       .replace(/^file:\/\//, "/")     // file://Users/...  → /Users/...
                       .replace(/^file:\//, "/");      // file:/Users/...   → /Users/...
        result = decodeURIComponent(result);
        // Strip trailing slash
        if (result.length > 1 && (result.charAt(result.length - 1) === "/" || result.charAt(result.length - 1) === "\\")) {
            result = result.slice(0, -1);
        }
        return result;
    }
    return "";
};

CSInterface.prototype.closeExtension = function () {
    if (window.__adobe_cep__) window.__adobe_cep__.closeExtension();
};

/* kb_common.js - helpers shared by the Knowledge Base pages (plain fetch, no libraries).
   Everything that comes from the server or the AI model is inserted with textContent, never as HTML. */
(function () {
  "use strict";

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) { n.className = cls; }
    if (text !== undefined && text !== null) { n.textContent = text; }
    return n;
  }

  function errorText(status, data) {
    if (data && typeof data.detail === "string" && data.detail) { return data.detail; }
    if (status === 401) { return "Your session has expired. Please sign in again."; }
    if (status === 403) { return "You do not have permission to do this."; }
    if (status === 503) { return "The knowledge base service is not running right now. Please try again later."; }
    return "Something went wrong (error " + status + "). Please try again.";
  }

  /* Calls one of our own endpoints. Always resolves with parsed JSON or throws Error(English message). */
  async function call(url, csrf, options) {
    options = options || {};
    var headers = Object.assign({ "X-CSRFToken": csrf, "Accept": "application/json" }, options.headers || {});
    var init = Object.assign({ credentials: "same-origin" }, options, { headers: headers });
    var res;
    try {
      res = await fetch(url, init);
    } catch (e) {
      throw new Error("Could not reach the server. Check your connection and try again.");
    }
    var data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) { throw new Error(errorText(res.status, data)); }
    if (data === null) { throw new Error("The server sent an answer the page cannot read. Please sign in again and retry."); }
    return data;
  }

  function showAlert(box, kind, message) {
    box.replaceChildren();
    var note = el("div", "alert alert-" + kind, message);
    note.setAttribute("role", kind === "danger" ? "alert" : "status");
    box.appendChild(note);
  }

  window.KB = { el: el, call: call, showAlert: showAlert };
})();

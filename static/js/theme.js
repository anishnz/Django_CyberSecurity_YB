/* theme.js - Display options: dark mode and larger text (saved in this browser only).
   Loaded in <head> so the page does not flash. No inline JavaScript (CSP). Owner: Dinesh Upreti. */
(function () {
  "use strict";
  var root = document.documentElement;
  function read(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function write(key, value) { try { localStorage.setItem(key, value); } catch (e) { /* private mode: ignore */ } }
  function apply() {
    root.setAttribute("data-bs-theme", read("cq-theme") === "dark" ? "dark" : "light");
    root.classList.toggle("cq-large", read("cq-large") === "1");
  }
  apply();
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-display-toggle]").forEach(function (btn) {
      var kind = btn.getAttribute("data-display-toggle");
      function sync() {
        var on = kind === "dark" ? read("cq-theme") === "dark" : read("cq-large") === "1";
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      }
      sync();
      btn.addEventListener("click", function () {
        if (kind === "dark") { write("cq-theme", read("cq-theme") === "dark" ? "light" : "dark"); }
        else { write("cq-large", read("cq-large") === "1" ? "0" : "1"); }
        apply();
        sync();
      });
    });
  });
}());

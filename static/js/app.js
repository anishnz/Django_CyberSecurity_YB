/* app.js - small helpers (no external libraries, works offline)
   Owner: Dinesh Upreti (Frontend Developer)
   1. Teacher question form: show only the categories of the chosen level,
      show/hide fields for each question type.
   2. Confirm buttons: ask "Are you sure?" before deleting (data-confirm). */
document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("question-form");
  if (form) {
    var levelSelect = form.querySelector("[name=level]");
    var categorySelect = form.querySelector("[name=category]");
    var typeSelect = form.querySelector("[name=q_type]");
    var all = JSON.parse(form.dataset.categories || "{}");
    var chosen = categorySelect.dataset.selected || "";
    function fillCategories() {
      var list = all[levelSelect.value] || [];
      categorySelect.innerHTML = "";
      list.forEach(function (pair) {
        var option = document.createElement("option");
        option.value = pair[0];
        option.textContent = pair[1];
        if (pair[0] === chosen) { option.selected = true; }
        categorySelect.appendChild(option);
      });
    }
    function showTypeFields() {
      var type = typeSelect.value;
      form.querySelectorAll("[data-for]").forEach(function (el) {
        var types = el.dataset.for.split(" ");
        el.hidden = types.indexOf(type) === -1;
        el.querySelectorAll("input, textarea").forEach(function (input) { input.disabled = el.hidden; });
        if (type === "true_false") { form.querySelectorAll("[name=correct]").forEach(function (c) { c.closest("span").hidden = (c.value === "C" || c.value === "D"); }); }
      });
    }
    levelSelect.addEventListener("change", function () { chosen = ""; fillCategories(); });
    typeSelect.addEventListener("change", showTypeFields);
    fillCategories();
    showTypeFields();
  }
  document.querySelectorAll("form[data-confirm]").forEach(function (f) {
    f.addEventListener("submit", function (event) {
      if (!window.confirm(f.dataset.confirm)) { event.preventDefault(); }
    });
  });
});

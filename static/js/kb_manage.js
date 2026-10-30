/* kb_manage.js - the "Manage Knowledge Base" page. Needs kb_common.js.
   Element ids match apps/kb/templates/kb/manage.html. Endpoint URLs come from data-* attributes. */
document.addEventListener("DOMContentLoaded", function () {
  "use strict";
  var root = document.getElementById("kb-app");
  if (!root || !window.KB) { return; }

  var el = window.KB.el;
  var csrf = root.dataset.csrf;
  var documentsUrl = root.dataset.documentsUrl;
  var quizUrl = root.dataset.quizUrl;
  var canDelete = root.dataset.canDelete === "1";
  var alertBox = document.getElementById("kb-alert");
  var docsBody = document.getElementById("kb-docs-body");

  function flash(kind, message) { window.KB.showAlert(alertBox, kind, message); }

  // ---- document list ----
  function messageRow(text, cls) {
    var tr = el("tr");
    var td = el("td", cls, text);
    td.colSpan = 4;
    tr.appendChild(td);
    return tr;
  }

  function renderDocs(docs) {
    docsBody.replaceChildren();
    if (!docs.length) {
      docsBody.appendChild(messageRow("No documents yet. Upload one above.", "text-muted"));
      return;
    }
    docs.forEach(function (d) {
      var tr = el("tr");
      tr.appendChild(el("td", null, d.title));
      tr.appendChild(el("td", "text-muted", d.tags || ""));
      tr.appendChild(el("td", "text-end", String(d.chunks)));
      var act = el("td", "text-end");
      if (canDelete) {
        var del = el("button", "btn btn-sm btn-outline-danger", "Delete");
        del.type = "button";
        del.setAttribute("aria-label", "Delete " + d.title);
        del.addEventListener("click", function () { removeDoc(d); });
        act.appendChild(del);
      }
      tr.appendChild(act);
      docsBody.appendChild(tr);
    });
  }

  async function loadDocs() {
    try {
      var data = await window.KB.call(documentsUrl, csrf);
      renderDocs(Array.isArray(data.documents) ? data.documents : []);
    } catch (err) {
      docsBody.replaceChildren();
      docsBody.appendChild(messageRow(err.message, "text-danger"));
    }
  }

  async function removeDoc(d) {
    if (!window.confirm("Delete \"" + d.title + "\" from the Knowledge Base? This cannot be undone.")) { return; }
    try {
      await window.KB.call(documentsUrl + encodeURIComponent(d.doc_id) + "/", csrf, { method: "DELETE" });
      flash("info", "Deleted \"" + d.title + "\".");
      await loadDocs();
    } catch (err) {
      flash("danger", err.message);
    }
  }

  // ---- upload (custom file button, so the browser's own language is never shown) ----
  var upForm = document.getElementById("kb-upload-form");
  var upBtn = document.getElementById("kb-upload-btn");
  var upBusy = document.getElementById("kb-upload-busy");
  var fileInput = document.getElementById("kb-file");
  var fileName = document.getElementById("kb-file-name");
  var NO_FILE = "No file chosen";

  fileInput.addEventListener("change", function () {
    fileName.textContent = fileInput.files.length ? fileInput.files[0].name : NO_FILE;
  });

  upForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (upBtn.disabled) { return; }
    var file = fileInput.files[0];
    if (!file) {
      flash("danger", "Please choose a file to upload.");
      return;
    }
    var fd = new FormData();
    fd.append("file", file);
    fd.append("title", document.getElementById("kb-title").value.trim());
    fd.append("tags", document.getElementById("kb-tags").value.trim());
    upBtn.disabled = true;
    upBusy.classList.remove("d-none");
    try {
      // No Content-Type header: the browser adds the multipart boundary itself.
      var data = await window.KB.call(documentsUrl, csrf, { method: "POST", body: fd });
      flash("success", "Uploaded. The document was split into " + data.chunks + " chunks.");
      upForm.reset();
      fileName.textContent = NO_FILE;
      await loadDocs();
    } catch (err) {
      flash("danger", err.message);
    } finally {
      upBtn.disabled = false;
      upBusy.classList.add("d-none");
    }
  });

  // ---- quiz ----
  var quizForm = document.getElementById("kb-quiz-form");
  var quizBtn = document.getElementById("kb-quiz-btn");
  var quizBusy = document.getElementById("kb-quiz-busy");
  var quizOut = document.getElementById("kb-quiz-out");

  function showQuiz(data) {
    quizOut.replaceChildren();
    if (!data.parsed) {
      quizOut.appendChild(el("div", "alert alert-warning",
        "The model did not return the questions in the expected format. Here is its raw answer; try Generate again for a cleaner result."));
      var pre = el("pre", "small border rounded p-2", data.raw || "");
      pre.style.whiteSpace = "pre-wrap";
      quizOut.appendChild(pre);
      return;
    }
    var questions = Array.isArray(data.questions) ? data.questions : [];
    if (!questions.length) {
      quizOut.appendChild(el("div", "alert alert-warning", "No questions were returned. Try a different topic."));
    }
    questions.forEach(function (q, i) {
      var card = el("div", "card mb-3");
      var body = el("div", "card-body");
      body.appendChild(el("h3", "h6", "Q" + (i + 1) + ". " + q.question));
      var ul = el("ul", "list-unstyled mb-2");
      (Array.isArray(q.options) ? q.options : []).forEach(function (o) { ul.appendChild(el("li", null, String(o))); });
      body.appendChild(ul);
      var det = el("details");
      det.appendChild(el("summary", "small", "Show answer"));
      det.appendChild(el("p", "mb-0 mt-2 small", "Answer: " + q.answer + (q.explanation ? ". " + q.explanation : "")));
      body.appendChild(det);
      card.appendChild(body);
      quizOut.appendChild(card);
    });
    var titles = [];
    (Array.isArray(data.sources) ? data.sources : []).forEach(function (s) {
      if (titles.indexOf(s.title) === -1) { titles.push(s.title); }
    });
    if (titles.length) { quizOut.appendChild(el("p", "small text-muted", "Based on: " + titles.join(", "))); }
  }

  quizForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (quizBtn.disabled) { return; }
    var topic = document.getElementById("kb-topic").value.trim();
    quizOut.replaceChildren();
    if (!topic) {
      window.KB.showAlert(quizOut, "danger", "Please type a topic first.");
      return;
    }
    var count = parseInt(document.getElementById("kb-count").value, 10);
    if (!(count >= 1 && count <= 20)) {
      window.KB.showAlert(quizOut, "danger", "The number of questions must be a whole number from 1 to 20.");
      return;
    }
    quizBtn.disabled = true;
    quizBusy.classList.remove("d-none");
    try {
      var data = await window.KB.call(quizUrl, csrf, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: topic, count: count, difficulty: document.getElementById("kb-diff").value })
      });
      showQuiz(data);
    } catch (err) {
      window.KB.showAlert(quizOut, "danger", err.message);
    } finally {
      quizBtn.disabled = false;
      quizBusy.classList.add("d-none");
    }
  });

  // ---- model settings (Super Admin only: the section is not in the page for other roles) ----
  var modelUrl = root.dataset.modelUrl;
  var modelTestUrl = root.dataset.modelTestUrl;
  var modelForm = document.getElementById("kb-model-form");
  if (modelUrl && modelTestUrl && modelForm) {
    var mAlert = document.getElementById("kb-model-alert");
    var mBusy = document.getElementById("kb-model-busy");
    var mSave = document.getElementById("kb-model-save");
    var mTest = document.getElementById("kb-model-test");
    var fields = {
      display_name: document.getElementById("kb-m-name"),
      base_url: document.getElementById("kb-m-url"),
      model_id: document.getElementById("kb-m-id"),
      temperature: document.getElementById("kb-m-temp"),
      max_tokens: document.getElementById("kb-m-tokens"),
      timeout: document.getElementById("kb-m-timeout")
    };
    var keyInput = document.getElementById("kb-m-key");
    var keyMask = document.getElementById("kb-m-key-mask");

    function fillModel(cfg) {
      Object.keys(fields).forEach(function (k) {
        fields[k].value = cfg[k] === undefined || cfg[k] === null ? "" : String(cfg[k]);
      });
      keyMask.textContent = cfg.api_key_masked || "not set";
      keyInput.value = "";
    }

    function setModelBusy(on) {
      mSave.disabled = on;
      mTest.disabled = on;
      mBusy.classList.toggle("d-none", !on);
    }

    async function loadModel() {
      try {
        fillModel(await window.KB.call(modelUrl, csrf));
      } catch (err) {
        window.KB.showAlert(mAlert, "danger", "Could not load the model settings. " + err.message);
      }
    }

    modelForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      if (mSave.disabled) { return; }
      var payload = {};
      Object.keys(fields).forEach(function (k) { payload[k] = fields[k].value.trim(); });
      payload.api_key = keyInput.value.trim();
      setModelBusy(true);
      try {
        var cfg = await window.KB.call(modelUrl, csrf, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        fillModel(cfg);
        window.KB.showAlert(mAlert, "success", "Model settings saved.");
      } catch (err) {
        window.KB.showAlert(mAlert, "danger", err.message);
      } finally {
        setModelBusy(false);
      }
    });

    mTest.addEventListener("click", async function () {
      if (mTest.disabled) { return; }
      setModelBusy(true);
      try {
        var res = await window.KB.call(modelTestUrl, csrf, { method: "POST" });
        window.KB.showAlert(mAlert, "success", "Connection works. The model replied: " + (res.reply || "(empty reply)"));
      } catch (err) {
        window.KB.showAlert(mAlert, "danger", "Connection test failed. " + err.message);
      } finally {
        setModelBusy(false);
      }
    });

    loadModel();
  }

  loadDocs();
});

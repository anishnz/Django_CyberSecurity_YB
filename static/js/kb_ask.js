/* kb_ask.js - the "Ask" page. Needs kb_common.js. Element ids match apps/kb/templates/kb/ask.html. */
document.addEventListener("DOMContentLoaded", function () {
  "use strict";
  var root = document.getElementById("kb-app");
  var form = document.getElementById("kb-ask-form");
  var input = document.getElementById("kb-question");
  var btn = document.getElementById("kb-ask-btn");
  var busy = document.getElementById("kb-busy");
  var out = document.getElementById("kb-result");
  if (!root || !form || !input || !btn || !busy || !out || !window.KB) { return; }

  var el = window.KB.el;
  var askUrl = root.dataset.askUrl;
  var csrf = root.dataset.csrf;

  function setBusy(on) {
    btn.disabled = on;
    input.readOnly = on;
    busy.classList.toggle("d-none", !on);
  }

  function showAnswer(data) {
    out.replaceChildren();
    var card = el("div", "card mb-3");
    var body = el("div", "card-body");
    body.appendChild(el("h2", "h5", "Answer"));
    var answer = el("div", "kb-answer", data.answer || "No answer was returned.");
    answer.style.whiteSpace = "pre-wrap";
    body.appendChild(answer);
    card.appendChild(body);
    out.appendChild(card);

    var sources = Array.isArray(data.sources) ? data.sources : [];
    var sCard = el("div", "card");
    var sBody = el("div", "card-body");
    sBody.appendChild(el("h2", "h6", "Sources"));
    if (!sources.length) {
      sBody.appendChild(el("p", "small text-muted mb-0", "No sources were used for this answer."));
    } else {
      var list = el("ul", "list-unstyled small mb-0");
      sources.forEach(function (s) {
        var li = el("li", "mb-2");
        li.appendChild(el("strong", null, "[" + s.n + "] " + (s.title || "Untitled")));
        if (s.snippet) { li.appendChild(el("div", "text-muted", s.snippet + "...")); }
        list.appendChild(li);
      });
      sBody.appendChild(list);
    }
    sCard.appendChild(sBody);
    out.appendChild(sCard);
  }

  function showError(message) {
    window.KB.showAlert(out, "danger", message);
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (btn.disabled) { return; }
    var question = input.value.trim();
    if (!question) {
      showError("Please type a question first.");
      input.focus();
      return;
    }
    setBusy(true);
    out.replaceChildren();
    try {
      var data = await window.KB.call(askUrl, csrf, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question })
      });
      showAnswer(data);
    } catch (err) {
      showError(err.message);
    } finally {
      setBusy(false);
    }
  });

  // Keyboard shortcut: Ctrl and Enter together also send the question (silent, no hint on the page).
  input.addEventListener("keydown", function (e) {
    if (e.ctrlKey && e.key === "Enter") {
      e.preventDefault();
      form.requestSubmit();
    }
  });
});

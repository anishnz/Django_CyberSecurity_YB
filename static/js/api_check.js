/* api_check.js - Check buttons on the API check page.
   Owner: Jihe Qi (QA / Integrations)
   Each row has data-url and data-method. "Check" calls the endpoint with fetch()
   and shows the HTTP status, the time and a short message. "Check all" runs the
   rows of its table one after another. */
document.addEventListener("DOMContentLoaded", function () {
  var tokenInput = document.querySelector("#api-csrf [name=csrfmiddlewaretoken]");
  var token = tokenInput ? tokenInput.value : "";

  function show(cell, ok, title, detail) {
    cell.innerHTML = "";
    var pill = document.createElement("span");
    pill.className = "pill " + (ok ? "pill-ok" : "pill-bad");
    pill.textContent = (ok ? "✓ " : "✗ ") + title;
    cell.appendChild(pill);
    if (detail) {
      var small = document.createElement("div");
      small.className = "small text-muted mt-1";
      small.textContent = detail;
      cell.appendChild(small);
    }
  }

  function summary(data) {
    if (Array.isArray(data)) { return data.length + " item" + (data.length === 1 ? "" : "s"); }
    if (data && data.endpoints) { return data.endpoints.length + " endpoints"; }
    if (data && data.plans) { return data.plans.length + " plans"; }
    if (data && data.status) { return "status " + data.status + ", database " + data.database; }
    if (data && "connected" in data) { return data.message; }
    return "";
  }

  function check(row) {
    var cell = row.querySelector(".api-result");
    var button = row.querySelector("[data-check]");
    var method = row.dataset.method;
    var started = performance.now();
    button.disabled = true;
    cell.innerHTML = '<span class="small text-muted">Checking…</span>';
    var options = { method: method, credentials: "same-origin", headers: { "Accept": "application/json" } };
    if (method === "POST") { options.headers["X-CSRFToken"] = token; }
    return fetch(row.dataset.url, options)
      .then(function (res) {
        return res.json().then(function (body) { return { res: res, body: body }; });
      })
      .then(function (r) {
        var ms = Math.round(performance.now() - started);
        var head = r.res.status + " " + (r.res.ok ? "OK" : r.res.statusText) + " · " + ms + " ms";
        if (!r.body.ok) { show(cell, false, "Failed", head + " – " + r.body.error); return; }
        var data = r.body.data;
        if (data && "connected" in data) {
          show(cell, data.connected, data.connected ? "Connected" : "Not connected", head + " – " + data.message);
        } else {
          show(cell, true, "Successful connection", head + " – " + summary(data));
        }
      })
      .catch(function (err) { show(cell, false, "No answer", String(err)); })
      .finally(function () { button.disabled = false; });
  }

  document.querySelectorAll("[data-api-row]").forEach(function (row) {
    row.querySelector("[data-check]").addEventListener("click", function () { check(row); });
  });
  document.querySelectorAll("[data-check-all]").forEach(function (button) {
    button.addEventListener("click", function () {
      var rows = button.closest("[data-api-group]").querySelectorAll("[data-api-row]");
      var chain = Promise.resolve();
      rows.forEach(function (row) { chain = chain.then(function () { return check(row); }); });
    });
  });
});

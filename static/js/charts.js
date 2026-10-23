/* charts.js - Draws Chart.js charts from <canvas data-chart="id"> + a JSON script tag.
   No inline JavaScript (Content Security Policy). Owner: Dinesh Upreti. */
(function () {
  "use strict";
  if (typeof Chart === "undefined") { return; }
  var css = getComputedStyle(document.documentElement);
  var blue = css.getPropertyValue("--harbour-2").trim() || "#16606B";
  var palette = [blue, "#2E7D4F", "#F2B705", "#0E3B43", "#B3263A", "#5B6E72"];
  document.querySelectorAll("canvas[data-chart]").forEach(function (canvas) {
    var source = document.getElementById(canvas.dataset.chart);
    if (!source) { return; }
    var data = JSON.parse(source.textContent);
    var kind = canvas.dataset.kind || "bar";
    var cfg;
    if (kind === "activity") {
      cfg = { type: "bar", data: { labels: data.labels, datasets: [
        { type: "bar", label: "Exams finished", data: data.exams, backgroundColor: blue, yAxisID: "y", order: 2 },
        { type: "line", label: "Average score %", data: data.average, borderColor: "#B8860B", backgroundColor: "#B8860B", yAxisID: "y1", tension: 0.3, order: 1, pointRadius: 5 }
      ] }, options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: "Exams" } },
        y1: { position: "right", min: 0, max: 100, grid: { drawOnChartArea: false }, title: { display: true, text: "%" } } } } };
    } else if (kind === "doughnut") {
      cfg = { type: "doughnut", data: { labels: data.labels, datasets: [{ data: data.values, backgroundColor: palette }] },
        options: { maintainAspectRatio: false } };
    } else {
      cfg = { type: "bar", data: { labels: data.labels, datasets: [{ label: data.label || "", data: data.values, backgroundColor: blue }] },
        options: { indexAxis: data.horizontal ? "y" : "x", maintainAspectRatio: false, plugins: { legend: { display: false } },
          scales: { x: { beginAtZero: true, max: data.max || undefined }, y: { beginAtZero: true } } } };
    }
    new Chart(canvas, cfg);
  });
}());

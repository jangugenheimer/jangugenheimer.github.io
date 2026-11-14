// Publications page: venue filter and a small timeline (one dot per paper).
// Without JavaScript the page is the plain list with the year links.
(function () {
  var box = document.getElementById("pubviz");
  var pubs = Array.prototype.slice.call(document.querySelectorAll(".pub[data-venue]"));
  if (!box || !pubs.length) return;

  var ALIAS = { "ACM TOCHI": "TOCHI", "IEEE TVCG": "TVCG", "AutomotiveUI": "AutoUI" };
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function family(venue) {
    var v = venue.replace(/\s*\b(19|20)\d\d\b/, "").replace(/\s*\(.*\)/, "").trim();
    return ALIAS[v] || v;
  }

  // Group papers by venue family.
  var counts = {};
  pubs.forEach(function (p) {
    p._family = family(p.dataset.venue);
    counts[p._family] = (counts[p._family] || 0) + 1;
    p.style.viewTransitionName = "pub-" + p.id;
  });
  var families = Object.keys(counts)
    .sort(function (a, b) { return counts[b] - counts[a] || a.localeCompare(b); });
  var chipsData = [["All", pubs.length]].concat(families.map(function (f) { return [f, counts[f]]; }));

  // Venue chips.
  var venues = box.querySelector(".venues");
  var chips = chipsData.map(function (c) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.dataset.family = c[0];
    b.innerHTML = c[0] + " <span>" + c[1] + "</span>";
    b.addEventListener("click", function () { apply(c[0]); });
    venues.appendChild(b);
    return b;
  });

  // Timeline: one column per year, one dot per paper.
  var timeline = box.querySelector(".timeline");
  var years = pubs.map(function (p) { return +p.dataset.year; });
  var first = Math.min.apply(null, years), last = Math.max.apply(null, years);
  var tip = document.createElement("div");
  tip.className = "viz-tip";
  tip.hidden = true;
  box.appendChild(tip);
  var dots = [], labels = {}, n = 0;
  for (var y = first; y <= last; y++) {
    var col = document.createElement("div");
    col.className = "tl-col";
    var stack = document.createElement("div");
    stack.className = "tl-dots";
    pubs.filter(function (p) { return +p.dataset.year === y; }).reverse().forEach(function (p) {
      var d = document.createElement("a");
      d.className = "dot" + (p.dataset.award ? " dot--award" : "");
      d.href = "#" + p.id;
      d.style.setProperty("--i", n++);
      d.setAttribute("aria-label", p.dataset.title + " (" + p.dataset.venue + ")");
      d._pub = p;
      d.addEventListener("mouseenter", function () { showTip(d); });
      d.addEventListener("focus", function () { showTip(d); });
      d.addEventListener("mouseleave", hideTip);
      d.addEventListener("blur", hideTip);
      d.addEventListener("click", function () { if (p.hidden) apply("All", true); });
      stack.appendChild(d);
      dots.push(d);
    });
    var label = document.createElement("a");
    label.className = "tl-year";
    label.href = "#y" + y;
    label.textContent = "’" + String(y).slice(2);
    label.setAttribute("aria-label", "Jump to " + y);
    labels[y] = label;
    col.appendChild(stack);
    col.appendChild(label);
    timeline.appendChild(col);
  }

  function showTip(d) {
    var p = d._pub;
    tip.innerHTML = "";
    var v = document.createElement("span");
    v.textContent = p.dataset.venue + (p.dataset.award ? " · " + p.dataset.award : "");
    tip.appendChild(v);
    tip.appendChild(document.createTextNode(p.dataset.title));
    tip.hidden = false;
    var b = box.getBoundingClientRect(), r = d.getBoundingClientRect();
    var x = r.left + r.width / 2 - b.left;
    var half = tip.offsetWidth / 2;
    x = Math.max(half + 8, Math.min(b.width - half - 8, x));
    tip.style.left = x + "px";
    tip.style.top = (r.top - b.top - 10) + "px";
  }
  function hideTip() { tip.hidden = true; }

  var status = box.querySelector(".viz-status");
  var sections = Array.prototype.slice.call(document.querySelectorAll(".year"));

  function update(f) {
    var shown = 0;
    pubs.forEach(function (p) {
      p.hidden = f !== "All" && p._family !== f;
      if (!p.hidden) shown++;
    });
    sections.forEach(function (s) {
      var any = !!s.querySelector(".pub:not([hidden])");
      s.hidden = !any;
      var l = labels[s.id.slice(1)];
      if (l) l.classList.toggle("is-off", !any);
    });
    dots.forEach(function (d) { d.classList.toggle("is-off", d._pub.hidden); });
    chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.family === f ? "true" : "false"); });
    status.textContent = f === "All" ? "" :
      shown + (shown === 1 ? " paper" : " papers") + " at " + f;
  }

  function apply(f, instant) {
    if (document.startViewTransition && !reduced && !instant) {
      document.startViewTransition(function () { update(f); });
    } else {
      update(f);
    }
  }

  var yearsNav = document.querySelector(".years");
  if (yearsNav) yearsNav.hidden = true;     // the timeline's year labels replace the year links
  box.hidden = false;
  update("All");
})();

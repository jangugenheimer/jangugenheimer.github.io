// Publications page: type tabs, venue filter and a small timeline (one dot per entry).
// Without JavaScript the page is the plain list with the year links.
(function () {
  var box = document.getElementById("pubviz");
  var pubs = Array.prototype.slice.call(document.querySelectorAll(".pub[data-venue]"));
  if (!box || !pubs.length) return;

  var TYPES = [["all", "All"], ["paper", "Papers"], ["poster", "Posters"], ["demo", "Demos"],
               ["workshop", "Workshops"], ["other", "Other"]];
  var ALIAS = { "ACM TOCHI": "TOCHI", "IEEE TVCG": "TVCG", "AutomotiveUI": "AutoUI" };
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var state = { type: "paper", venue: "All" };

  // "CHI EA 2025", "UIST Adjunct 2018" and "CHI Workshop 2022" all count as their conference.
  function family(venue) {
    var v = venue.replace(/\s*\b(19|20)\d\d\b/, "").replace(/\s*\(.*\)/, "")
      .replace(/\s+(EA|Adjunct|Companion|Workshop)$/, "").trim();
    return ALIAS[v] || v || "Other";
  }
  function inType(p) { return state.type === "all" || p.dataset.type === state.type; }
  function label(type) {
    for (var i = 0; i < TYPES.length; i++) if (TYPES[i][0] === type) return TYPES[i][1];
    return type;
  }

  pubs.forEach(function (p) {
    p._family = family(p.dataset.venue);
    p.style.viewTransitionName = "pub-" + p.id;
  });

  // Type tabs.
  var typesBox = box.querySelector(".types");
  var tabs = TYPES.filter(function (t) {
    return t[0] === "all" || pubs.some(function (p) { return p.dataset.type === t[0]; });
  }).map(function (t) {
    var n = t[0] === "all" ? pubs.length : pubs.filter(function (p) { return p.dataset.type === t[0]; }).length;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tab";
    b.dataset.type = t[0];
    b.innerHTML = t[1] + " <span>" + n + "</span>";
    b.addEventListener("click", function () {
      state.type = t[0];
      state.venue = "All";
      apply();
    });
    typesBox.appendChild(b);
    return b;
  });

  // Venue chips, rebuilt for the selected type.
  var venues = box.querySelector(".venues");
  var chips = [];
  function renderChips() {
    var counts = {}, total = 0;
    pubs.filter(inType).forEach(function (p) { counts[p._family] = (counts[p._family] || 0) + 1; total++; });
    var data = [["All", total]].concat(Object.keys(counts)
      .sort(function (a, b) { return counts[b] - counts[a] || a.localeCompare(b); })
      .map(function (f) { return [f, counts[f]]; }));
    venues.innerHTML = "";
    chips = data.map(function (c) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.dataset.family = c[0];
      b.innerHTML = c[0] + " <span>" + c[1] + "</span>";
      b.addEventListener("click", function () { state.venue = c[0]; apply(); });
      venues.appendChild(b);
      return b;
    });
  }

  // Timeline: one column per year, one dot per entry.
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
      d.addEventListener("click", function () { if (p.hidden) { state.venue = "All"; apply(true); } });
      stack.appendChild(d);
      dots.push(d);
    });
    var yl = document.createElement("a");
    yl.className = "tl-year";
    yl.href = "#y" + y;
    yl.textContent = "’" + String(y).slice(2);
    yl.setAttribute("aria-label", "Jump to " + y);
    labels[y] = yl;
    col.appendChild(stack);
    col.appendChild(yl);
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

  function update() {
    renderChips();
    var shown = 0;
    pubs.forEach(function (p) {
      p.hidden = !(inType(p) && (state.venue === "All" || p._family === state.venue));
      if (!p.hidden) shown++;
    });
    sections.forEach(function (s) {
      var any = !!s.querySelector(".pub:not([hidden])");
      s.hidden = !any;
      var l = labels[s.id.slice(1)];
      if (l) l.classList.toggle("is-off", !any);
    });
    dots.forEach(function (d) {
      d.hidden = !inType(d._pub);
      d.classList.toggle("is-off", d._pub.hidden);
    });
    tabs.forEach(function (t) { t.setAttribute("aria-pressed", t.dataset.type === state.type ? "true" : "false"); });
    chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.family === state.venue ? "true" : "false"); });
    var what = state.type === "all" ? (shown === 1 ? "entry" : "entries")
      : state.type === "other" ? (shown === 1 ? "other entry" : "other entries")
      : (shown === 1 ? label(state.type).slice(0, -1) : label(state.type)).toLowerCase();
    status.textContent = state.venue === "All" ? "" : shown + " " + what + " at " + state.venue;
  }

  function apply(instant) {
    if (document.startViewTransition && !reduced && !instant) {
      document.startViewTransition(update);
    } else {
      update();
    }
  }

  var yearsNav = document.querySelector(".years");
  if (yearsNav) yearsNav.hidden = true;     // the timeline's year labels replace the year links
  box.hidden = false;
  update();
})();

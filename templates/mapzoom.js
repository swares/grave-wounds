/* Map zoom, for the field and travel maps (built into each page): − and + buttons, Fit, and two-finger
   pinch on the map. The map's svg is drawn wider or narrower and the box scrolls, so a tap still lands
   on the hex drawn under it. The page's own size is zoom 1; the zoom holds when the map is redrawn. */
const MAPZOOM = (() => {
  const STEP = 2, MAX = 4;
  function attach(box){
    let f = 1, base = 0, pinch = null, vb = "";
    const bar = document.createElement("div");
    bar.className = "zoombar";
    bar.innerHTML = '<button type="button" class="small" data-z="out" aria-label="Zoom out">−</button>'
      + '<button type="button" class="small" data-z="in" aria-label="Zoom in">+</button>'
      + '<button type="button" class="small" data-z="fit">Fit</button><span class="muted zoomno" aria-live="polite"></span>'
      + '<span class="muted zoomtip">Two fingers to zoom on a phone.</span>';
    box.before(bar);
    const svg = () => box.querySelector(":scope > svg");
    const natural = s => {                       // the page's own width for the map, before any zoom
      const st = s.style.width; s.style.width = ""; s.style.minWidth = s.dataset.minw ?? s.style.minWidth; s.style.maxWidth = s.dataset.maxw ?? s.style.maxWidth;
      const w = s.getBoundingClientRect().width; s.style.width = st; return w;
    };
    const lo = () => { const s = svg(); if (s && (s.getAttribute("viewBox") || "") !== vb){ s.dataset.minw = s.style.minWidth; s.dataset.maxw = s.style.maxWidth; vb = s.getAttribute("viewBox") || ""; base = natural(s) } return base ? Math.min(1, box.clientWidth / base) : 1 };
    function apply(at){                          // at: [x, y] in the box's view to hold still
      const s = svg();
      if (!s) return;
      if (s.dataset.minw === undefined){ s.dataset.minw = s.style.minWidth; s.dataset.maxw = s.style.maxWidth }
      const v = s.getAttribute("viewBox") || "";
      if (!base || v !== vb){ vb = v; base = natural(s) }   // another map (or battlefield): its own size is zoom 1
      f = Math.min(MAX, Math.max(lo(), f));
      const old = s.getBoundingClientRect().width || base, w = base * f, k = w / old;
      const [ax, ay] = at || [box.clientWidth / 2, box.clientHeight / 2];
      const sx = box.scrollLeft, sy = box.scrollTop;
      s.style.minWidth = "0"; s.style.maxWidth = "none"; s.style.width = `${w.toFixed(1)}px`;
      if (k !== 1){ box.scrollLeft = (sx + ax) * k - ax; box.scrollTop = (sy + ay) * k - ay }
      bar.querySelector(".zoomno").textContent = `${Math.round(f * 100)}%`;
      bar.querySelector('[data-z="in"]').disabled = f >= MAX - 1e-6;
      bar.querySelector('[data-z="out"]').disabled = f <= lo() + 1e-6;
    }
    bar.addEventListener("click", e => {
      const b = e.target.closest("button[data-z]");
      if (!b) return;
      f = b.dataset.z === "in" ? f * STEP : b.dataset.z === "out" ? f / STEP : lo();
      apply();
    });
    new MutationObserver(() => { const s = svg(); if (s && s.style.width !== `${(base * f).toFixed(1)}px`) apply([0, 0]) }).observe(box, { childList: true });
    const gap = t => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
    const mid = t => { const r = box.getBoundingClientRect(); return [(t[0].clientX + t[1].clientX) / 2 - r.left, (t[0].clientY + t[1].clientY) / 2 - r.top] };
    box.addEventListener("touchstart", e => {
      if (e.touches.length !== 2) return;
      pinch = { d: gap(e.touches), f };
      e.preventDefault();
    }, { passive: false });
    box.addEventListener("touchmove", e => {
      if (!pinch || e.touches.length !== 2) return;
      e.preventDefault();
      f = pinch.f * gap(e.touches) / pinch.d;
      apply(mid(e.touches));
    }, { passive: false });
    box.addEventListener("touchend", e => { if (e.touches.length < 2) pinch = null });
    window.addEventListener("resize", () => { if (svg()) apply() });
    return { get zoom(){ return f }, set: z => { f = z; apply() } };
  }
  return { attach };
})();

/* Phone tabs, for the field and travel maps: buttons [data-tab] in #tabs; the page's parts carry
   data-pane (one or more tab names) and show only on their tabs (data-on, an attribute, so a page
   that rewrites an element's classes does not hide it). On a desktop the CSS shows every part.
   body[data-tab] names the open tab, for a page's own rules. */
const PHONETABS = (() => {
  let now = null, after = () => {};
  function set(t){
    now = t;
    document.body.dataset.tab = t;
    document.querySelectorAll("[data-pane]").forEach(el => el.toggleAttribute("data-on", el.dataset.pane.split(" ").includes(t)));
    document.querySelectorAll("#tabs [data-tab]").forEach(b => b.setAttribute("aria-selected", b.dataset.tab === t));
    if (matchMedia("(max-width:640px)").matches) scrollTo(0, 0);
    after();
  }
  function init(first, then){
    after = then || after;
    document.querySelectorAll("#tabs [data-tab]").forEach(b => b.onclick = () => set(b.dataset.tab));
    set(first);
  }
  return { init, set, get now(){ return now } };
})();

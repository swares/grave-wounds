/* US or metric units on every page (roller, travel map, field map). The rules and data stay
   metric; only what is shown and typed changes. One setting for all pages, remembered in
   the browser, US unless the reader picks metric. build.py puts this file into each page at
   its MEASURE_JS marker. */
const UNITS_KEY = "gravewounds-units";
let unitSystem = "us";
try{ unitSystem = localStorage.getItem(UNITS_KEY) === "metric" ? "metric" : "us" }catch(e){ unitSystem = "us" /* storage off: US */ }
const isUS = () => unitSystem === "us";
const roundTo = (x, places) => { const p = 10 ** places; return Math.round(x * p) / p };
// A distance in metres: yards in US units.
function fmtM(m, places = 0){ return isUS() ? `${roundTo(m * 1.0936133, places)} yd` : `${roundTo(m, places)} m` }
// A distance in kilometres: miles in US units.
function fmtKm(km, places = 1){ return isUS() ? `${roundTo(km * 0.62137119, places)} mi` : `${roundTo(km, places)} km` }
// A speed in km/h: mph in US units.
function fmtKmh(kmh, places = 1){ return isUS() ? `${roundTo(kmh * 0.62137119, places)} mph` : `${roundTo(kmh, places)} km/h` }
// A temperature in degrees C: degrees F in US units.
const tempOut = c => (isUS() ? roundTo(c * 9 / 5 + 32, 0) : c);
const tempIn = v => (isUS() ? roundTo((v - 32) * 5 / 9, 1) : v);
const tempUnit = () => (isUS() ? "°F" : "°C");
function fmtC(c){ return `${tempOut(c)} ${tempUnit()}` }
// A temperature change (a climate shift): no 32 offset.
function fmtCDelta(c){ return isUS() ? `${roundTo(c * 9 / 5, 1)} °F` : `${c} °C` }
// The US | Metric switch in a page's header. onChange redraws the page.
function unitToggle(el, onChange){
  const draw = () => {
    el.innerHTML = ["us", "metric"].map(u => `<button type="button" class="small" data-units="${u}" aria-pressed="${unitSystem === u}">${u === "us" ? "US" : "Metric"}</button>`).join("");
  };
  el.addEventListener("click", e => {
    const b = e.target.closest("button[data-units]");
    if (!b || b.dataset.units === unitSystem) return;
    unitSystem = b.dataset.units;
    try{ localStorage.setItem(UNITS_KEY, unitSystem) }catch(err){ /* storage off: the choice lasts while the page is open */ }
    draw();
    onChange();
  });
  draw();
}

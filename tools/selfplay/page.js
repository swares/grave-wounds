// Loads the rules out of a built field page (dist/field.html), as the page itself runs them.
// load(html path, extra names) -> {FD, api}: api holds selfPlay, SeededDice, playStances and the names asked for.
// hook: a function called after every move's end (B, result, positions before the move), or null.
"use strict";
const fs = require("fs");
const path = require("path");

const DEFAULT_PAGE = path.join(__dirname, "..", "..", "dist", "field.html");

function load(htmlPath, extra = [], hook = null){
  const html = fs.readFileSync(htmlPath || DEFAULT_PAGE, "utf8");
  const FD = JSON.parse(html.match(/const FD = (\{.*?\});\n/s)[1]);
  let src = html.slice(html.indexOf("// Hex helpers"), html.indexOf("/* ---------- the page ---------- */"));
  if (hook){
    src = src.replace(/function endMove\(B, rng\)\{/, "function endMove(B, rng){ const before = B.units.map(u => u.pos && [...u.pos]); const r = endMove0(B, rng); HOOK(B, r, before); return r }\nfunction endMove0(B, rng){");
  }
  const names = ["selfPlay", "SeededDice", "playStances", ...extra].join(", ");
  const api = new Function("FD", "HOOK", src + `\nreturn {${names}};`)(FD, hook);
  return { FD, api };
}

module.exports = { load, DEFAULT_PAGE };

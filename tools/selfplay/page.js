// Loads the rules out of a built field page (dist/field.html), as the page itself runs them.
// load(html path, extra names, hook) -> {FD, api}: api holds selfPlay, SeededDice, playStances and the names asked for.
// hook: a function called after every move's end (B, result, positions before the move), or null.
// The page's rules are written out once, as a module, to .cache/ beside this file and loaded from there.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const DEFAULT_PAGE = path.join(__dirname, "..", "..", "dist", "field.html");
const CACHE = path.join(__dirname, ".cache");

function rulesModule(html, names, hooked){        // the path of a module exporting make(FD, HOOK) -> {names}
  let src = html.slice(html.indexOf("// Hex helpers"), html.indexOf("/* ---------- the page ---------- */"));
  if (hooked){
    src = src.replace(/function endMove\(B, rng\)\{/, "function endMove(B, rng){ const before = B.units.map(u => u.pos && [...u.pos]); const r = endMove0(B, rng); HOOK(B, r, before); return r }\nfunction endMove0(B, rng){");
  }
  const body = `"use strict";\nmodule.exports = function make(FD, HOOK){\n${src}\nreturn {${names.join(", ")}};\n};\n`;
  const file = path.join(CACHE, crypto.createHash("sha256").update(body).digest("hex").slice(0, 16) + ".js");
  if (!fs.existsSync(file)){
    fs.mkdirSync(CACHE, { recursive: true });
    const tmp = `${file}.${process.pid}`;
    fs.writeFileSync(tmp, body);
    fs.renameSync(tmp, file);                       // whole or not at all, with several runs starting at once
  }
  return file;
}
function load(htmlPath, extra = [], hook = null){
  const html = fs.readFileSync(htmlPath || DEFAULT_PAGE, "utf8");
  const FD = JSON.parse(html.match(/const FD = (\{.*?\});\n/s)[1]);
  const make = require(rulesModule(html, ["selfPlay", "SeededDice", "playStances", ...extra], !!hook));
  return { FD, api: make(FD, hook) };
}

module.exports = { load, DEFAULT_PAGE };

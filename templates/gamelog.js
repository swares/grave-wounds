/* The event log: what happened in the fight, in order, and who may see it in full. The page appends
   an event for each thing the rules decided (a strike, a wound applied); nothing is changed or taken
   out after, so the log is the fight's record and its dice can be checked afterwards.

   An event: {n, round, type, vis, data, pub}
     vis  who sees it in full: "public", or a list of seats ("side:Yorkists"). The GM sees everything.
     data the whole of it: the rolls, the wound, its effects.
     pub  what everyone else is shown instead (the outcome, where a blow landed), or null for nothing.
   viewFor(log, seat) gives one seat's slice: the GM's ("gm") is the whole log; a side's has its own
   events in full and the others' public part. A seat played from another screen would be sent only
   its slice, so a player never holds what he is not meant to see.

   The log is kept with the fight in the browser, the last LOG_KEEP events. build.py puts this file
   into the roller at its GAMELOG_JS marker; in Node it is a module. */
const LOG_KEEP = 500;
const GM_SEAT = "gm";
const sideSeat = side => `side:${side}`;

function logEvent(log, ev){                      // append an event, numbered after the last; -> the event
  const last = log.length ? log.at(-1).n : 0;
  const e = { n: last + 1, round: ev.round ?? null, type: ev.type, vis: ev.vis || "public", data: ev.data || {}, pub: ev.pub ?? null };
  log.push(e);
  if (log.length > LOG_KEEP) log.splice(0, log.length - LOG_KEEP);
  return e;
}
function canSee(e, seat){
  return seat === GM_SEAT || e.vis === "public" || (Array.isArray(e.vis) && e.vis.includes(seat));
}
function viewFor(log, seat){                     // the events as one seat sees them, oldest first
  const out = [];
  for (const e of log){
    if (canSee(e, seat)) out.push({ n: e.n, round: e.round, type: e.type, data: e.data, full: true });
    else if (e.pub) out.push({ n: e.n, round: e.round, type: e.type, data: e.pub, full: false });
  }
  return out;
}
function seatsIn(sides){                         // the seats at the table: the GM, then a seat per side
  return [GM_SEAT, ...[...new Set(sides)].map(sideSeat)];
}

if (typeof module !== "undefined") module.exports = { LOG_KEEP, GM_SEAT, sideSeat, logEvent, canSee, viewFor, seatsIn };   // Node (the tests)

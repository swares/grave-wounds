// Builds data/maps/badajoz-1812.yaml: the third British siege of Badajoz, 16 March to 6 April 1812, on
// the travel map at 1 km a hex, on the ground of the Albuera map (albuera_base.mjs). Run from this
// folder after editing: node make_badajoz.mjs
//
// Sources (project doc "siege-phase-research"; historyofwar, Third British siege of Badajoz; Wikipedia,
// Siege of Badajoz (1812)): Graham's divisions crossed the Guadiana and cut Badajoz off on 16 March;
// the first parallel was begun on the night of 17 March in heavy rain, within 200 yards of Fort
// Picurina; batteries opened on the 25th, the heavy breaching fire from 31 March; by 5 April the
// Trinidad and Santa Maria bastions were breached; Wellington waited a day for a third breach and
// stormed late on 6 April. The garrison: about 5,000 under Philippon. The allied army: about 27,000,
// the 3rd, 4th, 5th and Light Divisions and nine Portuguese regiments, with Graham's 1st, 6th and 7th
// Divisions out to block Soult. Soult gathered an army slowly and came up toward Villafranca (just
// off the map's south-east corner); on 7 April, Badajoz fallen, he turned back for Seville. Drouet's
// corps, which had watched Badajoz, was beaten at Villagarcia on 11 April.
// The fortress (Sieges, docs/travel.md): 21 days of siege work to a practicable breach (the siege
// lines start in place on 16 March, so that day counts; breached by the night of 5 April, stormed
// the next); 2,000 workers and 60 days' stores are ours (no source reached gives the working parties
// or the garrison's provisions). Forces are round figures for play: the split of the 27,000 between
// the siege and the Portuguese, and the strengths of Graham's corps, the allied cavalry, Drouet's
// corps and Soult's army, are ours.
import { buildCampaign } from "./campaign_lib.mjs";
import { GROUND, BOX, P } from "./albuera_base.mjs";

const NAMES = { badajoz: "Badajoz", siege: "Siege lines", elvas: "Elvas", olivenza: "Olivenza", valverde: "Valverde de Leganés",
  albuera: "La Albuera", almendral: "Almendral", nogales: "Nogales", talavera: "Talavera la Real ford", lobon: "Lobón",
  solana: "Solana de los Barros", santamarta: "Santa Marta", villalba: "Villalba de los Barros", almendralejo: "Almendralejo",
  fuente: "Fuente del Maestre", torre: "Torre de Miguel Sesmero" };
const notes = {
  badajoz: "Held by Philippon's French and Hessian garrison, about 5,000; besieged from 16 March 1812 and stormed on the night of 6 April",
  siege: "Wellington's siege lines: the first parallel begun on the night of 17 March, in heavy rain, within 200 yards of Fort Picurina",
  elvas: "The Portuguese fortress across the border: the allies' base and siege park",
  santamarta: "Toward Graham's covering position on the road south (his divisions went on toward Llerena, off the map)",
  fuente: "On the road from Seville: Soult came up toward Villafranca, just beyond, and turned back on 7 April",
};

const map = buildCampaign({
  id: "badajoz-1812", script: "make_badajoz.mjs", title: "The third siege of Badajoz, March and April 1812, from Elvas to Santa Marta",
  name: "Badajoz, 1812 (the third siege)",
  start_date: "1812-03-16", ...BOX,
  header: [
    "The same ground as the Albuera map (albuera_base.mjs). Towns and villages are at their modern places;",
    "the siege lines are only approximate; rivers, brooks, woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly (dates Gregorian): Wellington, having taken Ciudad Rodrigo in January, came south",
    "to Badajoz. On 16 March his army cut the town off; the first parallel was dug the next night in pouring",
    "rain, Fort Picurina was stormed on the 25th, and from 31 March the breaching batteries battered the",
    "Trinidad and Santa Maria bastions. Philippon's garrison sallied, retrenched and mined the breaches.",
    "Graham covered the siege to the south against Soult, who came up too late. On the night of 6 April the",
    "4th and Light Divisions failed at the breaches with dreadful loss, while Picton's 3rd Division took the",
    "castle by escalade and Leith's 5th the San Vicente bastion; the town fell and was sacked for three",
    "days. Badajoz is a fortress here (docs/travel.md, Sieges). Numbers below are round figures for play.",
  ],
  ...GROUND, names: NAMES, notes,
  places: { ...P, siege: [38.873, -6.966] },   // the siege lines before Fort Picurina, within a hex of the town, so that they invest it (1811's were further out)
  kinds: { siege: "camp", badajoz: "objective" },
  depots: { elvas: ["Allies"] },   // where each side resupplies (the garrison lives on its stores; project doc "depots-research")
  tongues: { olivenza: ["portuguese", "spanish"], elvas: ["portuguese"] },
  fortresses: { badajoz: { side: "France", breach_days: 21, workers: 2000, stores: 60 } },   // a fortress to besiege: see the header
  forces: [
    { name: "The siege corps (3rd, 4th, 5th and Light Divisions)", type: "foot", side: "Allies", men: 18000, tools: true, at: "siege" },
    { name: "Portuguese brigades at the siege", type: "foot", side: "Allies", men: 9000, tools: true, at: "siege" },
    { name: "Graham's covering corps (1st, 6th and 7th Divisions)", type: "foot", side: "Allies", men: 15000, tools: true, at: "santamarta" },
    { name: "Allied cavalry (Cotton)", type: "mounted", side: "Allies", men: 3000, tools: false, at: "santamarta" },
    { name: "Badajoz garrison (Philippon)", type: "foot", side: "France", men: 5000, tools: true, at: "badajoz" },
    { name: "Drouet's corps of observation", type: "foot", side: "France", men: 10000, tools: true, at: "fuente" },
    { name: "French cavalry", type: "mounted", side: "France", men: 2000, tools: false, at: "fuente" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);

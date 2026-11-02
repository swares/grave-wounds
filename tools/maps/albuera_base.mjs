// The ground of the Albuera map, shared by the 1811 campaign (make_albuera.mjs) and the 1812 siege of
// Badajoz (make_badajoz.mjs): places, rivers, woods, hills and roads. Sources and drawing as in
// make_albuera.mjs: towns and villages at their modern coordinates; rivers, brooks, woods and roads
// drawn by hand after the modern ones, approximate.
// ---------- places (lat, lon) ----------
export const P = {
  badajoz: [38.879, -6.970], siege: [38.860, -6.950], elvas: [38.881, -7.163], olivenza: [38.686, -7.101],
  valverde: [38.674, -6.983], albuera: [38.716, -6.822], almendral: [38.611, -6.818], nogales: [38.583, -6.738],
  talavera: [38.880, -6.770], lobon: [38.851, -6.623], solana: [38.722, -6.538], santamarta: [38.513, -6.623],
  villalba: [38.611, -6.511], almendralejo: [38.683, -6.407], fuente: [38.528, -6.448], torre: [38.611, -6.795],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) and brooks ----------
export const RIVERS = {
  guadiana: [[38.870, -6.300], [38.860, -6.520], "lobon", [38.875, -6.700], "talavera", [38.880, -6.880], "badajoz", [38.840, -7.040],
             [38.790, -7.100], [38.740, -7.170], [38.700, -7.230]],
};
export const STREAMS = [
  ["nogales", [38.650, -6.780], "albuera", [38.790, -6.860], [38.870, -6.900]],      // the Albuera, from the Nogales brook to the Guadiana
  [[38.600, -6.700], [38.680, -6.790], "albuera"],                                  // the Chicapierna
];
export const FORDS = ["talavera"];

// ---------- woods (olive groves and holm-oak), hills (centre, radius km) ----------
export const WOODS = [[[38.700, -6.760], 2.5], [[38.640, -6.700], 3], [[38.560, -6.560], 3], [[38.760, -7.000], 2.5], [[38.620, -6.900], 2.5]];
export const HILLS = [[[38.560, -6.900], 4], [[38.520, -6.740], 3]];

// ---------- roads (through places, in order) ----------
export const ROADS = [
  ["badajoz", "siege", "albuera", "torre", "santamarta", "fuente"],           // the Seville road
  ["badajoz", "elvas"], ["badajoz", "talavera", "lobon", [38.870, -6.380]],    // to Mérida
  ["olivenza", "valverde", "albuera"], ["albuera", "almendral", "nogales", "santamarta"], ["albuera", "solana", "almendralejo"],
  ["santamarta", "villalba", "almendralejo"], ["badajoz", "olivenza"],
];

export const TOWNS = ["badajoz", "elvas", "olivenza", "almendralejo"];
export const VILLAGES = ["valverde", "albuera", "almendral", "nogales", "lobon", "solana", "santamarta", "villalba", "fuente", "torre"];

export const BOX = { calendar: "gregorian", latitude: 39, climate: "mediterranean", climate_shift: -1, bounds: [-7.20, 38.95, -6.38, 38.48], midLat: 38.72, hexKm: 1 };
export const GROUND = { places: P, rivers: RIVERS, majorRivers: ["guadiana"], streams: STREAMS, fords: FORDS, woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES };

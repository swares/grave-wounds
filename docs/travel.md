# Grave Wounds: the travel map (playtest draft)

The travel page (`dist/travel.html`) moves forces from camp to the battlefield across a hex
map. All the numbers live in `data/terrain.yaml`, and the maps are in `data/maps/`. The
page and the Python engine (`gravewounds/travel.py`) read them from there, so change them
there.

## Scale and time

- Each hex is usually 0.6 mile (1 km). A map can set its own size with `hex_km`.
- A force marches 8 hours a day, starting at 08:00, at its type's speed on a road:

  | Force type | Road speed | A day on the road |
  |---|---|---|
  | On foot | 2.5 mph (4 km/h) | 20 miles (32 km) |
  | Mounted | 3.7 mph (6 km/h) | 30 miles (48 km) |
  | Baggage wagons | 1.9 mph (3 km/h) | 15 miles (24 km) |

- Wagons cannot enter forest, marsh, mountains or heath.
- These speeds are for a small, fit band. A large army's column, with its halts and its
  stragglers, made less ground a day; cut its hours or its speed to suit.

## Terrain

Each terrain has a time multiplier against marching on a road. Moving from one hex to the
next costs the average of the two hexes' multipliers, so a step from road into forest is
charged half road, half forest. Rivers, lakes and the sea cannot be entered; cross a river
only at a ford or a bridge.

| Terrain | Time | | Terrain | Time |
|---|---|---|---|---|
| Road, bridge, village, town | ×1 | | Forest | ×2.5 |
| Open ground, farmland | ×1.5 | | Marsh | ×3 |
| Heath | ×1.75 | | Mountains | ×4 |
| Hills, ford | ×2 | | River, lake or sea | impassable |

These multipliers are design estimates from the usual rule of thumb: going across country
takes about half as long again as a road, woods and hills about twice as long, and marsh
or mountains far longer. The printed tables give the km a day for each force type on each
terrain.

Each terrain also records **cover**, **forage** and whether it is **wet**. Nothing uses them
yet. They are there for later rules on ambush, food, and fevers in damp camps.

## A day's march

A force stops for the night rather than start a hex it cannot finish that day. So the
last hour of a day can be partly lost when the next hex is slow going. **March 1 hour**
moves the force one hour along its route. **March to day's end** uses the rest of the
day's marching hours. The next march starts the following morning, an hour after sunrise
(see [weather.md](weather.md)).

## Marching together

A force can march with another force on its side, such as a band with its baggage train.
Pick the other force under **March with**. It must be within 0.6 mile (1 km; the same or the next
hex). The joining force closes up onto the other's hex at no cost in time. If one force's
clock is later, the column moves off when the last of them is ready.

- **One route.** The first force leads, and the column's route is the leader's. Plan it with
  either force selected.
- **One pace.** The column keeps out of ground any of its forces cannot enter. It moves at
  its slowest force's road speed, and at its most tired force's share of that speed. A
  band of foot (2.5 mph, 4 km/h) with its wagons (1.9 mph, 3 km/h) goes at 1.9 mph and stays off forest,
  marsh, mountains and heath.
- **One clock.** Every force in the column marches, halts and rests together. Each keeps
  its own men, tools, fatigue and log.
- **One camp.** A column makes one camp, sized for all its men. All of them dig, and tools
  carried by any force serve all. The baggage train's men speed up the work, though its
  wagons need more room inside the camp.
- **Leaving.** Choose **on its own** to leave the column where it stands. If the leader is
  removed, or leaves, the next force leads the rest. Moving a follower with **Move force**
  takes it out of the column; moving the leader takes the whole column.

Going ahead without the baggage is quicker and keeps to rougher ground, but the train
then marches on its own and reaches camp later.

## Making camp

Each force has a number of men and either has tools or doesn't. **Make camp** spends the
time to make a bivouac, a watched camp, a staked camp, a fortified camp, or quarters in a
village or town. The time depends on the force's size and tools and on whether woods are
near. A column makes one camp for all its forces (see *Marching together*). Camp work can use 4 evening hours after the march, so a camp made at the end of the
day costs no marching time. Once an enemy force has marched to within 0.6 mile (1 km), **Set up the fight** opens a battle page.
**Fight it on** picks which:
- **the wound roller**, man by man (up to 8 men a force), with the camp's works laid out
  on its battle map. See [works.md](works.md).
- **the field map**, in units: the forces arrive with their fit men, and the GM splits each
  into units there (billmen, archers, horse). Men left out of every unit stay in reserve.
  The day's weather and ground come too, and the camp's works, as far as they are built,
  are laid out around the defenders. When the battle ends, **Back to the travel map** brings
  the result home: the dead come off each force, and its wounded join its sick (below).
  Each force's clock moves on to the battle's end: a minute an exchange from when it
  started. A battle that runs past the evening's hours goes into the night, with its rest
  and the sick's night, like camp work. See [units.md](units.md).
- **a battlefield**, when the defender stands near one: within a hex (3.1 miles, 5 km) of
  Azincourt on the Agincourt campaign map, the field of Agincourt is offered and picked by
  default (the GM can still choose open ground or the roller). The armies stand there as
  drawn up, scaled to the forces' fit men. See [units.md](units.md#battlefields).

## Disease and camp hygiene

Before antibiotics, disease emptied armies faster than battle. Each force keeps count of
its sick: who has what, and how bad it is (mending, serious, grave or deadly). The numbers
are in `data/disease.yaml` and the printed tables, and the design behind them is in
[design.md](design.md) (*Recovery, sickness and downtime*).

- **Catching it.** Once a week, on the night of each 7th day on the force's clock, every
  well man may catch bloody flux, camp fever (typhus), typhoid, ague or plague. His chance
  depends on the camp's **hygiene**, on staying 4 weeks or more in one place, on the ground
  (marsh, a town or village, hills), and on the past week's weather (hot, warm, or cold and
  wet). The Health section shows each disease's chance this week. Ague needs warm marsh
  country, and plague needs **Plague in the region**, a switch by the weather.
- **Hygiene** comes from the camp: a bivouac is poor, quarters in houses are good, and
  other camps are fair. The GM can set it per force under **Camp hygiene**.
- **The course of a case.** A case shows after its incubation, from a day or two for flux
  to weeks for ague, and climbs to its peak. After that it gets better or worse each
  night. Rest, a camp and shelter help; marching, no camp, cold wet nights and filth hurt.
  At deadly, a bad night kills. Survivors of typhus and plague are immune, ague comes back
  in marsh country, and flux can drag on as a chronic case.
- **What it costs.** Men at serious or worse do not dig or fight: camps take longer, and
  only the fit go into a fight. Grave and deadly cases are carried on litters, and the
  force marches at 90%, or 50% if it has fewer than two fit men a litter. A force with no
  fit men cannot march at all. Deaths come off the force's strength.

**The wounded.** Men wounded in a battle on the field map are carried to their force's camp
and heal on the same track, with the same nightly roll for better or worse, but by the
week: one check every 7 days. A man starts at mending, serious or grave by his wound, and
at grave if it would kill in hours untreated. Three to five days after the battle each
wound turns septic or does not, by the infection risk of the wound (5% low, 15% medium,
30% high; +5 with no camp, −5 in quarters). A septic wound is **wound fever**: a step
worse, checked every night, and deadly (about 60% die of it in an ordinary camp). Resting
in an ordinary camp, `python3 -m gravewounds disease` gives:

| Wound | Die | Wound fever | Days unfit |
|---|---|---|---|
| Light, low infection risk | 2% | 5% | 0 |
| Serious, medium risk | 11% | 17% | 8 |
| Critical, medium risk | 14% | 16% | 10 |
| Serious and deadly in hours, high risk | 26% | 30% | 9 |

No camp roughly doubles the deaths; quarters in houses roughly halve them. Design
estimates; the records are in the design doc's disease table (Union pyaemia was 97% fatal;
Richard I died of an infected crossbow wound eleven days after he was hit).

As a guide (`python3 -m gravewounds disease`):

| A force in camp, dry weather | Dead of disease |
|---|---|
| A fair camp held a year | about 9% |
| Six weeks in a poor bivouac | about 10% |
| Six weeks of a hot, filthy siege camp | about 23% (near Harfleur, 1415) |
| Good quarters for a year | under 1% |

Typhus needs crowding: it breaks out in a camp that is both filthy (poor hygiene) and held
four weeks or more.

## Calendar and weather

Days have real dates, and daylight sets each day's marching hours. The weather is rolled
each day, and mud, snow and flooded fords change the going. See [weather.md](weather.md).

## In the page

- **Forces.** Click a force in the list or on the map to select it. **Add a force** puts a
  new one at the camp.
- **Plan route.** Click hexes to add waypoints for the selected force. Clicking an enemy
  force sets its hex as the next waypoint (select a force with the Forces list or by
  clicking a force on its own side). The page fills in
  the quickest route between them, using roads where they help. It shows:
  - the distance
  - the marching time
  - when the force arrives
  - an **N1**, **N2** and so on wherever it camps for the night

  Add waypoints to force a different way, for example by the ford instead of the bridge.
- **Move force.** Click a hex to put the selected force there. This clears its route.
- **Paint terrain.** Pick a terrain and click or drag on the map. Routes that the new
  ground blocks are cleared.
  - **Show map file** and **Download map file** give the painted map as YAML. Save it as
    `data/maps/<id>.yaml` and rebuild to keep it.
  - **Undo all painting** goes back to the map as built.
- Forces, routes, clocks and painting are kept in your browser.

## Maps

The test map, `data/maps/generic-valley.yaml`, is a made-up river valley about 25 by 16 miles
(40 by 26 km):

- The camp is in the west.
- The objective, Gallows Ridge, is in the east beyond the river.
- The river can be crossed at the bridge by Brigham on the road, or at the ford below the
  lake (the long way round, past Kelsey Market).

**The Agincourt campaign, 1415** (`data/maps/agincourt-1415.yaml`) covers Henry V's march
from Harfleur to Calais on 3.1-mile (5 km) hexes: 49 × 46 hexes, about 150 by 125 miles
(245 by 200 km), from the Seine to the Channel coast past Calais. It starts on 8 October 1415
(Julian), the day the army left Harfleur, with four forces: Henry V's army and its baggage at
Harfleur, a French vanguard at Abbeville and the French main army at Rouen. (In 1415 the main
army marched to join the vanguard around Péronne, and the two fought together at Agincourt;
the King and the Dauphin stayed at Rouen.) The Somme can be
crossed only at its towns, the bridges at Pont-Remy, Picquigny and Bray, and the fords at
Blanchetaque, Béthencourt and Voyennes, so the GM can play out the hunt for a crossing.
The Seine, the Bresle, the Béthune, the Authie, the Canche and the Ternoise have bridges
where the roads cross them.

How it is drawn, and what it owes to whom:
- The coastline is Natural Earth's 1:50m land outline, which is public domain.
- Towns, bridges and fords are placed at their modern coordinates (plain facts). A coastal
  place whose hex came out as sea is moved to the nearest land hex.
- Rivers, woods, marsh, hills and roads are drawn by hand through those places. They follow
  the modern rivers and the march as the chronicles describe it, and are approximate: a
  3-mile hex shows that a river or a wood is there, not where its banks are.
- The coast and the Somme estuary have changed since 1415 (the bay has silted up, and
  Harfleur's harbour is gone). At this scale that changes little.
- England's Kent coast shows in the north-west corner, across the Channel. It is not part
  of the march.

The map is generated by `tools/maps/make_agincourt.mjs`. Edit that file and re-run it
(`cd tools/maps && npm ci && node make_agincourt.mjs`), rather than editing the YAML.

For the battle itself, the field map has the field of Agincourt at its real size (see
[units.md](units.md#battlefields)). A fight within a hex of Azincourt is offered on it.

**The Towton campaign, 1461** (`data/maps/towton-1461.yaml`) covers the last days before the
battle on 0.6-mile (1 km) hexes: 42 × 48 hexes, about 26 by 26 miles (42 by 42 km), from
Wakefield and Pontefract in the south to York in the north. It starts on 27 March 1461
(Julian), with six forces:
- Yorkist: Edward's army and Fauconberg's mounted vanward at Pontefract, Fitzwalter's men
  holding the Aire crossing at Brotherton, and the Duke of Norfolk's men coming up the road
  from the south at Wentbridge.
- Lancastrian: the Lancastrian army under Somerset at Towton, and Clifford's horse at
  Sherburn-in-Elmet.

The Aire can be crossed only at Ferrybridge, the ford at Castleford, and the towns on it
(Leeds); the Wharfe only at Wetherby and Tadcaster; the Ouse only at York and Selby. So the
GM can play out Clifford's attack on the Ferrybridge crossing and Fauconberg's march round
by Castleford. Cock Beck is a brook, slow wet ground rather than a river. The weather is a
cold maritime spring (a climate shift of −1.8 °F, −1 °C), so snow is possible.

How it is drawn: towns, villages, the bridge and the ford are at their modern places, and
the rivers, brooks, woods and roads are drawn by hand through them (approximate). The map
is generated by `tools/maps/make_towton.mjs`. The two campaign maps share their drawing
code, `tools/maps/campaign_lib.mjs`, so a new campaign is a new spec: places, rivers,
roads, woods and forces.

The field of Towton is on the field map too; a fight within 3 hexes of Towton (Saxton,
Lead and the ground between) is offered on it.

Campaign and battle maps can be added in the same format, one file per map:

- `terrain`: rows of one character per hex. The keys are listed in `data/terrain.yaml`.
- `places`: the camp, the objective, villages, towns and landmarks.
- `forces`: the forces at the start, each with a type, a side and a starting hex.

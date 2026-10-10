# Grave Wounds: the travel map (playtest draft)

The travel page (`dist/travel.html`) moves forces from camp to the battlefield across a hex
map. All the numbers live in `data/terrain.yaml`, and the maps are in `data/maps/`. The
page and the Python engine (`gravewounds/travel.py`) read them from there, so change them
there.

## Scale and time

- Each hex is usually 1 km. A map can set its own size with `hex_km`.
- A force marches 8 hours a day, starting at 08:00, at its type's speed on a road:

  | Force type | Road speed | A day on the road |
  |---|---|---|
  | On foot | 4 km/h | 32 km |
  | Mounted | 6 km/h | 48 km |
  | Baggage wagons | 3 km/h | 24 km |

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
Pick the other force under **March with**. It must be within 1 km (the same or the next
hex). The joining force closes up onto the other's hex at no cost in time. If one force's
clock is later, the column moves off when the last of them is ready.

- **One route.** The first force leads, and the column's route is the leader's. Plan it with
  either force selected.
- **One pace.** The column keeps out of ground any of its forces cannot enter. It moves at
  its slowest force's road speed, and at its most tired force's share of that speed. A
  band of foot (4 km/h) with its wagons (3 km/h) goes at 3 km/h and stays off forest,
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
day costs no marching time. Once an enemy force has marched to within 1 km, **Set up the fight** opens the battle map
with the camp's works, its men and the enemy laid out. See [works.md](works.md).

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

As a guide, six weeks in a poor bivouac costs a company of 200 about a tenth of its men
dead, with a third unable to march or fight. A siege camp in a hot summer (poor hygiene, staying put) costs about
a fifth dead. That is near the losses recorded at Harfleur in 1415.

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

The test map, `data/maps/generic-valley.yaml`, is a made-up river valley about 40 km by
26 km:

- The camp is in the west.
- The objective, Gallows Ridge, is in the east beyond the river.
- The river can be crossed at the bridge by Brigham on the road, or at the ford below the
  lake (the long way round, past Kelsey Market).

Campaign and battle maps can be added in the same format, one file per map:

- `terrain`: rows of one character per hex. The keys are listed in `data/terrain.yaml`.
- `places`: the camp, the objective, villages, towns and landmarks.
- `forces`: the forces at the start, each with a type, a side and a starting hex.

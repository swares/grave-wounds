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

## One clock

Every force on a map keeps the same time. The map's clock (**Now**, above the forces) moves
on only when the GM moves it, and every force moves with it:

- **Orders.** A force given a route marches on it (**Orders: March on its route**); clicking
  the map to add a waypoint gives that order. **Halt where it is** stops it without losing
  the route, and a force with no route waits. A column's orders are its leader's.
- **1 hour** moves the clock on an hour; **To nightfall** to the end of the day's marching
  hours; **Until something happens** on until a force reaches the end of its route, a camp is
  finished, or forces of different sides come within fighting reach, passing the nights on
  the way (up to two weeks). At nightfall the first button becomes **Through the night**:
  every force has its night (rest, fatigue, the sick) and the clock moves to the next
  morning, an hour after sunrise (see [weather.md](weather.md)).
- **Busy forces.** A force making camp, or fighting, is busy until it is done: its own time
  runs ahead of the clock and it does nothing else until the clock catches up. The forces
  list shows each force's own time.
- **Meetings.** The clock watches every quarter hour for forces of different sides coming
  within fighting reach (the same or the next hex). When they do, it stops, both halt, and
  the fight can be set up as usual, with the usual chance of surprise; or the GM gives them
  new orders and they march on past each other.
- **Part of a hex.** A march stopped in the middle of a hex keeps the time already spent on
  it, so an hour at a time gets as far as a whole day at once. A force still stops for the
  night rather than finish a hex after its marching hours.
- **Saved campaigns** from before the clock start it at their latest force's time; the
  others wait where they are until then, their nights passing in place.

## Marching together

A force can march with another force on its side, such as a band with its baggage train.
Pick the other force under **March with**. It must be within 0.6 mile (1 km; the same or the next
hex). The joining force closes up onto the other's hex at no cost in time. If one force's
clock is later (one still making camp, say), the column moves off when the last of them is ready.

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
  on its battle map and the ground laid out to match the defenders' hex: woods in forest,
  rises and rocks in hills, marsh in marsh, rubble in a village or town. Where the map
  reaches past a side of that hex, the neighbouring hex's ground (or a lake or river) shows
  along that edge. A fight on a road, ford or bridge has the road and river through the
  middle, and the attackers come in from the way they marched. See
  [works.md](works.md) and [combat.md](combat.md).
- **the field map**, in units: the forces arrive with their fit men, and the GM splits each
  into units there (billmen, archers, horse). Men left out of every unit stay in reserve, and their side can bring them on during the
  battle.
  The day's weather and ground come too, and the camp's works, as far as they are built,
  are laid out around the defenders. When the battle ends, **Back to the travel map** brings
  the result home: the dead come off each force, and its wounded join its sick (below).
  Each force's clock moves on to the battle's end: a minute an exchange from when it
  started. A battle that runs past the evening's hours goes into the night, with its rest
  and the sick's night, like camp work. See [units.md](units.md).
- **a battlefield**, when the defender stands near one: within a hex (3.1 miles, 5 km) of
  Azincourt on the Agincourt campaign map, the field of Agincourt is offered and picked by
  default (the GM can still choose open ground or the roller). The armies stand there as
  drawn up, at their drawn numbers at most (fewer if a force is smaller); the rest wait in
  reserve and can be brought on during the battle. See [units.md](units.md#battlefields).

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
| A fair camp held a year | about 8% |
| Six weeks in a poor bivouac | about 10% |
| Six weeks of a hot, filthy siege camp | about 22% (near Harfleur, 1415) |
| Good quarters for a year | under 1% |

These include nursing and contagion (below). In a large force they change the toll by less
than a run's own spread; they bite in a small force or one where many are already sick.

Typhus needs crowding: it breaks out in a camp that is both filthy (poor hygiene) and held
four weeks or more.

**Nursing and spread.** The men too sick to work (Serious or worse) need nursing: one fit man
for every 5 of them, taken off digging. Each week every nurse may catch what his patients
have, as in the design doc: bloody flux 6%, typhoid 3%, camp fever (typhus) 8% and plague 1% a
week if all his patients have it, scaled by the share who do, and resisted with Endurance as
any catch. **Nurses keep clean** (a switch on the force's health panel: washing, boiling, the
sick kept apart) stops flux and typhoid reaching them, but not typhus (lice) or plague. If
there are too few fit men, the sick beyond what the nurses can tend recover with no care
(−20), whatever the camp. Contagion: the whole camp's weekly chance of flux and typhus rises
by 2, and of typhoid by 1, for every tenth of the force already sick with it. The health note
says how many are nursing and how many go untended. These numbers are design estimates.

**Named characters.** In the wound roller, a fighter's card can put him **With** a force on
the travel map. From then on, each night the travel map runs his own course of disease
alongside the force's men: the same camp, care, weather and marching, and the same weekly
outbreak roll, but with his own **Endurance** (from his team-builder sheet, or 50, or as the
GM sets it on his card). He is not one of the force's men: he is never counted in its sick or
its dead. The force's health note lists its named men and how they are, and its log says when
one falls ill, recovers or dies. Back in the roller his card shows his sickness, and it
weakens him in a fight by the worst step he is at:

| Step | In a fight |
|---|---|
| Mending | −10% attack and defence |
| Serious | −25%, cannot run |
| Grave | −25%, crawls only, defends only |
| Deadly | too ill to fight |

A named man catches from the camp's contagion like anyone. With **Nurses the sick** ticked on
his card he also nurses: each week he rolls as a nurse for what the force's sick have (unless
he is too sick himself). A sick named man is nursed first, so he gets the camp's care while
anyone fit can tend him.

A case still incubating does not show or weaken him. A named man who dies of disease is out
of every fight.

**A named man's wounds in camp.** After a fight, the GM presses **To camp** on the card of a
named man who is with a force. Each of his wounds then goes onto the wound track with the
force's wounded. It starts at the step for its severity, or worse for a death clock, with its
septic roll a few days on, and heals or kills by the week as theirs do. In camp his bleeding
stops, and each night with the force gives him back 4 of his 20 points of blood. While a
wound heals, its own pain and impairment stay on his card. Only wound fever counts as sickness
in the table above. His card shows each wound's step ("healing: wounds, serious"). A healed
wound leaves his list and stays as a scar on his figure and sheet. If a wound kills him, his
card says he died of his wounds.

**A leech in camp.** A named man with a force who has **Leechcraft** on his team-builder
sheet tends its sick and wounded while he is alive and not too sick to work himself. The
best leech with the force adds Leechcraft ÷ 10 (rounded down) to every recovery check of its
sick and wounded and of the named men with it, and takes as much off each wound's chance of
turning septic. The sick beyond what the nurses can tend get none of it. The health note
names him. A design estimate.

**Scurvy.** Each force counts its days without fresh food (fruit, greens, fresh meat,
onions). The count goes back to nought on a day that ends in farmland, a village or a town;
in open ground, forest or hills if the force spent the whole day camped there and foraging
(it did not march), or on a march day there if a named man with the force finds it (his
**Fieldcraft**, rolled each such day, the best with the force); or every day while **Fresh
food issued** is ticked on its health panel. Other ground has none. The health note says how many days it has gone without, and whether
fresh food can be had where it stands.

After 6 weeks without fresh food, each week every well man may fall ill: 10% the first week,
10 more each week after, times the chance he fails to resist (half, for a typical man). It
shows at once, at Mending, and is checked once a week:

- With fresh food in the past week, it heals two steps.
- Without it, he makes the recovery check (Endurance, care, rest and conditions, virulence
  −3). Success holds, failure is a step worse, and failure at Deadly kills. It never
  improves unfed.

As a guide (`python3 -m gravewounds disease`), for men resting in an ordinary camp:

| Fresh food comes | Dead of scurvy |
|---|---|
| 4 weeks after it shows | about 2% (Union army: 1.6%) |
| 8 weeks after | about a third |
| 12 weeks after | about 70% |
| Never | all of them, in about 11 weeks on average |

A named man falls ill the same way. When he does, every old wound from his team-builder sheet
and every scar comes back on the wound track at Mending, and shows on his card as "Old
wounds reopened". They cannot heal while he has scurvy; after that they heal by the week as
any wound. These numbers are design estimates.

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
- **Health.** The selected force's camp hygiene, **Nurses keep clean** and **Fresh food
  issued**, with a note on its sick, nursing, days without fresh food and the week's chances.
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

**Gotland, 1361** (`data/maps/visby-1361.yaml`) covers Valdemar IV's invasion on 0.6-mile
(1 km) hexes: 34 × 55 hexes, about 21 by 30 miles (34 by 48 km), the west side of the
island from Eksta to Visby. It starts on 22 July 1361 (Julian), the day the Danes landed,
with three forces: Valdemar's army at Vivesholm by Klintehamn (one of the two likely
landing places; Kronvald on the Eksta coast is the other), and the Gotland levies of the
southern districts at Hejde and of the northern districts at Roma, where the island's
assembly met.
- The Gotlanders broke the bridge at Ajmunds, by Mästerby, but the Danes crossed Fjäle mire
  beside it, dry that summer, and won there; the mire is marsh on the map.
- Visby is the objective. Korsbetningen, outside its wall by the south gate, is where the
  last battle was fought, on 27 July.
- Gotland has no rivers to speak of at this scale, so the march is a matter of roads,
  woods and time.

How it is drawn: the coastline is Natural Earth's (public domain); the villages and
landmarks are at their modern places, some (the landing places, Ajmunds bridge, Fjäle mire)
only to within a mile or so; the woods and roads are drawn by hand. The map is generated by
`tools/maps/make_visby.mjs`. A fight within a hex of Visby is offered on the Visby
battlefield (see [units.md](units.md#battlefields)).

**Lützen, 1632** (`data/maps/lutzen-1632.yaml`) covers the campaign's last two days on
0.6-mile (1 km) hexes: 50 × 53 hexes, about 31 by 28 miles (50 by 46 km), from Naumburg on the
Saale to Leipzig, and north to Halle. It starts on 15 November 1632 (Gregorian; the Swedes
reckoned it 5 November) with seven forces:
- Swedish: the foot and the horse in their camp at Naumburg.
- Imperial: Wallenstein's army and its horse at Lützen, a rearguard holding the Rippach
  crossing, and Pappenheim's horse and foot away at Halle.

The Saale and the Weiße Elster can be crossed only at their towns. The Rippach and the
Floßgraben are brooks, wet slow ground, so a rearguard at Rippach can hold up an army
without stopping it. The climate is continental and a little cold (a shift of −0.9 °F,
−0.5 °C). How it is drawn: towns and villages at their modern places; rivers, brooks,
woods and roads drawn by hand through them (approximate). The map is generated by
`tools/maps/make_lutzen.mjs`. A fight within 2 hexes of Lützen is offered on the Lützen
battlefield.

**Sidon, 1253** (`data/maps/sidon-1253.yaml`) covers the raid on Sidon on 0.6-mile (1 km)
hexes: 59 × 62 hexes, about 37 by 33 miles (59 by 54 km), from Tyre and Sidon on the coast up
into the hills to Beaufort and Banias. It starts in mid-June 1253; the true date is not known.
Five forces:
- The army of Damascus, horse and foot, at Banias, on the road from Damascus.
- Sidon's garrison and builders at Sidon, Beaufort's garrison in its castle, and Louis IX's
  army at Tyre. Louis was further south when Sidon fell and came afterwards; the force at
  Tyre lets the GM play a relief.

The Litani can be crossed only at Khardali bridge below Beaufort and at its mouth. The hills
inland are slow going and the southern end of the Lebanon range slower still; the coastal
plain is the quick road. How it is drawn: the coastline is Natural Earth's (public domain);
towns, castles and villages are at their modern places; rivers, hills, mountains and roads
are drawn by hand (approximate). The map is generated by `tools/maps/make_sidon.mjs`. A
fight within a hex of Sidon is offered on the Sidon battlefield.

**Albuera, 1811** (`data/maps/albuera-1811.yaml`) covers Soult's march to relieve Badajoz on
0.6-mile (1 km) hexes: 73 × 62 hexes, about 45 by 33 miles (73 by 54 km), from Elvas and
Badajoz east to Almendralejo and south to Fuente del Maestre. It starts on 13 May 1811
(Gregorian), as Beresford heard Soult was coming, with seven forces:
- Allied: Beresford's British and Portuguese in the siege lines before Badajoz, the allied
  cavalry at Santa Marta, and Blake's Spanish army at Almendral (approximate).
- French: Soult's army and Latour-Maubourg's cavalry at Fuente del Maestre, and the French
  garrison in Badajoz.

The Guadiana can be crossed only at Badajoz and at a ford by Talavera la Real; the Albuera
and its brooks are wet, slow ground. How it is drawn: towns and villages at their modern
places, the siege lines and Blake's start approximate; rivers, brooks, woods and roads drawn
by hand. The map is generated by `tools/maps/make_albuera.mjs`. A fight within 2 hexes of La
Albuera is offered on the Albuera battlefield.

**Cowpens, 1781** (`data/maps/cowpens-1781.yaml`) covers Tarleton's pursuit of Morgan in the
South Carolina upcountry on 0.6-mile (1 km) hexes: 53 × 64 hexes, about 33 by 34 miles (53 by
55 km), between the Pacolet and the Broad. It starts on 14 January 1781 (Gregorian), with
five forces:
- American: Morgan's 600 Continentals, 1,000 militia and riflemen, and Washington's 120 horse
  in camp above Grindal Shoals (approximate).
- British: Tarleton's 800 foot and 300 Legion horse at Wofford's Iron Works.

The country was mostly open forest then, so the map is forest with clearings and farms. The
Pacolet and the Broad can be crossed only at their shoals and fords. How it is drawn: the
battlefield at its modern site, the shoals, the fort, the iron works and the camps
approximate; rivers, creeks, woods and roads drawn by hand. It is generated by
`tools/maps/make_cowpens.mjs`. A fight within 2 hexes of Hannah's Cowpens is offered on the
Cowpens battlefield.

**Lundy's Lane, 1814** (`data/maps/lundys-lane-1814.yaml`) covers the Niagara campaign on
0.6-mile (1 km) hexes: 39 × 58 hexes, about 24 by 31 miles (39 by 50 km), from Lake Erie to
Lake Ontario. It starts on 24 July 1814 (Gregorian), with eight forces:
- American: Scott's and Ripley's brigades, Porter's volunteers and the dragoons in camp at
  Chippawa.
- British: Riall's advance guard and the light dragoons at Queenston, Drummond's column at
  Fort George, and the garrison of Fort Niagara.

The Niagara can be crossed only by boat, at the crossings marked as fords (Queenston to
Lewiston, Fort George to Fort Niagara, and Fort Erie to Black Rock). How it is drawn: forts,
villages and the battlefield at their modern places, a few nudged off the river to their own
bank at this scale; the lake shores (which the land data counts as land), the river, the
creeks, the escarpment, woods and roads drawn by hand. It is generated by
`tools/maps/make_lundys_lane.mjs`. A fight within 2 hexes of Lundy's Lane is offered on the
Lundy's Lane battlefield.

**First Bull Run, 1861** (`data/maps/bull-run-1861.yaml`) covers McDowell's advance on
Manassas Junction on 0.6-mile (1 km) hexes: 35 × 31 hexes, about 22 by 17 miles (35 by 27 km),
from Fairfax Court House to Gainesville. It starts on 18 July 1861 (Gregorian), with eleven
forces:
- Union: Tyler's, Hunter's and Miles's divisions and the cavalry at Centreville, and
  Heintzelman's division at Fairfax Court House.
- Confederate: Beauregard's brigades at Mitchell's Ford, Union Mills and Ball's Ford, his
  reserve at Manassas Junction, and Johnston's army and Stuart's cavalry, coming by train, at
  the junction.

Bull Run can be crossed only at its fords and the Stone Bridge; Cub Run has a bridge on the
turnpike. How it is drawn: villages, the junction, the Stone Bridge and Henry Hill at their
modern places, the fords approximate; streams, woods, roads and the railways (drawn as
roads) by hand. It is generated by `tools/maps/make_bull_run.mjs`. A fight within 2 hexes of
Henry Hill is offered on the First Bull Run battlefield.

**Fort Phil Kearny, 1866** (`data/maps/phil-kearny-1866.yaml`) covers the fort on the Bozeman
Trail under the Big Horn Mountains, in Red Cloud's War, on 0.6-mile (1 km) hexes: 32 × 30 hexes,
about 20 by 16 miles (32 by 26 km). Open grass unless drawn otherwise. It starts on 20
December 1866 (Gregorian), the day before the Fetterman Fight, with five forces:
- US Army: the fort's garrison (Carrington), the 2nd Cavalry's Company C, and the wood train
  and its guard at the pinery.
- Lakota, Cheyenne and Arapaho: the Lakota war parties (Oglala, Minneconjou, Brulé) and the
  Cheyenne and Arapaho warriors, coming down from the north.

The Big and Little Piney creeks and Peno Creek are brooks (wet, slow ground, crossed
anywhere). How it is drawn: the fort, the Fetterman battlefield and the Wagon Box site at
their published positions, rounded (the corral's exact place was never agreed); Pilot Hill,
the Sullivant Hills, Lodge Trail Ridge, the pinery, Lake De Smet and the Big Horns after the
descriptions of the fort's ground; creeks, woods, hills, the Bozeman Trail and the wood road
by hand. Its climate is new: the northern High Plains (Sheridan, Wyoming). It is generated by
`tools/maps/make_phil_kearny.mjs`. A fight within 2 hexes of the Fetterman battlefield is
offered on the Fetterman Fight's battlefield, and one within 2 hexes of the Wagon Box corral
on the Wagon Box Fight's.

**Mons, 1914** (`data/maps/mons-1914.yaml`) covers the battle of Mons on 0.6-mile (1 km)
hexes: 53 × 50 hexes, about 33 by 27 miles (53 by 43 km), from Condé to Binche and from
Soignies to Maubeuge. It starts on 22 August 1914 (Gregorian), with eight forces:
- British: the 3rd Division at Mons, the 5th at Boussu along the canal to the west, Haig's
  I Corps at Harmignies and the Cavalry Division at Binche.
- German: IX Corps at Soignies, III Corps and IV Corps coming down from the north-west, and
  Marwitz's cavalry to the west.

The Mons-Condé canal (and the Canal du Centre east of Obourg) can be crossed only at its
bridges, and the Sambre at Maubeuge. How it is drawn: towns and villages at their modern
places, the bridges approximate; the canals, rivers, woods, the slag-heap hills of the
Borinage and the roads by hand. It is generated by `tools/maps/make_mons.mjs`. A fight
within 2 hexes of the Nimy bridges is offered on the Mons battlefield.

**Bougainville, 1944** (`data/maps/bougainville-1944.yaml`) covers the Empress Augusta Bay
perimeter on 0.6-mile (1 km) hexes: 37 × 31 hexes, about 23 by 17 miles (37 by 27 km). The
land is jungle unless drawn otherwise. It starts on 7 March 1944 (Gregorian), with six forces:
- American: the 37th Infantry Division at the Piva airfields, the 145th Infantry on Hill
  700, and the Americal Division on the East-West trail.
- Japanese: the Iwasa unit (23rd Infantry) north of Hill 700, the Magata unit (45th
  Infantry) to the west and the Muda unit (13th Infantry) to the east.

The Torokina, Piva and Laruma rivers can be crossed only at their fords. How it is drawn: the
coast is Natural Earth's and coarse at this scale; the cape, river mouths, airfields, hills
and Mount Bagana after their published positions, rounded; rivers, swamps, ridges and trails
by hand. Its climate is new: tropical rainforest, hot and wet all year (rounded design
estimates for the Solomon Islands). It is generated by `tools/maps/make_bougainville.mjs`. A
fight within 2 hexes of Hill 700 is offered on the Hill 700 battlefield.

**Anzio, 1944** (`data/maps/anzio-1944.yaml`) covers the Anzio beachhead and the plain to
Cisterna, Velletri and Littoria on 0.6-mile (1 km) hexes: 31 × 41 hexes, about 19 by 22 miles
(31 by 36 km). Most of the plain is farmland, reclaimed from the Pontine marshes. It starts on
29 January 1944 (Gregorian), the eve of the attack on Cisterna, with eight forces:
- American: the 1st and 3rd Ranger Battalions where they crossed the west branch of the
  Mussolini Canal, the 4th Rangers and the 3rd Battalion, 15th Infantry at Conca, the 7th
  Infantry at Padiglione and the 504th Parachute Infantry on the canal.
- German: Hermann Göring Division battle groups in Cisterna, its assault guns and tanks (a wagon
  force, so on the field map they are fire support) on the Appian Way, and the 356th
  Reconnaissance and 7th Luftwaffe Jäger Battalions to the east.

The Mussolini Canal and its west branch can be crossed only at their bridges. How it is drawn:
the coast is Natural Earth's; the towns at their modern centres, rounded; Conca and Isola Bella
after the distances in the US Army's account (*Anzio Beachhead*) and approximate; the canals,
the Pantano ditch, roads, railroad, woods and hills by hand. It is generated by
`tools/maps/make_anzio.mjs`. A fight within 2 hexes of Cisterna is offered on the Cisterna
battlefield.

**Osan, 1950** (`data/maps/osan-1950.yaml`) covers the country between Suwon and P'yongt'aek,
with Ansong to the east, on 0.6-mile (1 km) hexes: 32 × 43 hexes, about 20 by 23 miles (32 by
37 km). The low ground is rice paddy and fields (farmland) unless drawn otherwise. It starts on 5
July 1950 (Gregorian), with six forces:
- United Nations: Task Force Smith (B and C Companies, 1st Battalion, 21st Infantry) at the
  saddle north of Osan, the battery of 105 mm howitzers behind it, and a battalion of the 34th
  Infantry at P'yongt'aek.
- North Koreans: the 107th Tank Regiment and the 16th Regiment of the 4th Division coming down
  the highway from Suwon, and the 18th Regiment down the railroad. The tanks are a wagon force
  on the travel map, so they stay in reserve when a fight is sent to the field map, where they
  are on call as fire support.

How it is drawn: the saddle at its memorial (Jukmiryeong), the towns at their modern centres,
rounded; the hill line, the streams, the highway, the railroad and the roads by hand, after the
US Army's account of the battle. Its climate is new: central Korea, monsoon continental
(rounded approximations of the Suwon and Seoul normals, see [weather.md](weather.md)). It is
generated by `tools/maps/make_osan.mjs`. A fight within 2 hexes of the saddle is offered on
the Osan battlefield.

A campaign spec can also draw `water` (lakes the land data counts as land, as hand-drawn shore
polygons), and on a forest base (`base: "F"`) paint `farms` and `clearings`.

Campaign and battle maps can be added in the same format, one file per map:

- `terrain`: rows of one character per hex. The keys are listed in `data/terrain.yaml`.
- `places`: the camp, the objective, villages, towns and landmarks.
- `forces`: the forces at the start, each with a type, a side and a starting hex.
- `period` (optional): the period the **Map** picker lists it under. Without it, a map takes
  the period of a battlefield drawn on it (its wound table's conflict, as the roller groups
  its tables), or "Any period". The picker lists the periods oldest first, and each period's
  maps by start date; Agincourt says `period: "Hundred Years' War"`, as it borrows the
  Towton tables.

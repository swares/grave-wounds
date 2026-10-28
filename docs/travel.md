# Grave Wounds: the travel map (playtest draft)

The travel page (`dist/travel.html`) moves forces from camp to the battlefield across a hex
map. All the numbers live in `data/terrain.yaml`, and the maps are in `data/maps/`. The
page and the Python engine (`gravewounds/travel.py`) read them from there, so change them
there.

## Scale and time

- Each hex is usually 0.6 mile (1 km). A map can set its own size with `hex_km`.
- A force marches up to 8 hours a day, starting an hour after sunrise and stopping an hour
  before sunset, so short days give fewer hours (see [weather.md](weather.md)). It goes at its
  type's speed on a road:

  | Force type | Road speed | A day on the road |
  |---|---|---|
  | On foot | 2.5 mph (4 km/h) | 20 miles (32 km) |
  | Mounted | 3.7 mph (6 km/h) | 30 miles (48 km) |
  | Baggage wagons | 1.9 mph (3 km/h) | 15 miles (24 km) |

- Wagons cannot enter forest, marsh, mountains or heath. On maps that start before 1914,
  horse-drawn wagons and guns cannot cross a ford deeper than 2 ft 4 in (0.7 m); routes go round it.
- A flooded ford stops everyone, unless the force has **Risk a flooded ford** ticked: a force
  without wagons then wades it, and every named man risks being swept off.
- **March on by night** lets a force march up to 4 more hours after dark, more slowly (see
  *One clock*, below).
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

Each terrain also records **cover**, **forage** and whether it is **wet**. **Forage** sets
where fresh food can be had against scurvy, and where a named man can forage it on the march
(see *Scurvy*, below). **Cover** and **wet** are not used yet: what hides a force from the
enemy (`sight.hidden_in`) and what breeds fevers (`disease.yaml` `terrain_factors`) have their
own lists of terrain.

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
  **Now** also shows the light at that hour (daylight, dusk or dawn, a moonlit or a dark night).
- **Busy forces.** A force making camp, or fighting, is busy until it is done: its own time
  runs ahead of the clock and it does nothing else until the clock catches up. The forces
  list shows each force's own time.
- **Meetings.** The clock watches for forces of different sides coming within fighting reach
  (the same or the next hex): every quarter hour, and more often while a column is about to
  enter its next hex, so it looks each time any column moves a hex. Fast columns on small
  hexes (mounted men on Mogadishu's 270-yard hexes cross several in a quarter hour) cannot
  pass through each other between two looks. When they meet, it stops, both halt, and
  the fight can be set up as usual, with the usual chance of surprise; or the GM gives them
  new orders and they march on past each other.
- **Part of a hex.** A march stopped in the middle of a hex keeps the time already spent on
  it, so an hour at a time gets as far as a whole day at once. A force still stops for the
  night rather than finish a hex after its marching hours.
- **By night.** A force with **March on by night** ticked keeps going after its marching hours,
  up to 4 hours more, and the day's end waits for it. Each hex takes 1.4 times as long. Once a
  night the best guide with it rolls Fieldcraft (Hard off the road, Ordinary on it): fail and
  the night's march goes slower again; fumble and 2 hours go on the wrong road. A night march
  of 2 hours or more costs a step of fatigue (`data/uses.yaml`, `night`).
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
- **the wound roller**, man by man (up to 8 men a force, or more if more of its named men are
  on the roller; the force's named men first, as
  themselves: the fighters they are on the roller, with their sheets, kit and wounds; a named man
  with the force who is not on the roller is named in the setup's notes), with the camp's works laid out
  on its battle map and the ground laid out to match the defenders' hex: woods in forest,
  rises and rocks in hills, marsh in marsh, rubble in a village or town. Where the map
  reaches past a side of that hex, the neighbouring hex's ground (or a lake or river) shows
  along that edge. A fight on a road, ford or bridge has the road and river through the
  middle, and the attackers come in from the way they marched. See
  [works.md](works.md) and [combat.md](combat.md).
- **the field map**, in units: the forces arrive with their fit men, and the GM splits each
  into units there (billmen, archers, horse). Men left out of every unit stay in reserve, and their side can bring them on during the
  battle.
  The day's weather and ground come too, with the hour's light (daylight, dusk, moonlit or
  dark: see [weather.md](weather.md#light-the-field-map)), and the camp's works, as far as they are built,
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

**Frostbite.** On a night whose low is 5 °F (−15 °C) or colder, every well man may be
frostbitten: 1% plus 0.15% for each degree (C) colder, less a quarter of that for each point of the
camp's shelter (a bivouac none, a watched, staked or fortified camp 1, quarters 3), times the
chance he fails to resist with Endurance. It shows at once: mending (60%), serious (30%) or grave
(10%, gangrene), and is checked every 3 days like a sickness. A force bivouacked in −22 °F (−30 °C)
loses about one man in sixty a night to it, as the Marines did at the Chosin Reservoir. Named
characters with the force can be frostbitten too.

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

**Keep.** A force is **Fed by its army** unless the GM unticks it on its health panel: a team
on its own, men on leave or off base. Then each night every named man with it who has a purse
(from the team builder) pays his keep from it: a day's food, and a bed if the night falls in a
village or town and the force has not made camp. The health note says the force is not fed
and what each man has left; his purse shows the keep as one running entry ("Keep with the
Retinue, 6 days"). A day he cannot pay for food he goes hungry: the log says so, it counts as a
day without fresh food for his scurvy count, and back in the wound roller his fatigue goes up a
step. A night he cannot pay for a bed he sleeps rough (the log says so). The force's own men
are fed or not as the GM decides; only named men keep purses.

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
food issued** is ticked on its health panel. Other ground has none. A night when **Hunt for
the pot** brings in enough game to feed the whole force also sets the count back to nought:
the meat is fresh. The health note says how many days it has gone without, and whether
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

## Supplies

Each force carries **ammunition** (a share of its full loads), **rations** (days a man carries),
**water** (litres a man) and **medical stores**. The numbers are in `data/supplies.yaml`, and the
rule book has them in full (`dist/rules.html#supplies`). The health
panel's note shows what the force has left. Each night:

- **Rations.** A day its army does not feed it (**Fed by its army** unticked), and it neither
  foraged nor hunted its food, it eats a day's rations. Men carry 2 to 4 days, by era. With
  none left it goes hungry until it is fed or refilled.
- **Water.** By a river, lake, ford, marsh, bridge, village or town, or in rain, it fills up.
  Elsewhere each man needs 2 L a day up to 59 °F (15 °C), 3 L up to 77 °F (25 °C), 5 L up to
  90 °F (32 °C) and 8 L above. Men carry about 1 L, or 3 L from Vietnam on. Short
  of it, the force is thirsty: a step more fatigue.
- **Medical stores** serve 10 wounded or sick for each 100 men. Each new wounded man draws one
  and each sick man a seventh a day; with none left, its sick and wounded are cared for a step
  worse.
- **Ammunition** goes into a battle on the field map as its share of a load, and what is left
  comes back.

To fill up:

- **Refill at the depot**: at its army's depot (where it started on the map, or a place marked a
  depot of its side) everything is filled.
- **Draw from the train**: a baggage train of its side in the same hex carries 10 days'
  rations, 2 loads of ammunition and 2 fills of medical stores for each 1,000 men. The force
  takes its own share and the train's stock falls by it.
- **Buy a day's rations**: in a village or town, a force its army does not feed can buy a day's
  rations for every man; its named men pay their army's keep from their purses.

## Events on the march

`data/events.yaml` (rules in `gravewounds/events.py`, repeated in `templates/events.js`) gives
each era, per man per day, the chance of **desertion**, **straggling** (lost to the force), a
**non-battle injury**, and for mounted forces and wagon trains a **horse** lost, by what the
force did that day: **camp** (it did not march), **march**, or **withdraw** (the GM ticks
**Withdrawing** on its health panel). Each night, after its keep and before its sick have their
night, every fit man rolls each chance in turn (one in a million); deserters and stragglers come
off its men, the injured go on its wound track (at Mending, or Serious one time in seven, with
a wound-fever day like any wound), and lost horses come off its horses. Then the era's **incident**
chance (5-8% a day): a d100 row of its table, which may apply only to some force types or to
small or large forces, may cost men or a step of fatigue, and carries a hook. The force's log
says what happened.

A map's period gives the era (`periods`); a map force may name its own (`era: plains_nations`
for the Lakota and Cheyenne at Fort Phil Kearny). **Events on the march** on the health panel
turns them off for a force; **Named men can be injured** gives its named characters the
injury chance too (a case on their own track, as a wound in camp). Sickness is not rolled here:
camp disease, scurvy and frostbite already are.

**Hunger and arrears.** Two more ticks on the health panel, **Short of food** and **Pay in
arrears**, multiply its chances (`conditions`): hungry, desertion 15 times (the starving Swedish
camp at Nuremberg in 1632 lost about 1 man in 200 a day, against 1 in 3,000-4,000 for a
provisioned army) and straggling 5 times (Lee's barefoot army in Maryland, 1862, an estimate);
in arrears, desertion 3 times (the Army of Flanders' often unpaid foreign units against the
tercios, `approx`). With both ticked the larger applies; they do not stack, since a starving
army is seldom paid and the Nuremberg figure holds both. No chance goes above 1.

**Horses.** A mounted force or wagon train has a **Horses** count on its force panel: one a man
until the GM sets it (for remounts, or a force with spare horses or too few) or the force loses
one. Each night every horse rolls its chance; a mounted deserter rides off on his. With too few
horses for its men (`horses_march`) it slows: a mounted force under half a horse a man marches
at foot pace (67% of its speed: 4 km/h of 6), and a wagon train keeps 75% under three teams in
four and 50% under half (estimates). The log says when it happens. A hungry force (the health
panel's Hungry, or its rations run out) loses its horses four times as fast: Cole's column, in
cold and hunger in 1865, lost 3.6% of its horses a day against a Union cavalry horse's 0.83% on
campaign (a single report). At its army's depot, **Refill at the depot** also makes a horsed
force its army feeds up to one horse a man (`remount`, a design estimate: armies kept remount
depots, but no source gives how fully a unit was made up); the log counts the remounts. Away
from a depot remounts are the GM's: raise the count when it finds or buys horses.

The rates and their sources are in the project doc "travel-events-research"; each rate in the
file has its source or `approx: true`. The best are Korea's injuries by kind of operation,
Valley Forge's desertion, the 1812 and Civil War horses, Corunna and the 1914 retreat; the
medieval and Thirty Years' War rates are thin, and incidents are design estimates throughout.

## Loads

`data/loads.yaml` (rules in `gravewounds/loads.py`, repeated in `templates/ranks.js`: `ldLoadKg`,
`ldBody`, `ldBand`, `ldBlister`, `ldFatigue`; research in the project doc "load-research"). Each
era gives the kg of fighting order, marching order and full kit (`kg`), its average man's weight
(`body_kg`; a woman 12 kg less), the order it fights in (`fights_in`), and whether armour is
already in the orders (from 1914). Otherwise his armour adds by its toil load (medium 12 kg, heavy
22 kg). Load ÷ (body × Strength's multiplier) gives the band (Unburdened to Immobile at 15, 30, 45,
65 and 90%).

On the travel map the force panel's **Load** sets the force's order (marching by default). Its
average man's band against the era's marching band gives `loadPct` (never above 100), part of
`speedOf`; the day's km (marching hours × the force type's road pace) add fatigue steps for each
`fatigue_km` beyond what the marching band's would; and each named man who marched rolls his own
band's blister chance (`ldBlister`: the band's % for 20 km or more, pro rata below, a quarter after
7 days on the march, none while a feet case is still open), a minor case on his track. Packs lost
in the roller (below) arrive as `gravewounds-packs-lost` (map and force): that night the force is
short of food for its events, a step more tired, and its named men have a hard night.

In the roller each team-builder man has a **Load** select on his card (his era's `fights_in` by
default). His band (a band heavier if he has one term: green under fire) costs Dodge in his
defence (`defenceFor`: the better of Parry and Dodge less the band's) and, Overloaded or worse,
the run. **Drop packs** (After the fight) puts a side in fighting order; if it loses the field its
packs are lost, and the travel forces its named men go with are told.

## Fog of war

What each side's forces see of the enemy's, for a player online (his map shows only what his side
sees; the GM's travel map shows everything). Sight is in kilometres, so a map's hex size does not
change it. On a clear day a force sees a body of enemy troops within 3 km on foot, 8 km mounted (its
patrols out) and 2 km with wagons. In rain, snow or fog it sees five times as far as a man can see
to aim in that weather (`weather.yaml` visibility): fog 250 m, rain 1.5 km. At dusk sight is halved;
by moonlight it is 500 m, and on a dark night 200 m. Within 1 km its outposts find an enemy in any
weather, light or cover, and a force in woods or a town or village is seen only that close. A side
sees what any of its forces sees. Each time the clock moves, each side remembers where it saw each
enemy force and when; a player's map shows that, faded, once the force is out of sight. The numbers
are in `data/terrain.yaml` (`sight`); where they come from, and what they leave out (campfires,
dust, height, optics and aircraft), is in `docs/fog-of-war-research.md`.

The GM's travel map shows everything; its **view** choice beside the map's scale (Everything, or
As *side* sees it) draws it as one side sees it, as that side's players see it online: the side's
own forces and routes, the enemy forces it sees now (ringed red), and, faded, where it last saw the
others. The choice is the page's only, never saved, and changes nothing.

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
- **Health.** The selected force's camp hygiene, **Nurses keep clean**, **Fresh food
  issued**, **Fed by its army**, **Events on the march**, **Withdrawing**, **Short of food**,
  **Pay in arrears**, **Hunt for the pot**, **Risk a flooded ford**, **March on by night**,
  **In the line** and **Named men can be injured**, with a note on its supplies, its sick,
  nursing, days without fresh food, its named men's keep and the week's chances.
- Forces, routes, clocks and painting are kept in your browser. When the day changes in another
  tab or in the campaign console, the page takes the new day and says so.

The page's rules are in one file with no page, `templates/travelrules.js`: the calendar,
daylight, weather, rest and fatigue; routes, marching, camps' hours and who fights; camp disease.
They are the same rules as `gravewounds/weather.py`, `travel.py` and `disease.py`.
`python3 tools/travel/parity.py` plays a few hundred cases of each through the Python and the
JavaScript on the same inputs and dice and checks that every result is the same
(`tools/travel/test.js`).

The day itself is in `templates/travelday.js`, also with no page: the forces and their state,
the march, the night (rest, food, water, supplies, events, disease, the named men's feet, keep
and kit), the one clock, setting up a fight (who fights, the camp at the time, surprise, the
handoff to the roller or the field map), a battle's result taken back, and saving and restoring it
all. The odds of surprise are a rule in `travelrules.js`, checked against
`gravewounds.travel.surprise`. The travel map draws it and gives it
orders; the campaign console can run the same clock. `tools/travel/day.js` plays it with no page
on real maps, with named men and seeded dice: the same dice play the same game, a game saved part
way and restored plays on as if it had not stopped, and the state holds together after every
move of the clock.

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

**The Crécy campaign, 1346** (`data/maps/crecy-1346.yaml`) covers the last three days before the
battle on 0.6-mile (1 km) hexes: 36 × 43 hexes, about 21 by 22 miles (34 by 36 km), from the Somme
at Blanchetaque, Abbeville and Saint-Riquier in the south to the Forest of Crécy, Crécy and the
Authie in the north, and from the Bay of the Somme to Labroye. It starts on 24 August 1346
(Julian), the morning of the crossing, with seven forces:
- England: Edward III's army and its horse at Saigneville, waiting for the tide at the south end
  of the ford, and the carts behind at Acheux.
- France: Godemar du Fay's 3,500 holding the north bank at Port-le-Grand, Philip VI's men-at-arms
  and the Genoese crossbowmen at Abbeville, and the foot and the levies coming up from Amiens.

The Somme can be crossed only at Abbeville, the bridge at Pont-Remy and the tidal ford of
Blanchetaque; below Abbeville its estuary is tidal marsh. The Maye is a brook (slow wet ground);
the Authie is crossed where a road bridges it. The Forest of Crécy is drawn at its modern extent
(its limits in 1346 are not known). The English resupply at Noyelles, which they sacked, the French
at Abbeville (both our reading). Its people speak Picard (and French). How it is drawn: towns and
villages at their modern town halls; Wadicourt, the windmill, the Croix de Bohême, Valloires and the
ford only approximate; the coast and the bay drawn by hand (the bay has silted since), as are the
rivers, woods and roads (no road map of 1346 was found). Michael Livingston's proposed site (2015),
some 5 km south between the forest and Domvast, is marked as a place but has no battlefield. It is
generated by `tools/maps/make_crecy.mjs`. A fight within a hex of the Vallée des Clercs is offered
on the Crécy battlefield.

**The Aljubarrota campaign, 1385** (`data/maps/aljubarrota-1385.yaml`) covers the last days
before the battle on 0.6-mile (1 km) hexes: 39 × 35 hexes, about 24 by 19 miles (39 by 30 km),
from Leiria and Ourém in the north and east to Porto de Mós and Alcobaça in the south and west.
It starts on 13 August 1385 (Julian), with eight forces:
- Portuguese: the vanguard and wings under the Constable Nuno Álvares Pereira just north of
  Porto de Mós, João I's rearguard, the English and Gascons and the baggage at Porto de Mós.
- Castilian: the vanguard of French lances and the Portuguese who held for Queen Beatriz just
  south of Leiria, and Juan I's main battle and wings, his crossbowmen and foot and his 700
  carts at Leiria.

The Serras de Aire e Candeeiros are hills south and east of Porto de Mós; the Lis, the Lena and
the Alcoa are crossed where a road bridges them; the Leiria-Alcobaça road runs over the plateau
of São Jorge, where the battle was fought, and the Castilians' way round it by Calvaria is drawn
too. The Portuguese resupply at Porto de Mós, Alcobaça and Ourém, the Castilians at Leiria. Its
climate is new: western Portugal (Leiria), warm and dry in August with northerly winds. Its people
speak Portuguese. How it is drawn: towns and villages at their modern places; the Castilians' halt
at Jardoeira, the first Portuguese position and Chão da Feira only approximate (no coordinates
found); rivers, hills, woods and roads by hand. Batalha is not on it: its monastery was vowed for
the victory and begun in 1386. It is generated by `tools/maps/make_aljubarrota.mjs`. A fight
within a hex of São Jorge is offered on the Aljubarrota battlefield.

**The siege of Jacob's Ford, 1179** (`data/maps/jacobsford-1179.yaml`) covers the upper Jordan on
0.6-mile (1 km) hexes: 38 × 66 hexes, about 22 by 35 miles (36 by 56 km), from Tiberias and the Sea of
Galilee in the south to Banias and the head of the Hula in the north, and from Safed to the Golan
edge. It starts on 25 August 1179 (Julian), the day Saladin came to the ford, with six forces:
- Kingdom of Jerusalem: the Templar garrison in the castle, and Baldwin IV's relief gathering at
  Tiberias with the king's knights.
- Ayyubids: Saladin's horse and his foot, archers and sappers by the ford, and Farrukh-Shah's
  horse at Banias.
The Jordan can be crossed only at Jacob's Ford; the Sea of Galilee and Lake Hula are water, the Hula
swamps marsh; Upper Galilee and the Golan are hills. The castle stands 200 m north of the ford, drawn
a hex west of it at this scale. The Franks resupply at Tiberias and Safed, the Ayyubids at Banias.
Its climate is new: the upper Jordan valley (Tiberias), with August highs near 38 C. Its people speak
Arabic. No source gives Saladin's numbers; the forces are round figures of our own. It is generated
by `tools/maps/make_jacobsford.mjs`. A fight within a hex of the castle is offered on the Jacob's
Ford battlefield.

**The Dornach campaign, 1499** (`data/maps/dornach-1499.yaml`) covers the Birs valley and the
Gempen plateau on 0.6-mile (1 km) hexes: 22 × 25 hexes, about 14 by 13 miles (22 by 21 km), from
Basel and the Rhine in the north to the Jura at Seewen, and from the Blauen to Liestal. It starts on
21 July 1499 (Julian), with nine forces:
- Swiss Confederates: the vanguard of Solothurn, Bern and Zürich on the Gempen, Bern's main
  banner at Liestal, Lucerne and Zug coming in from the east, and Dorneck's garrison.
- Swabian League and the Empire: Fürstenberg's Landsknechte and levies and the knights at
  Arlesheim, the Geldern Landsknechte at Dornach, the Welsche Garde across the Birs at Reinach, and
  the guns and baggage on the fields below the castle.

The Rhine is crossed only at Basel; the Birs and the Ergolz where a road bridges them. The Gempen
plateau, the Blauen, the Bruderholz and the Jura are hills, the scarp below the Gempen wooded. The
Confederates resupply at Liestal and Dorneck, the imperial army at its camp at Arlesheim. Its people
speak German. How it is drawn: towns and villages at their modern places, the monuments by the
Swiss Army's coordinates, the Gempenstollen and some castles only approximate; rivers, hills, woods
and roads by hand (no road map of 1499 was found). It is generated by
`tools/maps/make_dornach.mjs`. A fight within a hex of the fields below Dorneck is offered on the
Dornach battlefield.

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
is generated by `tools/maps/make_towton.mjs`. The campaign maps share their drawing
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

**Sevastopol, 1855** (`data/maps/sevastopol-1855.yaml`) covers the siege lines in the last
days of the siege on 0.6-mile (1 km) hexes: 32 × 25 hexes, about 20 by 13 miles (32 by 22 km),
from Kamiesh Bay to the Chernaya and from the North Side to Balaklava. Open upland, scrub on
the Inkerman heights and the Mackenzie heights, and hills round Balaklava. It starts on 7
September 1855 (Gregorian), the day before the final assault, in the new **Crimean coast**
climate, with twelve forces:
- Allies: the British Light, 2nd and reserve divisions at the British camp and their cavalry at
  Kadikoi; Bosquet's French corps behind the Mamelon, the French 1st Corps on the left attack, and
  the French and Sardinians on the Chernaya.
- Russians: the garrisons of the Karabelnaya and the town, the reserve on the North Side, and
  the field army and its cavalry on the Mackenzie heights.

The harbour cannot be crossed; the Chernaya only at the Traktir and Inkerman bridges and the
ford by Chorgun. How it is drawn: the town, Balaklava, the Malakhov, the Redan and the heights
at their modern places, the works and camps approximate; the coast and harbour (`coast:
"drawn"`, since the land data is too coarse for the Chersonese at this scale), the river, the
scrub, the roads and the Balaklava railway (drawn as a road) by hand. It is generated by
`tools/maps/make_sevastopol.mjs`. A fight within a hex of the Great Redan is offered on
either Great Redan battlefield: the final assault of 8 September or the first of 18 June.

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
on the Wagon Box Fight's. Its people are the Lakota, Cheyenne and Arapaho, who held the Powder
River country; getting by in any of their tongues, or in the Plains sign language, will do.

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
within 2 hexes of the Nimy bridges is offered on the Mons battlefield. Its people speak Picard
at home and French (data/languages.yaml); round Binche, Walloon.

**Beaumont-Hamel, 1916** (`data/maps/beaumont-hamel-1916.yaml`) covers the northern half of the
British front on the Somme on 0.6-mile (1 km) hexes: 40 × 26 hexes, about 24 by 13 miles (39 by
21 km), from Doullens to Bapaume and from Gommecourt to Albert. It starts on 30 June 1916
(Gregorian), the eve of the attack, with eleven forces:
- British: the 1st Newfoundland Regiment in its billets at Louvencourt, the rest of the 29th
  Division at Auchonvillers, the 4th Division at Mailly-Maillet, the 31st at Colincamps, the 36th
  (Ulster) at Aveluy, and the VIII Corps supply columns at Acheux.
- Germans: RIR 119 at Beaumont-Hamel, RIR 121 on Redan Ridge, IR 169 at Serre, RIR 99 at
  Thiepval, and the 26th Reserve Division's trains at Miraumont.

The Ancre is crossed where a road bridges it, its valley floor marsh. The roads include the
Albert-Doullens metre-gauge railway, cut back to Gézaincourt, and the standard gauge up the Ancre
to Miraumont and Achiet. The British resupply at the railheads of Acheux and Doullens, the Germans
at Miraumont. The front line is not drawn: the forces stand where the divisions held it. Its people
speak Picard and French. How it is drawn: towns and villages at their modern town halls; Serre,
Hamel, Gézaincourt and the woods only approximate; the river, ridges, woods, roads and railways by
hand. The strengths are round figures. It is generated by `tools/maps/make_beaumont.mjs`. A fight
within a hex of the Newfoundland Park is offered on the Beaumont-Hamel battlefield.

**Serbia, 1915** (`data/maps/serbia-1915.yaml`) covers the Serbian retreat of 1915 on 3.1-mile
(5 km) hexes: 47 × 73 hexes, about 145 by 195 miles (235 by 316 km), from Kraljevo and Niš
in the north to Durrës on the Adriatic and Bitola in the south. The land is hill country unless
drawn otherwise: the farmed plains (Kosovo, Metohija, the Morava valleys, Pelagonia, the
Albanian coast) are cleared from it, and the Prokletije, the Šar, Kopaonik, the north Albanian
highlands and the Montenegrin mountains are mountains. Its climate is new: the Balkan uplands
(Priština); the passes are far colder. It starts on 5 November 1915 (Gregorian), with nineteen
forces:
- Serbia and Montenegro: the 1st Army at Kraljevo, the 3rd at Kruševac, the 2nd at Prokuplje,
  the Timok group east of it, the Užice group at Novi Pazar, the Supreme Command with the King
  and the government (wagons) at Raška, the troops facing the Kačanik gorge at Ferizaj, the
  Macedonian group (the 2nd and 14th Regiments) on the Babuna pass, and Montenegrin troops in
  the Sandžak and at Andrijevica.
- Central Powers: the Austro-Hungarian 3rd Army and the German 11th Army coming down from the
  north, Austro-Hungarian mountain brigades in the north-west, the Bulgarian 1st Army at Niš
  and north of it, and the 2nd Army at the Kačanik gorge, Vranje, Skopje (its cavalry) and
  Izvor below the Babuna.
The positions and strengths on 5 November are our reading of the research, which has few
sourced figures for single armies.

The tracks over the Albanian and Montenegrin mountains are not roads, and the mountains shut
wagons out: men and pack animals cross on foot, but guns and wagons cannot follow, as the Serbs
found. The Drin and the Vardar can be crossed only at Vizier's Bridge, the crossing below Kukës,
and the towns on them; the Black Drin at the Struga bridge or by a road's bridge; Lakes Skadar
and Ohrid are drawn as water. The Serbs resupply at Priština, Prizren, Podgorica, Shkodër and
Durrës, the Central Powers at Niš and Skopje. Its people speak Albanian where no town says
otherwise (data/languages.yaml), as in Kosovo, Albania and western Macedonia; its towns name their
own: Serbian in the Morava valleys and highland Montenegro, Albanian and Serbian in Kosovo (Serbian
first at Mitrovica), Serbian and Albanian in the Sandžak, Bulgarian (the Macedonian Slavs, as
period sources count them), Turkish and Albanian in the Macedonian towns, and five tongues at
Bitola. The shares are from c.1900-1912 counts (Weigand, Kanchov), before the flight of 1912-13. How it is drawn: towns and villages at their
modern places, the passes and bridges approximate; rivers, mountains, woods, lakes and roads by
hand. It is generated by `tools/maps/make_serbia1915.mjs`. A fight within a hex of the Babuna
pass is offered on the Babuna battlefield, one within a hex of Topolčani on the Topolčani
rearguard, and one within a hex of Mojkovac (on the upper Tara, with Bijelo Polje and Kolašin,
reached by the road up the Lim from Berane) on the Bojna njiva of 6 January 1916.

**Snipe, 1942** (`data/maps/snipe-1942.yaml`) covers the northern sector of the Second Battle of
El Alamein on 0.6-mile (1 km) hexes: 38 × 37 hexes, about 23 by 19 miles (36 by 31 km), from the
coast at Sidi Abd el Rahman to El Alamein station and south past Miteiriya Ridge. It starts on 26
October 1942 (Gregorian), the evening before the night move to Snipe, with thirteen forces:
- Eighth Army: the 2nd Rifle Brigade with 239 Battery at the Kidney feature, the 24th Armoured
  Brigade and the rest of the 1st Armoured Division behind it, the 51st (Highland), 9th
  Australian and 2nd New Zealand Divisions in their sectors, and the supply columns at El Alamein.
- Axis: the leaguers of 15th Panzer and of the Littorio with Kampfgruppe Stiffelmayer by Snipe,
  21st Panzer coming north up the Rahman track, the 164th Light Division and Trento, the 90th Light
  and Trieste in reserve by the coast, and the supply columns at Tell el Aqqaqir.

The ground is open desert; Miteiriya Ridge, Tel el Eisa and Tell el Aqqaqir are hills. The coast
road and the railway run along the shore, the Rahman track south from Sidi Abd el Rahman, and the
northern corridor west through the minefields to Kidney and Woodcock (our line). The minefields
themselves are not drawn. Eighth Army resupplies at El Alamein, the Axis at Sidi Abd el Rahman (our
reading: the forward depots were not found). Its climate is new: the Egyptian coast (El Alamein).
Its people (the coast's Bedouin) speak Arabic. How it is drawn: El Alamein and Aqqaqir at the
NGA's points; Kidney, Snipe and Woodcock derived from Wikipedia's distances to Aqqaqir (no grid
reference for them was found; Wikipedia's own Snipe point lies 24 km off) and only approximate, as
are the ridges, the track and the divisions' ground. It is generated by `tools/maps/make_snipe.mjs`.
A fight within a hex of Snipe is offered on the Snipe battlefield.

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

**Chipyong-ni, 1951** (`data/maps/chipyong-1951.yaml`) covers the central Korean hills
from Yangpyong on the Han in the west to Wonju and Hoengsong in the east and Yoju in the south,
on 0.6-mile (1 km) hexes: 54 × 41 hexes, about 34 by 22 miles (54 by 36 km). Most of it is
steep hills, with farmland (rice paddy, frozen in February) along the valleys. It starts on
13 February 1951 (Gregorian), with five forces:
- United Nations: the 23rd Infantry Regimental Combat Team with the French Battalion at
  Chipyong-ni, and Task Force Crombez (the 5th Cavalry, with tanks) at Yoju.
- Chinese: the 40th Army from the north, the 39th from the north-west and the 42nd from the
  south-west. The numbers are round figures for play: US accounts put the Chinese at up to
  25,000, Chinese accounts at three regiments committed.

How it is drawn: the towns at their modern centres, rounded; the Twin Tunnels, Koksu-ri and
Hill 397 after the accounts and approximate; the Han (crossed at Yoju and Yangpyong), the hills,
roads and railroad by hand. It is generated by `tools/maps/make_chipyong.mjs`. A fight within 2
hexes of Chipyong-ni is offered on the Chipyong-ni battlefield.

**Ia Drang, 1965** (`data/maps/iadrang-1965.yaml`) covers the Ia Drang valley and the Chu
Pong massif by the Cambodian border, on 0.3-mile (0.5 km) hexes: 76 × 43 hexes, about 24 by 12
miles (38 by 19 km). Nearly all of it is scrub forest and tall elephant grass, with a few
clearings and no roads; the Ia Drang is crossed at its fords. It starts on 14 November 1965
(Gregorian), with seven forces:
- United States: the 1st Battalion, 7th Cavalry at landing zone X-Ray, the 2nd Battalion, 7th
  Cavalry and the artillery at Falcon, and the 2nd Battalion, 5th Cavalry at Victor.
- North Vietnamese: the 7th and 9th Battalions of the 66th Regiment on the Chu Pong, its 8th
  Battalion to the north-west, and two battalions of the 33rd Regiment from the west.
- Helicopters are not on the travel map: forces march. On the field map, units come in by air
  at a landing zone.

How it is drawn: X-Ray, Albany and Falcon at their published positions, rounded; Columbus,
Victor and the cut-off platoon's knoll after the accounts and approximate; the massif, hills,
river and streams by hand. Its climate is new: the Central Highlands of Vietnam (see
[weather.md](weather.md)). It is generated by `tools/maps/make_iadrang.mjs`. A fight within 2
hexes of X-Ray is offered on the X-Ray battlefield.

**Mogadishu, 1993** (`data/maps/mogadishu-1993.yaml`) covers the city from the airport in the
south-west to the Pakistani stadium in the north-east, on 270-yard (0.25 km) hexes: 42 × 40
hexes, about 6 by 5 miles (10 by 9 km). The city is built up throughout (village), and the
airport is open ground. It starts on 3 October 1993 (Gregorian), with five forces:
- United States: Task Force Ranger (Rangers and Delta) at the target near the Olympic Hotel,
  and the relief column (the 10th Mountain Division's infantry with Malaysian and Pakistani
  armour) at the New Port.
- Somali National Alliance: militia at the Bakara Market, in the north, and at K-4 and the
  south.

How it is drawn: the target, the crash sites and the Olympic Hotel at their published
positions, rounded; the airport compound, K-4, the New Port, the market and the stadium after
the US Army's account (*The United States Army in Somalia, 1992-1994*) and approximate.
Natural Earth's coast is a few kilometres out at this scale, so the coast is drawn by hand
past the airport, the old port and Lido beach (a campaign spec's `coast: "drawn"` takes the
sea from its own `water`). The streets are drawn by hand. Its climate is new: the Horn of
Africa coast (see [weather.md](weather.md)). It is generated by `tools/maps/make_mogadishu.mjs`.
A fight within 2 hexes of the first crash site is offered on the Mogadishu battlefield.

**Wanat, 2008** (`data/maps/wanat-2008.yaml`) covers the Waygal valley in north-eastern
Afghanistan from Camp Blessing on the Pech up past Wanat to Waygal, on 0.3-mile (0.5 km) hexes:
38 × 46 hexes, about 12 by 12 miles (19 by 20 km). Nearly all of it is steep mountainside; the
valley floors are terraced fields (farmland) and villages, and a track runs up the valley. It
starts on 13 July 2008 (Gregorian), with four forces:
- United States: 2nd Platoon, Chosen Company, 2nd Battalion, 503rd Infantry, with engineers,
  Marine trainers and Afghan soldiers, at Wanat, and a quick reaction force at Blessing.
- Insurgents: fighters from the village and the high ground to the north, and from the east.

How it is drawn: Wanat at its published position, rounded; Blessing, Nangalam, Waygal and the
side outposts after the US Army's accounts and approximate; the mountains, rivers, fields, woods
and track by hand. Its climate is new: the Hindu Kush valleys (see [weather.md](weather.md)).
It is generated by `tools/maps/make_wanat.mjs`. A fight within a hex of Wanat is offered on the
Wanat battlefield.

**Cassino, 1944** (`data/maps/cassino-1944.yaml`) covers the town of Cassino and the Monte
Cassino massif from Monte Cairo to the Liri valley, on 0.3-mile (0.5 km) hexes: 37 × 35 hexes,
about 11 by 9 miles (18 by 15 km). The massif is mountain and hill; the valleys are farmland;
the Rapido is crossed at its bridges. It starts on 15 February 1944 (Gregorian), with five
forces:
- Allies: the 4th Indian Division from the north and the 2nd New Zealand Division from the
  east.
- Germans: paratroops and panzergrenadiers on the massif and in the abbey, paratroops in the
  town, and reserves at Piedimonte.

How it is drawn: the abbey, the town and the villages at their modern centres, rounded; Castle
Hill, Hangman's Hill, Point 593, Snakeshead Ridge and Phantom Ridge after the accounts and
approximate; the massif, river, roads and railroad by hand. It is generated by
`tools/maps/make_cassino.mjs`. Three battlefields hang on it: a fight within a hex of Point 593
is offered the February battle on Snakeshead Ridge, within a hex of Phantom Ridge the Poles'
battle in May, and within a hex of the town the New Zealanders' battle in its ruins in March.

**Chosin Reservoir, 1950** (`data/maps/chosin-1950.yaml`) covers the road from Yudam-ni past
the Chosin Reservoir down to Hamhung and the port of Hungnam, on 0.6-mile (1 km) hexes: 55 ×
109 hexes, about 34 by 59 miles (55 by 94 km). Above the coastal plain it is all steep
mountains, with farmland in the valleys and one road down to the sea; the reservoir's shore is
drawn by hand (a campaign spec's `water`). It starts on 27 November 1950 (Gregorian), with nine
forces:
- United Nations: the 5th and 7th Marines at Yudam-ni, Fox Company, 7th Marines at Toktong
  Pass, the Hagaru-ri garrison, the 1st Marines and 41 Commando at Koto-ri, and Regimental
  Combat Team 31 east of the reservoir.
- Chinese: the 79th and 89th Divisions north-west of Yudam-ni, the 59th above Toktong Pass,
  the 80th east of the reservoir, and the 58th and 60th west of the road south.

How it is drawn: the towns and villages at their modern positions, rounded; Toktong Pass,
Funchilin Pass and the bridge after the accounts and approximate. Its climate is new: the
North Korean plateau, with nights of −4 to −22 °F (−20 to −30 °C) by late November, and two
degrees colder still for 1950 (see [weather.md](weather.md)); men in bivouacs there take
frostbite night after night. It is generated by `tools/maps/make_chosin.mjs`. A fight within a
hex of Toktong Pass is offered on the Fox Hill battlefield.

**Kapyong, 1951** (`data/maps/kapyong-1951.yaml`) covers the Kapyong valley from Kapyong on the
Pukhan north past Hills 504, 677 and 794, on 0.3-mile (0.5 km) hexes: 38 × 55 hexes, about 12
by 15 miles (19 by 24 km). Steep wooded hills (hills, mountains) either side of a narrow valley
of paddies; the Kapyong river is shallow and fordable, and the Pukhan is crossed at its bridge.
It starts on 22 April 1951 (Gregorian), with seven forces:
- United Nations: 3 RAR on Hill 504, 2 PPCLI on Hill 677, the 1st Middlesex and the brigade's
  guns at the blocking position, a company of American tanks (a wagon force) at Chuktun-ni, and
  the ROK 6th Division falling back down the valley.
- Chinese: the 118th Division from the north and the 60th from the north-west.

How it is drawn: Kapyong at its modern centre, rounded; the hills and hamlets after the
accounts and approximate. It is generated by `tools/maps/make_kapyong.mjs`. A fight within a
hex of Hill 504 is offered on the Kapyong battlefield.

**Heartbreak Ridge, 1951** (`data/maps/heartbreak-1951.yaml`) covers the ridge from Hill 894
north past Hill 931 to Hill 851, with the Mundung-ni valley to the west and the Sat'ae-ri valley
to the east, on 0.3-mile (0.5 km) hexes: 33 × 43 hexes, about 10 by 12 miles (16 by 19 km).
Steep wooded mountains; farmed valley floors. It starts on 13 September 1951 (Gregorian), with
seven forces:
- United Nations: the 23rd Infantry and the French Battalion at Hill 894, the 9th Infantry on
  Bloody Ridge, the 38th Infantry and the Netherlands Battalion to the south, and the 72nd Tank
  Battalion (a wagon force) at the foot of the Mundung-ni valley.
- North Koreans: the 6th Division on Hill 931 and the 12th on Hill 851, with the Chinese 204th
  Division to the north (on the North Korean side).

How it is drawn: the peaks at their published spacing, rounded; the villages, valleys and roads
after the US Army's account and approximate. It is generated by `tools/maps/make_heartbreak.mjs`.
A fight within a hex of Hill 931 is offered on the Heartbreak Ridge battlefield.

**Pork Chop Hill, 1953** (`data/maps/porkchop-1953.yaml`) covers the 7th Infantry Division's
outpost line north of Yeoncheon, on 0.3-mile (0.5 km) hexes: 28 × 30 hexes, about 8 by 8 miles
(14 by 13 km). Low, bare hills over paddy valleys. It starts on 16 April 1953 (Gregorian), with
five forces:
- United Nations: E Company, 31st Infantry on Pork Chop, the rest of the 31st on the main line,
  and the 17th Infantry in reserve.
- Chinese: the 141st Division from the north and the 67th from the north-east.

How it is drawn: Pork Chop at its published position, rounded; Old Baldy, Hill 200, T-Bone and
the main line after the US Army's accounts and approximate. It is generated by
`tools/maps/make_porkchop.mjs`. A fight within a hex of Pork Chop Hill is offered on its
battlefield.

**Hue, 1968** (`data/maps/hue-1968.yaml`) covers Hue and its approaches from the Phu Bai
combat base, on 0.3-mile (0.5 km) hexes: 51 × 46 hexes, about 16 by 12 miles (26 by 20 km).
Rice paddies and villages on the coastal plain, the Perfume River through the city, low hills
with the imperial tombs to the south-west. It starts on 31 January 1968 (Gregorian), in the
new **central coast** climate, with eight forces:
- United States and ARVN: the ARVN 1st Division's headquarters at Mang Ca, the MACV
  advisers' compound, two Marine battalions and their tanks at Phu Bai, and the 1st Cavalry
  Division's 3rd Brigade at PK-17.
- North Vietnamese: the 6th Regiment in the Citadel, the 4th Regiment in the new city, and
  the command post and reserves at La Chu.

How it is drawn: the Citadel, the bridges, Phu Bai and the villages after the US Marine Corps'
and Army's accounts and approximate; the river, the Phu Cam canal and Highway 1 by hand. It is
generated by `tools/maps/make_hue.mjs`. A fight within a hex of the new city is offered on the
Hue battlefield.

**Khe Sanh, 1968** (`data/maps/khesanh-1968.yaml`) covers the Khe Sanh plateau from the
Laotian border and Lang Vei east along Route 9, on 0.3-mile (0.5 km) hexes: 53 × 44 hexes,
about 16 by 12 miles (27 by 19 km). Steep hills under jungle and elephant grass, with the base
and the village's plantations on the plateau. It starts on 20 January 1968 (Gregorian), in the
new **Annamite hills** climate, with its long dry-season fogs, and has six forces:
- United States and ARVN: the 26th Marines, 1/9 Marines and the 37th ARVN Rangers at the
  combat base, the Marines on the hill outposts, and the Special Forces camp at Lang Vei.
- North Vietnamese: the 325C Division to the north-west, the 304th to the south-west, and the
  guns on Co Roc across the border.

How it is drawn: the base, Hills 881 South and North, 861, 861A, 558 and 950, the village and
Lang Vei after the US Marine Corps' account and approximate; the rivers and Route 9 by hand.
It is generated by `tools/maps/make_khesanh.mjs`. A fight within a hex of Hill 861A is offered
on the Khe Sanh battlefield.

**Dak To, 1967** (`data/maps/dakto-1967.yaml`) covers the country from the Dak To base and Tan
Canh on Highway 14 west along Route 512 to Ben Het and the hills towards the border, on
0.3-mile (0.5 km) hexes: 61 × 52 hexes, about 19 by 14 miles (31 by 23 km). Steep ridges under
jungle and bamboo, rising to 1,300 m, with a cleared valley floor round the base. It starts on
3 November 1967 (Gregorian), in the Central Highlands climate, with six forces:
- United States and ARVN: the 173rd Airborne Brigade and the 4th Infantry Division's 1st
  Brigade at the base, ARVN airborne and infantry at Tan Canh, and the Special Forces camp at
  Ben Het.
- North Vietnamese: the 1st Division to the south-west and the 24th Regiment to the
  north-west.

How it is drawn: the base, Tan Canh, Ben Het and Hills 724, 823, 875 and 1338 after the US
Army's accounts and approximate; the Poko river and the roads by hand. It is generated by
`tools/maps/make_dakto.mjs`. A fight within a hex of Hill 875 is offered on the Dak To
battlefield.

**Hamburger Hill, 1969** (`data/maps/hamburger-1969.yaml`) covers the A Shau valley from the
Laotian border and Dong Ap Bia (Hill 937) east across the valley floor to A Luoi and Ta Bat, on
0.3-mile (0.5 km) hexes: 53 × 63 hexes, about 16 by 17 miles (27 by 27 km). Mountains under
thick jungle on both sides of an open valley floor of elephant grass. It starts on 10 May 1969
(Gregorian), in the Annamite hills climate, with six forces:
- United States and ARVN: the 3rd Battalion, 187th Infantry at its landing zone, the 1st
  Battalion, 506th Infantry to the south, the 2nd Battalion, 501st Infantry at A Luoi, and the
  ARVN 2nd Battalion, 3rd Regiment to the east.
- North Vietnamese: the 29th Regiment on Ap Bia and reserves across the border in Laos.

How it is drawn: Ap Bia, A Luoi, Ta Bat and the landing zone after the US Army's accounts and
approximate; the A Sap river, the valley road and the mountains by hand. It is generated by
`tools/maps/make_hamburger.mjs`. A fight within a hex of Dong Ap Bia is offered on the Hamburger
Hill battlefield.

**Goose Green, 1982** (`data/maps/goosegreen-1982.yaml`) covers the Darwin isthmus on East
Falkland, from Camilla Creek House south to Darwin and Goose Green, on 0.3-mile (0.5 km) hexes:
36 × 40 hexes, about 11 by 11 miles (18 by 17 km). Open, treeless grass and peat between
Brenton Loch and Choiseul Sound, boggy in the hollows. It starts on 27 May 1982 (Gregorian), at
latitude 52° south (short days, late autumn), in the new **Falkland Islands** climate, with five
forces:
- British: the 2nd Battalion, the Parachute Regiment at Camilla Creek House.
- Argentines: a company on Darwin Hill, another at Boca House, the 12th Infantry Regiment
  at Goose Green, and air force men and anti-aircraft guns at the airstrip.

How it is drawn: the settlements and positions after the official history and approximate;
the shores (`coast: "drawn"`, since the land data is too coarse for an isthmus a mile wide)
and the tracks by hand. It is generated by `tools/maps/make_goosegreen.mjs`. A fight within a
hex of Darwin Hill is offered on the Goose Green battlefield.

**Tumbledown, 1982** (`data/maps/tumbledown-1982.yaml`) covers the hills west of Stanley on
East Falkland, from Two Sisters and Goat Ridge east to Sapper Hill and Stanley, on 0.3-mile
(0.5 km) hexes: 40 × 19 hexes, about 12 by 6 miles (20 by 9.5 km). Open, treeless grass and
peat with long rocky ridges. It starts on 13 June 1982 (Gregorian), at latitude 52° south
(midwinter), in the **Falkland Islands** climate, with five forces:
- British: the 2nd Battalion, Scots Guards and the 1st/7th Gurkha Rifles on Goat Ridge.
- Argentines: N Company of BIM 5 with army platoons on Tumbledown, BIM 5 on Mount William, and
  its headquarters and reserve on Sapper Hill.

How it is drawn: the hills and positions after the accounts' relative positions and
approximate; Stanley Harbour (`coast: "drawn"`) and the Fitzroy-Stanley track by hand. It is
generated by `tools/maps/make_tumbledown.mjs`. A fight within a hex of Mount Tumbledown is
offered on the Tumbledown battlefield.

**73 Easting, 1991** (`data/maps/easting73-1991.yaml`) covers the 2nd Armored Cavalry
Regiment's last day in the desert of southern Iraq, from about 60 Easting on the military grid
east to Objective Norfolk, on 0.3-mile (0.5 km) hexes: 67 × 55 hexes, about 21 by 15 miles
(34 by 24 km). Flat, hard, open desert with low rises that hide what lies behind them. It
starts on 26 February 1991 (Gregorian), in the arid climate, with nine forces:
- Coalition: Eagle and Ghost Troops of the 2nd Squadron and Iron and Killer Troops of the
  3rd, about 120 men each.
- Iraqis: infantry in the buildings near 68 Easting, the Tawakalna Division's 18th
  Mechanized Brigade on the rise at 73 Easting, the 37th Armored Brigade to the north-east,
  the 12th Armored Division's 9th Armored Brigade to the south-east, and the depot troops at
  Norfolk. Their strengths that day are not known; the numbers are estimates.

How it is drawn: the grid lines (60, 67, 70, 73 and 74 Easting) placed from the military grid;
the troops, the buildings, the rises, the depot and the IPSA pipeline road after the published
accounts and approximate, by hand. Ghost Troop's wadi is named, not drawn: we have no course for
it. It is generated by `tools/maps/make_easting73.mjs`. A fight within a hex of the rise at
73 Easting is offered on the 73 Easting battlefield. Its battlefield's weather is the
**sandstorm**, which the travel map never rolls; the GM can set it for the day.

**Grozny, 1995** (`data/maps/grozny-1995.yaml`) covers Grozny and its approaches, from the
Severny airport in the north to Khankala in the east, on 0.3-mile (0.5 km) hexes: 40 × 40
hexes, about 12 by 11 miles (20 by 17 km). The city's blocks fill an oval on both banks of the
Sunzha, with open steppe and fields round it and low hills to the south. It starts on
31 December 1994 (Gregorian), in the continental climate, with eight forces:
- Russians: the 131st (Maikop) Brigade from the north-west, the 81st Regiment from the north,
  and the western and eastern groups.
- Chechens: fighters at the Presidential Palace, round the railway station and at Minutka
  square, and reserves in the south.

How it is drawn: the palace, the station, Minutka square and the airports after the published
accounts and approximate; the Sunzha, the roads and the city's extent by hand. It is generated
by `tools/maps/make_grozny.mjs`. A fight within a hex of the railway station is offered on the
Grozny battlefield.

**Debecka, 2003** (`data/maps/debecka-2003.yaml`) covers the country south of Erbil in northern
Iraq, from Pir Da'ud south over the ridge of Zurqah Ziraw Dagh to the Debecka crossroads and west
to Makhmur, on 0.3-mile (0.5 km) hexes: 68 × 71 hexes, about 21 by 22 miles (34 by 35 km).
Open rolling plain rising north to the long ridge. It starts on 6 April 2003 (Gregorian), at
latitude 36° north, in the **mediterranean** climate, with four forces:
- Americans and Kurds: ODAs 391 and 392 and the KDP Peshmerga with them at Pir Da'ud.
- Iraqis: infantry on the ridge and a mechanised company at Debecka.

How it is drawn: only the crossroads has a published coordinate; the ridge, Press Hill, the
Alamo and Pir Da'ud are placed from the accounts' distances, and the roads beyond the crossroads
by inference. It is generated by `tools/maps/make_debecka.mjs`. A fight within a hex of the
crossroads is offered on the Debecka battlefield.

**Fallujah, 2004** (`data/maps/fallujah-2004.yaml`) covers Fallujah and its approaches, from the
Euphrates and the Jolan in the west to Camp Fallujah in the east, on 0.3-mile (0.5 km) hexes:
35 × 28 hexes, about 11 by 8 miles (18 by 12 km). The city's walled houses lie on the east bank,
with palm groves and fields by the river and open desert round it. It starts on 7 November
2004 (Gregorian), in the hot desert climate, with seven forces:
- Coalition: RCT-1 and RCT-7 north of the railway, the Iraqi army and commando battalions at
  the hospital, and the Army brigade holding the cordon to the south.
- Insurgents: in the Jolan, in the city centre and the Queens, and in Shuhada and the south.

How it is drawn: the districts, the railway station, the bridges, the hospital and Camp
Fallujah after the Marine Corps' and Army's histories and approximate; the river, the roads and
the city's extent by hand. It is generated by `tools/maps/make_fallujah.mjs`. A fight within a
hex of the Jolan is offered on the Fallujah battlefield.

**COP Keating, 2009** (`data/maps/keating-2009.yaml`) covers the Kamdesh valley in Nuristan
round Combat Outpost Keating, on 0.3-mile (0.5 km) hexes: 29 × 37 hexes, about 9 by 10 miles
(15 by 16 km). Nearly all of it is steep mountainside under deodar and scrub; the valley floor
and the villages' terraces are the only level ground. It starts on 3 October 2009 (Gregorian),
in the Hindu Kush climate, with five forces:
- Coalition: B Troop, 3-61 Cavalry, with Afghan soldiers and Latvian advisers, at the outpost,
  and Observation Post Fritsche on the ridge above.
- Insurgents: on the northern, eastern and western slopes.

How it is drawn: the outpost, the observation post, Urmul, Kamdesh and Mandigal after the
Army's investigation and approximate; the Landay-Sin, the Kushtoz, the terraces and the track
by hand. It is generated by `tools/maps/make_keating.mjs`. A fight within a hex of the outpost
is offered on the COP Keating battlefield.

A campaign spec can also draw `water` (lakes the land data counts as land, as hand-drawn shore
polygons), and on a forest base (`base: "F"`) paint `farms` and `clearings`.

Campaign and battle maps can be added in the same format, one file per map:

- `terrain`: rows of one character per hex. The keys are listed in `data/terrain.yaml`.
- `places`: the camp, the objective, villages, towns and landmarks.
- `forces`: the forces at the start, each with a type, a side and a starting hex.
- `period` (optional): the period the **Map** picker lists it under. Without it, a map takes
  the period of a battlefield drawn on it (its wound table's conflict, as the roller groups
  its tables), or "Any period". The picker lists the periods oldest first, and each period's
  maps by start date; Crécy, Aljubarrota and Agincourt say `period: "Hundred Years' War"`, as they
  borrow the Towton tables.

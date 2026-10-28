# Grave Wounds: calendar, weather, rest and fatigue (playtest draft)

All the numbers are in `data/weather.yaml`, and each map's calendar and climate are in its
file in `data/maps/`. The travel page, the roller and the Python engine
(`gravewounds/weather.py`, `travel.py` and `combat.py`) read them from there.

## Calendar and daylight

Each travel map has:
- a **start date**, read in its own **calendar**: Julian for medieval sources, Gregorian
  for modern ones
- a **latitude**
- a **climate**, with an optional **climate shift**

Day 1 is the start date, and the page shows each day's date and weekday. The test valley
starts on Sunday 20 October 1415 (Julian), five days before Agincourt.

Daylight comes from the latitude and the date. The march starts an hour after sunrise and
stops an hour before sunset, rounded to the quarter hour, up to the usual 8 hours.
- At 52°N that is 7 hours in late October and about 5½ in December.
- Midsummer gives the full 8.
- Camp work can still use 4 evening hours after the march.
- A force with **March on by night** ticked can march up to 4 more hours after its marching
  hours, at 1.4 times the time, with the guide's Fieldcraft to keep the way (see
  [travel.md](travel.md#one-clock)). A night march of 2 hours or more tires it (*Fatigue*, below).

`day_starts` in `data/terrain.yaml` is not used: the day starts from sunrise.

## Weather

Each day's weather is rolled from the climate's figures for that month:
- Each climate has monthly highs and lows, days with rain or snow, and days with fog.
  These are rounded modern climate normals for a typical place in the region.
- **Wet and dry spells last.** A wet day makes the next one more likely to be wet, and a
  dry day the next dry.
- **Warmth and chill carry over.** Half of a day's warm or cold spell carries into the next.
- On a wet day, rain falls as snow if the day's high is 36 °F (2 °C) or less.
- On a dry day it may be foggy, fair or overcast.
- The wind is rolled separately. A storm brings at least a strong wind, and a blizzard a gale.
- A **sandstorm** is never rolled. It is set only where a battlefield names it (73 Easting,
  1991) or the GM picks it: blowing sand with no rain, at least a strong wind. Thermal sights
  see through it further (Eagle Troop's first kill was at about 1,000 yards in the storm, and
  the GAO found thermal sights saw through haze and smoke).
- So is the wind's **direction**, where it blows from, one of eight points. Half the time a
  day keeps the day before's; otherwise it is rolled from the climate's prevailing winds:
  mostly from the west and south-west in north-west Europe, from the west in central Europe
  and the Mediterranean, from the north in the desert, and from the south-west in eastern
  North America.

The **climate shift** moves the modern figures, usually cooler. The Little Ice Age, roughly
1300–1850, ran somewhat cooler; the test valley uses −0.9 °F (−0.5 °C). Mons, 1914, is the one
map shifted warmer, +1.8 °F (+1 °C).

| Climate | Like |
|---|---|
| North-west Europe, maritime | England, the Low Countries, the Baltic coast, Gotland |
| Central and eastern Europe, continental | Bohemia, Poland, Hungary, the Rhine valley |
| Mediterranean and Levant coast | Acre, Sidon, Sicily, southern Spain |
| Hot desert and steppe | Mesopotamia, inland Syria, Egypt |
| Carolina piedmont, humid subtropical | upstate South Carolina (Greenville-Spartanburg) |
| Virginia piedmont, humid | northern Virginia (Washington Dulles) |
| Great Lakes, humid continental | the Niagara frontier (Buffalo) |
| Tropical rainforest, the western Pacific | the Solomon Islands (Bougainville); rounded design estimates |
| Northern High Plains, semi-arid | the Big Horn foothills (Sheridan, Wyoming) |
| Central Korea, monsoon continental | Suwon and Seoul; rounded approximations of the normals |
| Central Highlands of Vietnam, tropical monsoon | Pleiku: a dry season November to April, monsoon rains May to October; rounded design estimates |
| Horn of Africa coast, hot and semi-arid | Mogadishu; rounded design estimates |
| Central coast of Vietnam, tropical monsoon | Hue: rains September to January, the crachin drizzle into March; rounded design estimates |
| Annamite hills of Vietnam, monsoon and mist | Khe Sanh and the A Shau at about 400-600 m, with long fogs November to March; rounded design estimates |
| Crimean coast, Black Sea | Sevastopol; rounded design estimates |
| Falkland Islands, cold oceanic | Stanley, with the seasons reversed; rounded design estimates |
| North Korean plateau, bitter winters | the Changjin (Chosin) plateau at about 1,100 m; rounded design estimates |
| Hindu Kush valleys, hot summers and cold winters | the Kunar and Nuristan valleys at about 1,200 m; rounded design estimates |
| Balkan uplands, cold winters | the Kosovo basin at about 600 m (Priština); rounded design estimates |
| Western Portugal, Atlantic Mediterranean | Leiria and Alcobaça, behind the coast; rounded design estimates |
| Egyptian Mediterranean coast, desert | El Alamein; October from the published normals, the other months rounded design estimates |
| Upper Jordan valley, hot and dry | Tiberias, by the Sea of Galilee; rounded design estimates |

The four North American climates are rounded approximations of 1991–2020 station normals
for the places named; the Greenville-Spartanburg January figures and Sheridan's temperatures
and precipitation days were checked against the published normals (Sheridan's days of 1 mm
or more are scaled down from its days of 0.01 inch). The campaigns before 1850 there use a
shift of −1.8 °F (−1 °C), Bull Run and Fort Phil Kearny −0.9 °F (−0.5 °C), as does Sevastopol.

The weather strip on the travel map shows the selected force's day: its date, sunrise and
sunset, marching hours, weather and ground. The GM can **Roll again**, or set the weather,
wind, the wind's direction, low and high by hand. Earlier days are listed underneath.

## The ground

Mud and lying snow build up and wear off day by day:
- **Mud.** Rain adds one level; heavy rain or a storm adds two, up to three. Each dry day
  takes off one level, or two in warm weather.
- **Snow.** Snow adds one level, heavy snow two and a blizzard three. It melts by one or two
  levels a day once the high is above freezing.
- **Floods.** Heavy rain or a storm floods the fords that day and the next.

On the **travel map**, mud and snow slow the going. Mud is worst on unpaved roads and
ploughed fields, at one and a half times the usual time. Snow is one and a half times on most
ground, one and three quarters in the hills, double in the mountains, and one and a quarter on
a bridge or in a village or town. Where both lie, the worse counts. A flooded ford can't be
crossed, and routes go round it, unless a force without wagons has **Risk a flooded ford**
ticked: it wades, and its named men may be swept off (see [travel.md](travel.md#scale-and-time)).
On maps before 1914, wagons can't cross a ford deeper than 2 ft 4 in (0.7 m) even out of flood.
The planned arrival time uses each day's ground where that day's weather is already known
(a busy force's own time may be ahead of the map's clock). Beyond the last known day it repeats that day's ground,
and the summary says from which date the ground is a guess.

On the **battle map**, deep mud or deep snow (level 2 or more) costs +1 movement for every
hex. On the field map each hex a unit goes in it also counts one toil toward its fatigue
(*Fatigue*, below).

## Weather in battle

These apply to missile attacks once the turns start, on the battle map and the field map
alike (the field map counts its 11-yard, 10 m hexes as five battle-map hexes). Close combat is not
affected.

| Weather | Effect |
|---|---|
| Fog | Can't aim beyond 25 hexes (55 yards, 50 m) |
| Rain | Can't aim beyond 150 hexes; bows and crossbows −10% (wet strings) |
| Snow, heavy snow | Can't aim beyond 75 or 40 hexes; bows and crossbows −10% |
| Heavy rain, storm | Can't aim beyond 75 or 50 hexes; bows and crossbows −20% |
| Blizzard | Can't aim beyond 15 hexes; bows and crossbows −20% |
| Sandstorm | Can't aim beyond 200 hexes (440 yards, 400 m); thermal sights to 450 hexes (985 yards, 900 m) |
| Strong wind | Bows, crossbows, slings and thrown weapons −10% |
| Gale | Bows, crossbows, slings and thrown weapons −20%; firearms −10% |

**The wind's direction** counts too, when the wind is more than calm. It depends on how the
shot lies to the wind: **with it** (the wind behind the shot, within 45 degrees either way),
**into it** (within 45 degrees of straight into it), or across it.

| Wind | With it | Into it |
|---|---|---|
| Breeze | Range bands +10% | Range bands −10% |
| Strong wind | Range bands +20% | Range bands −20%, and −10% |
| Gale | Range bands +30% | Range bands −30%, and −20% |

- The range effect is on bows, crossbows, slings and thrown weapons. Bullets and round shot
  are too heavy to carry or drop much.
- **Driven rain or snow:** a shooter shooting into the wind in rain or snow has it in his
  face, and can see to aim only half as far.
- The strength's own penalty (above) still applies, whichever way the shot goes.
- North is at the top of the battle map and of most battlefields. A battlefield drawn
  otherwise says so (Sidon's has east at the top), and the page turns the wind to match.

A firearm can **misfire**, more often in the wet. Rolled before the attack, it loses the shot.
The chance depends on how the weapon is fired:

| Ignition | Dry | Rain, snow or heavy snow | Heavy rain, storm or blizzard |
|---|---|---|---|
| Matchlock | 15% | 45% | 75% |
| Wheellock, flintlock | 15% | 30% | 45% |
| Percussion cap | 0.6% | 5% | 10% |
| Cartridge | – | – | – |

The dry figures are the Woolwich trials of 1834 (flint about 1 in 6.5, percussion about 1 in
165; project doc "reliability-weapons-research"); no dry figure was found for the matchlock or
the wheellock, which take the flintlock's. The wet steps are design estimates; the one figure
found, about half of Austrian flintlocks failing in rain, is a single report. Automatic weapons
also lose fire to stoppages on the field map (see units.md, *Reliability*).

## Light (the field map)

The field map's weather has a **Light**: daylight, dusk or dawn, a moonlit night or a dark
night. A battlefield's phases can change it as the battle goes on (sunset at Lundy's Lane). In the dark no one can see to aim at, or to call fire on, anything further than the
light allows, and aimed fire, the guns' too, is harder. The weather's own limit still
applies: whichever is shorter counts.

| Light | No aiming or calling fire beyond | Aimed fire | Movement | Losing direction |
|---|---|---|---|---|
| Daylight | (the weather's limit) | – | – | – |
| Dusk or dawn | 20 hexes (219 yards, 200 m) | −5% | – | – |
| Moonlit night | 10 hexes (109 yards, 100 m) | −10% | +1 a hex | 10% |
| Dark night | 5 hexes (55 yards, 50 m) | −20% | +1 a hex | 25% |

- **Flares and illumination.** A hex that is lit is seen as if by day: no limit from the
  dark, and no penalty, for shots at it or for calling fire on it. The GM fires a flare
  with **Clicking the map: Fire a flare** (hand or rifle flares): it lights the hexes within
  10 (about 100 m) for the next 2 exchanges. Mortars and guns can fire **Illumination**
  (see [Indirect fire](units.md#indirect-fire-and-suppression)). Lit ground shows pale
  yellow on the map.
- **From the travel map**, a battle takes the hour's light. Within half an hour of sunrise
  or sunset it is dusk or dawn. At night it is moonlit if the moon is up, at least half lit,
  and the sky is clear (fair weather); otherwise it is dark. The moon is a simple model: it
  rises about 50 minutes later each day, with the sun at new moon and at sunset when full,
  and is up for 12 hours, so the hour can be off by an hour or so. The travel map's clock
  shows the light.
- **Muzzle flashes.** A unit that fires when the light limits sight to less than 30 hexes
  (328 yards, 300 m) shows where it is. Through the next exchange the hexes it fired from
  can be aimed at, and fire called on, from up to 30 hexes away. The light's aim penalty
  still applies. They show as a small star on the map, and the log says when a shot was
  aimed at muzzle flashes.
- **Night vision.** A unit can carry a night-vision device, chosen before the battle on
  the unit (**Night vision**), or set on the battlefield (`nv`). Each sees and aims further
  in the dark, where the light's own sight is shorter or its aim worse:

  | Device | Sees | Aims at worst | Notes |
  | --- | --- | --- | --- |
  | Starlight scope (1960s-70s) | 20 hexes (219 yards, 200 m) | −15% | one rifle in a squad, a dim picture |
  | Night-vision goggles (1990s on) | 30 hexes (328 yards, 300 m) | −5% | every man |
  | Thermal sight (tanks from the 1980s, teams from the 2000s) | 60 hexes (656 yards, 600 m) | as by day | also sees through smoke, by day or night |
  | Infrared searchlight and sights (tanks, 1950s-70s) | 16 hexes (175 yards, 160 m) | −20% | a tank's active infrared, a short reach |

  By default a unit in the Rangers' kit of 1993, Interceptor body armour or the plate
  carrier carries goggles; **No night vision** (`nv: none`) takes them away, and any unit of
  any side or era can be given a device. The device counts for aimed fire, a vehicle's
  guns and a battery's direct fire, and for calling fire. On the battlefields, the Marines
  on Hill 861A have a few Starlight scopes, the Rangers in Mogadishu left their goggles
  behind for what was to be a daylight raid, and the tanks and Bradleys at Fallujah have
  thermal sights. **Vehicles** (tanks, carriers, lorries, tractors) with no device chosen
  carry their war's: infrared searchlights in Vietnam, thermal sights in the late 20th
  century and in Iraq and Afghanistan, none before (`light.night_vision.vehicles`); a vehicle
  unit's **Night vision** has no "by kit" choice. No device sees past the weather's own
  limit (fog, rain or a sandstorm). The numbers are design estimates.
- **Infrared beams.** A unit whose device is an infrared searchlight (`beam`) that fires in the
  dark lights its target with a beam. Through the next exchange the hexes it fired from can be
  aimed at, and fire called on, from up to 100 hexes (1,094 yards, 1 km;
  `light.night_vision.beam`) by an enemy whose device picks the beam up (`sees_beam`: other
  infrared sets, Starlight scopes and goggles; not a thermal sight, which sees heat). They show
  as a small red star (✦) on the map, and the log says when a volley was aimed at a beam. A
  vehicle that only moves or watches by infrared is not shown (a design choice: it lit up only
  to shoot), and in any dark (dusk included) the beam counts.
- **Washed out.** A device that `washes` (Starlight scope, goggles, infrared set) is no use to a
  unit standing in a flare's or illumination round's light (its own hex lit): its men see the
  dark beyond with their own eyes, and an infrared searchlight there shows no beam. A thermal
  sight is not washed out. The selected unit's panel says so. Light lying between a unit and
  what it looks at does not wash its device out (a simplification).
- **Fixed lines.** A machine-gun unit can be **laid on a fixed line** (**Lay a fixed line**,
  then click the hex). This is done before the battle, by day or at dusk, and the line
  shows as a red dashed line. In the dark, when it has no target it can see, the unit
  fires blind down the line at the nearest enemy within 1 hex of it, in range, at −15%.
  The fog or the dark does not stop it.
- **Moving in the dark** costs 1 more a hex on a moonlit or dark night.
- **Losing direction.** Each unit that moved in the dark may lose its way when its side's
  move ends. The chance is the light's figure, plus half of how far its quality's Nerve is
  below 60 (less half of how far above): green +12%, regular +5%, veteran −3% (rounded down). A unit
  that loses its way ends turned one point off its line, if it still fits, and strays a hex
  on that way: to the front hexside on the side it turned to (veering left, the left one). It
  does not stray off the map, onto other units or ground it cannot stand on, or into contact
  with the enemy; then it only turns. Straying into a minefield sets it off, as any move does.
  It cannot move next exchange, though it may turn.

## Cold (the field map)

The field map's weather has a **Cold**: not freezing hard, hard frost or bitter cold. A battle
sent from the travel map takes it from the day's low: hard frost at 5 °F (−15 °C) or colder,
bitter cold at −13 °F (−25 °C) or colder.

| Cold | Automatic weapons (machine guns, submachine guns, assault rifles) | Movement |
|---|---|---|
| Hard frost | misfire 10% more | – |
| Bitter cold | misfire 25% more | +1 a hex |

Frostbite itself is taken on the travel map, night by night (see
[travel.md](travel.md#disease-and-camp-hygiene)).

**Set up the fight** carries the day's weather, the wind's direction and the ground to the battle map. The
roller's weather bar can change them.

## Rest

A night's rest starts from the camp's own rest: poor without a camp, fair in a watched or
staked camp, good when fortified or quartered.
- It drops one step for every point by which the night's hardship is more than the camp's
  shelter.
- Hardship: rain, snow or a sandstorm 1; heavy rain, a storm or heavy snow 2; a blizzard 3. A frosty
  night adds 1, and a hard frost (14 °F, −10 °C) adds 2.
- Shelter: none for a bivouac; 1 for a watched, staked or fortified camp (fires and the
  wagons drawn up); 3 for quarters under a roof.

Rest runs from bad, through poor and fair, to good.

## Fatigue

Each force carries a fatigue level from one day to the next.

| Level | In a fight | Marching speed |
|---|---|---|
| Fresh | – | full |
| Tired | −5% | full |
| Weary | −10% | 90% |
| Exhausted | −20% | 75% |
| Spent | −30% | cannot march |

Fatigue changes each night, when the force's day ends: when the map's clock passes the
night (**Through the night**, or **Until something happens**), when camp work runs past
the evening, or with **Rest until next morning** (the force stops for the day and waits for
the clock to reach the next morning).
- **Heat:** +1 if the force marched 4 hours or more with the high at 86 °F (30 °C) or over; +2 at
  97 °F (36 °C).
- **Cold:** +1 if it marched 4 hours or more with the high at 23 °F (−5 °C) or under.
- **Heavy going:** +1 for 6 hours or more of marching in deep mud or snow.
- **The night:** a bad night +1; poor 0; fair −1; good −2.

Then, after the night's rest:
- **The night's events** (with **Events on the march**): what desertion, straggling, injuries,
  horses and incidents add (see [travel.md](travel.md#events-on-the-march)).
- **Load:** a force carrying more than its usual load takes a step for every 20 km (12 miles)
  marched under a medium load, 12 km heavy, 6 km overloaded or 2 km immobile, less what its usual
  load would cost (`data/loads.yaml`, `fatigue_km`).
- **Packs lost:** +1 if its men lost the packs they dropped before a fight (no blankets or rations).
- **Thirst:** +1 if it had no water to be had and not enough carried (see
  [travel.md](travel.md#supplies)).
- **Night march:** +1 for 2 hours or more of **March on by night** (`data/uses.yaml`, `night`).

On the battle map each fighter's card shows his fatigue. A fight set up from the travel
map gives each side its force's level.

On the field map, units tire by the same toil rule as a fighter. Each exchange a unit
fights hand to hand counts one toil, and so does each hex it goes in deep mud or snow. The
kit's load sets how much toil makes a step: heavy 12, medium 20, light 30. Units reach
Exhausted at most, and the levels' fight penalty comes off their attack and parry. They
start the battle fresh, and nothing takes the fatigue back before it ends. See
`docs/units.md`, *Fatigue*.

All of this is a first draft, to be tuned in play.

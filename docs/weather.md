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

## Weather

Each day's weather is rolled from the climate's figures for that month:
- Each climate has monthly highs and lows, days with rain or snow, and days with fog.
  These are rounded modern climate normals for a typical place in the region.
- **Wet and dry spells last.** A wet day makes the next one more likely to be wet, and a
  dry day the next dry.
- **Warmth and chill carry over.** Half of a day's warm or cold spell carries into the next.
- On a wet day, rain falls as snow if the day's high is 2 °C or less.
- On a dry day it may be foggy, fair or overcast.
- The wind is rolled separately. A storm brings at least a strong wind, and a blizzard a gale.

The **climate shift** cools the modern figures. The Little Ice Age, roughly 1300–1850, ran
somewhat cooler; the test valley uses −0.5 °C.

| Climate | Like |
|---|---|
| North-west Europe, maritime | England, the Low Countries, the Baltic coast, Gotland |
| Central and eastern Europe, continental | Bohemia, Poland, Hungary, the Rhine valley |
| Mediterranean and Levant coast | Acre, Sidon, Sicily, southern Spain |
| Hot desert and steppe | Mesopotamia, inland Syria, Egypt |

The weather strip on the travel map shows the selected force's day: its date, sunrise and
sunset, marching hours, weather and ground. The GM can **Roll again**, or set the weather,
wind, low and high by hand. Earlier days are listed underneath.

## The ground

Mud and lying snow build up and wear off day by day:
- **Mud.** Rain adds one level; heavy rain or a storm adds two, up to three. Each dry day
  takes off one level, or two in warm weather.
- **Snow.** Snow adds one level, heavy snow two and a blizzard three. It melts by one or two
  levels a day once the high is above freezing.
- **Floods.** Heavy rain or a storm floods the fords that day and the next.

On the **travel map**, mud and snow slow the going. Mud is worst on unpaved roads and
ploughed fields, at one and a half times the usual time. Snow is one and a half times
everywhere, and double in the mountains. A flooded ford can't be crossed, and routes go
round it. The planned arrival time uses today's ground as an estimate for later days.

On the **battle map**, deep mud or deep snow (level 2 or more) costs +1 movement for every
hex.

## Weather in battle

These apply to missile attacks once the turns start. Close combat is not affected.

| Weather | Effect |
|---|---|
| Fog | Can't aim beyond 25 hexes (50 m) |
| Rain | Can't aim beyond 150 hexes; bows and crossbows −10% (wet strings) |
| Snow, heavy snow | Can't aim beyond 75 or 40 hexes; bows and crossbows −10% |
| Heavy rain, storm | Can't aim beyond 75 or 50 hexes; bows and crossbows −20% |
| Blizzard | Can't aim beyond 15 hexes; bows and crossbows −20% |
| Strong wind | Bows, crossbows, slings and thrown weapons −10% |
| Gale | Bows, crossbows, slings and thrown weapons −20%; firearms −10% |

In the wet, a firearm can **misfire**. Rolled before the attack, it loses the shot. The
chance depends on how the weapon is fired:

| Ignition | Rain, snow or heavy snow | Heavy rain, storm or blizzard |
|---|---|---|
| Matchlock | 30% | 60% |
| Wheellock, flintlock | 15% | 30% |
| Percussion cap | 5% | 10% |
| Cartridge | – | – |

**Set up a fight here** carries the day's weather and ground to the battle map. The
roller's weather bar can change them.

## Rest

A night's rest starts from the camp's own rest: poor without a camp, fair in a watched or
staked camp, good when fortified or quartered.
- It drops one step for every point by which the night's hardship is more than the camp's
  shelter.
- Hardship: rain or snow 1; heavy rain, a storm or heavy snow 2; a blizzard 3. A frosty
  night adds 1, and a hard frost (−10 °C) adds 2.
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

Fatigue changes each night, when the force's day ends: after **March to day's end**, when
camp work runs past the evening, or with **Rest until next morning**.
- **Heat:** +1 if the force marched 4 hours or more with the high at 30 °C or over; +2 at
  36 °C.
- **Cold:** +1 if it marched 4 hours or more with the high at −5 °C or under.
- **Heavy going:** +1 for 6 hours or more of marching in deep mud or snow.
- **The night:** a bad night +1; poor 0; fair −1; good −2.

On the battle map each fighter's card shows his fatigue. A fight set up from the travel
map gives each side its force's level.

All of this is a first draft, to be tuned in play.

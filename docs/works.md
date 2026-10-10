# Grave Wounds: camps and defensive works (playtest draft, medieval)

All the numbers are in `data/works.yaml`. The travel page, the roller's battle map and the
Python engine (`gravewounds/travel.py` and `gravewounds/combat.py`) read them from there.

## Making camp (travel map)

Each force on the travel map has a number of **men** and either has **tools** (spades and
axes) or doesn't. Select a force, pick the kind of camp and press **Make camp**.

| Camp | What it is | Needs |
|---|---|---|
| Bivouac | Sleep where you stop. Nothing built and no proper watch. | – |
| Watched camp | A cleared site with fires, the baggage drawn up and a sentry roster. 1 hour. | – |
| Staked camp | A watched camp ringed with sharpened stakes, like archers' stakes against horse. | tools |
| Fortified camp | Ditch, bank and palisade all round, with a gate. | tools |
| Quartered | Billeted in the houses of a village or town. Half an hour. | a village or town |

**How long it takes.**

1. Work out the perimeter. It is a circle round the ground the camp needs: about 20 m² a
   man on foot, and 40 m² with horses or wagons.
2. Multiply the perimeter by each work's labour per metre. Timber for palisades and
   stakes takes longer to fetch when no woods are within a hex.
3. Divide by the men working. Only three-quarters of them work at once; the rest guard
   and cook.

Camp work can use whatever is left of the day's 8 marching hours and then 4 evening hours,
so a camp made at the end of the march costs no marching time. Work beyond that runs on
into the next day and uses that day's marching hours first.
The results are realistic, if harsh: a band of 12 can stake its camp in an afternoon but
would need days to fortify it, while 1,000 men fortify a camp in about 5 hours. That is in
line with the few hours a Roman legion took for its marching camp.

Each kind of camp also records how hard it is to surprise and how well the men rest. These
are for later rules on surprise, rest, camp hygiene and disease.

A force can make each kind of camp once in a place. Changing to another kind there (say, a
watched camp to a staked camp) costs the new camp's work but not its set-up hour again.

The Camp section names the selected force. **Set up a fight with … at its camp** opens the
roller's battle map with:
- the selected force's camp laid out in the middle, sized for its men
- up to eight of its men inside the camp, as the defenders
- the nearest force from another side on the travel map, up to eight of its men, at the
  far edge facing the way in, as the attackers

**Add** brings in more fighters on the attackers' side.

## Works on the battle map

Linear works lie along the edges between hexes. The others fill a hex.

| Work | Lies on | Crossing | Cover against missiles | Close combat | Breach |
|---|---|---|---|---|---|
| Ditch | edge | +2 movement | – | −10% attacking up out of it | – |
| Earth bank | edge | +1 | −20%, high side only | −10% attacking up | – |
| Palisade | edge | blocks | −40% | only reach 2 strikes over it | 12 man-rounds |
| Gate | edge | barred: blocks; open: free | −40% while barred | only reach 2 while barred | 20 |
| Stone wall | edge | blocks | −50% | −20% attacking up; only reach 2 strikes over it | – |
| Stakes | hex | +1; no horses | – | – | 2 |
| Abatis (felled trees) | hex | +2; no horses | −20% to a man in it | – | 8 |
| Pavise | hex | free | −20% to the man behind it | – | – |
| Wagon | hex | blocks | −40% to a man behind it | – | 10 |

- **Cover** applies to a man right behind the work, on the side away from the shooter.
- **Height** applies when the attacker is on the low side and the defender on the high,
  inner side of a bank, ditch or wall.
- A man can strike over a palisade, a barred gate or a wall only with a spear, a bill or
  another weapon with reach 2.
- **Breaching.** On his turn, a fighter next to a breachable work can spend his attack on
  it: one man-round of axe or fire work. When the man-rounds reach the breach number it is
  open, and he can move and fight through the gap. A bank or ditch under a breached
  palisade stays.
- **Gates.** A gate can be opened from inside, and barred again from either side.

**Building works by hand.**
- Press **Build works**, pick a work and click the map.
- For a ditch, bank or wall, click just inside the edge, on the side that should be high.
  For a gate, click on the inside.
- Click the same place again to take the work away.
- The page shows roughly how many man-hours the works on the map would take to build.

## Where the ideas come from

These are described in our own words.
- **Stakes.** English archers in the Hundred Years' War planted sharpened stakes in front
  of their line against cavalry; Agincourt (1415) is the best-known case.
- **Wagon laager.** The Hussites in the 1420s fought from chained war-wagons. Armies on the
  move often drew their baggage wagons up as a barrier.
- **Ditch, bank and palisade.** The standard field fortification of camps and siege lines,
  from Roman marching camps through the Middle Ages.
- **Pavise.** The tall shield that crossbowmen set up and shot from behind.

All labour figures and effects are design estimates, to be tuned in play.

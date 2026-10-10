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

1. Lay the camp out as the battle map would. Its ring of 2 m hexes is big enough for the
   ground the camp needs: about 20 m² a man on foot, and 40 m² with horses or wagons.
   A fortified camp puts its bank and palisade on the ring's outer edges, its ditch one
   ring further out and its gate on the east side; a staked camp fills the next ring out
   with stakes.
2. Add up the labour of everything laid out: each work's labour per metre along each hex
   side, and its labour for each gate or hex of stakes. Timber for palisades and stakes
   takes longer to fetch when no woods are within a hex.
3. Divide by the men working. Only three-quarters of them work at once; the rest guard
   and cook.

Camp work can use whatever is left of the day's 8 marching hours and then 4 evening hours,
so a camp made at the end of the march costs no marching time. Work beyond that runs on
into the next day and uses that day's marching hours first.
The results are realistic, if harsh: a band of 12 can stake its camp in an afternoon but
would need days to fortify it, while 1,000 men fortify a camp in about 6 hours. That is in
line with the few hours a Roman legion took for its marching camp.

Each kind of camp also records how hard it is to surprise and how well the men rest. These
are for later rules on surprise, rest, camp hygiene and disease.

A force can make each kind of camp once in a place. Changing to another kind there (say, a
watched camp to a staked camp) costs the new camp's work but not its set-up hour again.

A column of forces marching together makes one camp, sized for all its men, and all of them
dig (see [travel.md](travel.md)). Their camp's men and area count every force in it.

Because the travel map costs exactly the works the battle map lays out, the camp's
man-hours on the travel map and on the battle map agree.

**A camp too big for the battle map** (about 700 or more men on foot, at the map's largest
of 80 × 60 hexes) is laid out at its true size, with its middle moved west. The stretch
with the gate is on the map, facing the attackers at the east edge, and the rest runs off
it. The defenders start inside, near the gate. The labour line gives the works on the map
and the whole camp's figure, which matches the travel map.

**A fight needs the enemy there.** An enemy force must first march to within 1 km of the
camp (the same or the next hex): select it, and in **Plan route** click the camp's force
to send it there. Until then the fight button is off and says why.

**Set up the fight** then opens the roller's battle map with:
- the defending force's camp laid out in the middle, sized for its men. If the selected
  force has no camp, the fight is at a camp within reach: a friendly force's first (that
  force defends, with the selected one beside it), else an enemy's (the enemy defends).
- up to eight men from each defending force inside the camp, the camp's own force nearest
  the middle. Friendly forces within reach of the camp join the defence if they had
  arrived by the time the fight starts; a force still on the road misses it, and the page
  says so. A force that made camp counts as there from when it began, since it was there
  while it dug.
- every force from another side within reach, up to eight men each, at the far edge facing
  the way in, as the attackers
- the fight's date and time: once the defender is ready (its camp finished) and the last
  attacker has arrived. The page says which.
- **If the attackers arrive before the camp is finished, the GM chooses.** The page says
  how far along the camp is when they arrive. **Attack now** fights at that moment, against
  only the works built so far. **Wait** fights once the camp is finished. Works go up in
  the order the camp lists them: for a fortified camp the ditch first, then the bank, then
  the palisade, and the gate last. Each kind goes all the way round, starting from the gate,
  before the next begins. A stretch shows on the battle map only once its labour is done.
- that day's weather and ground, each side's fatigue, and whether the timber was hauled

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
- The page shows how many man-hours the works on the map would take to build. Tick
  **Timber hauled from afar** when no woods are near; a camp from the travel map sets it.

## Works on the field map

The field map (10 m hexes, units of the rank and file) uses the same works with the same
numbers along its hex sides and in its hexes, and lays out a camp from the travel map at
its own scale. How they act on units is in [units.md](units.md) (*Ground, works and
weather*).

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

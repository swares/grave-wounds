# Unit combat (playtest draft)

Rolling for every man every round is fine for a skirmish of a dozen. For a battle of
hundreds, the rank and file fight as **units**, resolved in bulk. Named characters still
fight one by one with the full rules in [combat.md](combat.md), and can lead or stand in
a unit.

All the numbers are in `data/units.yaml`. They are design estimates, tuned by simulation:
`python3 -m gravewounds units` prints the pace and the example fights below.

The rules and engine are in `gravewounds/units.py`; the field map page, `dist/field.html`,
runs the same rules in the browser (`templates/units.js`, checked against the Python).

## The choices behind it

- **Heroes and units.** The rank and file are units; named characters fight individually.
- **A field map.** Hexes of about 10 m. A unit is a block of hexes along its front, one
  or more deep. A hex holds about 40 men in close order: 10 abreast, 4 deep.
- **An exchange is about a minute**, roughly ten individual rounds.
- **Casualties come from the wound tables in bulk.** Each blow that gets through is rolled
  like a single fighter's, so the battle's wound records still decide what kind of hurt a
  unit takes.

## One exchange

1. **Who strikes.** In melee, the front rank of each hex touching the enemy: 10 men to a
   hex face. With spears, bills and other reach-2 weapons the second rank strikes too.
   With missiles, the men who have the target in range; the field map counts them (the
   front two ranks of a line).
2. **How many blows tell.** Most of a minute in a press is shoving, guarding and watching
   for an opening. Each exchange, a share of the striking men (`melee.tempo`, about one in
   eleven) makes a real attempt. Archers loose `rate` shots a minute, and a share of those
   (`missile.tempo`) are aimed at a man rather than at the mass.
3. **Each attempt is an individual attack.** d100 against the unit's attack %:
   - green 40%, regular 50%, veteran 60%;
   - plus situation: flank +20, rear +30, a mounted charge +20 (and twice the tempo) in
     its first exchange, shaken −10;
   - for missiles, minus the range band (medium −20, long −40), weather and cover.

   A critical (a tenth of the chance or less) cannot be parried. Otherwise the defender
   parries on d100 against his unit's defence: green 25%, regular 35%, veteran 45%. There
   is no parry from the flank or rear, or against missiles. A shield still counts, through
   the hit-location tables.
4. **The wound.** Location, mechanism and severity from the margin, then armour, exactly
   as for a single fighter.
   - A light wound, or a graze: he fights on.
   - Serious or critical: a stop check against the unit's Nerve (−10 for critical).
     Failing takes him out of the fight (*down*).
   - A wound that kills within rounds or outright: dead (and down).
5. **Morale** (below), then the next exchange.

## Morale

After each exchange a unit checks if any of these happened:
- it lost the exchange in contact (more of its men put down than it put down);
- a quarter of its starting men are down;
- a tenth of its men went down in this exchange;
- it was struck in flank or rear.

The check is d100 against its Nerve (green 35, regular 50, veteran 65), with modifiers:

| Modifier | |
|---|---|
| Still steady (ranks closed) | +20 |
| A named leader with it, up | +10 |
| Its leader down | −20 |
| Half its men down | −20 |
| Struck in flank or rear | −20 |
| A steady friendly unit beside it | +10 |
| Lost the exchange | −5 a man more lost than it put down (at most −30) |

- **Steady, fails:** shaken. A shaken unit fights at −10 and cannot charge. It breaks at
  once instead if it fails by more than 20 while flanked or with half its men down.
- **Shaken, fails:** broken.
- **Shaken, passes out of contact:** it rallies to steady.

## The rout

A broken unit runs. Every enemy man in reach strikes it, not just the front rank, at +20,
with no parry, at twice the melee tempo, for as long as the pursuers keep contact (the
simulation assumes three exchanges). This is where most of a battle's dead fell: the
defeated sides at Towton and Agincourt lost far more men in flight than in the press.

## What the numbers give

Regular swordsmen front to front, on the Towton tables, per minute:

| Against | Hit | Put out of the fight |
|---|---|---|
| No armour | 3.2% | 1.1% |
| Gambeson and cap | 2.6% | 0.7% |
| Jack and sallet | 1.5% | 0.4% |
| Mail hauberk | 1.1% | 0.3% |
| Full plate | 0.2% | 0.0% |

Example fights, 120 men a side, 30 abreast (medians of 40 runs):

| Fight | Breaks after | Who broke | Winner down | Loser down |
|---|---|---|---|---|
| Equal regulars, no armour | 12 min | either | 3 | 22 |
| Equal regulars in jacks | 27 min | either | 2 | 10 |
| Regulars v greens, in jacks | 17 min | greens 36 of 40 | 1 | 13 |
| Bills v swords, in jacks | 16 min | swords 29 of 40 | 1 | 12 |
| Veterans in mail v unarmoured regulars | 9 min | regulars every time | 0 | 28 |

A melee of tens of minutes, decided by morale more than by wounds, with the beaten side
losing most of its men in the rout: that is the shape the records show.

Missiles: 100 longbowmen at medium range hit about 8 unarmoured men a minute, and about
7 men in mail. At long range it is about a third of that.

## The field map

`dist/field.html` fights a battle on a field of 10 m hexes (60 × 40 by default, 600 × 400
m). Pick the wound tables, name the two sides, and add units: men, quality, close or open
order, weapon, armour, and whether they are mounted.

**A unit on the map.** A unit is a block of hexes. Its front row runs along its line, and
it faces the corner between two hexsides (the arrow). Close order holds 40 men a hex, 10
abreast and 4 deep; open order holds 20, 10 abreast and 2 deep. A unit's width is how many
hexes its front row has; the rest of its men stand in rows behind. As men go down, the
block shrinks from the back.

**Arcs.** The two hexsides either side of the facing corner are the front; the next one on
each side is the flank; the two behind are the rear.

**Turn order.** Each exchange (about a minute):
1. Every broken unit runs straight back, as far as it can move; a unit that runs off the
   map has fled the field.
2. Side A moves its units, then side B moves its units.
3. Every melee and volley is resolved at once from where the units now stand, then losses,
   then morale. A unit that breaks is struck at once by every man of each enemy unit
   touching it.

**Movement**, in hexes an exchange:

| | Hexes |
|---|---|
| Close order on foot | 6 |
| Open order on foot | 8 |
| Mounted | 15 |

- Turning the facing one step (60°) costs 1 hex for every 2 hexes of front (at least 1).
- A unit cannot pass through other units' hexes.
- A unit in contact with an enemy cannot move.
- **A charge:** a steady unit whose move ends in contact may move up to twice its
  allowance. Mounted men who charge get the charge bonus (+20, twice the tempo) in that
  exchange's fight.
- **Pursuit:** contact with a broken unit is a charge like any other, and every man of the
  pursuing unit strikes the fleeing.

**Who fights.** A front hex fights the enemy hex across its front hexsides; whether that
is the enemy's front, flank or rear depends on the side it is struck from. Each front hex
puts its front rank in (10 men), or its first two ranks with reach-2 weapons.

**Who shoots.** A unit with missile weapons that is not in contact shoots at the nearest
enemy in range ahead of it (in the half of the field its front faces). The front two ranks
of each front hex shoot. Shots at a unit in open order count 0.8.

**Range** is the weapon's battle-map range in 2 m hexes, divided by 5 for field hexes:
a longbow's long range of about 250 m is 25 field hexes.

The page keeps the battle in the browser, so it can be closed and reopened. *New battle*
starts again from the starting units.

## From the travel map

On the travel map, **Set up the fight** with **Fight it on: the field map** opens this page
with the forces that are there: the defender and any friends beside it on side A, the
attackers on side B, each with its fit men (the sick stay out). The GM splits each force
into units with **Add a unit**, choosing the force to draw the men from. A force's men left
out of every unit stay in reserve and do not fight.

## After the battle

**End the battle** stops the fighting (at any time; usually when one side has no unit left
standing). Every wounded man was remembered as he was hit: the wound's severity, its
untreated time to death and its infection risk, and whether he went down. Then:

1. **The field.** A side with no unit still standing has lost the field: the men it had
   down there are left behind and die. The wounded still on their feet go with their units.
2. **The death clock.** A wound that kills in minutes kills before help comes, unless he is
   bound in time (1 in 10). One that kills in hours kills unless his camp can treat it: no
   chance with no camp, 40% in a camp, 60% in quarters.
3. **To camp.** The rest are carried to their force's camp and heal on the wound track,
   where wound fever can still take them (see [travel.md](travel.md), *The wounded*).

A man wounded twice is counted once. **Back to the travel map** (for a battle set up from
there) takes the dead off each force, adds its wounded to its sick, and moves each force's
clock on by the battle's length (a minute an exchange). The numbers are in
`data/units.yaml` (`aftermath`) and `data/disease.yaml` (`wounds`).

## Heroes

Named fighters from the wound roller can join a unit (**Heroes**, during set-up). Each
keeps his own attack and defence (from his experience: green 40/25, regular 50/35, veteran
60/45, and the GM can change them), his Nerve, weapon and armour. He is extra to the
unit's men. Where he stands decides what he does:

- **Front rank** (a hand weapon): whenever his unit fights hand to hand, he makes his own
  telling attempts, three times a ranker's (he seeks the fight), with his own attack, and
  the blows on his unit's front fall on him twice as often as on any man of its front rank.
- **Shooting** (a missile weapon): whenever his unit shoots, he shoots three times a
  ranker's aimed shots with his own attack. Missiles at his unit fall on him as on any of
  its men, and in contact he is in its front rank like a front-rank hero, but does not
  strike.
- **Behind** (commanding): only at risk if his unit routs.

His wounds use the full rules: location, mechanism, severity from the margin, his own
armour, his own parry. A serious or critical wound calls for his stop check against his
Nerve; a failure puts him down for the rest of the battle. A wound that kills within rounds
kills him. A **leader** gives his unit +10 morale while he is up, and −20 once he is down.
A unit with a hero still up shows a star on the map.

After the battle, **Heroes' wounds to the roller** puts each wound on his record in the
wound roller (with its bleeding, pain and clock), and marks him out of the fight if he went
down. A duel between two heroes facing each other is not fought here: take it to the roller.
`python3 -m gravewounds units` shows how heroes fare:

| A hero leading billmen in jacks, until one side breaks | Wounded | Down | Killed | Men he puts down |
|---|---|---|---|---|
| Knight in mail | 48% | 14% | 0% | 0.3 |
| Knight in plate | 22% | 0% | 0% | 0.3 |
| Champion, no armour | 69% | 28% | 2% | 0.3 |

A hero matters most through morale and through what happens to him: in a press of hundreds,
one man fells few. The numbers are in `data/units.yaml` (`heroes`).

## Ground, works and weather

**Clicking the map** picks what a click does: place and move units, open or bar a gate,
paint the ground, or build works. Ground and works are set before the battle starts; a gate
can be opened or barred at any time.

**The ground**, painted hex by hex (drag to paint several):

| Ground | Movement to enter | Other |
|---|---|---|
| Open | 1 | |
| Rough | 2 | |
| Woods | 2 | −20% to shots at men in it |
| Marsh | 3 | no horses |
| High ground | 1 | −10% to blows struck up at men on it from lower ground |

**Works** are the battle map's (see [works.md](works.md)), with the same numbers, along
the sides of the 10 m hexes or in a hex. For a ditch, bank or wall, click just inside the
side, on the high side; for a gate, on the inside. Click again to take it away.
- **Crossing:** a unit's move pays each work its middle hex crosses or enters (a ditch +2,
  a bank +1, stakes +1, felled trees +2). A palisade, wall or barred gate stops it, and a
  unit cannot stand across one. Wagons fill their hex. Horses cannot go into stakes, felled
  trees, wagons or marsh.
- **Close combat:** across a palisade, wall or barred gate, only reach-2 weapons strike, and
  only the front rank. Striking up a bank, ditch or wall costs its height (−10%, a wall
  −20%), as does striking up onto high ground. Horses charging into stakes or felled trees
  get no charge bonus.
- **Shooting:** the target takes the best cover of the works and ground where the volley
  lands (the target's hex nearest the shooters): a bank on its side −20%, a palisade or
  barred gate −40%, a wall −50%, a pavise or felled trees in its hex −20%, wagons in front
  −40%, woods −20%.
- **Breaching:** a unit's **Breach the works** order puts half of each front hex's front
  rank to hacking at the palisade, gate, stakes, felled trees or wagons in front of it, every
  round of the exchange, until the work is down. The work's breach figure is for a 2 m side;
  a 10 m side takes five times as much, so ten men open a stretch of palisade in about a
  minute. A bank or ditch under a breached palisade stays.

**The weather** (set under *Weather*, or brought from the travel map) works as on the
battle map: no shooting beyond what can be seen (fog 5 hexes, heavy rain 15), wet strings
−10% or −20% for bows and crossbows, a strong wind −10% (a gale −20%) on missiles, firearms
misfiring in the wet (a share of the shots lost), and deep mud or snow (level 2 or more)
+1 movement a hex.

**A camp from the travel map.** A fight sent from a force's camp lays the camp's works out
at the field map's scale (sized for the defender's men on 10 m hexes), as far as they were
built when the fight starts, with the gate on the east, facing the attackers' edge. The
defenders' units start inside it, the attackers at the east edge.

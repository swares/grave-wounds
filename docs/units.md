# Unit combat (playtest draft)

Rolling for every man every round is fine for a skirmish of a dozen. For a battle of
hundreds, the rank and file fight as **units**, resolved in bulk. Named characters still
fight one by one with the full rules in [combat.md](combat.md), and can lead or stand in
a unit.

All the numbers are in `data/units.yaml`. They are design estimates, tuned by simulation:
`python3 -m gravewounds units` prints the pace and the example fights below.

This is step 1, the rules and the engine (`gravewounds/units.py`). Step 2 puts units on
the field map (see *Still to come*).

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

## Still to come (step 2)

- **The field map page:** units as blocks of hexes with a front and a facing; moving,
  wheeling and charging; contact and range worked out from the map; flank and rear; works
  and weather from the battle map's rules.
- **From the travel map:** a fight set up from the travel map can open on the field map,
  with each force as one or more units (fit men only).
- **Heroes in units:** a named character in a unit's front rank fights with the full
  individual rules, against an enemy hero or into the enemy unit, while his unit fights in
  bulk around him. His blows count toward the exchange. A leader adds to his unit's morale
  while he is up.
- **After the battle:** the wounded who fought on, and those down, carried to camp, where
  wound fever and disease (camp disease) can take them.

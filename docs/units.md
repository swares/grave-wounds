# Unit combat (playtest draft)

Rolling for every man every round is fine for a skirmish of a dozen. For a battle of
hundreds, the rank and file fight as **units**, resolved in bulk. Named characters still
fight one by one with the full rules in [combat.md](combat.md), and can lead or stand in
a unit.

All the numbers are in `data/units.yaml`. They are design estimates, tuned by simulation:
`python3 -m gravewounds units` prints the pace and the example fights below.

The rules and engine are in `gravewounds/units.py` (the enemy commander in `commander.py`, the
turn of a battle in `battle.py`); the field map page, `dist/field.html`, runs the same rules in
the browser (`templates/units.js`, checked against the Python).

## The choices behind it

- **Heroes and units.** The rank and file are units; named characters fight individually.
- **A field map.** Hexes of about 11 yards (10 m). A unit is a block of hexes along its front, one
  or more deep. A hex holds about 40 men in close order: 10 abreast, 4 deep.
- **An exchange is about a minute**, roughly ten individual rounds.
- **Casualties come from the wound tables in bulk.** Each blow that gets through is rolled
  like a single fighter's, so the battle's wound records still decide what kind of hurt a
  unit takes.

## One exchange

1. **Who strikes.** In melee, the front rank of each hex touching the enemy: 10 men to a
   hex face, and one more rank for each hex of the weapon's reach past the first, up to the
   formation's ranks: spears and bills (reach 2) strike from two ranks, the pike (reach 3)
   from three.
   With missiles, the men who have the target in range; the field map counts them (the
   front two ranks of a line).
2. **How many blows tell.** Most of a minute in a press is shoving, guarding and watching
   for an opening. Each exchange, a share of the striking men (`melee.tempo`, about one in
   eleven) makes a real attempt. Archers loose `rate` shots a minute, and a share of those
   (`missile.tempo`) are aimed at a man rather than at the mass.
3. **Each attempt is an individual attack.** d100 against the unit's attack %:
   - green 40%, regular 50%, veteran 60%;
   - plus situation: flank +20, rear +30, a mounted charge +20 (and twice the tempo) in
     its first exchange, shaken −10; pikemen striking horse to their front +20 (see *A
     front of pikes*, below);
   - for missiles, minus the range band (medium −20, long −40), weather and cover;
   - a tired unit: its fatigue level's penalty (*Fatigue*, below) off its attack, struck or
     shot, and off its parry.

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
   - **Modern fire** (`modern_fire` in `data/units.yaml`: breech-loading rifles and
     carbines (from the Sharps, Spencer and Springfield of the 1860s), magazine rifles,
     machine guns, pistols and submachine guns, grenades, mortars, shell and mines)
     stops more men: a serious or critical wound always puts him down, and a light one calls
     for the stop check; a graze still leaves him fighting. Casualty returns from 1914 on
     count nearly every man hit as out of the line: he went back to the aid post. With
     regulars that puts down about two hits in three on the First World War table (one in
     five under the old rule), 72% on the 1944 table. Muskets, older guns and blades keep
     the rule above.
5. **Morale** (below), then the next exchange.

### Fatigue

Units tire by the same rule as a single fighter's toil (`characteristics.toil` in
`data/wounds.yaml`). Every exchange a unit strikes or is struck in hand to hand counts one
toil, and so does every hex it goes in deep mud or snow (level 2 or more), counted as the
hexes from where it stood at the end of the last exchange to where it stands now. Its kit's
load sets how much toil makes it a step worse: 12 for heavy kit (plate harness, a 1630
cuirassier's, the heaviest modern body armour), 20 for medium (a hauberk, a jack, a
brigandine, most modern vests), 30 for light (everything not listed: a gambeson, no armour). Toil takes it to Exhausted at
most (`worst`, 3 steps). Each step costs its fatigue level's penalty (`fatigue.levels` in
`data/weather.yaml`: Tired 5, Weary 10, Exhausted 20) off its attack, in hand to hand and
shooting, and off its parry. The unit's line on the map shows its level. Nothing takes it
back during the battle. Shooting and being shot at cost no toil. Vehicles don't tire. Heroes
fight on their own sheets, untouched by their unit's fatigue. Units start the battle fresh
(a fight sent from the travel map does not yet carry the force's own level onto its units).

This is what costs the French at Agincourt: their men in plate reach the English line
already Tired from the mud, and the fighting and the mud behind them soon make them
Exhausted. Measured over the battlefields there were then (37; there are now 44), 4 seeds each, only Agincourt changes its
result. The English still have units standing at the end of all four runs (before, two runs
ended with the whole English army gone), and they win one of the four outright. The other three still go to
the French on the share of men lost, because one English archer block breaks and is cut
down in the rout. See the review for the morale trigger behind that.

### Quick-play blows and shellfire

Rolling every blow (steps 3 and 4) is exact but slow at a table. `quick` in `data/units.yaml`
gives a GM's alternative, **off by default** (`quick.blows: false`; the field page's
*quick-play blows* box turns it on for the battle in hand):

- **The rates.** For each pairing (wound table, weapon, armour kit, the target's quality,
  attack %, parry %) the share of tries that end each way (missed, parried, stopped, a light,
  serious or critical wound, a man down, a man dead, and each kind of wound for the
  aftermath) is the per-blow rules' own, worked out once from `quick.samples` (4,000) tries
  on dice of the pairing's own (seeded from the pairing, so the same every time). This is the
  page's stand-in for the printed chart.
- **The roll.** A group's men down are one d100 read on the binomial curve for its tries
  at that share: the per-blow dice's own spread, not just their average. A small group
  reads the curve's own percentiles; from a spread (variance) of `quick.normal_from` (9) it
  reads the normal curve's. The dead among the men down, and the lightly wounded who fight
  on, are the averages rounded at random (bookkeeping, not a table roll).
- **Heroes.** A blow that falls on a hero is still rolled on its own, as before; quick-play
  covers the rankers only.
- **Shellfire.** The same switch rolls a battery's shellfire on a unit once: each man within a
  burst's reach would be struck at the % for his distance (cut for going to ground and
  cover), so the average is the sum of those chances over every burst of that fire, and the
  men struck are one d100 on the binomial curve, as for blows (`_shell_struck_unit`). Each man
  struck still rolls his wound. In the modern battlefields 89% of the d100s were these
  per-man rolls; counted on one run of every battlefield, quick-play took the d100s an exchange
  from 1914 on from 126 to 17 (blows alone: 120), and before 1914 from 296 to 52. The average is exact (the same per-man chances); the spread is a little wider than
  rolling each man, since one curve stands for men at different distances from the bursts.
- **On paper.** The tables carry a chart for each era: men down per 100 tries for its
  example weapons against its example armour at attacks 30, 45, 60 and 75, against regular
  men, with the green and veteran factors and the parry factor (×(1 − parry × 0.9)), and a
  d100 spread chart (Poisson below an average of 9, the normal curve above). The field page's
  *Quick-play sheet* prints the exact figures for the units on the field.

Measured in self-play (12 runs a battlefield, quick-play on): the share of blows of each
kind that put a man down matched the per-blow rules (a volley at North Vietnamese 0.243 a
try, against 0.235), and 285 of 444 runs matched the battle as fought, against 313 with
per-blow dice. The same rules on seeds 13 to 24 gave 290 against 313 on seeds 1 to 12, so a
12-run difference of this size is within the runs' own spread; it is a GM's choice, not a
change to the rules. The Python mirror is `gravewounds/units.py` `_quick_blows`.

## Morale

After each exchange a unit checks if any of these happened:
- it lost the exchange in contact (more of its men put down than it put down; for a unit holding
  a position, below, only its losses hand to hand count here);
- a quarter of its starting men are down (for a unit holding a position, below, only in an
  exchange it lost men);
- a tenth of its men went down in this exchange;
- it was struck in flank or rear.

The check is d100 against its Nerve (green 35, regular 50, veteran 65), with modifiers:

| Modifier | |
|---|---|
| Still steady (ranks closed) | +20 |
| A named leader with it, up | +10, and his rank bonus |
| Its leader down | −20 |
| Half its men down | −20 |
| Struck in flank or rear | −20 |
| A steady friendly unit beside it | +10 |
| Dug in: gone to ground or in a bunker | +10 |
| Lost the exchange | −5 a man more lost than it put down (at most −30) |

- **Steady, fails:** shaken. A shaken unit fights at −10 and cannot charge. It breaks at
  once instead if it fails by more than 20 while flanked or with half its men down (a unit
  holding a position is not flanked; see below).
- **Shaken, fails:** broken.
- **Shaken, out of contact:** it checks to rally each exchange nothing new strikes it: passing,
  it rallies to steady; failing, it stays shaken. (Until October 2026 a failed rally broke it,
  so a shaken company out of contact broke about half the time each exchange; self-play, all
  46 battlefields: 202 of 276 runs as fought, against 198.)

**Holding a position** (`morale.posture`). A unit of a side the commander has holding its ground
(not attacking), that holds a position, and is not struck in flank or rear, checks for being a
quarter down only in an exchange in which it lost men. Holding a position means: in a bunker, dug
in or emplaced, behind works with cover toward the nearest enemy, in ground that hides men
(buildings, tall buildings, rubble), or gone to ground in ground that gives cover (woods, scrub;
`morale.posture_cover`). Units in the open, and attackers wherever they lie, check
every exchange as before. A garrison in its holes no longer breaks from the passing of time; one
that is being hit still checks, as does any unit flanked, hit hard, or losing the fight in contact.
The research behind it (the project's breakpoints-pre1914 and morale-two-kinds notes): breaks
come cheap from flanks, charges and neighbours running, but late from frontal attrition, and dug-in
units hold far past any threshold. Measured on 24 runs of every battlefield: 642 of 888 from 628,
the morale targets unchanged; Keating 12 to 20, Pork Chop 10 to 16, X-Ray 7 to 9. A first version
applied it to attackers in cover too, and at Wanat the Taliban in the draw stopped breaking (23 to
16); a check when a unit of its own side within 2 hexes broke was measured and changed nothing.

**Flanked, holding a position** (`morale.posture_flank`). A unit holding a position (as above)
is not flanked: men in buildings or works face every way. Being struck in flank or rear neither
calls a check, nor costs it 20, nor breaks it at once. Before 23 October, at Keating, the barracks
(B Troop, 10 to 21 men, steady) broke in 4 of 24 runs the first time one to three insurgents
reached its flank hand to hand, having lost no one or one man; the accounts have the men in its
buildings holding all morning. A failure only shaking it was measured first and changed nothing
there: shaken and still flanked, it broke the next exchange.

**Losing the fight, holding a position** (`morale.posture_hand`). A unit holding a position (as
above) and not flanked has lost the exchange in contact only if it lost more men hand to hand than
it put down hand to hand. Men lost to fire from afar still count toward the quarter-down and shock
checks. At the June Redan the 600 Russians behind the parapet checked, and broke, over men lost to
British rifles about 180 m off, which their smoothbores could not answer, while the fight with the
ladder party at the parapet was even. Units in the open and attackers count every loss: the French
at Agincourt broke under the archery while at the English line, as they did in 1415. Measured on
24 runs of every battlefield: 671 of 912 from 658; the June Redan 2 to 14 (British losses 25% to
60%, as the assault was cut down), the September Redan 21 to 22, Babuna 5 to 6, Lützen 18 to 17;
before 1914 units break at a median 20% down (from 17%) and the rout's share is 8% (from 4%).

Lying in cover was added later (`morale.posture_cover`). At X-Ray no American company counted as
holding a position: they lay in the trees, the elephant grass and the dry creek bed, not in works,
and still broke a quarter down. Measured on 24 runs of every battlefield against main at 642 of
888: 652, X-Ray 9 to 18, Hamburger 19 to 20, the morale targets unchanged. Counting only losses hand
to hand for "lost the exchange in contact" was measured with it and not built: it did not help Hue
(1 to 0), where the Marines then broke from the hand-to-hand fights they met storming the
buildings, and it cost Agincourt (8 to 3) while lifting the June Redan (2 to 13).

## The rout

A broken unit runs. Every enemy man in reach strikes it, not just the front rank, at +20,
with no parry, at twice the melee tempo, for as long as the pursuers keep contact (the
simulation assumes three exchanges). This is where most of a battle's dead fell: the
defeated sides at Towton and Agincourt lost far more men in flight than in the press.

**Cornered** (`rout.surrender`). A broken unit that cannot run (no clear ground back, so it
would stand where it is) with an enemy touching it gives up at the start of the exchange,
rather than being struck again and again. The war's quarter % of its men standing
(`heroes.quarter`, the same figure as for a man found lying out) are taken prisoner and the
rest killed; its heroes on their feet are taken. The log says so, *After the battle* counts
the prisoners, and a team's side offers the enemy it took to the team builder's captives, as
with the pursuit. Sides the accounts show fighting to the end do not surrender
(`fight_on` in `data/orders.yaml`): the North Vietnamese at Hue (about 52 killed for each
prisoner), X-Ray, Dak To, Hamburger Hill and Khe Sanh (about 20 for each in Vietnam's official
counts, 1965-67), the Japanese at Bougainville (about 83 for each on Iwo Jima), and the
Chechens at Grozny (about 11 to 14 for each). Sides with no figure (the Chinese in Korea, the
insurgents, the Somali militia) can surrender. The research (the project's surrender notes:
The Dupuy Institute's capture-rate study, Shils and Janowitz, Dstl): a defender's prisoners
rise steeply once it is penetrated and again once it is enveloped; being cut off was the
cause veterans gave most for units giving way; men trapped in cellars and bunkers gave up as
a group; and towns cornered more defenders (a median 32% of urban defenders' losses were
prisoners, 8% in the open). Self-play showed the gap: cornered Somali militia at Mogadishu
were cut down almost to the last man over 79 and 187 exchanges. Measured on 24 runs of every
battlefield: 658 of 912 from 657, the morale targets about as before (the rout's share of the
loser's losses 5% to 4%, now counting prisoners); Visby 23 to 24 (the Gotlanders' losses 21% to
32%: Visby's quarter is 20%), X-Ray, Grozny, Lützen and Agincourt +1; Mogadishu 21 to 19, Wanat
and the September Redan -1. The self-play tools count prisoners as losses.

## What the numbers give

Regular swordsmen front to front, on the Towton tables, per minute:

| Against | Hit | Put out of the fight |
|---|---|---|
| No armour | 3.2% | 1.1% |
| Gambeson and cap | 2.6% | 0.7% |
| Jack and sallet | 1.4% | 0.4% |
| Mail hauberk | 1.1% | 0.3% |
| Full plate | 0.2% | 0.0% |

Example fights, 120 men a side, 30 abreast (medians of 40 runs):

| Fight | Breaks after | Who broke | Winner down | Loser down |
|---|---|---|---|---|
| Equal regulars, no armour | 12 min | either | 3 | 22 |
| Equal regulars in jacks | 24 min | either | 2 | 11 |
| Regulars v greens, in jacks | 16 min | greens 35 of 40 | 1 | 13 |
| Bills v swords, in jacks | 14 min | swords 26 of 40 | 2 | 12 |
| Veterans in mail v unarmoured regulars | 9 min | regulars every time | 0 | 28 |

A melee of tens of minutes, decided by morale more than by wounds, with the beaten side
losing most of its men in the rout: that is the shape the records show.

Missiles: 100 longbowmen at medium range hit about 8 unarmoured men a minute, and about
7 men in mail. At long range it is about a third of that.

## The field map

`dist/field.html` fights a battle on a field of 11-yard (10 m) hexes (60 × 40 by default, about
660 × 440 yards, 600 × 400 m). Pick the wound tables, name the two sides, and add units: men, quality, close or open
order, weapon, armour, and whether they are mounted.

**A unit on the map.** A unit is a block of hexes. Its front row runs along its line, and
it faces the corner between two hexsides (the arrow). Close order holds 40 men a hex, 10
abreast and 4 deep; open order holds 20, 10 abreast and 2 deep. A unit's width is how many
hexes its front row has; the rest of its men stand in rows behind. As men go down, the
block shrinks from the back. A new unit comes in one row wide, all its men abreast; if
that does not fit down its side's edge, it is added narrower and deeper (a quarter narrower
at a time, its rear still on the map) until it fits, and the message says so. **Wider**
and **Narrower** change it afterwards.

**Entry edges.** Each side brings new units in at its own map edge. In set-up they come in
8 hexes in from it, from the middle of the edge outwards, facing into the map. During the
battle they come on at the edge itself.
- **Which edge.** A battlefield can name the edges (`entry: [S, N]`, side A's first).
  Otherwise each side uses the edge behind the way most of its men face, which puts the
  Redan's British in at the south and the Russians at the north.
- **Sharing.** If both sides would use the same edge, the second side takes the opposite
  one. That happens at Mogadishu, where both sides mostly face north.
- **No units yet.** A side with no units uses the edge opposite the other side's. On open
  ground with no units at all, side A uses the west edge and side B the east.

**Unit markers.** On its centre hex each unit carries a marker, drawn like a military map
symbol:
- **Frame.** The first side's units have a rectangle, the second side's a diamond, in the
  side's colour. The sides stay apart in greyscale and for colour-blind players.
- **Glyph.** The glyph shows the unit's type: ✕ infantry; a reversed marker (filled, with a
  light ✕) for skirmishers in open order; one diagonal for cavalry; an arc for archers; a dot
  for artillery; ✕ under a filled bar for machine guns; an inverted V for anti-tank guns; an
  oval for armour; an oval with ✕ for mechanised infantry; a bar on wheels for transport.
  The type comes from the unit's vehicle, arms, mounts and order. A battlefield can set it
  outright with `type` on a unit (units.yaml `markers.types` lists them).
- **Size mark.** A unit that sets `size` (section, platoon, company, battery, battalion,
  regiment, brigade or division) shows its mark above the frame (•, •••, I, II, III, X, XX)
  when size marks are on. A unit facing up has it above its arrow. On a field where no unit
  sets a size, the *size marks* box is greyed out and says so.

  Every battlefield's units have a size. The marks give the scale of what stands on the map,
  not a formal organisation: a detachment of a few companies is marked I, two battalions'
  worth III, a group of regiments X. The Redan's sizes are set in its generators; the
  others are in `tools/maps/unit_sizes.mjs`, which says how they were worked out:
  - **Guns** are a battery; **vehicles** go by number; **machine-gun teams** go by men.
  - **Named units:** the rest go by name where the name says what stands there (A Company,
    1/9th Gurkha Rifles), if that is within a step of the numbers.
  - **The scale:** otherwise by men on one scale for every period (up to 12 a section, 60 a
    platoon, 250 a company, 1,000 a battalion, 3,000 a regiment, 6,000 a brigade, more a
    division).

  So "29th Regiment in the south bunkers", 60 men, is a platoon. Scott's and Ripley's
  brigades at Lundy's Lane are brigades: whole brigades, under strength.
- **Label.** The label sits beside the marker. *Unit labels* under the map chooses names,
  IDs or both. An ID is the side's initial and the unit's number on its side (B3), or A and
  B when the two sides share an initial. A unit keeps its ID for the whole battle, and the
  units list shows it with each unit's full name. *Strength* adds the men after the label.

**Rules on the map.** Four overlays, each switched on or off under the map (all on by
default):
- **Move and fire (selected unit).** The hexes the selected unit's centre can reach this
  exchange are shaded in its side's colour, from the same movement rules the board uses
  for a move. Paler shading covers the ground it can shoot into: ahead of its front, within
  its weapon's reach after the weather and the height between. The shading uses the same
  test as choosing a target, seen from the nearest front hex. A unit or ground in the way
  may still block a shot. Hand weapons have no field of fire.
- **Entry edges (set-up only).** Hatching in each side's colour marks the 8 hexes in from
  its entry edge (above), where its new units come in.
- **Grid references and scale.** Every tenth column and row is numbered and dashed. These
  are the numbers the messages use for hexes (34,60). A scale bar shows 10 hexes (5 on a
  small field) in the distance units chosen at the top of the page.
- **Batteries on call.** A side's batteries with no place on the map show as chips on the
  edge behind its army: tubes, kind, "on call". The edge behind is the way its units face.
  A placed battery is drawn where it stands, as before.

The defaults are units.yaml `markers` (names, strength on, size marks off). A battlefield
can set its own with `markers: {labels, strength, size}`: both Redan battlefields use IDs,
because eleven or more units stand in a narrow space. The legend under the map shows the
types on the field and each side's frame.

**Arcs.** The two hexsides either side of the facing corner are the front; the next one on
each side is the flank; the two behind are the rear.

**Turn order.** Each exchange (about a minute):
1. Every broken unit runs straight back, as far as it can move; a unit that runs off the
   map has fled the field. Its own side's units do not stop it: it runs on through them to
   the first clear ground beyond (up to three times its move in all, `rout.through`; with
   none in that, it stops where it last stood clear). Each friendly unit it runs through is
   **jostled**: its move that exchange is halved, rounded down (`rout.jostle`). Enemy units,
   impassable ground and the map edge stop it as before. A broken unit with no men left has
   gone from the field.
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

- Turning the facing one step (60°) costs 1 hex for every 2 hexes of front (at least 1),
  plus the ground its ends sweep over: the worst extra going of the hexes it comes to stand
  on (+1 for rough ground or woods, +2 for marsh or rubble).
- A unit cannot pass through other units' hexes, except that a steady unit charging may pass
  through its own side's men (not the enemy's) when it cannot get round them: its move must
  end in contact with the enemy, and each friendly unit with a hex on the straight line from
  where it started to where it ends is **jostled**, its move that exchange halved (as when
  broken men run back through it).
- A unit in contact with an enemy cannot move.
- **A charge:** a steady unit whose move ends in contact may move up to twice its
  allowance. Mounted men who charge get the charge bonus (+20, twice the tempo) in that
  exchange's fight.
- **A front of pikes:** a steady unit in close order armed with pikes, charged by horse from
  its front, takes no charge from them (as stakes and felled trees give none), and its men
  strike mounted men to their front at +20 (`melee.pikes`). Shaken, in open order, or
  struck in the flank or rear, it loses that edge. One minute of 80 regular horse charging
  the front of 120 regular pikemen (400 runs, the Thirty Years' War table, no armour on
  either side): the horse hit 0.65 pikemen, against 1.7 if the pikes gave no edge; the
  pikemen hit 4.1 horse, against 3.1. Spears and bills get no such edge. Design estimates.
- **Pursuit:** contact with a broken unit is a charge like any other, and every man of the
  pursuing unit strikes the fleeing.

**Who fights.** A front hex fights the enemy hex across its front hexsides; whether that
is the enemy's front, flank or rear depends on the side it is struck from. Each front hex
puts its front rank in (10 men), or its first two ranks with reach-2 weapons.

**Who shoots.** A unit with missile weapons that is not in contact shoots at the nearest
enemy in range ahead of it (in the half of the field its front faces). The front two ranks
of each front hex shoot. Shots at a unit in open order count 0.8.

**Line of fire.** A unit cannot shoot through another unit, friend or enemy, standing between
it and its target: it shoots at the nearest enemy it has a clear line to. From high ground it
can shoot over a unit on lower ground. Bows, longbows and crossbows can loose high over
units instead, at 20% off; the log notes it. (Guns: see *Guns*.)

**Sight through cover.** Woods, buildings and tall buildings between the shooter's hex and the
target's block aimed fire, as they block the sight for calling fire, unless they stand lower
than the shooter (from high ground a man sees over woods and houses on the flat, from a
slope over woods; tall buildings stand as high as high ground). Men see one hex into cover
(`line_of_fire.see_into`): the hex next to either end of the line does not block, so a unit
at a wood's edge fires out of it, and a target just inside it can be seen; deeper in, it
cannot. The same goes for guns firing directly and for vehicles' guns. Shell fire, bombs and
a machine gun firing blind down its fixed line need no sight. Rubble gives cover and hides men,
but its heaps are low: it does not block sight. In a town, then, the fighting is close: across
a street or along it, not through a block. At Fallujah, Keating and Hue a few units stand a
hex or a few nearer the edge of their cover than before, so that they fire from where they
are drawn up.

**Dead ground.** Ground on the line between two hexes that stands higher than both of them (a
slope or high ground) hides each from the other. Two men on the flat either side of a rise
cannot see each other, and neither can a man on the flat and one on a slope behind a higher
crest. A man on the top sees down both slopes, because nothing between stands higher than
him. Crest hexes within 1 hex of either end (`line_of_fire.crest_clear`) do not count, so a
unit pulled up just behind a crest (a tank hull-down) sees over it and is seen. Dead ground
blocks whatever sight blocks: aimed fire ("Higher ground between: dead ground" in the log),
direct gun fire and vehicles' guns, calling fire, and what the enemy commander's units see.
Shell fire, bombs and a machine gun firing blind down its fixed line still need no sight. It
applies on the field map; the roller's battle map has no heights. At 73 Easting the Iraqi
tanks dug in behind the rise cannot be seen, nor see, until Eagle Troop comes onto it.

**Range** is the weapon's battle-map range in 2-yard (2 m) hexes, divided by 5 for field hexes:
a longbow's long range of about 270 yards (250 m) is 25 field hexes.

The page keeps the battle in the browser, so it can be closed and reopened. *New battle*
starts again from the starting units.

## The enemy commander

**Enemy commander** (under the battle buttons) hands a side to a scripted commander, either
**attacking** or **holding**; each side has its own choice, and *You move them* keeps it the
GM's. At the start of each of that side's moves it orders the side's
units, one after another, and logs each order ("Billmen (Lancastrians) move 6 hexes toward
Billmen (Yorkists)."). **Undo its orders** puts the units back where they began the move, so
you can move them yourself or press **Give its orders** for a fresh set. Nothing else
changes: you still press the side's *done* button, and you can still adjust its units by
hand before you do. It is a rule of thumb, as a GM would play the other side, not a
general. All its numbers are in units.yaml `commander`.

- **What it knows.** It knows of an enemy unit one of its own units can see now, by the
  same sight as calling fire: the weather's and the light's reach, woods and buildings in
  the way, smoke. It is enough to see the enemy's middle hex or either end of its front.
  It orders its units one after another, and an enemy that a unit sees from where it has
  just moved is known to the units ordered after it in the same move.
  An enemy it saw before but cannot see now it remembers where it was last seen, for 3
  exchanges; then it forgets it. It never targets an enemy it does not know of, and a unit
  with no enemy known holds where it is. On a dark night, then, a side waits until the
  enemy comes within sight, or shows itself by firing.
- **Its target.** Each unit picks among the enemies it knows of. Green men take the
  nearest. Regulars, and veterans twice as much, weigh up as well:
  - each % of the enemy's men down, a point;
  - an enemy that is shaken, 20 points;
  - an enemy that is a danger to it, 20 points: shooters, for men without missiles; men
    without missiles within a charge of it, for shooters;
  - against 10 points off for each hex away.
  A remembered enemy is gone for where it was last seen, and the log says so ("move 4 hexes
  toward where Archers (Yorkists) were last seen (exchange 2)").
- **Not steady.** A shaken unit stays where it is. If an enemy's missile weapon reaches it,
  it goes to ground (not a vehicle unit).
- **Searching.** Attacking, with no objective marked and no enemy its side knows of, a unit
  goes forward to find one: a move toward the last hex on the map straight ahead along its
  facing, as toward an objective ("move 6 hexes forward to find the enemy"). Holding, it stays.
- **Nerves.** A steady unit first rolls d100. At or under its quality's chance it hesitates
  and does nothing this move: green men 30%, regulars 10%, veterans never.
- **Where to go.** It scores every hex it could reach, facing the target, and takes the
  best one it can legally move to:
  - 10 points for each hex nearer the target.
  - For cover from the target's shots there (woods 20%, buildings 30%), a point per % for
    regulars and 2 for veterans. Green men ignore cover.
  - One point off for each hex of movement.
  - If no hex it would move to is in reach (it faces away from the target, and turning alone
    takes its whole move), it turns where it stands toward the target, as far as its move
    allows, and moves on next time. Holding units do the same. If it cannot turn at all (a wide line with no room, or a turn its move cannot pay for), it
    stays facing as it is and still goes to ground under fire where it stands. Before 21 October
    such a unit had no order at all: at X-Ray C Company, a 26-hex line, stood in the open trading
    volleys with a battalion at 6 to 9 hexes.
  - **Room to move.** If a hex would do but the unit cannot stand there facing its target or
    objective (no room for its ranks, or the turn costs more than its move), it tries the
    facings a point either side, then two, then the way it faces now, and moves facing the
    first that it can; it turns to face its goal later, when there is room. This goes for every
    move the commander orders: on a target, on the objective, falling back, searching, plugging
    a gap (not an air controller's spot, which must face what it is to see). Self-play showed
    big units on narrow or rough ground (Kapyong, Cassino) never moving at all.
  - **Routes.** A battlefield can give a unit a route (`via`: waypoints, from the account's
    march round a flank). Its commander moves it on to each waypoint in turn, as it advances on
    an objective, and drops each once the unit's middle hex is within `commander.route.reach`
    (3) hexes of it. It shoots at what it can reach as it goes, as every unit does, but turns
    aside only for an enemy in contact with it or one it knows of across its way within its
    move (a hex either side of the straight line to the waypoint); then it fights as any other
    unit, and takes up its route again when the way is clear. With no waypoints left it is
    ordered as any other. A unit with a route is never held back in reserve. Design choice:
    the battlefield says where the flank march went, so the commander does not guess.
  - Of hexes that score the same and cost the same, it takes the one nearest the straight
    line to the target (or the objective), so a long advance goes straight rather than
    drifting to one side.
- **Shooters.** A unit with missiles stops where the target is in range and shoots rather
  than closing. In range means its weapon (or main gun) reaches, the weather and light let it
  see that far (for its small arms as for a main gun: at 73 Easting the tanks, whose machine
  guns reached the Iraqi trenches from 500 m, stopped there in a sandstorm their thermal
  sights saw only 450 m through, and never fired), and nothing blocks the line from that hex (woods, buildings or a crest, as firing
  itself checks). Before 20 October the line was not checked: Hue's tanks stopped 25 hexes
  out behind blocks of houses, counting the Treasury in range, and never fired. It keeps off the enemy (2 hexes or more) if it can, and never charges,
  except when storming works (below). A unit with a main gun (a vehicle's, or anti-tank guns)
  counts the target in range where the gun reaches it and the weather and light let it see it
  there, not only its own weapon's (self-play showed tanks closing to their machine guns'
  reach). A vehicle with a main gun also likes (`commander.stand_off`, 500 points) a spot where
  it can so hit the target but the target can neither reach it nor see it there: beyond the
  enemy's weapons, or, with thermal sights in a sandstorm, beyond the enemy's sight.
  With a modern weapon (breech-loaders on), regulars and veterans under fire go to ground
  where they stand. Older armies stand up, and so do vehicles (tanks and carriers do not go
  to ground; self-play showed tanks lying still under fire for the rest of a battle).
- **Men without missiles** charge only with the odds their quality wants: their men times
  attack % against the target's. The men of steady friendly units touching it (not guns or
  vehicles) count with its own: a column backed by its supports goes in together.
  - Attacking: green men want even odds, regulars take on an enemy up to a quarter
    stronger, and veterans one two-thirds stronger.
  - Holding: green men want half as many again as the enemy, regulars a fifth more, and
    veterans even odds.
  - Without the odds they close to just short of contact and wait. A friend behind with the
    odds may charge through such a waiting unit (see moving, above).
- **Storming works.** Attacking, a unit armed with a smoothbore musket, a rifle-musket, a
  breech-loader, a modern service or assault rifle or a sub-machine gun (`commander.storm`)
  whose target holds works
  does not stop at range. The target holds works if it is dug in or emplaced where it
  stands, if any of its hexes has cover from works toward the attacker (a bank, trench, wall,
  palisade or the like), or if it stands in buildings, tall buildings or rubble. The unit
  scores hexes as men without missiles do, taking no account of cover on the way, and
  charges with the same odds; it still fires as it goes. Holding units, other weapons
  (flintlock rifles, matchlocks, bows, machine guns, rocket launchers) and targets in woods or
  scrub are not stormed. Modern infantry joined the list after self-play (see
  `docs/selfplay-review.md`): firing from range alone almost never shifted men under cover, and
  attacks stalled. Measured and not built: black-powder units charging any target in the open
  that they have the odds against (Albuera 12 of 12 runs to 2, Bull Run 12 to 5), or only
  batteries (Albuera to 9; Lundy's Lane unchanged, since the guns are never the target chosen).
  A wall or palisade
  blocks hand-to-hand fighting, so stormers stop at its foot unless they carry ladders (see
  *Escalade*), when they go up it; breaching it is still the GM's order.
  - **In bounds** (`commander.bounds`). Storming with a modern weapon (breech-loaders on), a
    unit that heeds cover (regulars and better) and was fired on (hit or not) or pinned in the
    last exchange goes to ground where it is and fires this move, rather than walking on upright; it gets
    up and goes on once a bound draws no fire, or at once if its target is pinned or it can
    charge home this move. Fire and movement: self-play showed 2 Para's A Company walking
    upright into two machine guns at Goose Green and breaking in three minutes. Measured on 24
    runs of every battlefield: 628 of 888 from 620; Hamburger Hill 18 to 23, the morale
    targets unchanged. Goose Green still does not match (British losses 63% to 55%): the bound
    after a lull still goes into machine guns nothing has pinned.
  - **Every advance** (`commander.bounds_all`). In the wars of fire and movement (WWII on, by
    the wound table's war), the same holds for any attacking modern foot unit, not only one
    storming works: fired on in the last exchange, it goes to ground and fires rather than
    walking on to a better hex or the objective, unless its target is pinned or it can charge
    home. And "drew fire" now means fired on, not only men lost: a company lying under fire
    that lost no one had drawn fire. Self-play at Goose Green: A Company, moving as shooters on
    a target not in works, walked upright under two machine guns and lost 30 men in two
    exchanges, and, under the old test, a company that lay under the guns and lost no one got
    up into them. Fire and movement became standard from 1917-18; applied to the Germans at
    Mons in 1914, who came on in close order, it cost Mons 23 to 15, so it is not used before
    WWII. Measured with the fixes below on 24 runs of every battlefield: 700 of 936 from 692.
- **Facing.** A unit whose target is already in its front arc keeps its facing rather than
  turning to face it squarely, so a wide line does not spend its move turning. A unit on the
  ground whose target is out of its front arc turns toward it where it lies, and stays down.
  Before 22 October a unit on the ground never turned: at Keating a guard post faced east all
  battle while it was shot at from 30 m to the west, and never fired back.
  - Veterans prefer a hex off the target's front (30 points more).
- **Holding.** A side that holds does not leave its ground. A unit only charges an enemy
  it can reach with the odds, turns to face its target, or goes to ground; the exceptions
  are set out below: falling back to the objective (or the second objective), a reserve
  unit going to plug a gap, guns pulling back from an enemy that could charge them, and
  riders getting down.
- **Digging in.** A unit that can dig in (a foot unit with a modern weapon; see *Digging in*
  under the field map's rules) and is not dug in where it stands digs in there when it is
  safe: not under fire, and no enemy it knows of within its weapon's range (a known enemy
  further off does not stop it). A unit gone to ground digs too, and stays down. It does so:
  - at the objective, within its radius (attacking or holding);
  - holding with no objective, wherever it stands;
  - in reserve, while it waits (attacking or holding).
  Once digging it holds until the 3 exchanges are done, or until it is stopped (it moves,
  breaks or comes into contact).
- **Its reserve.** At its first move it holds back its rearmost units, those furthest from
  the nearest enemy (not a unit on a route, nor vehicles with a main gun, which go in with the
  attack: self-play held Hue's tanks and Ontos back, then sent them to plug gaps inside the
  blocks, where vehicles cannot go). It takes them up to a share of the side's men, set by the quality most
  of its men have: regulars a quarter, veterans a third, green men none. The GM can decide
  instead: **Hold in reserve** on a unit of the commander's side marks or releases it, and
  once any is marked the commander leaves the choice to the GM.
  - A reserve unit holds where it is, going to ground under fire as the rule above. While it
    waits it digs in there when it is safe to (see *Digging in*, below).
  - It commits one reserve unit a move, the one nearest the enemy, when one of its own units
    has broken or fled since its last move, or when an enemy it knows of comes within 12
    hexes of a reserve unit.
  - Veterans also commit to exploit when an enemy unit breaks.
  - Attacking, it also commits one when the attack has stalled: 5 of its moves in a row
    (`commander.stall`) without putting down 1% of the enemy's starting men or bringing any
    of its units (not reserves) nearer an enemy it knows of. The count starts again then.
    Without this, an attack that stalled with nobody breaking kept its reserve out all
    battle (Cowpens' Legion dragoons, Sidon's heavy horse, Visby's men-at-arms).
  - **Plugging the gap.** Committed because one of its units broke or fled, it sends the
    reserve unit nearest where that unit stood at its side's last move, and that unit goes
    to plug the gap: it treats that hex as its own objective (attacking or holding as its
    side does, within 1 hex of it), going for the enemy only as a unit does on the way to an
    objective. If it breaks in turn, the next reserve goes where it stood.
  - The log says why ("committed from the reserve: one of its units has broken; they go to
    plug the gap at 31,21, where it stood").
- **Narrowing to fit the ground.** Attacking, a formed unit (hand to hand, close order) out of
  contact that cannot move nearer its target closes its front in a quarter at a time, deeper, to
  the widest front that lets it move nearer, and moves (`commander.narrow`). It never goes
  narrower than half the front it started with (`narrow_to`). Self-play showed Agincourt's
  French held off by the narrowing ground between the woods: Agincourt went from 1 of 12 runs
  matching to 8. Without the floor, Towton's Norfolk closed to a column 4 hexes wide and was cut
  down. The log says when a unit closes its front, and to how many hexes.
- **Orders from the accounts** (`data/orders.yaml`, researched in the project's
  hold-or-give-way notes, each battlefield with its source). Two kinds, for named units:
  - **hold**: the sources say the unit held its ground to the end of the fight the set-up
    covers. It fights where it stands: it does not fall back to the objective, and a holding
    side's unit with no target stays put rather than drawing back.
  - **withdraw** `{unit, at, to}`: the unit gave way on orders at a known time. From exchange
    `at` (a minute each) it falls back to `to`, a hex (and then holds it) or a map edge (N, S,
    E or W), and leaves the field there ("withdraw off the field, as ordered"; it counts as
    gone, not broken). Mons (the Fusiliers at 281), Osan (the hillock platoon at 46, the rest
    at 166), X-Ray (A and B Companies to the landing zone at 246), Kapyong (the battalion
    HQ and Shermans at 466, B Company at 586), Snipe (the 47th and 41st RTR at 166) and the
    Babuna pass (the Serbs at 931) give way so.
  A unit the sources say was driven off, or that they do not cover, has no entry, and the fight
  decides. Bull Run has none: its brigades held Henry Hill, which is the objective, so they go
  up onto it as any holding unit does (marked to hold where they stood, they let the Union take
  the empty summit: 12 of 12 runs to 5).
  Measured on 24 runs of every battlefield: 620 of 888 matched, from 603. 73 Easting 7 to 19,
  Lützen 9 to 17, X-Ray 12 to 15; Agincourt 11 to 8 and the Monastery 5 to 2, within their own
  spread. The morale targets did not move (T1 before 1914 5/15/26%, T2 3.1, T5 6/68%; T3 8% to
  5%, the target that varies most).
- **Pursuit.** A steady unit that fights hand to hand goes after a broken enemy: horse one within
  a charge of it (twice its move) when no standing enemy is within a charge of it, foot one within its own move
  when it is nearer than any standing enemy. It moves or charges into contact, and the broken unit
  is struck each exchange it stays in reach (*The rout*). It keeps on until the fugitives are out
  of reach or off the map; veterans (and better) give it up after 2 moves (`commander.pursuit.rally`)
  if a standing enemy is within their reach, and go back to the fight. Shooters on foot, vehicles
  and units on a route do not pursue. Before 17 October 2026 the commander never went after a
  broken unit, so the rout struck only while the fugitives happened to stay in contact. Measured on
  all 37 battlefields there were then (there are now 44), four runs each: 101 of 148 runs matched, against 98, Lützen 0 to 3 of 4 (the
  Swedish horse run down the broken Imperial units). The loser's men lost after breaking did not
  rise (a median 14-20% before 1914, against most in the sources): losers still lose most of their
  men in the line before they break.
- **Shooters give way.** Attacking, after its units' orders, a formed unit (close order, no
  missile weapon, not a vehicle, not in reserve or on a route) that neither moved nor
  hesitated looks at its own open-order shooters within 4 hexes (`commander.give_way`) that
  are nearer its target than it is. If, with them gone, it would move nearer its target,
  those standing on the ground it would cross step aside. Each goes to the best spot it can
  reach off that ground, facing as it was: in range of its own target if it can be, else the
  least movement. Shooters that hesitated this move stay. The formed unit is then ordered again
  and goes on (the log: "Danish crossbowmen step aside 6 hexes to let the formed men behind them
  through"). Skirmishers and archers did this: they fell back through the intervals or to the
  flanks as the formed men came up. Before, at Visby both sides' archers stood and shot while
  the men behind them never came on, and three in four of the men never fought. A formed unit
  held up behind another formed unit (the French main battle behind the vanguard at
  Agincourt) is not covered.
- **Known minefields.** Each hex of a minefield it knows of (marked, found by setting it
  off, or laid by its own sappers) on the straight way to a hex costs that hex 5 points for green men, 40 for regulars
  and 80 for veterans. Green men may still blunder in; veterans go round. Hidden fields it
  has not found it cannot see.
- **An objective.** With **Clicking the map: Mark or clear the enemy commander's objective**
  the GM marks one hex (O on the map) for the commander's side, at any time; click it again
  to clear it. Without one, the commander plays as above.
  - **Attacking**, a unit within 1 hex of the objective holds it: it stays, turning to its
    target, and charges only with the odds a holding side wants. While its target (where
    last seen) is on the objective too, it goes on attacking as before until the objective
    is clear. Before 22 October it held at once, and at Keating an insurgent company inside
    the wire lay 30 m from a guard post for 300 exchanges, firing at men it could not see,
    without ever closing on them (6 runs in 24 ended with the outpost contested). A unit with no enemy to go
    for advances on it, and so does one that would only stand or turn where it is (a
    shooter already in range, say) while its target is not guarding the objective (within
    4 hexes of it). It advances as far as its allowance lets it, to the hex nearest the
    objective (cover from its target and known minefields count as above), facing its
    target, else the objective.
  - **Holding**, a unit more than 3 hexes from the objective falls back toward it, facing
    its target, unless it can charge. One with no enemy to go for and within 3 hexes stays.
  - Its units weigh an enemy within 4 hexes of the objective 30 points more as a target.
  - A unit at the objective digs in there when it is safe to (*Digging in*, above).
- **Fixed lines.** Holding, by day or at dusk (a line cannot be laid in the dark), each of
  its machine guns on foot, steady and with men:
  - **On an enemy.** With no fixed line yet, it is laid on the hex where the nearest enemy
    it knows of stands (or was last seen), if its guns reach it.
  - **Ahead.** With no enemy it knows of within its reach, it is laid ahead: from the middle
    of its front toward the nearest enemy it knows of (out of reach), or along its facing if
    it knows of none, as far as its guns reach and it can see now. The line stops before the
    first hex it cannot reach or see (woods, buildings, a crest, the weather's sight or the
    light's at dusk) or the map's edge; if it cannot see even the first hex, none is laid.
  - **Shifted once.** A line laid ahead is shifted onto the hex of the nearest enemy it
    knows of that comes into its reach, unless that enemy already stands within a hex of the
    line. A line laid on an enemy, or by the GM, is not moved, and a shifted line is not
    shifted again.
  - Once dark, it fires blind down its line as a machine gun the GM laid does (see Night).
    Attacking, it lays none.
- **Its sappers** (units marked sappers; see Minefields).
  - **Attacking**, they lift the known enemy mines in the row ahead of their front when the
    straight way to their target (where last seen), or with no target to the objective,
    crosses known mines. Mines their own side laid are left: they do not strike its men.
    With that row clear but known enemy mines further along that straight way, they first
    **close up**: they turn to face along the way and go along it as far as their move
    allows without a hex of theirs in known enemy mines, stopping once the row ahead is
    mined. So they work a lane through a belt row by row: close up, lift (2 exchanges), step
    into the gap, lift the next. Other units steer for the cleared ground as they steer
    round known mines. If they cannot get on along that way (a unit or a work in it), they
    move as any unit does.
  - **Holding, or at the objective** (within its radius), with no enemy it knows of within
    8 hexes, they lay mines in the row ahead where it is not mined yet and no unit stands:
    mixed if an enemy unit it knows of has vehicles, otherwise anti-personnel.
  - Once at work they hold until the work is done or stopped (`commander.sappers` in
    `data/units.yaml`).
  - After each exchange the log says who holds it: the one side with a standing unit
    within 1 hex of it (a battlefield's objective: within its radius), "contested" if
    both have, or no one (`commander.objective` in `data/units.yaml`).
- **A second objective.** With **Mark or clear its second objective** the GM marks a second
  hex (2 on the map), once there is a first; clearing the first clears it too. It counts
  within the commander's own radius (1 hex), and the log says who holds it as well.
  - **Attacking**, once its side holds the first objective (at the start of its move: its
    men there and no enemy), the units standing on the first then stay there and hold it
    (digging in where they can), and the rest go for the second, as above. If the enemy
    takes the first back (or contests it), every unit goes for the first again, and when it
    holds it again it picks the units on it afresh.
  - **Holding**, its units hold the first as above until the enemy holds it; then they all
    fall back to the second and hold that.
  - The move's first log line says when it goes on to (or falls back to) the second.
- **Riders.** At the start of its move, before the other orders:
  - **Getting down.** Its carriers (armoured carriers, fighting vehicles, lorries, tanks with
    men on the hull) with men aboard set them down beside them (see Riders) once an enemy it
    knows of is within reach of the riders' weapon or the carriers' own, or once the carriers
    stand at the objective. The riders fight on foot from the next exchange.
  - **Getting on.** Attacking, a foot unit (steady, out of contact, not in reserve, not at
    the objective, not digging, laying or lifting mines, not gone to ground) gets aboard the
    first empty carriers of its side beside it with room for all its men (not gun tractors,
    not immobilised) when no enemy it knows of is within reach of its weapon or the
    carriers', from where either stands. The carriers then move as any unit does, the riders
    with them.
  - With machine guns reaching 100 hexes (1,000 m), riders get down about that far out; a
    carrier that knows of no enemy takes them to the objective.
- **Its guns.**
  - Its batteries and anti-tank guns on the map, in action, turn to face the nearest enemy
    it knows of.
  - **Moving its guns.** Attacking, a battery or anti-tank guns with no enemy it knows of
    within their reach (and, with none known, short of the objective) go forward. A
    battery in action limbers (an exchange changing over), moves, and unlimbers once an
    enemy it knows of is in reach. Anti-tank guns hook up to an empty tractor of their side
    beside them, are towed, and are unhooked once an enemy is in reach (counting 4 hexes
    less from the tractor, so the guns land in reach); they fire from the next exchange.
    Moving guns go to the hex in their allowance nearest the enemy that has it in reach but
    is no nearer than 2 hexes (`commander.keep_off`), never touching it; known minefields on
    the way count as for other units.
  - Holding, its guns unlimber, or are unhooked, where they stand, and move only to pull
    back.
  - **Pulling back.** Attacking or holding, guns that a known enemy could reach at a charge
    (in its allowance times `charge_move`, not broken or fled, with men) pull back, unless a
    steady unit of its side (not guns or a vehicle) stands on the straight line between
    them. A battery in action limbers first (an exchange changing over); limbered guns, and
    towed anti-tank guns (which hook up to an empty tractor beside them first), go to the hex
    in their allowance furthest from that enemy, keeping their facing and never touching
    it. Guns that can get no further away stay put.
  - Attacking, an empty tractor of its side goes to fetch the nearest anti-tank guns that
    want a tow and that it can tow (one tractor to a gun unit): to the hex in its allowance
    beside them it reaches cheapest, else as near as it can get, facing where the guns will
    go. The guns hook up at the side's next move.
  - Emplaced guns stay put.
  - Its off-map batteries (not tanks) with no mission are called on the enemy unit it sees
    now that scores best as a target. It fires at the first of that unit's hexes its side
    can see and the battery reaches, and never where its own men are within the burst and
    scatter.
  - **Aircraft.** Its aircraft on call with attacks left are called the same way, unless the
    weather or the dark grounds them. Fighter-bombers come in two exchanges later; a forward
    air controller of its side who sees the aim cuts their scatter as usual.
    - **With a controller.** It prefers an enemy one of its forward air controllers (a unit
      marked Air controller) can see, then the best-scoring as above. Where a controller sees
      the aim, it keeps its men clear of the burst and the cut scatter only (fighter-bombers:
      4 + 1 hexes rather than 4 + 3), so it can call them closer to its own men; the same
      goes for a strafing run's or napalm strip's line. The order says a controller is
      talking them on.
    - **Moving a controller up.** Attacking, when its aircraft can fly and have no mission,
      and none of its controllers sees where an enemy it knows of stands (woods, buildings
      or a crest between), a controller unit that would otherwise stand or turn moves up to
      see one instead ("move up to see ... for the aircraft"). It looks for a spot within
      three moves' worth of going (`commander.spot.moves`) from which, facing that enemy, it
      sees where it was last seen: not its own hex, not touching the enemy and with no known
      minefield on the straight way. It prefers a spot out of the reach of the enemies it knows
      of (where each was last seen), if one costs no more than the cheapest by one move
      (`spot.safe`); else the cheapest; of equals, the one that sees the best target. A spot
      within this move it goes to; one further off it heads for, a move at a time, to the hex
      within its move nearest the spot ("move up ... toward ..., from where they will see ..."),
      choosing again each move from what its side knows then. It never gives up shooting,
      charging, going to ground or digging for it, and stays while it has a fight of its own:
      an enemy touching it, an enemy it sees within its own weapon's reach, or under fire:
      pinned, or it lost men last exchange (each unit is marked `hit` for the moves after an
      exchange in which it lost men). A
      controller gone to ground, digging or in reserve stays too. If no spot within three moves
      sees one, it stays. Holding, it does not
      move its controllers: its aircraft wait for an enemy to come into their sight.
    - On an enemy whose front is as wide as a run, they fly it along that front: a napalm
      strip (3 hexes; fighter-bombers, in the wars that used napalm), else a strafing run
      (5 hexes). They do so only when none of its men are within the aircraft's scatter of
      any hex of the line; otherwise, and on narrower fronts, a plain attack with bombs or
      rockets.
  - **Creeping barrage.** Attacking, when one of its units moves or charges on a known enemy
    it can see within 20 hexes, one free battery (not aircraft) puts a creeping barrage on
    that enemy: the battery that lands soonest, with none of its men within the burst and
    scatter of the aim. It lifts a hex each exchange along that unit's facing, for 3 lines.
    One creeping barrage at a time (`commander.creep` in `data/units.yaml`). Riflemen stop
    and shoot once in range, so this mostly covers men closing to charge.
  - **Smoke.** Attacking, before that, one battery lays smoke on the nearest enemy it knows
    of whose missiles reach one of its units that cannot shoot back at it (men without
    missiles, or out of their range): at the first of the enemy's hexes it can see and is not
    already smoked, by the battery that reaches it and lands soonest (mortars before guns).
    Not in the dark, and not in a gale (the smoke would blow away at once). A holding side
    never smokes.
  - **Displacing.** First of all, each of its located batteries that an enemy counter-battery
    mission is aimed at displaces (not one already moving, or tanks): its own mission ends,
    it is silent for its kind's exchanges, and then it is no longer located. A placed
    battery also moves its place 30 hexes (`indirect.displace_shift`) along the nearest map
    edge, away from the battery firing on it (or, with that one off the line, toward the
    side with more room), and no further than the corner.
  - **Illumination.** In the dark (any light that limits sight), before anything else, one
    free battery with illumination rounds (mortars, field guns, howitzers) fires
    illumination over the enemy it has lost sight of (remembered, but not seen now) nearest
    one of its units, at the hex where it was last seen, unless a flare or round already
    lights it or one is on its way there. The battery that lands soonest fires (the first
    listed of equals); a placed battery only within its range. One a move.
  - **Counter-battery.** Next, attacking or holding, one of its free batteries fires on a
    located enemy battery (one that has fired: ◉). The shooter is the free battery with the
    highest counter % that can reach one (howitzers, then field guns; mortars cannot; a
    placed battery only within its range of a placed target). It fires on the reachable
    one with the most tubes served (the first listed of equals). Its other batteries shell
    units as above.
  - **Undo its orders** calls that fire off again.

What it does not do yet:
- It leaves works alone, lays a fixed line ahead only straight toward the nearest enemy it
  knows of or along its facing (no lines across its front, no interlocking lines), moves its air controllers to see a target only when attacking,
  at most three moves away, and only when they would otherwise stand (not when pinned or after
  losing men the exchange before); it plans no creeping barrage for
  riflemen who stop at range.
- Its reserve holds until committed; then a unit sent to plug a gap goes there, and others
  fight. Reserve units ignore the objective until committed.
- It has at most two objectives, taken (or held) in turn: no third or more, no phase lines
  across the whole front, no feints or scouting. Battlefields mark only one. Victory is still the GM's call; the objective
  line in the log only says who stands on it.
- It plays only on the field map, not the travel map.

### Both sides (self-play)

With the commander on both sides the GM only watches, steps in or ends it. **Next** steps a move
at a time; **Run** (shown only then) plays a move about every 0.7 seconds until the GM presses
**Stop**, takes a side back, or the run stops itself (units.yaml `commander.self_play`):

- a side has no unit left standing (steady or shaken) and none still to come on (a later
  phase's units, or a lift still in the air);
- an attacking side has taken the (first) objective and held it `held` (5) exchanges running,
  with no standing enemy within `secure` (10) hexes of it and none still to come, once every
  phase of the battlefield has begun (the account goes on: the Poles at Cassino take Point 593
  in the first hour and are forced off it hours later) (a holding side standing on its own
  ground does not count, or a defended objective would end every run at once; nor does a hold
  with the enemy still close round it; nor a side that held it from the start, until it has
  changed hands);
- `limit` (60) exchanges have been fought, or, on a battlefield with phases, `after_phases`
  (30) past the last phase's start if that is later, but at most `most` (1,200, about twenty
  hours: every battlefield's phases now all come, Chipyong-ni's last at 1,156; a battle that
  went on for days after its last phase, such as Cassino town, is still cut short). A
  battlefield can also say how long its account says the fight went on (`ends`, in exchanges
  from the first); a run then goes at least that long, still no more than `most`. Where the
  account gives only a vague end, `ends` is the earliest the words allow: "before noon" is noon,
  "the next afternoon" 12:00, "near midnight" 23:30, and "at dawn" the sunrise worked out for the
  place and day. Twenty-one battlefields set it: Lundy's Lane 271 (counter-attacks until near
  midnight), the Monastery 418 (failed by dawn, sunrise about 06:57), Lützen 541 (Wallenstein
  withdraws at 20:00), Keating 361, Mogadishu 783 (out at dawn, sunrise 05:44), Kapyong 871,
  Crécy 241 (four hours into the moonlight, our cut), Beaumont-Hamel 181 (to the Essex's attack, our cut), Snipe 806 (the last round at 19:40), Aljubarrota 61 (the attack broken in less than an hour), Dornach 241 (four to five hours), Jacob's Ford 121 (a morning's storm, our reading),
  the Babuna pass 931 (the retreat ordered at 22:00),
  Heartbreak Ridge 901, and, past `most` and so cut short at 1,200, X-Ray, Pork Chop, Grozny, Hue,
  Bougainville, Dak To and Cassino town. `ends` never shortens a run.
  Until 17 October 2026 it was 240, which stopped a run before the last phase began on fifteen
  battlefields (Bougainville, the Poles at Cassino, Cassino town, the Monastery, Chipyong-ni,
  Cisterna, Dak To, Goose Green, Heartbreak Ridge, Kapyong, Lützen, Mogadishu, Mons, Pork Chop
  and Wanat), unless the battle had ended sooner.

Then the battle ends, as with *End the battle* (the dead counted, the wounded carried off, each
side's medevac as ticked). On a battlefield the side its objective names attacks and the other
holds (marked *as fought* in the list); a battlefield with no objective may say how its armies
fought (`stances`: Agincourt, Cowpens and Sidon hold and attack, Fallujah attack and hold);
otherwise, and on open ground, both attack. These are design choices.

The turn itself (phases beginning and bringing on units, broken units running, losing the way
in the dark, the exchange, the end of the battle) is in the rules, `templates/units.js` (the turn)
and `gravewounds/battle.py`, so the page and Python play a battle the same way. From Python:

```
python -m gravewounds selfplay --field wanat-2008             # one battle, the stances as fought
python -m gravewounds selfplay --field visby-1361 -n 5 --seed 3 --stances attack,attack
```

Each battle prints why it stopped, after how many exchanges, and each side's men: killed, left
on the field, died of wounds, carried to camp, and units still standing. Python is slower than
the page (a second or so a move on a large field).

Three things are worked out once and remembered, because nothing in a battle changes them; they
change no result, only the time a battle takes (every battlefield plays move for move as before,
the page about five times faster):

- what the ground lets a man see from one hex to another (dead ground behind a crest, woods
  and buildings between, light cover thinning his aim), kept for the field's ground until the
  GM paints it (smoke drifts and thins, so it is looked at every shot);
- what ground stands on each hex, kept the same way;
- what each step costs a unit to move (works, ground, mud and snow, the dark), kept while a
  commander orders its side: nothing changes the works, ground or weather until the exchange.

### The narrative and the narrator

Under the map, **Narrative** tells the battle's turning points, an entry an exchange when
something worth telling happened (`turningPoints` in units.js, `turning_points` in battle.py,
checked against each other):

- a phase beginning, and the units it brings on;
- units of a side breaking (no longer steady or shaken) or fleeing the field;
- a reserve committed by the commander (an *Undo* takes it back out);
- the objective (or the second) taken by a side, or no longer held;
- the battle's end: why, and each side's killed, died of wounds, carried to camp and units
  still standing.

**Narrator** (folded under it) is optional. With an API key of the player's own, a language model
retells each entry in a short passage (units.yaml `narrator`: at most `words`, 70). Its voice is
set by the wound table's war: a chronicle for the medieval fields, a dispatch from the Thirty
Years' War to the Indian Wars, a war diary for the world wars, Korea and Vietnam, a situation
report after. **Voice** lets the GM pick another for the battle: any of those four, a soldier's
account (first person, an unnamed man in the ranks, who claims nothing the facts do not state) or
a plain, neutral summary. The choice is kept with the battle (*New battle* goes back to the war's),
and applies to passages written after it; earlier ones stay as written. It is told to use only the facts sent (the battlefield's name, the sides, the war,
the entry's plain text and the last two passages for continuity), to invent no people, numbers,
places or events, and to write original prose imitating no real writer or document. The plain
line stays under each passage, so what the game decided can always be checked.

- **Providers.** Anthropic (Claude, `claude-haiku-5-5` by default, called from the browser with
  Anthropic's browser-access header) or any OpenAI-compatible chat-completions service (an
  address and model the player enters). The model name can be changed. Both Anthropic's and
  OpenAI's APIs are paid with prepaid credit, separate from any chat subscription. Two free
  routes, both through *OpenAI-compatible*:
  - *Google Gemini's free tier* (an AI Studio key, no card): address
    `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`, and a Flash or
    Flash-Lite model named as AI Studio lists it. Its limits are per Google project and modest,
    but one call per turning point fits well inside them. On the free tier Google may use what
    is sent (the turning points' plain text) to improve its products. Tested in October 2026:
    the page's call passes Google's browser (CORS) check from a website and from a file opened
    on the computer. (The OpenAI JavaScript library's extra `x-stainless-*` headers do not pass
    it; the page does not use that library.)
  - *A model on the player's own computer* (Ollama, LM Studio): its address at `localhost`,
    `127.0.0.1` or `[::1]`, for example `http://localhost:11434/v1/chat/completions`, and its
    model name; no key is needed there. If the local server refuses the page, allow the page's
    origin in its settings (Ollama: `OLLAMA_ORIGINS`). Not yet tested against a local server.
- **The key.** Sent only to the provider's address, in its header; never in the battle's save.
  Kept only while the page is open, unless **Remember on this computer** is ticked; **Forget the
  key** clears it. The service charges the key's owner, or counts the calls against a free
  allowance. A service's error message is shown as it gave it (Gemini's, which comes inside a
  list, included).
- **Pace.** During a Run, play does not wait: passages are written in turn and appear as they
  arrive. With no key, or when a call fails, the plain entry stands, with the reason shown.

From Python, `selfplay --story` prints the same turning points in plain words (no model).

Every battlefield was played this way and set against the battle as fought:
`docs/selfplay-review.md` says what went wrong, what was changed and what is left.

Still left out: a commander's plan (an envelopment, a withdrawal when outflanked); a run stops
only after a whole exchange; no narrated summary of the battle.

## From the travel map

On the travel map, **Set up the fight** with **Fight it on: the field map** opens this page
with the forces that are there: the defender and any friends beside it on side A, the
attackers on side B, each with its fit men (the sick stay out). Attackers from different
sides on the travel map fight together on side B, named for all of them ("Lancaster and
Burgundy"), and each unit keeps its own side's name in the lists and the log. The GM splits each force
into units with **Add a unit**, choosing the force to draw the men from. A force's men left
out of every unit stay in reserve and do not fight until their side brings them on (see
*Reserves in the battle* under [Battlefields](#battlefields)).

## After the battle

**End the battle** stops the fighting (at any time; usually when one side has no unit left
standing). Every wounded man was remembered as he was hit: the wound's severity, its
untreated time to death and its infection risk, and whether he went down. Then:

1. **The field.** A side with no unit still standing has lost the field: the men it had
   down there are left behind and die. The wounded still on their feet go with their units.
2. **The death clock.** A wound that kills in minutes kills before help comes, unless he is
   bound in time (1 in 10). One that kills in hours kills unless his camp can treat it: no
   chance with no camp, 40% in a camp, 60% in quarters.
   - **Medevac.** Where a side had it, its wounded carried off reach care sooner, and each
     gets the better of his camp's figures and these (`aftermath.medevac` in
     `data/units.yaml`; design estimates, following the eras' died-of-wounds share of the
     wounded as commonly cited: about 14% in the Civil War, 8% in WWI, 4.5% in WWII, 2.5% in
     Korea and Vietnam):

     | Medevac | Wars (by the wound tables) | Dying within hours saved | Within minutes |
     |---|---|---|---|
     | Ambulance wagons | Civil War, Indian Wars | 50% | 10% |
     | Motor ambulances | WWI, WWII | 65% | 10% |
     | Helicopters | Korea, Vietnam, the later wars | 85% | 20% |

   - Helicopters need a landing zone on the field and a helicopter of the side that was not
     lost (damaged or downed), else the side has motor ambulances.
   - Under the side names, a tick for each side (both on) says it had medevac; the GM
     unticks a side that had none (guerrillas, a besieged garrison). *After the battle* says
     which each side had.
   - Medevac does not save men left behind on a lost field, and it takes nothing from the
     helicopters' lifts during the battle.
3. **To camp.** The rest are carried to their force's camp and heal on the wound track,
   where wound fever can still take them (see [travel.md](travel.md), *The wounded*).

**The result.** *After the battle* opens with a verdict and a table, side by side. The
verdict says who holds the field (a side with no unit left standing has lost it; while both
have, the field is undecided) and, with an objective, who holds it (and the second) at the end, as the
exchange log counts it. The table gives each side's men at the start and still standing,
men down, killed in the fighting, died of wounds before help came, left on the field, the
wounded taken to camp (the walking wounded too), units broken or fled, and batteries and
vehicles lost (those rows only when there are some). The crews of the fire-support batteries
(not aircraft) count with their side as a unit does: their men at the start, those down and
killed by counter-battery fire, and their wounded, who die before help comes or are carried
to camp as other men are. The lines below it are as before.

A man wounded twice is counted once. **Back to the travel map** (for a battle set up from
there) takes the dead off each force, adds its wounded to its sick, and moves each force's
clock on by the battle's length (a minute an exchange). The numbers are in
`data/units.yaml` (`aftermath`) and `data/disease.yaml` (`wounds`).

## Heroes

Named fighters from the wound roller can join a unit (**Heroes**, during set-up). A team
from the team builder can also come straight here with its followers as units and its men
as their heroes (see [team.md](team.md), *Followers*). Each
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

His wounds use the full rules, as in the roller:
- **The blow:** location, mechanism, severity from the margin, his own armour, his own parry.
- **Pain:** each wound's pain, and the pain of any wounds he came with from the roller, takes
  10% a step off his attack and defence, to −30% at most.
- **Impairments:** each wound's impairment counts as in the roller, both the ones he came with
  and the ones he takes here. An arm wound counts by which arm it is, so a useless weapon arm
  is −40% attack and a useless shield arm −10% defence. Dazed is −20%, and a leg −20%
  defence. A wound that collapses him, leaves him unable to stand or knocks him out puts him
  down.
- **Sickness:** a fighter who goes with a force on the travel map brings his sickness, as in
  the roller. Mending is −10%, serious and grave −25%. At grave he only defends (he makes
  no attempts and does not shoot). A man at the deadly step cannot join a unit.
- **Bleeding:** he bleeds each exchange (about a minute, 10 rounds): a seeping wound 1 Blood,
  a heavy one 10, an arterial one 30. His Blood starts from his Endurance (and where the
  roller left it). At three-quarters he is −10% more, at half −20%, at a quarter he is down,
  and at none he is down, unconscious and dying.
- **The stop check:** the roller's own, for a wound with shock (serious or critical). Failed
  by 20 or less: defend only, by 40 or less: stunned; either way he makes no attempts in his
  next exchange, and stunned he cannot parry either. Failed by more: down for the rest of the
  battle. Pain above the cap calls for a check at the end of each exchange.
- A wound that kills within rounds kills him.

**Duels.** When two units with front-rank heroes fight hand to hand, the heroes fight each
other instead of the rankers: each makes 3 telling attempts an exchange at the other, the
hero of the unit that struck first first, with the full rules. The first hero of one side
meets the first of the other; a hero left over strikes the rankers as usual.

**Arms and legs.** With an arm hurt (an arm wound, a lost grip, a useless hand or arm,
on either side) a hero cannot use a two-handed weapon: bows, crossbows, muskets and
rifles, machine guns and rocket launchers, bills, halberds, pikes and poleaxes (`two_handed` in
weapons.yaml). He only defends: no strikes, no shots, no attempts in a duel, though blows
still fall on him and he still parries. A one-handed weapon he goes on using, off-hand if
it is his weapon arm. A hero lamed (a leg wound, cannot stand, collapsed, slowed), from this
battle or one he came with, or down and carried by his comrades, halves his unit's move (at
least 1 hex) while he is with it. On his line in the heroes' list, when his unit is moving,
there are two ways to stop that:

- **Carry him back.** Two of the unit's men carry him back (the unit must be steady or
  shaken and have men to spare).
  - **With an aid post** for his side, they carry him there across the map, 3 points of
    movement an exchange (3 hexes on open ground, about half a man's move), by the cheapest
    way over the ground and works: woods, rough ground and banks cost them as they cost a
    unit, they go round water, walls and enemy units, and they pass through their own
    side's units. They make at least a step an exchange. The party shows as ↩.
    - With no way to the post (a river with no crossing, say), they make for the map edge
      behind the unit instead, the same way, and the log says so; with no way there either,
      for whatever edge they can reach.
    - On the way, shell bursts strike its men as men in the open.
    - A bearer put down is lost to the unit. With no bearers left, a man who cannot walk
      lies where he is (▼).
    - At the post the bearers start back, and rejoin their unit after as many exchanges as
      the carry took.
  - **With no aid post**, he leaves the battle at once and safe, as before. The bearers
    come back after 3 exchanges.

  If the unit has broken or been destroyed by the time the bearers are due, they stay at
  the rear, alive and not counted as lost.
- **Leave him.** He is left behind, lying on his unit's hex (▼). He is out of its fight, no
  longer slows it, and goes on bleeding.
  - A unit of his side that stands on that hex at the end of an exchange picks him up. He
    goes with it (behind), and it can carry him back in turn. The unit that left him can
    only do this once it has moved off and come back.
  - An enemy unit, not broken, that stands there finds him. d100 against the war's
    **quarter** (below): at or under, he is taken prisoner; over, he is killed.

A hero who is wounded but can still walk (up, not lamed) has a third choice:

- **Go back.** He leaves his unit and walks back alone, 3 points of movement an exchange,
  by the cheapest way, as a party goes. He goes to his side's aid post, or with none (or no
  way there) to the map edge behind his unit. Shells can catch him on
  the way as they can a party, and a wound that lames him there leaves him lying.

Out of his unit's fight any of these ways, a leader counts as a leader down.

**Aid posts.** Before the battle the GM can place one aid post (AP) for each side, with
**Clicking the map: Aid post**. Click the post's hex again to clear it.
- **Moving it.** In battle, on its own side's move, the GM can move a side's post with the
  same tool (it cannot be cleared then, or moved once overrun). The men at it go with it,
  and parties on their way head for its new place; for that exchange it gives no first aid
  (shown on the post: "moving").
- **First aid.** A man at the post gets first aid every exchange, at 75% (as a skilled
  healer, binding 2 steps of bleeding). Its tourniquets and cautery work as with his unit.
- **After the battle.** His wounds go back to the roller treated at the aid post, so they
  are off the death clock.
- **Overrun.** An enemy unit, not broken, standing within a hex of the post overruns it.
  Each man there is found by the enemy and taken or killed by quarter. From then on the
  side has no aid post.

All of these numbers are in units.yaml `heroes.aid_post` and are design estimates.

**Left on the field.** When the battle ends, a hero still lying out there is one left behind,
one still on his way back, or one who was down when his unit broke, fled or was destroyed. If his side
holds the field (it still has a unit standing, or neither side has), it finds him. If only
the enemy holds it, d100 against the war's **quarter** decides: at or under, he is taken
prisoner; over, he is killed where he lies.

| War | Quarter |
|---|---|
| The Crusades, Wars of the Roses | 30% |
| Visby 1361, the Indian Wars | 20% |
| The Thirty Years' War | 40% |
| The American Revolution | 70% |
| The Napoleonic Wars, 1812 | 80% |
| The Civil War | 85% |
| The First World War, the later 20th century | 70% |
| The Second World War | 60% |
| Korea, Vietnam, Iraq and Afghanistan, and any other | 50% |

These are design estimates. Medieval armies spared those worth a ransom and few others,
the horse-and-musket wars mostly took prisoners, and the wars since vary with the enemy.
The after-battle list says what became of each hero. A prisoner goes back to the roller out
of the fight, marked taken prisoner; the GM decides what comes next.

A **leader** gives his unit +10 morale while he is up, and −20 once he is down. While he is
up his rank adds too: 3 a step above the lowest rank (`heroes.rank_step`), at most 12
(`rank_cap`). An officer is struck twice as often (`officer_exposure`) by the blows that fall
on his unit's heroes. A unit with
a hero still up shows a star on the map. The heroes' list shows each one's attack and defence
after his wounds, his state and his Blood.

After the battle, **Heroes' wounds to the roller** puts each wound on his record in the
wound roller (with its bleeding, pain and clock), and marks him out of the fight if he went
down, and his Blood where the field left it.

**First aid.** In a quiet exchange (his unit not in contact, not under fire, losing no one)
his worst-bleeding wound gets first aid, whether he is up or down: one from this battle or
one he came with from the roller. The best Leechcraft among his unit's heroes still up (the
team builder's skill; it may be his own) is the chance on d100, as in the roller, and a
success binds two steps of bleeding. The unit's **medics** count too, at their quality's
chance: green 30%, regular 45%, veteran 60% (a hero as good is preferred). With no healer
in the unit, his comrades bind one step at 60%.

On a success, an arm or leg bleeding heavily or worse (2+) is tourniqueted instead and
stops. Where a tourniquet cannot go (head, neck or body), a wound bleeding heavily or worse
is **cauterised** in the wars before 1914 (on the wound tables from the Crusades to the
Indian Wars): it stops, at a step more pain unless a healer did it.

The log says who did it and how. The roller takes the wounds as they were left, marked
"bind (on the field)", "tourniquet (on the field)" or "cauterise (on the field)", the ones
he came with too.

**Medics.** The selected unit's **Medics** choice (before the battle) gives it medics at its
own quality. The team builder's **Send to the field map** adds the followers of a healing
career (barber-surgeons, surgeon's mates, stewards, healers, medics, corpsmen and
stretcher-bearers) to the team's biggest unit as its medics, at their usual quality, instead
of making them a unit of their own. `python3 -m gravewounds units` shows how heroes fare:

| A hero leading billmen in jacks, until one side breaks | Wounded | Down | Killed | Men he puts down |
|---|---|---|---|---|
| Knight in mail | 51.5% | 30.0% | 0.5% | 0.24 |
| Knight in plate | 23.5% | 5.5% | 0.0% | 0.30 |
| Champion, no armour | 72.0% | 56.5% | 2.0% | 0.19 |

A fight of this kind lasts a quarter of an hour or more, long enough for a hero's wounds to bleed him
down: about three wounded heroes in five end the fight down.

A hero matters most through morale and through what happens to him: in a press of hundreds,
one man fells few. The numbers are in `data/units.yaml` (`heroes`).

## Ammunition

A unit with a missile weapon carries a load into action, and runs short as it shoots. The
numbers are in `ammunition` in `data/units.yaml`.

- **Who counts.** Every unit whose weapon shoots: bows, crossbows and slings, muskets,
  rifles, pistols, machine guns, anti-aircraft guns, grenades and rockets. Not vehicles
  (they carry far more than a fight uses; their riders do count), batteries or anti-tank
  guns (they count their own rounds; see *Guns*).
- **The load, in exchanges of fire.** The rounds, arrows or bolts a man carries (a gun's
  belts, for machine guns and anti-aircraft guns), over the weapon's rate a minute, times
  0.3: the share of its full rate a unit really spends in an exchange it shoots, since men
  do not fire every round they could. That share is a design estimate, the one tuned figure;
  the loads are sourced where a regulation or account gives one, else estimates (marked so
  in the data):

| Weapon | Load | Exchanges of fire |
|---|---|---|
| Longbow | 48 arrows (two sheaves) | 20 |
| Crossbow | 18 bolts | 30 |
| Matchlock musket | 12 charges | 40 |
| Smoothbore musket | 60 rounds | 100 |
| Rifle-musket | 60 rounds | 100 |
| Breech-loader | 100 rounds | 42 |
| Service rifle (1914-53) | 120 rounds | 40 |
| Assault rifle | 300 rounds | 67 |
| Machine gun | 2,000 rounds a gun | 22 |
| Hand grenade | 4 | 13 |
| RPG | 3 rockets | 10 |

- **Spending it.** Each exchange a unit shoots (aimed or blind down a fixed line) uses one
  exchange of fire; riders shooting from a vehicle use their own. At a quarter of a full load
  or less it is **low** and shoots at half rate (half its shooters). With none it is **out**:
  it cannot shoot, still fights hand to hand, and checks morale at −10. Heroes with missile
  weapons shoot while their unit can.
- **Resupply.** On its side's move, out of contact and before it moves, **Resupply** sets a
  unit to resupply: it neither moves nor fires that exchange, and at its end it has a full
  load again (logged). It needs a source within 5 hexes:
  - its side's map edge: the edge behind the way most of its standing men face (as a rule
    the edge its new units come on from);
  - a lorry or armoured carrier (APC or IFV) of its side, steady;
  - a **supply dump** of its side. **Clicking the map: Supply dump** places or clears one
    in set-up, and a battlefield file can place its own (`dumps: [{at, side}]`: RIR 119's
    ammunition in its dugouts at Beaumont-Hamel). In the battle, from the Second World War on, the same tool calls an **air
    drop** on the moving side's move: it lands at the end of the exchange as a dump, a d6
    direction and 0 to 2 hexes off the mark (kept on the map).
- **In set-up** **Ammunition** sets a unit full, low or out, and **Resupply** fills it at once.
  No battlefield starts a unit short: none of the accounts used says a unit began its fight
  low on ammunition.
- **The enemy commander.** A unit that is out, or low with no enemy it knows of within its
  weapon's range, resupplies when a source is in reach. Attacking, a unit out with no source
  in reach falls back toward its side's edge (straight across, as it falls back to an
  objective); holding, it stays and fights hand to hand.
- **Not yet:** riders cannot resupply aboard their carrier (they get down first), the travel
  map does not carry a force's ammunition from one fight to the next. From Vietnam on a
  helicopter can also bring a dump in (see *Landing by air*).

## Machine guns and modern infantry

The wars after 1865 fight with magazine rifles and machine guns, and their infantry spread
out. All of this is design estimates (`data/units.yaml`).

- **Extended order**: 3 men a hex, a few yards apart; shots at it count half (×0.5), and it
  moves 8 hexes. Choose it in *Order* when adding a unit.
- **Rifles**: bolt-action magazine rifles fire 10 rounds a minute, self-loading and assault
  rifles 15, pistols and submachine guns 12, rolled as aimed shots at the same rate as a
  musket's (3.3% of rounds fired).
- **Going to ground**: on its own side's move (or in set-up), **Go to ground** lays a unit
  down in the folds of the ground. Shots at it lose 15% on top of the ground's cover, and it
  cannot move until **Get up**. It still shoots, and fights hand to hand as it stands. The map
  marks it ↓.
- **Digging in**: a foot unit with a modern weapon (the same weapons that go to ground),
  not mounted and not in a vehicle, can **Dig in** on its own side's move, out of contact and
  before it moves. For 3 exchanges it neither moves nor fires; if it moves, breaks or comes
  into contact it stops. Then it is dug in where it stands (logged): it counts as gone to
  ground (−15%, hidden, less struck by shellfire, steadier) while it stays in that hex, and
  the map marks it ◠ like an emplaced gun. Unlike guns it can get up and move, leaving its
  holes (coming back to them, it is dug in again). In set-up **Dig in** starts the unit dug
  in at once. Design estimates (`dig_in` in `data/units.yaml`).
- **Emplaced guns**: in set-up only, **Emplace** digs in a gun unit (anti-tank guns,
  anti-aircraft guns, machine-gun teams, batteries) for the battle. While it stands, it
  counts as gone to ground: shots at it lose 15%, it is hidden, shellfire strikes it less
  and it holds better. It cannot move all battle, though it can turn, and it cannot limber
  or go to ground. A unit that breaks leaves its pits and is in the open. The map marks
  it ◠ with a dashed parapet across its front, and its unit line says "emplaced".
- **Hidden men**: men gone to ground, in a bunker or a trench, or in buildings, tall buildings or rubble show little of themselves.
  Of the aimed shots fired at them, only 10% find a man to aim at (5% of a machine gun's: it
  sprays where they are thought to be, and still pins them); the rest go at the smoke and the
  flashes. Cover and range then cut those as usual. The log says so ("hidden: 10% of shots
  find a man"). Men standing in the open are as easy to hit as ever, and dug-in men hold
  better (+10 on morale). Tuned on Osan: left alone, the dug-in line there now lasts about an
  hour (median of ten runs; 50 minutes to three and a half hours) against five times its
  numbers, where before it broke in about five minutes. The real fight lasted about two and a
  half hours, but the North Koreans spent much of it moving round the flanks, which a GM
  plays out on the map.
- **Machine-gun teams**: pick a machine gun as the weapon and the unit becomes a team: a gun
  and its crew of 5 a hex, so 10 men serve 2 guns. A gun goes on firing while one of its crew
  is up. Each gun fires 300 rounds a minute, and a tenth of them are rolled as aimed shots
  (a rifleman's rate is far lower: the gun's cone of fire sweeps the target's depth). It
  shoots at the nearest enemy in front, in range and in sight, as any unit.
- **The beaten zone**: the cone falls on past the target. The first other unit, friend or foe,
  within 20 hexes (220 yards, 200 m) past it on the line of fire takes half as many shots, at
  the longer range. Ground that stops shots stops it: rough ground, woods, marsh, buildings,
  tall buildings and rubble.

What the numbers give (`python3 -m gravewounds units --runs 200`, 1,000 runs, the First World War table),
fire for one minute at 100 unarmoured regular riflemen:

| Shooting | Target | Hit | Put down |
|---|---|---|---|
| 2 machine guns, 440 yd (400 m) | close order | 18.0 | 10.3 |
| 2 machine guns, 440 yd | extended order | 9.0 | 5.2 |
| 2 machine guns, 440 yd | extended, to ground | 0.3 | 0.1 |
| 2 machine guns, 880 yd (800 m) | extended order | 3.1 | 1.2 |
| 100 riflemen, 440 yd | close order | 9.9 | 5.7 |
| 100 riflemen, 440 yd | extended order | 5.2 | 3.0 |
| 100 riflemen, 440 yd | extended, to ground | 0.3 | 0.1 |

Men gone to ground are hidden (above): the machine guns' fire still pins them, but it seldom
finds a man. Under the modern-fire rule (see *The wound*, above) most men hit are put down; the rest are
light wounds whose men passed the stop check. Hit and put down differ also by the men a
hit kills outright, counted in both.

## Indirect fire and suppression

Modern artillery and mortars fire from off the map, on call (`indirect` in
`data/units.yaml`). The **Fire support** panel on the field map appears on any wound table
with shell wounds (the First World War and later):

- **Add a battery**: a side, a kind and how many tubes (guns or mortars). Each tube carries
  its kind's rounds and has its crew: 4 men a mortar, 6 a field gun, 8 a heavy howitzer.
- **Call fire**: on the battery's side's move (or in set-up), press **Call fire**, then click
  the hex to fire on. One of the side's units must see it: within the weather's sight and the light's, with
  no woods or smoke between. Tick **Keep firing each exchange** before calling to repeat the
  mission until **Stop** or the rounds run out. The map marks the hex ⌖ and the last
  exchange's bursts ✷. Before calling, **Fire** picks high explosive, smoke or illumination, and **Creep**
  makes a creeping barrage (below).
- **When it lands**: mortars in this exchange, field guns and heavy howitzers in the next.
- **Where it lands**: each shell scatters, d6 for the direction and 0 to the kind's scatter in
  hexes.
- **What it does**: every man (friend or foe) in a hex within the burst's radius is struck at
  the % for his distance from it, less for men gone to ground (×0.35) and less the ground's
  cover. A struck man rolls a wound as a hit by the table's shell weapon (mortar and
  artillery fragments) at 70%.
- **Tree bursts**: over men in woods, shells burst in the branches and shower them from
  above. The woods give no cover, the struck % is ×1.5, and going to ground cuts it only to
  ×0.7. The jungle at Bougainville is woods.
- **Smoke**: a smoke mission spends the same rounds and wounds no one. Each burst fills its
  hex and the hexes round it with smoke (grey on the map). No one sees or shoots into, out
  of or through smoke, and fire cannot be called on a hex behind it. The shooting in an
  exchange comes before the shells land, so smoke screens the exchanges after: 3 in calm
  air, 2 in a breeze, 1 in a strong wind; a gale blows it away at once. At the end of each
  exchange it drifts downwind (towards the hex side nearest the way the wind blows): a hex
  in a breeze, 2 in a strong wind or a gale; calm air leaves it where it is. Smoke blown off
  the map is gone.
- **Illumination**: mortars, field guns and heavy howitzers can fire illumination instead
  (**Fire: Illumination**). It can be called on any hex, with no one needing to see it,
  spends one round a tube, and wounds no one. It lights the hexes round its aim (out to 15
  hexes for mortars, 30 for field guns, 40 for heavy howitzers) for the 2 exchanges after
  the one it is fired in. A lit hex is seen as by day (see
  [Light](weather.md#light-the-field-map)). Tanks have none.
- **Aircraft**: **Fighter-bombers (bombs, napalm)** and **Helicopter gunships (rockets,
  guns)** are added and called like batteries (a "tube" is an aircraft). Fire can be called
  only where one of the side's units sees it fall, as for guns.
  - Fighter-bombers come in two exchanges after the call, two bombs an aircraft a pass,
    scattering up to 3 hexes and striking everyone within 4 (45% in the hex hit, falling to
    2% at 4 hexes). Each aircraft has two sorties.
  - Gunships come at once: four rocket and gun passes an aircraft an exchange, scattering
    up to a hex, striking within 1 (20%, then 6%), 24 passes an aircraft.
  - Aircraft are never located (no counter-battery fire on them) and lose no crews. They do
    not fly in fog, storm, heavy snow, a blizzard or a sandstorm, and fighter-bombers not on a
    moonlit or dark night: a mission called then waits, and flies when it clears. The support list shows
    **grounded** and why. They drop no smoke and carry no illumination.
  - **Strafing runs and napalm strips**: before calling, **Fire** picks *Strafing run* (fighter-bombers
    and gunships) or *Napalm strip* (fighter-bombers, in the wars from 1944 on), and
    **Towards** the way the run flies. Each attack is a pass along a line through the aimed
    hex, after its scatter: 5 hexes for strafing, 3 for a napalm strip. Every man in a hex
    of the line is struck.
    - **Strafing** strikes at 12%, less the ground's cover and for going to ground, as
      shellfire. Its wounds are the table's machine gun's.
    - **Napalm** strikes at 45%, and neither cover nor going to ground helps. A man struck is
      down with critical burns, and 35% of them are killed outright.
    - A vehicle on the line is knocked out at 3% (strafing) or 15% (napalm), times its
      armour's shell factor.
  - **Marking the target**: an air attack whose aimed hex is in smoke (a mortar's or gun's
    smoke round laid on it after the aircraft were called) scatters half as far, as with a
    forward air controller (not both). The log says the target was marked.
  - **Ground fire**: after each attack run, each aircraft that attacked is hit at a chance
    from the enemy (not in vehicles, not broken):
    - within 30 hexes (328 yards, 300 m) of the aim, 0.5% for each machine gun served, 1% for
      each unit with RPGs or recoilless rifles, and 0.2% for every 100 men with other
      firearms, at most 12%;
    - then, on top, **anti-aircraft guns** within 100 hexes (1,094 yards, 1,000 m), 3% for
      each gun served.

    Gunships, low and slow, count all of it twice, and the whole is at most 35%. Of the
    aircraft hit, 40% are brought down and the rest are damaged and turn for home. Either
    way the aircraft is out of the mission and takes its share of the flight's attacks with
    it; the log says which.
  - **Anti-aircraft guns** (the Second World War on: 20 mm and 40 mm guns, the ZPU mounts,
    37 mm guns, the ZSU-23) are a unit like a machine-gun team (*AA gun* as the weapon, 5
    men a gun). Besides their ground fire they shoot at men as a heavy machine gun, 150
    rounds a minute a gun.
  - **Forward air controllers**: a unit can be given one before the battle (**Air
    controller**, shown while aircraft are on call). When a controller of the aircraft's
    side can see the aim, the attack scatters half as far and the log says it was talked
    on. Without one, aircraft will not attack a hex within 10 hexes (109 yards, 100 m) of
    their own men: the mission waits ("hold off") until it can. On the battlefields the
    Marine companies at Fallujah, B Troop's command post at Keating and the Rangers north of
    the crash at Mogadishu have controllers; elsewhere the GM may give one. The numbers are
    design estimates.
- **Creeping barrage**: before calling, pick **Creep** (1 to 3 hexes a lift), **Each line**
  (1 to 4 exchanges on each line before it lifts), **Lines** (how many lines it fires on, or
  until it leaves the map) and **Towards** (the way most of the side's units face, or a
  direction on the map). That is the fire plan: the mission keeps firing, lifting its aim
  on by the timetable, ahead of an advance that keeps to the same timetable. **Then** gives
  the plan another leg after the last line: the same lift, on the same way or turned left
  or right (from the leg before), for its own number of lines. **Another leg** adds more legs,
  up to eight; **Fewer legs** takes the last off. A leg set to stop, or to run until the
  map's edge, ends the plan there. It ends after its last line, when it leaves the map, or on
  **Stop**.
- **Counter-battery**: a battery that has fired is located (◉ in the list), by its flashes
  and sound. On its own side's move a field gun or howitzer battery can then fire on it
  instead of on a hex (**Counter-battery…**), with no one needing to see it. Each shell
  lands among its guns at 2% (field guns) or 4% (heavy howitzers), knocking out a tube and
  striking 2 of its crew; at three times that it bursts close by and strikes one. Mortars
  cannot reach. Struck crewmen roll wounds as men struck by shellfire, and those put down
  are lost to the battery, their wounds kept on it as on a unit (they count in the
  after-battle reckoning; see The result): it fires only the tubes it has men for (2 a mortar, 3 a field
  gun, 4 a howitzer), and with none left it is silenced. Six heavy howitzers firing on a
  located battery knock out about one tube every four minutes and put down a crewman or
  two: counter-battery wears a battery down over a battle, it does not end it in an
  exchange. The list shows each battery's tubes served and crew left.
- **Displace**: on its side's move a battery can move to a new position: silent for an
  exchange (mortars), 2 (field guns) or 3 (heavy howitzers), still located and open to
  counter-battery fire while it limbers up and goes, and then no longer located. Missions
  on it end. Tanks never need to (they are never located). A placed battery is asked where
  it goes (click the hex), and it stands there once it has moved.
- **Batteries on the map**: in set-up, **Place it** puts a mortar, field gun or howitzer
  battery's guns on a hex of the map (a grey square).
  - From there it reaches only its range: mortars 360 hexes (2.2 miles, 3.6 km), field guns
    1,100 (6.8 miles, 11 km), heavy howitzers 1,450 (9 miles, 14.5 km). A call out of reach
    is refused.
  - Counter-battery fire reaches a placed battery only from within range.
  - An enemy unit within a hex of a placed battery **overruns** it: its tubes are lost.
  - Batteries with no place fire from off the map, as before.
  - **Off the map**: once placed, a battery's **Off the map** choice stands it 5 to 120 hexes
    behind the map's edge nearest where it was placed, straight out from there. It reaches its
    range from there (so a call far across the map may be out of reach), counter-battery fire
    needs to be within range of it, and no one can overrun it. The list says how far behind
    the edge it stands.

| Kind | Shells a minute a tube | Rounds a tube | Lands | Scatter | Struck % at 0, 1, 2 … hexes |
| --- | --- | --- | --- | --- | --- |
| Mortars | 3 | 60 | this exchange | 2 hexes | 15, 5, 1 |
| Field guns | 2 | 80 | next exchange | 4 hexes | 20, 8, 3, 1 |
| Heavy howitzers | 1 | 40 | next exchange | 5 hexes | 30, 12, 5, 2, 1, 0.5 |
| Tanks (direct fire) | 2 | 60 | this exchange | none | 25, 5 |

**Tanks** are in the list as a kind of battery: tanks close behind the line, firing over open
sights at a hex the side can see. Their shells land at once and do not scatter; they are never
located for counter-battery fire, and small arms cannot hurt them. Each tank shell bursting on a
bunker's hex knocks the bunker out at 8% (a heavy howitzer's shell at 2%), and the bunker's men
get its cover (−50%) against shellfire while it stands.

**Trenches.** A trench (a hex work, from the 20th century: **Clicking the map: Trench**, ≡)
is dug chest-deep. The men in its hex get 40% cover and are hidden (as men gone to ground),
it costs +1 movement to enter, and horses cannot go into it. Unlike a bunker, it does not
stop blows hand to hand: men in a trench fight as usual and can be fought.

**Storming bunkers.** A bunker (a hex work, from the 20th century) shelters the men in it:
−50% to shots and to shellfire at them, and no one can strike them hand to hand, nor they
strike out; they shoot out of it even with enemies next to it. To take it, a unit next to
it is ordered to storm (**Storm a bunker** on the selected unit, on any wound table with
grenades: the First World War and later), with one of three means. Once an exchange, for
each enemy-held bunker across its front, it rolls d100:

| Means | Knocks the bunker out on | Men in its hex struck |
| --- | --- | --- |
| Grenades | 10 or less | 40%, as grenade wounds |
| Satchel charges | 25 or less | 60%, as grenade wounds |
| Flamethrowers | 40 or less | 70%, burned |

+20 if the bunker's men are pinned. A man reached by flame is out of the fight with critical
burns (burns are not on the hit-location tables, so no location is rolled), and 40% of them
are killed outright. A knocked-out bunker (drawn faded) is a hex like any other: the men in it
can be fought hand to hand and lose its cover. On a table without grenades a bunker cannot be
stormed at all. All design estimates (`assault` in `data/units.yaml`).

**Suppression.** A unit that a shell burst near, or a machine gun fired on (or caught in its
beaten zone), checks at the end of the exchange: d100 against its Nerve (+10 if gone to
ground). A failure pins it for the next exchange: it cannot move and shoots at half its rate.
The list shows "pinned". Broken units do not check.

One minute of fire on the middle of 100 regular riflemen (`python3 -m gravewounds units --runs 200`,
1,000 runs, the First World War table):

| Fire | Target | Struck | Put down | Pinned |
| --- | --- | --- | --- | --- |
| 2 mortars | close order | 29.9 | 16.7 | 51% |
| 2 mortars | extended order | 3.3 | 1.9 | 53% |
| 4 field guns | close order | 39.0 | 21.9 | 48% |
| 4 field guns | extended order | 6.1 | 3.4 | 47% |
| 4 field guns | extended, to ground | 1.8 | 1.0 | 39% |
| 4 field guns | extended, in woods | 8.7 | 4.9 | 48% |
| 4 field guns | extended, to ground in woods | 6.1 | 3.4 | 37% |
| 4 heavy howitzers | extended order | 4.7 | 2.6 | 50% |

Dense formations under shellfire are slaughtered; spread out and gone to ground, men are hit
far less but are still pinned about half the time. In woods, going to ground does much less
good. All design estimates. The batteries are off the map: counter-battery fire is the only
way to reach them, and moving the only way to get away. The support list, the smoke and which batteries are located belong to the
battle (New battle or a new battlefield clears them).

## Guns

A **battery** is a unit armed with guns (the smoothbore artillery of the wound tables, or the
Civil War's artillery), its guns smoothbore, rifled or howitzers, in
**battery order**: two guns and their crews to a hex, 20 men. Its men are the crews, 10 to a
gun, so a battery of 120 men is 12 guns, and as crews fall fewer guns are served. Picking a
gun as the weapon in *Add a unit* sets the battery order.

**Fire.** Each served gun fires one round an exchange at the nearest enemy unit in front of
it within 1,090 yards (1,000 m, 100 hexes), in sight and with a clear line of fire. At 330
yards (300 m, 30 hexes) or less it fires canister; beyond, round shot (see *Shot* for
orders).

**Targets.** The GM can name a battery's target (*Battery fires at*, under the selected
unit): an enemy battery for counter-battery fire, say, or the column behind the nearest
line. The battery fires at it whenever it is in range, in sight, in front and in the line of
fire, and at the nearest enemy when it is not; the log marks fire at a named target "as
ordered".

**Shot.** Left alone, the range picks the shot (canister close in, round shot from
smoothbores beyond, shell from howitzers and rifles). The GM can order it instead (*Shot*,
under the selected battery): smoothbores fire round shot, shell (spherical case) or canister;
howitzers shell or canister; rifles shell, solid bolts (fired as round shot) or canister.
Canister is fired only within its 330 yards (300 m); ordered beyond it, or an order the guns
cannot carry out, the battery fires what the range calls for.

**Sections.** A battery can split off sections at other targets (*Split off a section at*,
*Guns in the section*, *Section's shot*, **Add the section**), as many as it has guns to
spare: at least one gun stays with the battery.
- Each section fires at its own target, with its own shot, whenever it can, and the rest
  fire at the battery's target.
- A section that cannot fire on its target (out of range, sight or line) fires with the
  rest.
- Each section carries its own share of the rounds left, by its guns (12 guns with 9 rounds
  left: a section of 4 has 3, one of 2 has 1, and the battery's other 6 guns the rest), so a
  section is not left without rounds while the battery's guns still have some.
- The list under the battery shows its sections, each with **Remove**. The log gives each
  section its own line, "a section of 2 guns, as ordered".

**Cut fuses.** Gunners cut their fuses to the range rather than leave them to chance. Every
shell's fuse table has its air band widened (taken from the ground band after it): +10 for
veteran crews, none for regulars, −10 for green crews; and +15 more when the battery fired at
the same target last exchange at much the same range (within 22 yards, 20 m, 2 hexes), its
range found. A veteran howitzer battery that has found the range gets 50% air bursts, against
25% for a regular one firing at a new target. The log shows the setting ("fuses cut: air
bursts +15%").

**Canister at the charge.** A battery that can fire, charged in its front, gives its first
charger one round of canister a gun, at point-blank range, as the charge comes in, before
the melee. The men it puts down do not strike: the charging unit's blows that exchange are
cut in the same share as its men (60 men down out of 200 strike with 70% of their blows). The
log says how many fewer struck. A charge into its flank or rear meets no canister.

**Line of fire.** A gun cannot fire through another unit, friend or enemy, standing between
it and its target. The one exception is round shot fired from high ground over a unit on
lower ground; canister never goes over anyone's head, and a unit on the same hill blocks.
Howitzers fire shell over anything (see *Shell*); rifled guns' shell needs a clear line, as round
shot does.
- **Round shot** strikes the unit on a roll: 60% to 550 yards (500 m), 40% to 820 yards
  (750 m), 25% to 1,090 yards. Then it goes through the ranks: each man in its path is hit at
  40%, and the path is the unit's ranks deep (its formation's ranks times its rows of hexes,
  at most 12). A line four deep loses a man or two a ball; a deep column loses five.
- **Ricochet.** On firm ground round shot bounds on past its target. The first other unit on
  the line of fire within 330 yards (300 m, 30 hexes) past the target, friend or enemy, is
  struck by each round at 30% within 110 yards (100 m) past it, 20% to 220 yards (200 m) and
  10% to 330 yards (times its order's missile factor), and the ball goes through its ranks
  as above. Supports drawn up behind a line suffer, and so can a side's own men beyond the
  enemy. Rough ground, woods, marsh, or any mud or snow on the ground stop the bounce.
- **Guns knocked out.** Each round-shot ball fired at a battery that strikes it (not one
  bounding on into it) has a 10% chance of knocking a gun off its carriage, out for the rest
  of the fight. A battery serves the fewer of its guns left and its crews left (10 men a gun).
- **Canister** throws 8 chances a round, each hitting at 50% to 110 yards (100 m), 30% to 220
  yards (200 m) and 15% to 330 yards (300 m). On firm ground all the way to the target (as for
  ricochet) the balls skip on into it: +5% beyond 110 yards.
- **Shell.** A battery of **howitzers** (*Guns: Howitzers* when adding a battery) fires shell
  beyond canister range, in a high arc over anything between. Each shell falls on the target
  at 45% to 550 yards (500 m), 30% to 820 yards (750 m), 20% to 1,090 yards (cut by the
  weather and open order). Then its **fuse** decides (before the gunners' setting; see *Cut fuses*): 15% early (it bursts short,
  harmlessly), 25% in the air over the men, 45% on the ground as it lands, 15% blind (it never
  bursts). A burst throws 12 chances to hit: at 35% each in the air, where cover counts only
  half, and at 25% on the ground, less the full cover. The log counts the bursts and how many
  were in the air. A burst on a battery can knock out a gun, as a round-shot
  strike can. Within canister range howitzers fire canister like guns. Shell rolls on the
  same artillery wound data as the guns: the Peninsular ordnance records include shell.
- **Rifled guns.** A battery of **rifled guns** (*Guns: Rifled guns*), the Civil War's Parrotts
  and ordnance rifles, reaches 1,750 yards (1,600 m, 160 hexes), against 1,090 for smoothbores.
  Beyond canister range it fires percussion shell on a flat path (it needs a clear line of
  fire, like round shot, and does not bound on): it falls on the target at 60% to 550 yards
  (500 m), 45% to 1,090 yards (1,000 m) and 30% to 1,750 yards (cut as round shot is), and its
  fuse (before the gunners' setting) does: 5% early, 5% in the air, 75% on the ground as it strikes, 15% blind. It bursts
  as shell does. Its canister throws 5 balls a round, not 8.
- Cover, the weather (fog and rain hide targets; the wind costs as for firearms) and open
  order cut both, as they cut volleys. Every man hit takes a wound roll at 80%, with no parry,
  on the gun's wound data (lower on the body and deadlier than musketry).

What that gives, from `python3 -m gravewounds units`: 6 guns firing for a minute at 1,600 men
in close order on firm ground strike about 17 men with canister at 220 yards (6 put down), 6
with round shot at 440 yards against a line (2 down), 17 against a column (6 down), and 7
against a column at 870 yards. Six howitzers strike about 6 with shell at 440 yards, line or
column alike (2 down), and 3 at 870 yards. Six rifled guns strike about 9 men in a column with
shell at 440 yards (3 down), 7 at 870 yards, and still 5 at 1,530 yards (1,400 m), beyond a
smoothbore's reach; against a line at 870 yards they do about three times what round shot does,
but against a deep column about the same, and their canister at 220 yards strikes about 10 to the
smoothbore's 17. A battalion of 600 muskets at 110 yards hits about 6.

**Ammunition.** Each gun goes into action with 50 rounds (its limber chest and its share
of the caissons, a figure for play), spent one a gun each exchange it fires. A battery that
has run out falls silent; one nearly out fires the rounds it has. *Resupply* brings the
caissons up: like limbering it takes the whole exchange, ordered in its side's move instead
of moving, out of contact with the enemy, and it neither moves nor fires; at the end of the
exchange it has a full load again. In set-up the button fills it at once. The unit list shows
the rounds left, and the selected battery its guns served, knocked out and rounds.

**Limbering.** A battery is limbered or unlimbered (the *Limber* button). Limbered, it moves
like its formation (horse artillery, marked mounted, as horse) but cannot fire. Unlimbered,
it fires, but its crews can only manhandle it 2 hexes, or turn it. Changing over takes the
whole exchange: order it in its side's move, instead of moving, and it neither moves nor
fires until the exchange is over. In set-up the button changes it at once.

**Hand to hand** the crews fight with swords. A battery whose crews **break** loses its
guns: it never fires again, even if it rallies, and its men run on foot.

Guns roll on their tables' own artillery wounds where the tables have them (the Peninsula,
1812, the Civil War and later). The Thirty Years' War tables borrow the Peninsular ones, the
nearest in time with the same kind of round shot and case shot. We looked for artillery
wounds from 1618-48 to replace them and found none usable: the one battlefield grave with a
published injury count, Lützen (Nicklisch and others, 2017), records lead balls, blunt and
sharp injuries, but no gun wounds. A table can borrow a weapon
from another with `borrowed` in its file: the Indian Wars' arrow report borrows the Civil
War table's gunshots (rifle-musket, breech-loader, revolver and artillery), as it has none of
its own, so soldiers and warriors with guns can fight on it.

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
| Scrub and orchard | 2 | brush, gorse, orchards, hedgerows, tall grass: −10% to shots at men in it; it **thins** sight rather than blocking it (see *Seeing*) |
| Marsh | 3 | no horses |
| Slope | 2 | the side of a hill, half as high as high ground: −5% to blows struck up at men on it from lower ground; shooting down from it +5% with range bands 10% longer, shooting up at it −5% (not guns) |
| High ground | 1 | −10% to blows struck up at men on it from lower ground; shooting down from it +10% with range bands 20% longer, shooting up at it −10% (not guns). From a slope to high ground counts half |
| Buildings | 2 | −30% to shots at men in it; men in it are hidden; no horses; stops round shot |
| Tall buildings | 3 | blocks of several storeys (a modern town): −40% to shots at men in it; men in it are hidden; high ground (as above) for shooting and for blows struck up at them; from the upper floors they see over lower roofs and woods and shoot over units on lower ground; no horses; stops round shot. The streets between are open ground. |
| Rubble | 3 | a town bombed or shelled to ruins (Cassino): −40% to shots at men in it; men in it are hidden; no horses; stops round shot |
| Water | can't enter | a canal or river: shots cross it, men cross only at a bridge (paint the bridge open) |

**Works** are the battle map's (see [works.md](works.md)), with the same numbers, along
the sides of the 11-yard (10 m) hexes or in a hex. For a ditch, bank or wall, click just inside the
side, on the high side; for a gate, on the inside. Click again to take it away.
- **Crossing:** each step of a unit's move costs what the worst of all its hexes pays for
  the same step (its front, flanks and rear). That is the ground it enters and each work it
  crosses or enters (a ditch +2, a bank +1, stakes +1, felled trees +2, barbed wire +3). A
  line half in a wood moves at the wood's pace, and so does a column whose tail is still in
  it. A palisade, wall, barred gate or water under any of its front stops it, and a
  unit cannot stand across one. Wagons fill their hex. Horses cannot go into stakes, felled
  trees, wagons or marsh.
- **Close combat:** across a palisade, wall or barred gate, only reach-2 weapons strike, and
  only the front rank. Striking up a bank, ditch or wall costs its height (−10%, a wall
  −20%), as does striking up onto high ground. Horses charging into stakes or felled trees
  get no charge bonus.
- **Seeing:** higher ground between two men than either stands on hides them from each other
  (*Dead ground*). Woods and buildings block the sight of men calling fire and of aimed shots
  (*Sight through cover*), unless they stand higher than them: from high ground or a tall
  building a man sees over woods and lower roofs, and from a slope over woods and houses on
  the flat. A man sees one hex into cover, and out of it from its edge. **Scrub and
  orchards** thin sight instead: each hex of them on the line between the shooter and his
  target (not the hexes they stand in, and not below him) costs aimed fire −10%, and more
  than 3 block sight as woods do (aimed fire, guns laying, calling fire). The field map's own
  battlefields have it only where the accounts name it: the gorse at Goose Green, the
  elephant grass at Khe Sanh and X-Ray, the brush in Wanat's draw, the scrub on Keating's
  lower slopes and Cassino's; and Aljubarrota, the Babuna pass, Beaumont-Hamel, Crécy, Dornach
  and Jacob's Ford draw it too. Each field's notes say so.
- **Shooting:** the target takes the average cover of its row nearest the shooters (rounded
  down), each hex the best of the works and ground there: a bank on its side −20%, a palisade
  or barred gate −40%, a wall −50%, a pavise or felled trees in its hex −20%, wagons in front
  −40%, woods −20%. Half a line behind a wall gets −25%.
- **Breaching:** a unit's **Breach the works** order puts each front hex's front rank to
  hacking at the palisade, gate, stakes, felled trees or wagons in front of it (half of them
  at a time, every round of the exchange) until the work is down. While they work they
  neither strike nor shoot; the ranks behind fight as usual. The work's breach figure is for a battle-map side
  (about 1.2 yards, 1.15 m); a field-map side takes five times as much, so ten men open a stretch of palisade in about a
  minute. A bank or ditch under a breached palisade stays.
- **Escalade:** a unit on foot marked **Ladders** (set-up only, on a field with a wall,
  palisade or gate; or `ladders: true` in a battlefield file) fights across a palisade, wall
  or barred gate and climbs over it. Across it only a quarter of the front rank of each front
  hex fights, at least one man (`escalade.share`), at −20% (`escalade.penalty`) besides the
  climb up a wall's height; the defenders' front rank strikes back at the men on the ladders.
  Stepping over the work costs 4 hexes of movement (`escalade.cross`), into hexes clear of
  the enemy. Mounted units and guns cannot use ladders. Without ladders, a unit still stops at
  the foot, and only reach-2 weapons strike over. The GM marks the units that carried them.
  The ladder parties on the two Great Redan battlefields are marked, as in the accounts, but
  there the ladders change nothing: the Redan is a ditch and an earth bank, which men cross
  and fight over without them (no figures were found for how much the ladders helped).

**The weather** (set under *Weather*, or brought from the travel map) works as on the
battle map: no shooting beyond what can be seen (fog 5 hexes, heavy rain 15), wet strings
−10% or −20% for bows and crossbows, a strong wind −10% (a gale −20%) on missiles, firearms
misfiring in the wet (a share of the shots lost), and deep mud or snow (level 2 or more)
+1 movement a hex.

**A camp from the travel map.** A fight sent from a force's camp lays the camp's works out
at the field map's scale (sized for the defender's men on 11-yard, 10 m hexes), as far as they were
built when the fight starts, with the gate on the east, facing the attackers' edge. The
defenders' units start inside it, the attackers at the east edge.

## Vehicles

Tanks, infantry fighting vehicles and armoured carriers fight on the field map as units, one
vehicle to a hex (second cut; the numbers are in `vehicles` in `data/units.yaml`). On a wound
table of the machine-gun age or later, **Add a unit** offers **Tanks**, **Infantry fighting
vehicles** or **Armoured carriers**, and **Men** is then how many vehicles; their men are the
crews (4 a tank, 3 an infantry fighting vehicle or carrier).

- **Moving.** Tanks move 12 hexes, infantry fighting vehicles and carriers 14. Each hex costs
  open or high ground 1, rough ground or a slope 2, woods 3. They cannot enter scrub or
  orchard, marsh, buildings, tall buildings, rubble or water, so in a town they keep to the streets. Works
  and deep going cost them what they cost men.
- **Their machine guns** fire as a machine-gun team's, about a gun a vehicle.
- **Main guns** fire each exchange at the nearest enemy in range, in sight (as guns are: the
  weather and the light) and in front, enemy vehicles first, with a clear line of fire. A
  vehicle whose gun is out does not fire it.
- **Fire control.** A tank's gun hits and reaches by its fire control (`vehicles.fire_control`):
  its war's (by the wound table's battle) unless the battlefield gives its own (`fc`). Hits at a
  standing target, first round, by range:

  | Fire control | Wars | 500 m | 1,000 m | 1,500 m | 2,000 m | 3,000 m |
  |---|---|---|---|---|---|---|
  | Optical sight | Second World War, Korea | 50% | 25% | 5% | — | — |
  | Stadia reticle | Vietnam | 98% | 35% | 4% | 4% | — |
  | Laser rangefinder | Late 20th century | 98% | 94% | 75% | 55% | 35% |
  | Thermal fire control | Iraq & Afghanistan (and Eagle Troop's M1A1s) | 98% | 94% | 75% | 55% | 35% |

  (The optical sight's nearer bands are the old tank figures, 75% to 200 m.) Sources: Isby,
  *Weapons and Tactics of the Soviet Army* and *Armies of NATO's Central Front* (an M48's 90 mm
  by stadia, a 125 mm with a laser rangefinder; a Second World War 76 mm tank needing about 13
  rounds for an even chance of a hit at 1,500 m); the GAO's Desert Storm assessment (NSIAD-92-94)
  for the M1A1, which hit at 3,000 m and more and did better than the projections: no published
  figure, so the laser figures stand as its floor.

  | Kind | Range | Rounds a vehicle | Hits a vehicle (to 20 / mid / full range) | At men |
  |---|---|---|---|---|
  | Tank | by its fire control (below) | 1 | by its fire control | bursts as a tank's round on call (25% in the hex, 5% next to it) |
  | Infantry fighting vehicle (autocannon) | 80 hexes (875 yards, 800 m) | 2 | 70% / 45% (40 hexes) / 20% | bursts as an autocannon round (20% in the hex) |
  | Ontos (106 mm recoilless rifles) | 100 hexes (1,100 yards, 1,000 m) | 1 | 75% / 50% (50 hexes) / 25% | bursts as a tank's round on call |

  The Ontos (M50: six 106 mm recoilless rifles on a light tracked carrier, crew of 3, light
  armour) is on the field map for Hue, where the Marines used it to blow holes in walls before
  the infantry went in. Its gun as a tank's without fire control, one round a vehicle an
  exchange (the rifles were fired singly and reloaded from outside): design estimates.

- **Armour.** Small arms cannot hurt an armoured vehicle, and men armed only with them do
  not shoot at one. No one strikes a vehicle hand to hand, or is struck by it.
  - **Soft-skinned vehicles** (gun tractors and lorries) are the exception: rifles and
    machine guns shoot at them as at men, half an aimed shot a man an exchange (3 a machine
    gunner), and each hit knocks one out at 5%, with no lesser damage. Shells count 6 times
    (light armour 3, heavy 1). Design estimates (`vehicles.armour.soft`, `vehicles.small_arms`).
  - **Tank riders.** Up to 6 men can ride on each tank's hull ("desant"), mounting and
    getting down as riders do. Out in the open there, they draw small arms: rifles and
    machine guns shoot at a tank unit with men on its hull (as at soft-skinned vehicles),
    and each hit strikes one of the riders, wounded by that weapon; the tanks themselves
    are unhurt (the log says "On the hull"). A knocked-out tank throws its riders off as a
    carrier does. Shells and bombs bursting near the tanks strike the men on the hulls as
    men in the open (the kind's struck % by distance, no cover), spread over the tanks'
    hexes, whether or not a tank is knocked out ("burst among the men riding on").
  - **Riders shooting.** Men riding an infantry fighting vehicle shoot through its firing
    ports, a quarter of them; men on a tank's hull, half of them. They fire their own weapon
    (rockets at vehicles too) from the vehicles' hexes at its nearest target in range and in
    front, as a unit of their own would; the log names them ("Desant, riding on T-34s, shoot
    at…"). Men inside armoured carriers and lorries do not shoot. Design estimates
    (`vehicles.rider_fire`).
  - **Lorries** (2 crew, 14 hexes a move) carry 20 men each, as carriers carry riders. A
    small-arms hit on a lorry that does not knock it out goes through the sides: it strikes
    one of the men aboard, wounded by that weapon (the log says "Through the sides").

  | A hit from | Tank (heavy armour) | Infantry fighting vehicle or carrier (light) | Gun tractor or truck (soft) |
  |---|---|---|---|
  | A rocket (RPG, bazooka, recoilless rifle) | 15% | 50% | 80% |
  | A guided missile | 60% | 90% | 95% |
  | A main gun | 35% | 75% | 90% |
  | A rifle or machine-gun bullet | — | — | 5% |

  Those are the chances that a hit knocks the vehicle out. A rocket hits as a shot at a man
  does, by the shooter's attack less the range band; a **guided missile** hits at a fixed 85%
  (less cover and the weather) at any range out to its 4 km, as at Debecka in 2003, where 19
  Javelins fired at 2,200 to 4,200 m scored 17 hits (`anti_armour.atgm.hit`). A hit into its **flank** counts
  twice that, and into its **rear** three times, to 100% at most. Which it is depends on
  where the shooter stands, by the vehicle unit's facing (the front is the two directions
  either side of its arrow).
- **Anti-armour weapons:** the **RPG**, the **bazooka** (and Panzerschreck, for the Second
  World War and Korea), the **recoilless rifle** (Korea and Vietnam) and the **guided
  missile** (the Falklands, the Gulf, Chechnya, Iraq and Afghanistan). A rocket, bazooka or
  recoilless team fires a round for every four men each exchange, and a missile team one for
  every ten. Every round is aimed, and range, cover and the weather count as for shots at men.
  Fired at men, a rocket or recoilless round is aimed at the target's hex (the window, not a
  man seen: the hidden rule does not cut it), and one that hits bursts there: each man in the
  hex is struck at 25% in the open (as a tank's round), 50% in buildings (below).
- **HE inside a building** (`indirect.room`). A main gun's round (a tank's, an Ontos's, an
  anti-tank gun's, or tanks called as fire support) or a rocket bursting in a buildings or tall
  buildings hex strikes each man there at 50%, with no cut for the building's cover or for
  lying down: it bursts in the room. British trials of 1944 (AORG Report 167, *Street
  Fighting*): a 2-inch mortar bomb through a window put out about half the room's occupants
  and a PIAT bomb about three-quarters; the lower is used. Small arms into rooms did little
  (about one occupant in five for every 100 Bren rounds that got in), which the hidden rule
  already gives, and the same research (the project's town-fire notes) found nothing to raise
  it. Measured on 24 runs of every battlefield: 652 of 888, as before, the morale targets
  unchanged; Keating 20 to 23 and Mogadishu 19 to 21, but Wanat 23 to 19 and Hue 1 to 0. Only
  the side whose rockets are on the map gains: Hue's North Vietnamese RPG teams are, the
  Marines' 3.5-inch rockets, LAWs and 106s are not (no sourced counts).
- **Damage.** A hit that does not knock a vehicle out strikes the turret (35%) or the hull.
  - On the turret, it puts the main gun out of action at 40% and immobilises the vehicle at 5%.
  - On the hull, it immobilises it at 35% and puts the gun out at 5%.

  Over all hits that comes to about the old 25% immobilised and 15% gun out. The log counts
  the turret hits. A unit with an immobilised vehicle cannot move (it can still turn) until
  it **abandons** them. Their crews then leave the fight unhurt. The enemy commander, attacking,
  abandons them when the unit has vehicles that can still move, and goes on with those
  (`commander.leave_disabled`): at 73 Easting a platoon with one M1 immobilised stood where it
  was for the rest of the battle.
- **Shells and bombs** bursting in a vehicle's own hex knock it out at the firing kind's knock
  %: a heavy howitzer 2%, fighter-bombers 15%. Light armour is three times as likely to go.
- **Knocked out.** A knocked-out vehicle's crew are out of the fight. Each is struck at 50% and
  rolls a wound as one hit by shellfire; the rest have bailed out. Vehicle units check morale
  like any other, but count whole vehicles lost, not crewmen hit in vehicles still fighting.
- **Composite armour** (`armour: composite` on a battlefield's unit: the M1A1s at 73 Easting
  and Fallujah): as heavy, but a main gun's round from its front does not knock one out. The
  GAO found no T-72 round reported through an M1A1's front, even from 2,000 m, and no Abrams
  destroyed by enemy fire in the war. From the flank or rear it is heavy armour.
- **Riders.** Infantry fighting vehicles carry 7 men each and carriers 10. A foot unit of the
  same side within a hex of them can **Mount on** them (all its men must fit, and neither may
  be in contact).
  - The riders move with the vehicles. They do not fight, shoot or check morale, and the map
    shows them as "+40" after the vehicles' men.
  - **Dismount the riders** sets them down beside the vehicles (behind if they fit), facing
    the same way. They can move next exchange.
  - When a carrier is knocked out, its share of the riders are each struck at 30% and
    wounded as by shellfire. When the last carrier goes, the riders get out where it stood.
  - Men still aboard when the battle ends count with their force.

**Anti-tank guns** (the Second World War and Korea). On those wound tables a unit can take
the **Anti-tank gun** as its weapon, and its order becomes *Anti-tank guns*: a towed gun and
its crew of 5 to a hex, manhandled 2 hexes an exchange. They stand for the British
6-pounder, the US 57 mm, the German Pak 38 and 40, the Soviet and North Korean 45 mm and
the Japanese 47 mm (`anti_tank_guns` in `data/units.yaml`).
- **Fire.** Each gun its crews still serve fires one round an exchange, as a tank's main
  gun does, out to 100 hexes (1,094 yards, 1,000 m). It fires at the nearest enemy in sight
  and in front, vehicles first.
  - At a vehicle it hits at 70%, 45% or 20% by range, and the hit knocks the vehicle out at
    its armour's main-gun %.
  - At men its high explosive bursts as a tank's round does.
- **Crews.** The crews are men. Rifles, machine guns and shells strike them, and hand to
  hand they fight with bayonets.
- **Gun shields.** Anti-tank and anti-aircraft guns have shields: small arms (rifles, machine
  guns, pistols) fired at them from their front lose 30%. Shields do nothing against shells,
  bombs or fire from the flank or rear (`gun_shields` in `data/units.yaml`). Some machine
  guns had shields (a Maxim on a wheeled mount, say) and most did not: in set-up,
  **Shielded** marks a machine-gun unit's guns as shielded, with the same cover; the unit
  shows "shielded" and its Guns line says so. Batteries on the map are smoothbore and Civil
  War guns, which had no shields.
- **Towing.** A vehicle unit can be **Gun tractors and trucks** (2 crew a vehicle, 12 hexes a
  move, soft-skinned: see Armour), each towing one gun. With
  the guns beside their side's tractors, out of contact, **Hook up to** puts them on tow: they
  move with the tractors as riders do, and neither fire nor fight. **Unhook the guns** sets
  them down beside the tractors; in the battle they fire from the next exchange. Tractors
  knocked out spill their guns' crews as carriers spill riders. Emplaced guns cannot hook up,
  and anti-tank guns ride only behind tractors, not in carriers. The enemy commander hooks up,
  tows and unhooks its own (see The enemy commander: Its guns).
- **Rounds.** Each gun brings 40 rounds. A gun out of rounds does not fire its main gun.
  **Resupply** brings a full load, as for a battery: at once in set-up, or over an exchange
  out of contact in which the guns neither move nor fire.
- **Ordered by the commander.** The enemy commander moves them forward on tow and unhooks
  them in reach, as it limbers and moves its batteries (see The enemy commander: Its guns).

**Minefields** (wound tables with mine wounds: 1939 on). In set-up, **Clicking the map:
Minefields** paints a hex as anti-personnel, anti-tank or mixed, **marked** or **hidden**.
Click it again with the same choice to clear it.
- **Showing.** A marked field shows as a hatched hex (a.p., a.t., mix). A hidden one shows
  faintly while setting up, then not at all until something goes into it.
- **Setting them off.** A unit that moved into minefield hexes since the last exchange sets
  them off when the exchange is resolved, before the shooting. The ground it crossed is its
  footprint along the way it went from where its move began: the cheapest way over the
  ground and works, within its move (twice that for a charge), that crosses the fewest
  minefield hexes its side knows of (marked, found, not its own side's), and of equal ways
  the one nearest the straight line. So a unit, moved by hand or by the commander, that went
  round a known minefield does not set it off; hidden ones on its way still catch it. Other
  units are left out of the way (they have moved since). A unit moved further than its
  move allows (placed by the GM) is taken on a straight line.

| Minefield | Each man going into a hex struck | Each vehicle going into a hex struck |
|---|---|---|
| Anti-personnel | 10% | — |
| Anti-tank | — | 30% |
| Mixed | 8% | 25% |

- **Men.** For each hex, a hex's worth of the unit's men is at risk. A man struck rolls a
  wound as one hit by a mine at 70%; mine wounds fall on the feet, legs and groin.
- **Vehicles.** A vehicle struck is knocked out at 25% (heavy armour) or 60% (light), and
  otherwise has a track blown off: it is immobilised.
- **Sappers.** In set-up, **Sappers** marks a foot unit (not mounted, guns or a battery) as
  sappers. In play, on its own side's move, before it moves and out of contact, **Sapper
  work** starts it laying anti-personnel, anti-tank or mixed mines, or lifting mines. While
  it works it neither moves nor fires; moving, turning, breaking or coming into contact
  stops it (so does **Stop work**).
  - **Laying** takes 3 exchanges. Then the row of hexes just ahead of its front (as wide as
    its front row, on the map) is a hidden minefield of that kind. Hexes where a unit stands
    are left clear.
  - **Lifting** takes 2 exchanges. Then the minefield hexes in that row its side knows of
    (marked, found, or laid by its own sappers) are lifted: a lane. Hidden enemy mines stay.
  - **Its own mines.** A side knows where its sappers laid mines: its commander steers round
    them as round any known field, and they do not strike its own men. They show faintly on
    the map for the GM; the enemy commander learns of them only once it sets them off.
  - The log says when a field is laid or a lane lifted. The enemy commander sets its own
    sappers to work (see The enemy commander: Its sappers).

All design estimates (`mines` and `mines.sappers` in `data/units.yaml`). No battlefield has minefields laid yet;
they are for the GM to place, and for the battlefields only where the accounts name them.

## Landing by air

For helicopter landings (Vietnam and later). The numbers are in `heliborne` in
`data/units.yaml`.

- **Landing zones.** A battlefield can mark landing zones, shown as a dashed ring with an H.
  Before the battle the GM can mark or clear one with **Clicking the map: Mark or clear a
  landing zone**.
- **Helicopters.** Each side has so many helicopters: by default X-Ray's, 16 Hueys of 5 men
  each, back for the next load 30 exchanges after they land (about the half-hour round trip
  to the pick-up zone). With a landing zone marked, the list under the units sets them for
  each side in set-up, and in the battle shows how many are free, away (and when the next is
  back), damaged and downed. At most 8 land at one zone in an exchange (X-Ray's zone took
  about eight at a time).
- **Coming in by air.** With a landing zone marked, **Add a unit** offers **By air at** and
  a zone. The unit waits in the air (listed under the units as a lift), and at the end of
  each exchange the side's free helicopters fly the lifts in the order they were called,
  each with as many helicopters as it needs. A lift lands two ranks deep. The unit's first
  men come down on the zone, or the nearest spot within 4 hexes where they fit; later loads
  join them, filling the unit out. It can move in the next exchange. A battlefield's units
  can start in the air too (`lands`).
- **Helicopter resupply** (Vietnam on). In the battle, **Clicking the map: By helicopter**
  and a click on a landing zone, on that side's move, sends one helicopter with supplies: it
  sets a supply dump down on the zone when it flies (see *Ammunition*).
- **Flying out.** On its side's move, **Fly out** lifts a unit (on foot, out of contact)
  away from a landing zone within 4 hexes of it. It does not move while it boards; each
  exchange the free helicopters take as many of its men as they carry, until all are gone.
  It cannot board in contact or once it has left the zone's reach (the log says so; **Cancel
  the lift** stops it). Its men flown out are safe: *After the battle* counts them on their
  own row, not as standing on the field nor as lost.
- **Blocked.** No one lands while an enemy unit stands within 2 hexes of the zone, or where
  there is no room: the lift is waved off and tries again next exchange.
- **Turned back.** Once the men of a unit already down have broken or fled, the rest of its
  lift turns back and does not land (before, they landed into the rout).
- **A hot landing zone.** If any enemy unit (not broken) could shoot at the zone's hex, with
  its weapon in range and in sight (in the weather and the light), the zone is hot. Each man
  landing is struck at 10% and rolls a wound as one struck by shellfire, and those put down
  are down at once. Each helicopter that lands there (bringing men or supplies, or lifting
  men out) is hit at 10%: a fifth of those are downed, a wreck on the nearest hex to the zone
  with no work on it (its crew out of the fight), the rest go home damaged. Either way it is
  lost for the battle. Design estimates.
- **Downed helicopter.** The GM can put a downed helicopter (✈) on any hex at any time, with
  **Clicking the map: Downed helicopter**. Its hull is cover (30%) for the men in that hex,
  and it is slow ground to cross.

## Battlefields

Besides open ground, the field map can lay out a real battlefield. Pick it under
*Battlefield* and press *Lay it out* during set-up. That brings in the field's size, its
ground, its works and its weather. With *with the armies as drawn up* ticked, it also
brings the sides, the wound tables and each army's units in their starting places. Every
unit can still be moved, changed or removed before the battle starts. *New battle* goes
back to the same battlefield.

**Objectives.** Where the accounts name the place a battle was fought for, the battlefield
marks it as the objective (`objective` in its file: the hex, the army that attacked it, its
name and its radius), and laying out the field marks it on the map (O, with a dashed ring
when it is wider than a hex).
- **Radius.** A hill or a perimeter is more than one hex, so each battlefield gives its
  objective a radius that takes in the position as the map draws it: 22 hexes round the Snipe
  outpost, 12 at Crécy, 10 at Beaumont-Hamel, 9 round Pork
  Chop's top (its trench ring) and round the position behind the rise at 73 Easting, 8 at
  Khe Sanh, Kapyong and Keating, 7 at Fox Hill, Darwin
  Hill and on Bougainville, down to 1 for the wagon-box corral. Within the radius counts as
  on the objective, for holding it and for the log. The commander's other distances widen to
  match: holding, units fall back if more than 2 hexes outside it; enemies within 3 hexes
  outside it count as guarding it. An objective the GM marks by hand has the commander's own
  radius, 1 hex. The enemy commander then takes
it or holds it, as under [The enemy commander](#the-enemy-commander); the GM can move or
clear it with **Clicking the map**. Thirty-seven battlefields have one: Point 593 at
Cassino, Castle Hill in the town, the crests of Hills 875, 861A, 931 and 937, Pork Chop,
Fox Hill, Hill 504 at Kapyong, G Company's hill at Chipyong-ni, Darwin Hill, the Iraqi position behind the rise at 73 Easting, the station
at Grozny, the provincial headquarters at Hue, the crash site in Mogadishu, Observation
Post Topside at Wanat, Combat Outpost Keating, X-Ray's landing zone, the saddle at Osan
and on Bougainville, the railway bridge at Mons, the German front line at Y Ravine (Beaumont-Hamel), the hollow at Snipe, the saddle of the Babuna pass, the English position between Crécy and Wadicourt, the Portuguese position at São Jorge (Aljubarrota), the imperial guns and camp at Dornach, the castle at Jacob's Ford, Henry Hill, the Redan's salient (on both of its battlefields), the British guns at Lundy's
Lane, the windmill battery at Lützen, the heights at Albuera, the edge of Cisterna and the
wagon-box corral. The open-field battles (Agincourt, Towton, Visby, Cowpens), the ambush
on Lodge Trail Ridge, the Jolan at Fallujah and the unfinished wall at Sidon have none:
they were not fought for one place, or the map does not place it.

**Phases.** A battlefield can split its battle into phases (`phases` in its file). Each phase
has a name, the exchange it begins (the first at 1; an exchange is about a minute), a note on
what happened, and the units it brings on.
- **Waiting units.** Laying out the armies holds those units off the map. They keep their
  IDs, so the Redan's supports are still B5.
- **The strip.** A strip above the map lists the phases during set-up. In the battle it
  shows the current phase, its note and what comes next. The log marks each new phase.
- **Arriving.** When a phase begins, its units come on where the battlefield draws them, or
  at their side's entry edge if that ground is taken. Like any unit brought on, they can
  move from the next exchange. A unit with no room at all waits and tries again each
  exchange.
- **The light.** A phase may set the light (`light`: dusk, moonlit, night or day) from then
  on: the sun setting or rising during the battle. The log and the turning points say so.
- **By air.** A unit that comes in by air (`lands`) takes off when its phase begins and lands
  at its landing zone by the usual rules, as many men an exchange as the lift allows. That is
  how X-Ray's D Company and the 2nd Battalion's B Company come in.
- **Where they're used.** Phases apply with *the armies as drawn up*, not to forces sent
  from the travel map.

**Which account.** Where a battlefield's sources disagree on something the battle turns on
(how many attacked, when help came), `data/accounts.yaml` makes it a choice. It is kept apart
from the battlefield files because their generators write those.
- **The questions.** Each has an id, a question and two or more options, each with a label and
  its source (`single: true` for a single report). The first option is the game's own and
  changes nothing.
- **The changes.** Each other option changes the armies as drawn up: a side's men scaled
  (`side`, `scale`), a unit's men set or scaled (`unit`, `men` or `scale`), or a phase moved
  (`phase`, `at`, still in order). The ground, works and units stay as drawn.
- **On the field map.** Choosing the battlefield shows a *Which account?* box during set-up:
  a select for each question, and *Roll it* (each option as likely). The armies are drawn up
  again as chosen, and the message says by which accounts.
- **Scoring.** The enemy commander's benchmark is run on the game's own account, and the
  accounts are left out of the battlefield's stamp. A battle on another account is scored
  against history only, with no commander's bar, and the scorecard marks it so.
- **In the books.** Each battlefield's section lists its questions under *The accounts to
  choose*.
- **Where.** Twenty-three battlefields, 36 questions. The other battlefields with disputes
  have none the changes can express: their figures are for a whole army the field shows only
  part of, the time in dispute is the battle's start, or a phase would have to jump past the
  next. Where the field's own figure matches no account, its option says "the game's figure".

Thirty-five battlefields have phases. Each phase's time is our reading of the accounts, rounded to the
minute from the deployment moment (exchange 1). The sources are named in each generator's notes
where they are not plain.
- **The Redan, 8 September:** the stormers go over (1); the supports come forward (10); the
  Russian reserves counter-attack (80, after about an hour and a half).
- **The Redan, 18 June:** the two flank columns go out (1); their supports follow (4); the Russian
  reserve comes up (15).
- **Lundy's Lane:** Scott attacks the hill (1, about 7 pm); sunset, dusk (31, about 7:30);
  dark, by moonlight (61, about 8); Ripley, Porter and Hercules Scott's column come up (120, about
  9 pm); Drummond counter-attacks (150, until near midnight).
- **Lützen** (from about 11:00): Pappenheim's horse arrive (76); the King is killed and the
  second line goes in (151, an estimate); a lull (241); the windmill hill falls (271); Pappenheim's foot
  arrive, too late (421).
- **Jacob's Ford** (from sunrise, 05:35): full light (25); the second wave of volunteers and
  foot comes up to the breach (31, our reading).
- **Dornach** (from about 16:00): the Welsche Garde comes over the Birs (31); Bern's main
  banner comes out of the trees (46); Lucerne and Zug come up (181, about 19:00); sunset (217)
  and moonlight (253). When the horse and the Bernese came is our reading.
- **Crécy** (from about 17:00, as the shower passes): Alençon's men ride through the Genoese
  (16); the King of Bohemia (31); Lorraine, Blois and Flanders (61); sunset (101); Philip's own
  battle and the foot that came up (121); moonlight (135). When each came in is our reading.
- **Aljubarrota** (from about 18:00): the vanguards meet (16); Juan I's main battle comes up
  and the Master of Alcántara's ginetes ride round to the baggage (31); sunset (51) and moonlight
  (76). Which way the ginetes went is our reading.
- **Snipe** (from first light, 06:15 Egyptian summer time): civil dawn, daylight (36); sunrise (61); 24th Armoured Brigade
  and the long-gunned Panzers (76, 07:30); the brigade pulls back (166, 09:00); Italian infantry
  (226) and a dozen Italian tanks (256); the Italian tanks over the western ridge (406, 13:00);
  Rommel's counter-stroke with the Stukas (646, 17:00); sunset (727) and dark (780). Where each
  Axis attack came from is our reading.
- **Beaumont-Hamel** (from zero, 07:30 BEF time): the second wave (6); the white rockets (31);
  the order to the 88th Brigade (76, 08:45); the Newfoundlanders go over (106, 09:15); Hadow
  reports failure (136); the Essex (146, 09:55 by the Museum, 10:50 by Veterans Affairs).
- **Mons** (from 09:00): a renewed attack through the woods (31); the attack in force (121);
  the Fusiliers withdraw (251). Which German battalion came in when is our reading.
- **The Babuna pass** (from dawn, about 06:30, a day of our reading): up the spurs (61); the
  east spur pressed (391); a battalion from the Veles front (571); dusk (631) and night (661);
  the retreat ordered at 22:00 (931).
- **Osan** (from about 11:45): a battalion works round the west (46, 12:30); another comes
  down the railroad and Smith withdraws (166, 14:30).
- **Chipyong-ni**, the night of 14–15 February and the day after (from 22:00): G Company's hill
  falls and the Rangers counter-attack (331, about 03:30); the dawn counter-attack fails (496,
  06:15); B Company counter-attacks (721, 10:00); the hill retaken (1111); Task Force Crombez
  (1156, about 17:15).
- **Kapyong**, the night of 23–24 April (from 21:30): the Chinese reach headquarters (31);
  the main assaults (201); headquarters pulls out (451); B Company called up the hill (586).
- **Pork Chop Hill** (from 23:05): L Company (176, shortly after 02:00); K Company
  counter-attacks (326, 04:30); a fresh Chinese company, and G Company of the 17th Infantry
  with it (550, 08:14).
- **X-Ray** (from about 13:35): D Company lands (56, 14:30); the push for the cut-off platoon
  (131); B Company of the 2nd Battalion at dusk (211, 17:05).
- **Dak To** (from 10:30): the attack from behind onto A Company (241, 14:30); C Company
  surrounded (271); the stray bomb (509, 18:58).
- **73 Easting** (from 16:18): through the trenches (5); the T-72s on the high ground beyond
  (19, about 16:36).
- **Grozny** (from about 16:30, as the sun sets): dark (31, about 17:05).
- Fifteen more, from the second round of research (times and sources in the project's
  `battle-phases-research-round2.md`): Fox Hill, Wanat (the Apaches at 61, the QRFs at 102 and
  241, the jets on call at 131), Khe Sanh 861A, First Bull Run (Chinn Ridge at 121), Cisterna
  (the tanks at 351), Wagon Box, Fetterman, Cowpens, Goose Green, Bougainville, the Poles at
  Cassino, the abbey and the town at Cassino, Heartbreak Ridge and Mogadishu (the relief column
  at 553). Where a time is our estimate the phase's note says "(est.)".
- **Batteries and aircraft.** A phase can also bring on a battery or aircraft on call (a
  `support` entry, by name): it is not on call until its phase begins.

**From the travel map.** A battlefield can name a place on a travel map and how close
counts (`travel` in its file). Agincourt names Azincourt, within 1 hex. When the defender
of a fight stands that close, the travel page offers the battlefield under **Fight it on**
and picks it by default. On the field page the battlefield is laid out with that day's
weather (not the battlefield's own), and each force's fit men are put into the armies as
drawn up:
- **Which army.** The defender with its allies, and the attackers, each take the army of
  their side's name in the battlefield's `travel.sides` (Agincourt: England, then France).
  A side not named there takes the other army. If neither is named, or both name the same
  army, the defenders take the first army and the attackers the second.
- **How many.** A battlefield is a slice of the battle, so each unit stands at its drawn
  numbers at most: 6,000 English fill the battlefield's English line of 5,960, and 40 wait in
  reserve. A smaller force fills it scaled down, in the same shape (3,000 English stand at
  half strength). Three German corps at Mons put the battlefield's 3,630 Germans in line and
  keep the rest in reserve. Each unit is drawn from the force with the most men left, the
  biggest units first, so they are the least likely to be cut short. A mounted unit comes from a mounted force and a unit on
  foot from a force on foot, when there is one with men left; a mounted unit drawn from a
  force on foot fights on foot.
- **The baggage.** Wagon forces stay in reserve unless their army has no other force.
- **Room.** A unit that no longer fits where it stood stays in reserve.
- **Reserves in the battle.** On its own move a side can bring on a unit from its forces'
  reserves with **Add a unit** (any men, order and arms, up to the force's reserve). It comes
  on at the map edge behind its side (the side the most of its men face away from), as wide
  as asked if that fits, else narrower and deeper, and it can move from the next exchange.
  Any battle can bring on units this way; a battle from the travel map draws them from the
  forces' reserves.

The GM can still move, change or remove any unit, or pick open ground instead, which lets
the units that fit stay. A battle sent from the travel map to open ground can be put on a
battlefield the same way: the ground and works come, the forces and weather stay, and
units that no longer fit are taken off.

**Agincourt, 25 October 1415** (`data/fields/agincourt-1415.yaml`). The field is 100 × 80
hexes, about 1,090 by 760 yards (1,000 by 690 m), with north at the top:
- The woods of Azincourt (west) and Tramecourt (east) close in on both sides. The gap
  between them narrows from about 950 yards (870 m) at the French end to about 840 yards
  (770 m) at the English end.
- Azincourt village is in the north-west corner, a clearing by Tramecourt is in the east,
  and the rest is ploughed land.
- The weather is overcast and calm after a night of heavy rain, with deep mud (level 3).
  Every hex costs one more to enter, so the French walk about half their usual pace.
- The English stand in one line. Three small bodies of dismounted men-at-arms (320 each, in
  plate, with poleaxes) have archers between them and on both wings: 5,000 archers with
  longbows, padded jacks and a row of stakes in front.
- The French come in three lines about 260 yards (240 m) away, within long bowshot: a
  dismounted vanguard of 4,800 men-at-arms with a mounted wing of 800 on each side, a main
  battle of 4,800 behind it, and 3,000 mounted men in the rear.
- The numbers are round figures for play; the real ones are disputed.
- The wound tables are Towton's (1461), the nearest the set has to a battle of this kind.
  Archers in close combat fight with their bows' numbers, as every unit fights with one
  weapon.

How it is drawn: the woods' edges are drawn by hand to the shape the accounts give, not
traced from any map. The deployment is the outline most modern accounts share, put in our
own words. The file is generated by `tools/maps/make_agincourt_field.mjs` (no packages
needed: `node make_agincourt_field.mjs`).

**Crécy, 26 August 1346** (`data/fields/crecy-1346.yaml`). The field is 200 × 160 hexes, about
2,190 by 1,520 yards (2,000 by 1,390 m), with WEST at the top: the traditional site, as Cassini
fixed it in 1757 and Preston reads it (Ayton and Preston, 2005).
- The English ridge runs across the top from the edge of Crécy and the Maye (left, south) towards
  Wadicourt (right, north), with the windmill behind the middle and the wood and the wagon park
  (the carts round the horses, one way in) behind that. Its slope, scrub and ripe wheat, falls to
  the Vallée des Clercs across the middle; two terraces cross the slope towards Crécy.
- The valley's far side is Preston's bank, steep and 2-6 m high, for about 1.4 km, open at the
  south end (the way in from the Fontaine-sur-Maye road, bottom left) and wet at the north end;
  beyond it is the Estrées plateau. The bank and the terraces play as earth banks; the shallow
  pits before the English line play as stakes.
- Overcast after the shower, a breeze from the west, the ground wet; the Genoese come on at about
  17:00, the sun sets at 18:40, and a moon about three-quarters full is up after.
- The English face east, by Froissart's battles: the Prince of Wales's (800 men-at-arms on foot
  with Warwick, 1,000 Welsh spearmen behind, 1,000 archers on each wing) in front on the right;
  the second battle under Arundel (800 men-at-arms, 600 archers on each wing) to its left and a
  little back; and Edward III's (700 men-at-arms, 2,000 archers and 1,500 spearmen) by the
  windmill. All the men-at-arms are on foot in the coat of plates and mail.
- The French come up the valley from its south end: the Genoese (6,000, without their pavises),
  then Alençon's 3,000 men-at-arms, the King of Bohemia's 500, Lorraine, Blois and Flanders (3,000)
  and Philip VI's own battle (4,000) with 2,000 foot, each in its phase.
- The English hold where they stand (data/orders.yaml).
- The wound tables are Towton's (1461).

How it is drawn: the ridge, the valley, the bank and the terraces to the accounts' words, not
traced from any survey; the terraces come from an unsourced guide, and the way the French came in
is our reading of Preston. The rules have no edge that horses cannot cross, so the bank only slows
them. The English guns (ribalds under the carts) are not on the field. In self-play the English hold (3 of 3 runs, seeds 1 to 3) and the French lose
more (about 6.5% of their men to the English 2.4%), but far fewer than the 1,542 knights and squires the
heralds counted, nor does the field play the next morning's pursuit. The file is
generated by `tools/maps/make_crecy_field.mjs`.

**Aljubarrota, 14 August 1385** (`data/fields/aljubarrota-1385.yaml`). The field is 100 × 130
hexes, about 1,090 by 1,240 yards (1,000 by 1,130 m), with north at the top: the plateau of São
Jorge.
- A stream valley runs down each side (the Vale de Madeiros to the west), its stream marsh,
  its floor brush and trees, its sides slopes; between them the plateau is open with low
  scrub, about 350 m wide at the Portuguese line and widening to the south.
- The works the excavations found: a ditch of about 182 m round the east side of the chapel's
  ground, a shallow ditch of about 330 m across the Portuguese front, and a field of pits on
  the vanguard's right (they play as stakes: they stop horses and slow men). The baggage
  wagons are at the north end.
- Fair, a breeze from the north-west, dry ground; the attack is at about 18:00, the sun sets at
  18:50 and a moon a little over half full is up after.
- The Portuguese face south, by Fernão Lopes's figures: the Constable's vanguard (600
  men-at-arms on foot, in mail and plates, with 1,200 foot behind), a wing of 200 on each side
  (the Ala dos Namorados on the right), 400 crossbowmen on the right and 300 English archers
  and 400 crossbowmen on the left, João I's rearguard (700 men-at-arms and 1,500 foot) behind
  and a guard on the baggage.
- The Castilians come up from Chão da Feira: the French vanguard on foot (1,200) with 400
  Portuguese who held for Castile, the Master of Alcántara's 700 ginetes on the left (they ride
  round to the baggage) and the Master of Calatrava's 700 lances on the right, and Juan I's
  three mounted bodies (3,000), who come up in the third phase. His crossbowmen and foot, left
  behind, and the bombards, which fired once to little effect, are not on the field.
- The Portuguese line holds where it stood (data/orders.yaml).
- The wound tables are Towton's (1461); the ossuary's bone evidence, the leg fractures of at
  least 414 men, is its own table in the roller.

How it is drawn: the valleys, ditches and pit field to the excavated and chronicle figures, not
traced from any plan. In self-play the Portuguese hold (3 of 3 runs, seeds 1 to 3), but losses
come out about even, where the Castilians lost far more, most of them in the rout and the pursuit
that the field does not play. The file is generated by `tools/maps/make_aljubarrota_field.mjs`.

**Jacob's Ford, 30 August 1179** (`data/fields/jacobsford-1179.yaml`). The field is 40 × 70 hexes,
about 440 by 660 yards (400 by 600 m), with north at the top: the storm of the Templar castle.
- The castle on its low tell, 50 by about 150 m as the excavators give it: stone walls 4 m thick
  as wall edges (no crossing but at the gates and the breach), the south gate, the east postern,
  the square tower at the south-west corner (tall building) and the vaulted kitchen and stores;
  the north-east corner fallen (rubble), where the mine brought it down. The Jordan runs down the
  east foot of the tell and round its south to the ford, about 200 m below the castle.
- Fair, a breeze from the west (a wind fanned the fire in the timber wall behind the breach,
  which is not on the field: it burned as the wall fell); dawn light, full day from the 25th
  exchange.
- The garrison, by al-Qadi al-Fadil's figures: 160 Templar knights and squires at the breach,
  450 sergeants and 300 crossbowmen and archers inside; they hold. The craftsmen and the 100
  Muslim slaves at work on the building are not on the field.
- Saladin's men (no source gives their numbers; ours): Farrukh-Shah's storming column of 1,000
  at the breach, 600 archers north of the castle and 400 across the river, and 1,500 volunteers
  and foot in the second phase.
- The wound tables are Sidon's (1253): the castle's own five skeletons are too few for one.

How it is drawn: the castle to the excavated figures, the tell, river and camp by hand. In
self-play (3 runs) the garrison breaks under the arrows in one run, but the storming column
does not go in through the breach in any. The file is generated by
`tools/maps/make_jacobsford_field.mjs`.

**Dornach, 22 July 1499** (`data/fields/dornach-1499.yaml`). The field is 120 × 140 hexes, about
1,310 by 1,320 yards (1,200 by 1,210 m), with EAST at the top (`up: E`), so the Swiss come down
the map as they came down the scarp: north, towards Arlesheim, is on the left.
- The wooded scarp below the Gempen across the top, slope and scrub below it; Dorneck castle on
  its spur at the top right; Oberdornach below it; the harvest fields and the imperial camp (its
  carts and tents as wagons) in the middle, with a rise later called Blood Hill; the edge of
  Arlesheim on the left; the Birs (shallow, fordable: marsh) and Dornachbrugg's bridge at the
  bottom, the meadows towards Reinach beyond.
- Fair and calm, the July heat; the attack at about 16:00, sunset at 19:36, a full moon after.
- The Confederates (by the chronicles' strengths): Solothurn's vanguard of 1,000 pikes under
  Niklaus Conrad and 500 halberdiers, 500 Bernese under Kaspar von Stein, 400 of Zürich, Bern's
  main banner of 3,000 under Rudolf von Erlach (in the third phase), Lucerne and Zug's 1,000 (in
  the fourth), and Dorneck's twenty men with handguns, who hold.
- The imperial army (about 10,000; the split is ours): the guns before Dorneck and in the
  Ramstel, Fürstenberg and the knights, handgunners, 3,000 Landsknechte, 2,000 Geldern
  Landsknechte, 3,000 Swabian and Alsatian levies (green) and the Welsche Garde's 1,000 horse
  from across the river (in the second phase).
- The wound table is Dornach's (Towton's body, the Dornach skulls' head); the ossuary crania are
  their own bone-evidence table in the roller.

How it is drawn: the scarp, castle, villages, river and camp by hand to the accounts' shape. In
self-play (3 runs, seeds 1 to 3) the Swiss hold the guns in one run and lose more men than the
imperials: the field does not play the surprise of the camp in the afternoon heat, nor the rout
over the Birs where most of the imperial dead fell. The file is generated by
`tools/maps/make_dornach_field.mjs`.

**Towton, 29 March 1461** (`data/fields/towton-1461.yaml`). The field is 150 × 120 hexes,
about 1,640 by 1,140 yards (1,500 by 1,040 m), with north at the top:
- The plateau between Saxton (south) and Towton (north). Its west side drops steeply
  (rough ground) to Cock Beck, in flood (marsh), with Castle Hill Wood on the slope at the
  north-west and Renshaw Wood towards Saxton.
- Two ridges (high ground) cross the plateau with a shallow dale between them: the
  Lancastrians on the northern ridge, the Yorkists on the southern.
- The weather is snow with a strong wind from the south and snow lying (level 1). In the snow
  no one can aim beyond 15 hexes (about 160 yards, 150 m), so the archers, about 270 yards
  (250 m) apart at the start, must close before they can shoot.
- The wind (see [weather.md](weather.md)): the Yorkists shoot with it, their bows reaching
  20% further. The Lancastrians shoot into it, with the snow in their faces: they can see to
  aim only about 80 yards (70 m), their bows reach 20% less, and they are a further −10%.
- The Yorkists: 5,000 archers under Fauconberg in front of Edward's battle (11,000 billmen),
  and the Duke of Norfolk's 5,000 coming up late at the south-east corner, on the Yorkist
  right.
- The Lancastrians: 6,000 archers in front of Somerset's battle (14,000), a rear battle of
  6,000, and 1,500 men hidden in Castle Hill Wood, on the Yorkist left.
- Everyone wears jack and sallet; the wound tables are Towton's own.

It is drawn the same way, by `tools/maps/make_towton_field.mjs`. The battlefield scripts share
their drawing code, `tools/maps/field_lib.mjs`.

**Visby, 27 July 1361** (`data/fields/visby-1361.yaml`). The field is 80 × 70 hexes, about
870 by 650 yards (800 by 600 m), with north at the top:
- The town's ring wall runs along the north edge (a stone wall on the hex sides, the town
  behind it as rough ground), with the south gate barred: the townsmen kept it shut.
- Solberga nunnery's buildings and closes are rough ground to the north-east, with stony
  ground to the west and woods to the south-east; the rest is open pasture.
- Fair summer weather.
- The Gotlanders, with their backs to the wall: 400 bowmen in front, 1,600 levy with spears
  in padded coats and mail hoods (green), and 500 better-armed freeholders with axes in
  coats of plates.
- The Danes, about 240 yards (220 m) to the south: 500 crossbowmen, 1,000 veteran sergeants
  with spiked clubs, and 500 men-at-arms in full harness.
- The wound tables are Visby's own (the gameplay version).

It is drawn by `tools/maps/make_visby_field.mjs`. The wall, the gate and the nunnery are
drawn by hand to the accounts' description, not traced from any map.

**Lützen, 16 November 1632** (`data/fields/lutzen-1632.yaml`). The field is 220 × 120 hexes,
about 2,410 by 1,140 yards (2,200 by 1,040 m), with north at the top:
- The high road from Lützen to Leipzig runs east and west across the field. Its ditches were
  dug out and lined with musketeers: a bank on its north side and a ditch on its south side,
  as hex-side works.
- Lützen, burning, is rough ground at the west end, north of the road, with the windmill hill
  (high ground) beside it. The Floßgraben, a timber canal the Swedes crossed at dawn, runs
  behind them as wet ground.
- The weather is fog (no aiming beyond 5 hexes, about 55 yards, 50 m). It came and went all
  day: the GM can lift it.
- The Swedes, south of the road: 3,000 veteran musketeers and 3,000 pike in the first line,
  4,000 in the second, and horse on both wings (3,000 under the King on the right, 2,500 under
  Bernhard on the left).
- The Imperialists, north of the road: 1,600 musketeers in the road ditch, 4,000 musketeers and
  4,000 pike in the centre, 800 musketeers guarding the battery on the windmill hill, 1,500
  horse on the right and 2,000 cuirassiers on the left, with Pappenheim's 2,500 horse coming
  up at the north-east corner and his foot coming up, too late, at 18:00.
- Pikemen fight with the pike (`weapon: pike`): no count of pike wounds was found, so it rolls
  on the Visby melee table as a spear, with no shield.
- The guns (see *Guns*): the windmill battery of 7 on the hill, 14 in the Imperial centre
  behind the road, and 20 heavy Swedish guns in front of their foot. The regimental guns are
  left out. No gun wounds survive from the Thirty Years' War, so they roll on the Peninsular
  table's (borrowed).

It is drawn by `tools/maps/make_lutzen_field.mjs`.

**Sidon, 1253** (`data/fields/sidon-1253.yaml`). This field is drawn with **east at the
top**, as medieval maps were: the town and the sea are at the bottom (west) and north is on
the left, so the attack comes down the page. It is 110 × 90 hexes, about 1,200 yards (1,100 m)
north to south and 850 yards (780 m) east to west:
- The town's landward wall runs across the page with a ditch in front of it. One stretch is
  not yet built, only its footing (a low bank behind the ditch); the gate is barred.
- The town is rough ground behind the wall, with the mound where the land castle stands;
  orchards and gardens outside, and the first foothills at the top.
- Fair weather.
- The Franks, inside the wall: 300 crossbowmen and 500 sergeants of the garrison in mail, 100
  knights, and 600 builders and townsmen with axes and no armour (green).
- The army of Damascus, about 340 yards (310 m) up the page: 1,500 horse archers, 800 heavy
  horse and 1,500 foot.
- The wound tables are Sidon's own (the gameplay version). The written record of the raid is
  thin: the numbers and the deployment are our guesses for play.

It is drawn by `tools/maps/make_sidon_field.mjs`, after the excavators' description of the
ditch, the gateway and the castle mound, not traced from any map.

**Albuera, 16 May 1811** (`data/fields/albuera-1811.yaml`). The field is 150 × 230 hexes, about
1,640 yards (1,500 m) east to west and 2,190 yards (2,000 m) north to south, with north at the
top. It runs from La Albuera village south over the heights where the battle was decided; the
allied line north of the village is off the map.
- The Albuera stream (wet ground) runs down the east side, turning south-east as the Nogales
  brook, with olive woods beyond it that hid the French flank march. The allied ridge and the
  heights to the south are high ground; the village is rough ground by the stream.
- Overcast with a breeze. The hailstorm that broke during the lancers' charge is not set:
  the GM can bring it in (storm) when the moment comes.
- The moment of Soult's flank attack. The allies, wheeled to face south: Zayas's 4,000
  Spaniards on the heights, Colborne's 1,600 coming up on their right, Hoghton's and
  Abercrombie's 3,500 behind them, Lumley's 2,000 cavalry, Cole's 5,000 coming up from the
  north-west, Hamilton's 5,000 Portuguese in reserve and Alten's 1,000 Germans in the village.
- The French, coming up from the south: Girard's 4,500 and Gazan's 4,000 in deep columns
  (narrow fronts, many ranks), Werlé's 5,600 in reserve (Oman), 880 Polish lancers and hussars (Oman: 580 and 300)
  out on the west flank, Latour-Maubourg's 2,000 dragoons, and Godinot's 3,500 making their
  show against the village from the east (facing west, so its front runs on the diagonal).
- The guns (see *Guns*): 20 French with the columns and 12 allied on the heights.
- The wound tables are the Peninsular War's (the gameplay blend).

It is drawn by `tools/maps/make_albuera_field.mjs`.

**Cowpens, 17 January 1781** (`data/fields/cowpens-1781.yaml`). The field is 120 × 100 hexes,
about 1,310 yards (1,200 m) east to west and 950 yards (870 m) north to south, with north at the
top and the British coming up from the south.
- An open pasture of scattered trees, with a low crest across the middle where the
  Continentals stood, a second rise behind it where Washington's horse waited out of sight,
  wet ravines down both flanks and woods beyond them.
- Cold and clear.
- Morgan's three lines: 150 riflemen skirmishing in front, 900 militia (most with rifles) 130
  yards (120 m) behind them, and 550 Continentals and Virginia men on the crest; 150 of
  Washington's horse behind the rise.
- Tarleton's line as it formed after the night march: the Legion infantry, the 7th Fusiliers
  and the light infantry, two small "grasshopper" guns, dragoons on both flanks, and the 71st
  Highlanders and most of the Legion horse in reserve.
- The wound tables are the American Revolution's.

It is drawn by `tools/maps/make_cowpens_field.mjs`.

**Lundy's Lane, 25 July 1814** (`data/fields/lundys-lane-1814.yaml`). The field is 130 × 110
hexes, about 1,420 yards (1,300 m) east to west and 1,040 yards (950 m) north to south, north at
the top; the Portage road and the Niagara are off the map to the east.
- A low hill across the north of the field, the lane along its crest, the churchyard behind the
  British guns; woods to the south-west, where Scott's men formed, and along the river side.
- Fair, and most of the fighting at night: the phases bring dusk at sunset (about 7:30, exchange
  31) and a moonlit night from about 8 (61). Sunset and the moon (about eight days old, more than
  half lit, up until after midnight) are worked out for the place and the day; the accounts
  speak only of darkness and thick smoke.
- The evening's opening: Scott's 800 in front of the hill, Jesup's 25th working round the
  British left, Towson's guns, and Ripley's brigade and Porter's volunteers coming up behind.
- Jesup's 25th has a route up the east side, round the British left, to behind their line
  (our reading: he took Riall prisoner on the road behind it).
- On the hill: five British guns at the churchyard, the 89th, the 8th and 41st, the
  Incorporated Militia, the Glengarry Light Infantry on the west, the 19th Light Dragoons, and
  Drummond's 1,000 coming up behind the crest.
- The wound tables are the War of 1812's.

It is drawn by `tools/maps/make_lundys_lane_field.mjs`.

**The Great Redan, Sevastopol, 8 September 1855** (`data/fields/redan-1855.yaml`). The field
is 100 × 80 hexes, about 1,090 yards (1,000 m) east to west and 750 yards (690 m) north to
south, north at the top: the Redan's point toward the British trench at the bottom.
- The Redan: two faces meeting in a salient, each with a **ditch** and an **earth bank** (the
  parapet) along it, joined to the Russian line running off either side of the map. The back
  (the gorge) is open, with a **breastwork** (an earth bank) across it. What is left of the
  **abatis** lies in scattered hexes in front of the faces.
- The British advanced **trench** about 200 yards (180 m) from the salient, with a zig-zag
  back from it; open ground pitted with shell holes (rough ground) between; ravines down both
  sides; the shelled ruins of the Karabelnaya suburb (rubble and buildings) behind the Redan.
- Fair and cold, with a strong north wind.
- Just after noon: the covering party of riflemen and the ladder party (marked with ladders,
  which do nothing on an earthwork; see *Escalade*) out in front, the
  stormers of the Light and 2nd Divisions in the trench, and green supports behind.
- The Russians: the Vladimirski Regiment at the salient and behind the breastwork, guns at
  each shoulder, riflemen on the line to the west, and the Iakutski and Selenginski regiments
  in reserve in the suburb. The Russian infantry have smoothbore muskets, their riflemen and
  the British rifle-muskets; the guns are smoothbore.
- The wound tables are the Crimean War's. The siege guns on both sides, the French attack on
  the Malakhov to the east and the flanking fire from the Russian batteries either side are
  not on the map.
- The point of the salient is drawn cut off square, 120 m across, so that units in line can
  reach the men in it; the real salient came to a sharper point.
- The objective is the salient inside the parapet (3 hexes round its middle), so men in the
  ditch outside it are still attacking it.
- Played by the enemy commander, the British storm the salient (see *Storming works*): the
  covering party and the stormers reach it in four or five exchanges. Broken units run back
  through the supports, the columns behind go in together, and stronger units charge through
  waiting ones. In three test runs the British got into the salient once, after about 80
  exchanges; in the others they were held, or broke after about 50, as the real assault was
  driven out.

It is drawn by `tools/maps/make_redan_field.mjs`, the work and the ground by `tools/maps/redan_lib.mjs`.

**The Great Redan, 18 June 1855** (`data/fields/redan-1855-june.yaml`). The first assault, at
dawn: the same work, drawn by the same script (`tools/maps/redan_lib.mjs`), on a field of
100 × 105 hexes (about 1,090 by 1,000 yards, 1,000 by 910 m), with the British trench about
440 yards (400 m) from the salient, the **abatis** still whole (a belt two rows deep in front
of the faces) and fewer shell holes.
- Daybreak, fair and calm, light enough to see across the open ground (the columns were
  under fire as soon as they left the trenches).
- Two British columns, each with covering riflemen of the Rifle Brigade, a ladder and
  wool-bag party of sailors and soldiers (marked with ladders, which do nothing on an
  earthwork), a storming party and green supports: the right
  column (Yea) facing the Redan's left face, the left column (Campbell) the right face and
  the angle beyond it. The centre column, meant to follow against the salient, never left the
  trenches (Engels, writing in 1855; the losses fell almost all in the flank columns'
  brigades), so it is not on the map.
- The Russians, the works fully manned: infantry at the salient and behind the breastwork,
  guns at each shoulder, a battery and riflemen on the line either side, and a reserve in the
  suburb.
- The wound tables are the Crimean War's. The French attack on the Malakhov, the siege guns
  and the diversions on either flank are not on the map.
- Played by the enemy commander, the columns cross the open under grape and musketry and
  storm the salient; in three test runs the British had a fifth to a quarter of their men
  down, most of the columns broke and ran, and in one run a few men got into the salient. The
  real attack never reached it.

It is drawn by `tools/maps/make_redan_june_field.mjs`.

**First Bull Run, 21 July 1861** (`data/fields/bull-run-1861.yaml`). The field is 140 × 130
hexes, about 1,530 yards (1,400 m) east to west and 1,240 yards (1,130 m) north to south, north
at the top: Henry Hill, with the turnpike and Young's Branch along the north, the Sudley road
down the west side and Chinn Ridge beyond it.
- The broad top of Henry Hill (high ground), the pines along its south-east edge where
  Jackson's brigade formed, Young's Branch (wet ground) below it, and the south slope of
  Matthews Hill north of the turnpike.
- Fair and very hot.
- The early afternoon: Ricketts's and Griffin's batteries pushed onto the hill near the Henry
  house with the Fire Zouaves, the Marines and the 14th Brooklyn, Willcox's and Franklin's
  brigades behind them and Sherman's coming over the turnpike.
- The Confederates: Jackson's brigade and its guns at the edge of the pines, the 33rd Virginia
  in the woods by the Sudley road, Hampton's Legion by the Robinson farm, Bee's and Bartow's
  men rallied behind, and Stuart's horse to the south-west. Kirby Smith's (Elzey's once Smith fell) and Early's brigades
  come in on Chinn Ridge at about 16:00, against Howard's Union brigade.
- The wound tables are the Civil War's, its guns on the Civil War artillery wounds. Ricketts's
  six 10-pounder Parrotts and Griffin's battery are rifled guns; the Confederate guns, mostly
  6-pounders and howitzers, are smoothbore (see *Guns*).

It is drawn by `tools/maps/make_bull_run_field.mjs`.

**The Fetterman Fight, 21 December 1866** (`data/fields/fetterman-1866.yaml`). The field is
150 × 120 hexes, about 1,640 yards (1,500 m) east to west and 1,140 yards (1,040 m) north to
south, north at the top: the north end of Lodge Trail Ridge.
- The ridge's narrow crest (high ground) down the middle, with rocks (rough) where the
  infantry fought near its south end and where Wheatley and Fisher held further north;
  ravines (rough) cutting down both slopes; Peno Creek (marsh) and its flats at the top.
- Clear and cold, a little snow on the ground.
- The moment the decoys turned: the 18th Infantry (49 men, rifle-muskets, open order) on the
  rocks; Wheatley and Fisher (2 civilians with repeating rifles, as breech-loaders) further
  up; the 2nd Cavalry's 27 troopers (Spencer carbines, as breech-loaders) a long way ahead.
- About a thousand warriors: the ten decoys, Lakota horsemen on the flats beyond the creek,
  Lakota on foot in the west ravines, and Cheyenne and Arapaho in the east ravines, with bows
  and rawhide shields (veteran).
- The wound table is the Army surgeons' arrow report, with the Civil War's gunshots borrowed.

It is drawn by `tools/maps/make_fetterman_field.mjs`.

**The Wagon Box Fight, 2 August 1867** (`data/fields/wagon-box-1867.yaml`). The field is
100 × 80 hexes, about 1,090 yards (1,000 m) east to west and 750 yards (690 m) north to south,
north at the top: the plateau between the Big Piney (top) and the Little Piney (bottom).
- Open summer grass; the creek bottoms (marsh) with cottonwoods and pines (woods) along them,
  pine woods towards the pinery to the west, a ravine (rough) to the east.
- The corral in the middle: a ring of wagon hexes round two hexes (wagons: −40% to shots at
  the men behind them, no way through, no horses). The real corral of 14 boxes was about 60-70
  feet by 25-30 feet: the ring is larger than it was.
- Captain Powell's 26 soldiers of the 27th Infantry with Springfield breech-loaders, and 6
  civilians with repeating rifles, in the corral.
- The first charge: mounted warriors (Lakota and Cheyenne) from the north, warriors on foot
  from the ravine, and warriors with guns along the plateau's edge to the west. Estimates of
  the warriors present run from 300 to 1,000; here 650.
- Major Smith's relief column (100 men) comes from the fort, to the east, in the last phase;
  its mountain howitzer is not on the map.
- Fair, a breeze from the west.

It is drawn by `tools/maps/make_wagon_box_field.mjs`.

**Mons, 23 August 1914** (`data/fields/mons-1914.yaml`). The field is 150 × 120 hexes, about
1,640 yards (1,500 m) east to west and 1,140 yards (1,040 m) north to south, north at the top:
the canal salient at Nimy.
- The Mons-Condé canal loops north across the middle (water: crossed only at the road and
  railway bridges near its tip); Nimy's houses on the south bank (buildings), the edge of Mons
  to the south-west, a slag heap behind the line, open fields and two woods to the north.
- Overcast and calm.
- Mid-morning: the 4th Royal Fusiliers in extended order at both bridges, with their two
  machine guns at the railway bridge and two companies in Nimy behind; the 4th Middlesex and
  its machine guns along the canal to the east. All long-service regulars (veteran).
- The Germans: two battalions of Infantry Regiment 84 in close order in the fields north of
  the bridges, its machine-gun company with them, its third battalion in extended order
  behind, and a battalion of Fusilier Regiment 86 coming out of the woods to the north-east.
- Fire support: six British 18-pounders against twelve German 77 mm field guns and six field
  howitzers.
- The wound tables are the First World War's.

It is drawn by `tools/maps/make_mons_field.mjs`.

**Beaumont-Hamel, 1 July 1916** (`data/fields/beaumont-hamel-1916.yaml`). The field is 80 × 116
hexes, about 870 yards (800 m) north to south and 1,100 yards (1,000 m) east to west, with EAST at
the top: the ground of the Newfoundland Memorial Park.
- St John's Road, the support trench, runs across the bottom; the British front line stands on
  the crest about 230 m beyond it, with its wire in front and a lane cut every 80 m. No man's land
  falls about 400 m to the German wire (three belts, a few shell gaps) and the German front system,
  three trenches deep with dugouts every 46 m. Y Ravine runs up from the German front line on the
  left (north), forking at its foot, with dugouts in its sides. The Danger Tree stands halfway
  across.
- Fair and calm, the ground dry; the sun is up from 04:43.
- British, all in Brodie helmets in extended order: the 87th Brigade's first wave (2nd South Wales
  Borderers on the left, opposite Y Ravine; the 1st Inniskillings, 952 strong by their war diary,
  on the right) at zero, and its second wave (1st Border, 1st KOSB) five minutes later; the 1st
  Newfoundland Regiment (780, by Nicholson: A and B Companies in front, C and D behind) from St
  John's Road at 09:15; and two companies of the 1st Essex on their right at 09:55.
- German: two companies of RIR 119 in the front trench, four pairs of machine guns (at the head
  of Y Ravine, in the front trench, behind on the right, and on the right firing across), a company in Y Ravine and
  another in the third trench, all dug in; twelve field guns and four howitzers on call for the
  barrage on the British trenches. The British barrage lifted at zero and is not on call.
- The Germans hold where they stand (data/orders.yaml).
- The wound tables are the First World War's.

How it is drawn: the lines, the slope and the ravine to the distances the sources give, not
traced from a trench map. RIR 119's companies and machine guns here, and the British battalions'
strengths but the Inniskillings' and the Newfoundlanders', are not known and are ours, with round
numbers; whether RIR 119 wore steel helmets on 1 July is not known (it wears none here). No man's
land plays as open ground, not slope: the rules count height in steps, and a slope hex would hide
the forward slope from the German line. RIR 119's ammunition is in its dugouts (supply dumps the
battlefield places), or its machine guns fall silent within twenty minutes. In self-play the
Germans hold (3 of 3 runs, seeds 1 to 3), but the British lose about 14% of their men to the
Germans' 6%, where the Newfoundlanders lost 88% and the 87th Brigade's battalions more than half:
the first wave goes to ground in no man's land and the Germans go on firing at it, the nearest
target, while it screens the waves behind (no unit shoots through another, even one lying down),
so the Newfoundlanders cross almost untouched.
It is drawn by `tools/maps/make_beaumont_field.mjs`.

**The Babuna pass, November 1915** (`data/fields/babuna-1915.yaml`). The field is 130 × 110
hexes, about 1,420 yards (1,300 m) east to west and 1,040 yards (950 m) north to south, north
at the top: the pass on the road from Veles to Prilep.
- The road climbs in hairpins from Izvor (north) to the saddle in the middle, between two
  spurs that push north; the crest is high ground with rock, the faces slopes with scrub oak
  and beech in the gullies; the road goes on down towards Prilep (south).
- Overcast, a breeze from the north, the ground muddy.
- The Serbian 2nd Regiment holds one battalion's stretch of the crest: a company on each spur
  and one astride the road, in trenches and gone to ground, two machine guns at the saddle
  and a company behind it. The Bulgarians: a battalion up the road, one onto the west spur,
  their machine guns, and later one onto the east spur and one from the Veles front.
- Fire support: two old Serbian mountain guns against twelve Bulgarian field guns and four
  heavy guns.
- The day is our reading of the accounts (Sandes and the Nelson history): the regiments held
  the crest for a week and more and went at 22:00 on the night the retreat was ordered, which
  is when the Serbian companies withdraw (data/orders.yaml). The machine guns, the companies
  and which Bulgarian division attacked are not in the sources found.
- The wound tables are the First World War's.

It is drawn by `tools/maps/make_babuna_field.mjs`.

**Snipe, 27 October 1942** (`data/fields/snipe-1942.yaml`). The field is 200 × 160 hexes, about
2,190 yards (2,000 m) west to east and 1,520 yards (1,390 m) north to south, north at the top: the
hollow of Snipe, west of the Kidney feature at El Alamein.
- The hollow, an oval about 900 by 450 m with its long axis north-east to south-west, lies in the
  middle of flat desert, with a low ridge to the west and another to the east (high ground with
  slopes). The hollow plays as open ground, as the desert does: its depth is not known, and its
  camelthorn is not drawn (the rules' scrub would keep tanks out of it); the objective's ring marks
  it, and the British stand in it, dug in.
- Fair and calm; first light at 06:15 (dusk light), daylight from civil dawn at 06:50 (the guns
  were firing at 800 yards by then), sunrise 07:15, sunset 18:21, dark at 19:14,
  the moon not up until about 20:55. The clock is Egyptian summer time (GMT+3).
- British, all dug in: the 19 six-pounders by company sector (anti-tank guns, five men to a gun in
  the rules): 239 Battery's six to the north and north-east, A Company's four to the north-west,
  C Company's four to the south-west, B Company's five to the south-east; 30 riflemen of each of
  A, B and C Companies behind their guns, the 22 carriers (armoured carriers) and the 16 sappers
  in the middle. 47th and 41st RTR (24 tanks each, ours) come over the eastern ridge at 07:30
  and go back at 09:00 (data/orders.yaml); the rest hold.
- Axis, in waves (tanks four men to a tank; the Panzers heavy armour, the Italian M13s, M14s and
  Semoventi light): 15 German tanks passing north and 17 Italian passing south at dawn; 25
  long-gunned Panzers from the south at 07:30; 200 Bersaglieri at 10:00; a dozen Italian tanks
  and eight German at 10:30; nine Italian over the western ridge at 13:00; and at 17:00 Rommel's
  counter-stroke, 15 Panzer IIIs on the north-west with 30 German and 10 Italian tanks from the
  south, after 20 Stukas. German guns and 88s (8, field) on call.
- The wound tables are the Owens WWII table.

How it is drawn: the hollow to the accounts' size, the ridges, its depth and the guns' places
inside their sectors ours; the attacks the accounts number at those numbers, the rest ours, with
round numbers. The British artillery (its observer lost at 04:00) and the friendly fire are not
played. In self-play the battalion does not hold: all three runs end about 10:30 with every
British unit gone (0 of 3 matched), the British losing about 40% of their men to the Axis 14%,
where in fact 72 of under 300 were hit and some 32 tanks and 5 SP guns were left burnt out round
the hollow. The guns break and run under the dawn and morning attacks; how the anti-tank guns,
their crews' morale and the tanks' fire on dug-in guns play is a lead for the self-play review. It
is drawn by `tools/maps/make_snipe_field.mjs`.

**Hill 700, Bougainville, 8-12 March 1944** (`data/fields/bougainville-1944.yaml`). The field
is 120 × 100 hexes, about 1,310 yards (1,200 m) east to west and 950 yards (870 m) north to
south, north at the top: the ridge across the middle.
- Hill 700's crest (high ground) with a saddle between two knobs; a line of pillboxes
  (bunkers: −50% to shots at men in them) along the front of the 145th's battalions on the
  crest, one every seventh hex, and under each machine-gun section, a belt of barbed wire below
  with lanes through it, a cleared belt of stumps and shell holes below that, and jungle
  (woods) beyond and behind.
- Rain, the ground muddy.
- The 145th Infantry's 2nd Battalion on the two knobs in extended order, machine guns covering
  the saddle, and the 3rd Battalion in reserve in the jungle behind.
- The Japanese 23rd Infantry's II and III Battalions in the jungle below (veteran, extended
  order), with their machine-gun company.
- Fire support: American 105 mm and 155 mm howitzers and 81 mm mortars; Japanese mountain guns
  and mortars.
- The wound tables are Bougainville 1944's.

It is drawn by `tools/maps/make_bougainville_field.mjs`. Both are design sketches drawn from
the accounts' plain facts, not traced from any map.

**The Rangers at Cisterna, 30 January 1944** (`data/fields/cisterna-1944.yaml`). The field is
150 × 120 hexes, about 1,640 yards (1,500 m) east to west and 1,140 yards (1,040 m) north to
south, north at the top.
- The southern edge of Cisterna along the top and the railroad station top left (buildings);
  a cross ditch below the town; the Conca road from the bottom left; the Pantano ditch (marsh)
  from the bottom right; open, treeless fields with farmhouses (buildings) and haystacks
  (rough).
- A cold, still dawn, the reclaimed ground soft.
- The 1st and 3rd Ranger Battalions (veteran, extended order) in the open fields 800 yards
  short of the town. (The 3rd Reconnaissance Troop's platoon behind them on the road was caught
  on a road block before dawn, so it is not on the map.)
- The Germans gone to ground in the houses on the town's edge, in farmhouses with machine
  guns, and in haystacks and dugouts on both flanks; paratroops by the station.
- Fire support: the 3rd Division's 105 mm howitzers and the Rangers' 4.2-inch mortars; German
  mortars, three self-propelled guns and, later in the morning, tanks, all firing over open
  sights.
- The wound tables are the Owens WWII set (hospitalized wounded).

It is drawn by `tools/maps/make_cisterna_field.mjs`, from the plain facts of the US Army's
account (*Anzio Beachhead*), not traced from any map.

**Task Force Smith at Osan, 5 July 1950** (`data/fields/osan-1950.yaml`). The field is 220 ×
110 hexes, about 2,410 yards (2,200 m) east to west and 1,040 yards (950 m) north to south,
north at the top.
- A line of hills across the middle (high ground, scrub pine), steep on the forward side, with
  the highway over it at a saddle on the left and the railroad on the right; a hillock west of
  the road and a finger ridge running south beside the railroad. Rice paddies (marsh, their
  dikes open ground) before and behind.
- Overcast after rain, the ground muddy.
- Task Force Smith dug in (gone to ground, green): B Company at the saddle and east of it, a
  platoon on the hillock, the recoilless rifle and bazooka teams by the road, machine guns, C
  Company along the ridge east and its right bent back by the railroad.
- The North Korean 4th Division's infantry (veteran, extended order) across the paddies, working
  round the west, in column on the highway, and coming down the railroad, with machine guns. The
  battalion working round the west has a route over the hill west of the highway and round
  behind the ridge; the one on the railroad, down past C Company's right and behind the ridge
  (our reading of the account).
- Fire support: American 105 mm howitzers, 4.2-inch and 60 mm mortars; North Korean mortars and
  the T-34s of the 107th Tank Regiment firing over open sights. The tanks are kept on call as fire
  support, and the recoilless rifles and bazookas fight as riflemen: a design choice, not a
  gap in the vehicle rules.
- The wound tables are Korea's (hospitalized wounded).

It is drawn by `tools/maps/make_osan_field.mjs`, from the plain facts of the US Army's account,
not traced from any map. A battlefield's units may start gone to ground (`prone: true`).

**The perimeter at Chipyong-ni, 14-15 February 1951** (`data/fields/chipyong-1951.yaml`). The
field is 200 × 170 hexes, about 2,190 by 1,610 yards (2,000 by 1,470 m), north at the top.
- The village in the middle (buildings), the railroad through its south and the road north
  and south; the ring of low hills the 23rd Infantry dug in on (high ground, scrub), about a
  mile across; frozen paddies (open ground) inside and out, wooded hills beyond.
- A clear, bitter **dark night**, snow on the ground. No one sees beyond 55 yards (50 m)
  unless the ground is lit: fire illumination or flares.
- United Nations, dug in round the ring: A and C Companies (1st Battalion) on the north, I, K
  and L (3rd) on the east, E, G and F (2nd) on the south, G on the southern hill, and the
  French Battalion's three companies on the west (veteran). The AAA's quad .50s and the
  battalion machine guns are on the line, and B Company and the 1st Ranger Company are in
  reserve. Task Force Crombez's tanks come up Route 24A from the south in the last phase
  (about 17:15 on the 15th).
- Chinese (veteran, extended order): a regiment from Hill 397 against G Company, and
  battalions against E, C and K Companies and the French, with machine guns.
- Fire support: 105 mm and 155 mm howitzers, 4.2-inch mortars and the regimental tanks inside
  the perimeter, and fighter-bombers, which fly only by day; Chinese mortars.
- The wound tables are Korea's (hospitalized wounded).

It is drawn by `tools/maps/make_chipyong_field.mjs`, from the plain facts of the battle, not
traced from any map.

**Landing zone X-Ray, 14 November 1965** (`data/fields/xray-1965.yaml`). The field is 160 × 130
hexes, about 1,750 by 1,240 yards (1,600 by 1,130 m), north at the top.
- The clearing right of the middle is the landing zone (H): elephant grass and a termite hill
  or two. The dry creek bed (rough) runs west of it. The lower slopes of the Chu Pong massif
  (woods on high ground) are on the left, with the knoll where B Company's 2nd Platoon was cut
  off to the north-west. Scrub trees, tall grass and termite hills are all round.
- A fair, still afternoon.
- United States (1st Battalion, 7th Cavalry):
  - B Company across the creek bed;
  - its 2nd Platoon on the knoll;
  - A Company along the creek bed on B's left;
  - C Company south of the clearing;
  - the command post's machine guns and mortars.
- **In the air:** D Company, and B Company of the 2nd Battalion at dusk, coming in at the
  landing zone (see *Landing by air*).
- North Vietnamese (veteran): the 9th Battalion of the 66th Regiment down off the massif, the
  7th from the south-west, a company round the knoll, and machine guns.
- Fire support: 105 mm howitzers at Falcon, 81 mm mortars, rocket helicopters (gunships) and
  Skyraiders and jets with bombs and napalm (fighter-bombers); North Vietnamese mortars.
- The wound tables are Vietnam's (hospitalized wounded).

It is drawn by `tools/maps/make_xray_field.mjs`, from the plain facts of the battle, not traced
from any map.

**Mogadishu: the crash sites, 3 October 1993** (`data/fields/mogadishu-1993.yaml`). The field
is 110 × 110 hexes, about 1,200 by 1,040 yards (1,100 by 950 m), north at the top.
- A grid of narrow sand streets (open ground) between one-storey stone houses behind walls
  (buildings). The Olympic Hotel (tall buildings) is on Shalalawi Street, with a few other
  blocks of several storeys. The Bakara Market's stalls and sheds are to the south-west. The
  first crash site is north-east of the target, the second to the south, each with its downed
  helicopter.
- A **dark night**; the Little Birds fly at night.
- United States (veteran, the 1993 Ranger body armour): Rangers and Delta in the houses round
  the first crash and their machine guns; at the second, the crew and the two Delta snipers.
- Somali National Alliance militia (green, extended order): from the market, the north and the
  east, and the crowd at the second crash site, with RPG teams and machine guns.
- The relief column (10th Mountain infantry, Malaysian APCs and Pakistani tanks) reaches the
  trapped force at 01:55, in the last phase.
- Fire support: Little Bird gunships.
- The relief column comes on as two units: the 10th Mountain infantry, and the Malaysian APCs
  and Pakistani tanks together as **armoured carriers**.
- The wound tables are Somalia's (penetrating wounds).

It is drawn by `tools/maps/make_mogadishu_field.mjs`, from the plain facts of the US Army's
account and the published positions, not traced from any map or photograph.

**Wanat: the patrol base and the observation post, 13 July 2008** (`data/fields/wanat-2008.yaml`).
The field is 90 × 70 hexes, about 980 by 660 yards (900 by 600 m), north at the top.
- The patrol base is an open field about 110 by 330 yards (100 by 300 m), with loose wire at
  places along its edges. Observation Post Topside sits among rocks on the ridge east of it,
  with the brush-filled draw (woods) past the post's north side and a two-storey building
  north of it. The bazaar and hotel are to the north, and the village and its mosque on the
  terraces to the west. Beyond them are the Waygal river (water, with a crossing by the
  track) and the high ground on both sides.
- First light (dusk or dawn), still.
- United States (veteran, Interceptor vests, dug in):
  - the post's six paratroopers and its M240;
  - 2nd Platoon at the base's north end and its east side;
  - the Humvee guns and the TOW;
  - the engineers and mortar section;
  - the Afghan National Army platoon (green) on the west side;
  - later, the quick reaction forces: Chosen Company's 1st Platoon from Camp Blessing (06:01)
    and A Company's 3rd Platoon with the scouts (08:20).
- Insurgents (in cover): in the bazaar and hotel, the village and mosque, on the high ground
  west of the river, in the draw, and from the farmland and slopes east, with RPG teams and
  PKM machine guns.
- Fire support: the base's own 120 mm mortar, the 155 mm guns at Blessing, Apaches
  (gunships) and later A-10s, B-1Bs and F-15Es (fighter-bombers).
- The wound tables are Iraq and Afghanistan's (combat wounds, 2001-05).

It is drawn by `tools/maps/make_wanat_field.mjs`, from the plain facts of the US Army's
accounts, not traced from any map or photograph.

**Snakeshead Ridge and the abbey, 17-18 February 1944** (`data/fields/cassino-monastery-1944.yaml`)
and **the Poles at Point 593 and Phantom Ridge, 12 May 1944** (`data/fields/cassino-poles-1944.yaml`)
share one ground, drawn in `tools/maps/cassino_massif.mjs`: 200 × 150 hexes, about 2,190 by
1,420 yards (2,000 by 1,300 m), north at the top. Point 593 is at the upper left (high ground
and rock). Snakeshead Ridge runs from it to the south-east past Point 444 to the abbey's ruins
(rubble), and Phantom Ridge lies to the west. Steep slopes of scrub and broken rock (woods,
rough) and gullies lie between.
- February, a **dark night**:
  - the 4/6th Rajputana Rifles along the ridge for Point 593, with three Royal Sussex companies;
  - two hours later, the 1/9th and 1/2nd Gurkhas down the slopes for the abbey (by Point 445
    in *The Tiger Triumphs*, Point 444 in other accounts);
  - German paratroops (veteran, dug in) on the tops and in the ruins, with machine guns.
- May, a **dark night**: the 1st Carpathian Rifle Brigade's 2nd Battalion for Point 593 and
  its 1st Battalion along Snakeshead for Albaneta,
  and the 5th Kresowa Division for Phantom Ridge, against the paratroops on all three tops and
  in the abbey. Each Polish battalion comes on as four companies of equal strength (our split,
  as deep as the battalion stood), side by side across its front; the Kresowa's companies have a
  route to Phantom Ridge first (the 1st Battalion's Albaneta is not on this map, so it goes for
  593); the February battalions stay
  whole (see `docs/selfplay-review.md`).
- Fire support on both sides; the wound tables are the Second World War's (Owens).

**Cassino town and Castle Hill, 15 March 1944** (`data/fields/cassino-town-1944.yaml`). The
field is 140 × 120 hexes, about 1,530 by 1,140 yards (1,400 by 1,040 m), north at the top.
- The terrain:
  - the bombed town is **rubble**, with flooded craters (marsh) and the shell of the
    Continental Hotel (tall buildings);
  - Castle Hill and its ruined castle are at the upper left, and the massif's foot rises to
    the abbey along the left edge;
  - the road from Caira comes in from the north, with Route 6 and the station to the south
    and the Rapido on the right.
- The paratroops' cellars are **bunkers**, one under the middle of each paratroop unit's
  front.
- The New Zealanders:
  - the 25th Battalion goes into the town from the north and its D Company for Castle Hill,
    with the 24th following;
  - the 19th Armoured Regiment's Shermans are on the fields north of the town. Tanks cannot
    enter the rubble.
- German paratroops are in the cellars and ruins, at the hotel and by the station, with
  machine guns.
- Fire support: guns and fighter-bombers; German mortars and guns. Overcast and wet.

**Fox Hill at Toktong Pass, 27-28 November 1950** (`data/fields/foxhill-1950.yaml`). The field
is 150 × 120 hexes, about 1,640 by 1,140 yards (1,500 by 1,040 m), north at the top.
- The hill Fox Company held is in the middle (rocks on high ground, slopes of scrub pine and
  boulders). The road through the pass runs below it to the south. The heights are to the
  north, and a ridge lies across the road.
- **Bitter cold** (automatic weapons jam 25% more, +1 movement a hex). Snow lies, the wind
  is strong from the north-west, and it is a **dark night**.
- United States (dug in): Fox Company's three platoons round the crest, its heavy machine
  guns (laid on a **fixed line** up the slope to the heights), and the headquarters, mortars
  and road block.
- Chinese (veteran): a company from the heights to the north, companies fed in later against
  the 2nd and 3rd Platoons, and men walking down the road into the command post, with machine
  guns. The Marine official history (Montross and Canzona) opens the attack at about company
  strength, so the Chinese here are that night's, not the regiment's.
- Fire support: 105 mm howitzers at Hagaru-ri, the company's 60 mm mortars, Corsairs (by day
  only); Chinese mortars.
- The wound tables are Korea's (hospitalized wounded).

**Hill 504 and the valley at Kapyong, 23-24 April 1951** (`data/fields/kapyong-1951.yaml`). The
field is 220 × 160 hexes, about 2,410 by 1,520 yards (2,200 by 1,390 m), north at the top.
- In the middle is the valley: paddies (marsh, with dry patches), the road and the shallow
  river (marsh), B Company's knoll by the road, and Chuktun-ni at the bottom. Hill 504's summit
  and wooded spurs are on the right, and the hills towards 677 on the left.
- A **dark night**.
- United Nations: 3 RAR's A Company (north spur), D (summit), B (the knoll), C (reserve),
  machine guns and headquarters; a platoon of Shermans (**vehicles**) on dry ground by the
  road.
- Chinese (veteran): battalions down the valley, onto the north spur and round the west of the
  hill, with machine guns. The battalion round the west has a route down the west of the hill
  and down the valley to battalion headquarters at Chuktun-ni (where the phase note has the
  Chinese at about 22:00; the way is our reading).
- Fire support: the New Zealand 25-pounders and 3 RAR's mortars; Chinese mortars.

**Hill 931 on Heartbreak Ridge, October 1951** (`data/fields/heartbreak-1951.yaml`). The field
is 170 × 260 hexes, about 1,860 by 2,460 yards (1,700 by 2,250 m), north at the top.
- The narrow, rocky crest (high ground) runs north and south up the middle, with Hill 931 in
  the upper part and Hill 894 at the bottom. Spurs run off both sides, the slopes are steep,
  wooded and shattered, and the Mundung-ni valley (paddies, a stream and a dry track) lies
  along the west edge.
- The North Koreans' log-and-earth **bunkers** are dug into the crest. A fair day.
- United Nations: the 2nd Battalion, 23rd Infantry along the crest from 894 with the 3rd behind
  it, and the French Battalion coming in from the north at daylight (Hermes, *Truce Tent and
  Fighting Front*), and a company of tanks (**vehicles**) in the valley. The tanks came up the
  valley from 10 October, four days after 931 fell, so the GM can leave them off.
- North Koreans (veteran, dug in): on 931 and the crest either side, with machine guns.
- Fire support: division and corps artillery, 4.2-inch mortars, fighter-bombers; North Korean
  mortars and guns.

**Pork Chop Hill, 16-17 April 1953** (`data/fields/porkchop-1953.yaml`). The field is 160 × 130
hexes, about 1,750 by 1,240 yards (1,600 by 1,130 m), north at the top.
- Pork Chop is in the middle, ringed with **trenches**, sandbagged **bunkers** and barbed
  wire. Hill 200, with its trenches, is to the south-east and the main line's hills are along
  the bottom. The valleys between are old paddies, craters and wire.
- A **dark night**.
- United Nations (M1952 flak vests): E Company, 31st Infantry in the north and west trenches
  with its machine guns (laid on a **fixed line** down the north slope), L Company on Hill
  200, and K Company coming up from the main line; G Company of the 17th Infantry comes up at
  08:14.
- Chinese (veteran, submachine guns): a battalion up the north slope, a company from Old Baldy
  in the west, and machine guns.
- Fire support: the 7th Division's artillery ("flash fire" round the outposts), heavy
  howitzers, 4.2-inch mortars; Chinese mortars and guns.

**Hue: the new city, 4-6 February 1968** (`data/fields/hue-1968.yaml`). The field is 150 × 110
hexes, about 1,640 by 1,040 yards (1,500 by 950 m), north at the top.
- The Perfume River runs along the top, with its bridge into the Citadel, and Le Loi street
  and a park along the bank. Highway 1 comes up from the An Cuu bridge on the Phu Cam canal
  along the bottom.
- Between them are blocks of houses (**buildings**, with **rubble** where shells fell) and the
  stone public buildings (**tall buildings**): the MACV compound, the university, the
  provincial headquarters, the Treasury, the hospital and the prison.
- Cold drizzle and low cloud.
- United States: three companies of the 2nd Battalion, 5th Marines and A Company, 1st
  Marines, attacking east, with machine guns, two M48 **tanks** on Highway 1 and two **Ontos**
  (106 mm recoilless rifles) with H Company.
- North Vietnamese (veteran, in cover): the provincial headquarters, the Treasury, the
  hospital and the prison held (a strongpoint, a **bunker**, under the middle of the front
  in the Treasury, the hospital and the prison), with RPG teams that can knock out tanks,
  and machine guns.
- A run goes on for the account's length (`ends` 3,301: 07:00 on 4 February to the flag over
  the provincial headquarters a little past 14:00 on the 6th), so at most 1,200 exchanges.
- Fire support: Marine 81 mm mortars and 105 mm howitzers (held back at first to spare the
  city); North Vietnamese mortars, rockets and guns.

**Hill 861A, Khe Sanh, 5 February 1968** (`data/fields/khesanh-1968.yaml`). The field is
140 × 120 hexes, about 1,530 by 1,140 yards (1,400 by 1,040 m), north at the top.
- The knoll is in the middle, ringed with **trenches**, **bunkers** and barbed wire. The ridge
  runs down to the south-west towards Hill 861. The slopes are cleared to elephant grass and
  craters, with jungle beyond.
- **Fog** on a **dark night**.
- United States (flak vests, in the trenches): E Company, 2nd Battalion, 26th Marines on the
  north and flanks, its reserve platoon, and its machine guns (laid on a **fixed line**
  through the north wire). The 05:00 counter-attack was Lieutenant Shanley's 1st Platoon, from
  the alternate positions it had been pushed back to (Shulimson et al., *The Defining Year*).
- North Vietnamese (veteran): about 200 through the north wire (here a battalion of 400), and
  machine guns.
- Fire support: the base's howitzers and 4.2-inch mortars and the guns on 881 South; North
  Vietnamese mortars, rockets and guns.

**Hill 875, Dak To, 19 November 1967** (`data/fields/dakto-1967.yaml`). The field is 120 × 140
hexes, about 1,310 by 1,330 yards (1,200 by 1,210 m), north at the top.
- The crest is below the middle, ringed with **bunkers** and two lines of **trenches**. The
  north slope above it is shattered bamboo and fallen trees, with jungle all round.
- Fair and dry.
- United States (veteran paratroopers, flak vests): two companies of the 2nd Battalion, 503rd
  Infantry going up the north slope, a third cutting a landing zone behind them, and
  machine guns.
- North Vietnamese (veteran, dug in): the 174th Regiment on the crest and in the lower
  trenches, with machine guns, and a company coming in behind the Americans from the west.
- Fire support: howitzers at the fire bases, fighter-bombers and the battalion's mortars;
  North Vietnamese mortars.

**Hamburger Hill (Dong Ap Bia), 20 May 1969** (`data/fields/hamburger-1969.yaml`). The field
is 140 × 140 hexes, about 1,530 by 1,330 yards (1,400 by 1,210 m), north at the top.
- The summit is in the middle, stripped to stumps and craters, with three tiers of
  **bunkers** down its slopes. Spurs run down to the north-west and the south, with blasted
  jungle and bamboo below.
- Overcast, the slopes mud after days of rain.
- United States and ARVN: the 3rd Battalion, 187th Infantry up the north-west spur, the 1st
  Battalion, 506th Infantry up the south spur, and the ARVN 2nd Battalion, 3rd Regiment from
  the east.
- North Vietnamese (veteran, dug in): the 29th Regiment's survivors on the summit and in the
  bunkers, with machine guns.
- Fire support: howitzers at the fire bases, fighter-bombers and battalion mortars; North
  Vietnamese mortars.

**Darwin Hill, Goose Green, 28 May 1982** (`data/fields/goosegreen-1982.yaml`). The field is
140 × 110 hexes, about 1,530 by 1,040 yards (1,400 by 950 m), north at the top.
- Darwin ridge runs across the middle, with the Argentine **trenches** along its crest, under
  the two groups of platoons, and **bunkers** in the middle of each and under the machine guns. The gorse gully lies below Darwin Hill on the right, and a gorse hedge crosses
  the open slope.
- Darwin settlement sits by its inlet of Choiseul Sound in the lower right, with Brenton Loch
  along the left.
- **Dawn**, overcast, a cold westerly.
- British (veteran paratroopers): A Company pinned in the gully, B Company on the open slope,
  the battalion headquarters, D Company coming up, and machine guns.
- Argentines (green conscripts, dug in): two groups of platoons in the ridge trenches,
  machine guns, and a reserve at Darwin.
- Fire support: three 105 mm light guns and 81 mm mortars; Argentine pack howitzers and
  120 mm mortars.

**Mount Tumbledown, 13-14 June 1982** (`data/fields/tumbledown-1982.yaml`). The field is
220 × 120 hexes, about 2,410 by 1,140 yards (2,200 by 1,040 m), north at the top.
- The long rocky ridge runs across the middle: its western end on the left, the summit
  **crags** (rough ground and high ground) in the middle, the eastern end on the right. Steep
  **slopes** fall to Moody Brook along the top and to peat and bog along the bottom.
- The Argentine **trenches** run along the crest east of the summit and under the platoons
  that held it, with **bunkers** in the summit crags under the 4th Platoon, its machine guns
  and the RI 4 platoon.
- **Night** and falling snow, with snow and mud on the ground (`light: night`; the moon rose at
  22:45, behind cloud).
- British (regular): G Company on the empty western end, Left Flank among the crags (pinned, gone
  to ground), the battalion's machine guns, and Right Flank, which comes on at the phase
  *Bayonets* to go round.
- Argentines: the marines of N Company, BIM 5 (regular, dug in): the 4th Platoon at the summit,
  its heavy machine guns and snipers with **night sights** (`nv: starlight`; the kind is not
  recorded), the engineers' platoon and the 3rd Platoon on the north; army platoons of RI 4 and
  RI 12 (green), and RI 6's counter-attack platoon, which comes on at about 02:00.
- Fire support: British 105 mm light guns, a frigate's 4.5-inch gun and 81 mm mortars; the
  marines' 60 and 81 mm mortars and pack howitzers.
- Orders (`data/orders.yaml`): the 4th Platoon and the RI 4 platoon hold; the rest fall back
  east at exchange 526 (07:15), when BIM 5 was ordered back to Sapper Hill.

**73 Easting: Eagle Troop crests the rise, 26 February 1991** (`data/fields/easting73-1991.yaml`).
The field is 200 × 120 hexes, about 2,190 by 1,310 yards (2,000 by 1,200 m), north at the top,
from about 72.2 to 74.2 Easting on the military grid.
- Flat, hard desert, stony in places. A low rise (**high ground**, a few metres) runs north
  to south across the left middle; the Iraqi **trenches** lie on its reverse (east) slope,
  under the infantry and the RPG teams, with a **bunker** in the middle of each. The high ground about 74 Easting is on the right.
- A **sandstorm**: sight cut to 440 yards (400 m), but thermal sights see to about 985 yards
  (900 m) through it; a strong north-westerly; no aircraft fly. Daylight, late afternoon.
- Eagle Troop's M1A1s have the thermal fire control and **composite armour**; the T-72s the
  war's laser rangefinder.
- Coalition (veteran, thermal sights): Eagle Troop of the 2nd Armored Cavalry Regiment, its
  nine M1A1 **tanks** in two groups at the front and its M3 Bradleys (**infantry fighting
  vehicles**) in two scout platoons on the flanks behind.
- Iraqis (regular, no night sights): two groups of Tawakalna T-72s dug in behind the rise,
  BMP-1s, infantry in the trenches with **RPG** teams, **lorries** behind the position, and
  eighteen T-72s on the high ground beyond.
- Fire support: Eagle Troop's two mortars and 2nd Squadron's howitzer battery; Tawakalna
  guns.
- No minefields: the accounts we used name none on this ground. The buildings where Eagle
  first took fire lie further west, on the campaign map.

**Grozny: the railway station, 31 December 1994** (`data/fields/grozny-1995.yaml`). The field
is 140 × 110 hexes, about 1,530 by 1,040 yards (1,400 by 950 m), north at the top.
- The station building is in the middle, with its square to the north and the platforms,
  tracks and freight yard to the south.
- Older houses (**buildings**) stand round the station, with five- and nine-storey apartment
  blocks (**tall buildings**) beyond and streets with wrecks and **rubble** between.
- **Dusk** on a winter afternoon (about 16:30), and from exchange 31 (about 17:05) a **dark
  night**: overcast, the moon a day from new (worked out for the place and day).
- The objective is the Chechens': the night was their attack on the station the battalion
  had taken that afternoon. A run goes on for the account's length (`ends` 1,531: 16:30 on 31
  December to the survivors' break-out about 18:00 the next day), so at most 1,200 exchanges.
- Russians (green): the 131st Brigade's 1st Battalion in the station and the freight yard,
  with its **infantry fighting vehicles** (BMPs) and **tanks** parked in the square.
- Chechens (veteran, in cover): **RPG** teams in the buildings on three sides of the square
  that can knock out the armour, fighters to the north and south, and machine guns.
- Fire support: Russian artillery and mortars; Chechen mortars.

**The Debecka crossroads, 6 April 2003** (`data/fields/debecka-2003.yaml`). The field is
150 × 290 hexes, about 1,640 by 2,740 yards (1,500 by 2,500 m), north at the top.
- Press Hill, the second ridge, at the top; the low ridge the teams called **the Alamo** just
  below it; the crossroads, with an earth berm along Highway 2, 900 m south of it; the edge of
  Debecka (**buildings**) south-east of the crossroads; open plain to the south edge.
- Overcast and hazy (the accounts' low cloud and haze), by day.
- The objective is the Iraqis': the field is their counter-attack on the Alamo. They come on at
  the south edge, about 2 km off, as the accounts have them first seen 2 km away.
- Americans and Kurds: ODAs 391 and 392's gun trucks (**lorries** with heavy machine guns), their
  **Javelin** teams (`atgm`, with thermal sights), the combat controllers (`fac`) and the
  intelligence men, all veteran, in Interceptor vests; the Peshmerga with the teams and those
  with the command vehicles at Press Hill (regular, unarmoured). A **supply dump** behind Press
  Hill for the "War Pigs" that brought ammunition forward.
- Iraqis: the official history's force: five **T-55s** (aiming by a stadia reticle, `fc: stadia`,
  not the war's thermal fire control, which was the coalition's), four **MT-LBs**, troop trucks and
  command vehicles, and motorised infantry (green).
- Fire support: the teams' 60 mm mortars and Navy fighter-bombers; two Iraqi 120 mm mortars.
- The friendly-fire bomb on Press Hill is a phase note, not a rule: the GM takes its losses
  from the account.
- Orders: the two teams hold the Alamo.

**Fallujah: into the Jolan, 9 November 2004** (`data/fields/fallujah-2004.yaml`). The field is
140 × 120 hexes, about 1,530 by 1,140 yards (1,400 by 1,040 m), north at the top.
- Apartment blocks (**tall buildings**) and the railway run across the top, and the
  Euphrates and its palms down the left. The main street runs south from the railway.
- Everywhere else are the Jolan's lanes and walled houses (**buildings**, with **rubble**),
  with the park and four mosques among them.
- Overcast.
- Coalition (veteran, Interceptor armour): two Marine companies astride the main street,
  with machine guns, and 2-7 Cavalry's M1A1 **tanks** and Bradley **infantry fighting vehicles**
  leading down it.
- Insurgents (in cover): fighters in the houses and a mosque, **RPG** teams by the main
  street and in the park, and machine guns.
- Fire support: 155 mm howitzers, mortars and close air support; insurgent mortars.

**Combat Outpost Keating, 3 October 2009** (`data/fields/keating-2009.yaml`). The field is
120 × 110 hexes, about 1,310 by 1,040 yards (1,200 by 950 m), north at the top.
- The outpost sits on its flat in the middle, its buildings and trucks ringed with barbed
  wire.
- The Landay-Sin runs down the left, with the bridge to Urmul (**buildings**) across it. The
  Kushtoz comes in from the east below the outpost.
- Steep slopes of rock, scrub and deodar rise on every side.
- First light (**dawn**).
- Coalition: B Troop, 3-61 Cavalry (veteran, Interceptor armour) round the barracks and
  command post, at the guard posts and in the trucks with its machine guns, and Afghan
  soldiers on the east side.
- Insurgents (in cover): fighters on the north, east and south slopes and in Urmul, an RPG
  team, and machine guns.
- Fire support: the outpost's mortars, Apaches, and jets later in the morning; insurgent
  mortars and recoilless rifles.
- Observation Post Fritsche is off this field.

The **Battlefield** picker lists the battlefields under their periods, oldest first, as the
travel map's **Map** picker does: a battlefield's own `period` (optional), else its wound
table's conflict.

**A battlefield file** has an `id` and `name`, `sides` (two names), `table`, `size`
([cols, rows]) and `weather`. Its `ground` is rows of one letter per hex: `.` open, `r`
rough, `F` woods, `o` scrub and orchard, `m` marsh, `s` slope, `h` high ground, `T` buildings, `B` tall buildings, `x` rubble, `w` water (the `key` of each kind in `data/units.yaml`).
`up` (optional) is the compass point at the top of the map, if not north, and `weather` may
give the wind's direction as `dir` (where it blows from). `travel` (optional) is `{map, place, within, sides}`: the travel map and place it belongs
to, how many hexes from the place count as there, and the travel-map side names that stand
with each army. `works` has `hexes`, a list of `{type, at: [hexes]}`, and `edges`, a list of `{type, at:
[[hex, hex], ...]}` with the first hex the high or inner side. `units` lists `{name, side
(0 or 1), men, quality, weapon, kit, formation, width, pos (the middle of the front row),
facing, mounted}`. `support` (optional) lists each side's batteries on call, `{name, side
(0 or 1), kind (mortar, field, howitzer, tank, autocannon, fighter_bomber or gunship), tubes}`: loading the field fills the Fire support
panel. `python3 -m gravewounds check` makes sure every unit fits where it stands.

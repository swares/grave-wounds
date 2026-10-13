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
| Dug in: gone to ground or in a bunker | +10 |
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

- Turning the facing one step (60°) costs 1 hex for every 2 hexes of front (at least 1),
  plus the ground its ends sweep over: the worst extra going of the hexes it comes to stand
  on (+1 for rough ground or woods, +2 for marsh or rubble).
- A unit cannot pass through other units' hexes.
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

**Range** is the weapon's battle-map range in 2-yard (2 m) hexes, divided by 5 for field hexes:
a longbow's long range of about 270 yards (250 m) is 25 field hexes.

The page keeps the battle in the browser, so it can be closed and reopened. *New battle*
starts again from the starting units.

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
3. **To camp.** The rest are carried to their force's camp and heal on the wound track,
   where wound fever can still take them (see [travel.md](travel.md), *The wounded*).

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

A **leader** gives his unit +10 morale while he is up, and −20 once he is down. A unit with
a hero still up shows a star on the map. The heroes' list shows each one's attack and defence
after his wounds, his state and his Blood.

After the battle, **Heroes' wounds to the roller** puts each wound on his record in the
wound roller (with its bleeding, pain and clock), and marks him out of the fight if he went
down, and his Blood where the field left it.

**First aid.** In a quiet exchange his comrades bind his worst-bleeding wound from this
battle: arterial to heavy, heavy to seeping, seeping to none. A quiet exchange is one in
which his unit is not in contact, not under fire and loses no one. It works 60% of the
time, and he may be up or down. The log says when a hero is bandaged, and the roller takes
the wound as it was left (marked "bind (on the field)"). `python3 -m gravewounds units` shows how heroes fare:

| A hero leading billmen in jacks, until one side breaks | Wounded | Down | Killed | Men he puts down |
|---|---|---|---|---|
| Knight in mail | 50% | 30% | 0% | 0.2 |
| Knight in plate | 20% | 4% | 0% | 0.3 |
| Champion, no armour | 74% | 54% | 2% | 0.2 |

A fight of this kind lasts a quarter of an hour or more, long enough for a hero's wounds to bleed him
down: about one wounded hero in two ends the fight down.

A hero matters most through morale and through what happens to him: in a press of hundreds,
one man fells few. The numbers are in `data/units.yaml` (`heroes`).

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
  the longer range. Woods, rough ground and marsh stop it.

What the numbers give (`python3 -m gravewounds units`, 1000 runs, the First World War table),
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
    not fly in fog, storm, heavy snow or a blizzard, and fighter-bombers not on a moonlit or
    dark night: a mission called then waits, and flies when it clears. The support list shows
    **grounded** and why. They drop no smoke and carry no illumination.
- **Creeping barrage**: before calling, pick **Creep** (1 to 3 hexes a lift), **Each line**
  (1 to 4 exchanges on each line before it lifts), **Lines** (how many lines it fires on, or
  until it leaves the map) and **Towards** (the way most of the side's units face, or a
  direction on the map). That is the fire plan: the mission keeps firing, lifting its aim
  on by the timetable, ahead of an advance that keeps to the same timetable. **Then** gives
  the plan a second leg after the last line: the same lift, on the same way or turned left
  or right, for its own number of lines. It ends after its last line, when it leaves the map,
  or on **Stop**.
- **Counter-battery**: a battery that has fired is located (◉ in the list), by its flashes
  and sound. On its own side's move a field gun or howitzer battery can then fire on it
  instead of on a hex (**Counter-battery…**), with no one needing to see it. Each shell
  lands among its guns at 2% (field guns) or 4% (heavy howitzers), knocking out a tube and
  striking 2 of its crew; at three times that it bursts close by and strikes one. Mortars
  cannot reach. Struck crewmen roll wounds as men struck by shellfire, and those put down
  are lost to the battery: it fires only the tubes it has men for (2 a mortar, 3 a field
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

One minute of fire on the middle of 100 regular riflemen (`python3 -m gravewounds units`, 1000
runs, the First World War table):

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
- The battery's guns get their rounds first, then each section in order.
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
- **Seeing:** woods and buildings block the sight of men calling fire and of aimed shots
  (*Sight through cover*), unless they stand higher than them: from high ground or a tall
  building a man sees over woods and lower roofs, and from a slope over woods and houses on
  the flat. A man sees one hex into cover, and out of it from its edge.
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
  open or high ground 1, rough ground or a slope 2, woods 3. They cannot enter marsh,
  buildings, tall buildings, rubble or water, so in a town they keep to the streets. Works
  and deep going cost them what they cost men.
- **Their machine guns** fire as a machine-gun team's, about a gun a vehicle.
- **Main guns** fire each exchange at the nearest enemy in range, in sight (as guns are: the
  weather and the light) and in front, enemy vehicles first, with a clear line of fire. A
  vehicle whose gun is out does not fire it.

  | Kind | Range | Rounds a vehicle | Hits a vehicle (to 20 / mid / full range) | At men |
  |---|---|---|---|---|
  | Tank | 100 hexes (1,090 yards, 1,000 m) | 1 | 75% / 50% (50 hexes) / 25% | bursts as a tank's round on call (25% in the hex, 5% next to it) |
  | Infantry fighting vehicle (autocannon) | 80 hexes (875 yards, 800 m) | 2 | 70% / 45% (40 hexes) / 20% | bursts as an autocannon round (20% in the hex) |

- **Armour.** Small arms cannot hurt a vehicle, and men armed only with them do not shoot at
  one. No one strikes a vehicle hand to hand, or is struck by it.

  | A hit from | Tank (heavy armour) | Infantry fighting vehicle or carrier (light) |
  |---|---|---|
  | A rocket (RPG, bazooka, recoilless rifle) | 15% | 50% |
  | A guided missile | 60% | 90% |
  | A main gun | 35% | 75% |

  Those are the chances that a hit knocks the vehicle out. A hit into its **flank** counts
  twice that, and into its **rear** three times, to 100% at most. Which it is depends on
  where the shooter stands, by the vehicle unit's facing (the front is the two directions
  either side of its arrow).
- **Anti-armour weapons:** the **RPG**, the **bazooka** (and Panzerschreck, for the Second
  World War and Korea), the **recoilless rifle** (Korea and Vietnam) and the **guided
  missile** (the Falklands, the Gulf, Chechnya, Iraq and Afghanistan). A rocket, bazooka or
  recoilless team fires a round for every four men each exchange, and a missile team one for
  every ten. Every round is aimed, and range, cover and the weather count as for shots at men.
- **Damage.** A hit that does not knock a vehicle out immobilises it at 25%, or at the next
  15% puts its main gun out of action. A unit with an immobilised vehicle cannot move (it can
  still turn) until it **abandons** them. Their crews then leave the fight unhurt.
- **Shells and bombs** bursting in a vehicle's own hex knock it out at the firing kind's knock
  %: a heavy howitzer 2%, fighter-bombers 15%. Light armour is three times as likely to go.
- **Knocked out.** A knocked-out vehicle's crew are out of the fight. Each is struck at 50% and
  rolls a wound as one hit by shellfire; the rest have bailed out. Vehicle units check morale
  like any other.
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

## Landing by air

For helicopter landings (Vietnam and later). The numbers are in `heliborne` in
`data/units.yaml`.

- **Landing zones.** A battlefield can mark landing zones, shown as a dashed ring with an H.
  Before the battle the GM can mark or clear one with **Clicking the map: Mark or clear a
  landing zone**.
- **Coming in by air.** With a landing zone marked, **Add a unit** offers **By air at** and
  a zone. The unit waits in the air (listed under the units), and at the end of each
  exchange up to 80 men land at each zone, the lifts in the order they were called. A lift
  lands two ranks deep. The unit's first men come down on the zone, or the nearest spot
  within 4 hexes where they fit; later lifts join them, filling the unit out. It can move
  in the next exchange. A battlefield's units can start in the air too (`lands`).
- **Blocked.** No one lands while an enemy unit stands within 2 hexes of the zone, or where
  there is no room: the lift is waved off and tries again next exchange.
- **A hot landing zone.** If any enemy unit (not broken) could shoot at the zone's hex, with
  its weapon in range and in sight (in the weather and the light), the zone is hot. Each man
  landing is struck at 10% and rolls a wound as one struck by shellfire, and those put down
  are down at once.
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

It is drawn the same way, by `tools/maps/make_towton_field.mjs`. The two battlefields share
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
  up at the north-east corner.
- Pikemen fight with the spear's numbers, the nearest the Thirty Years' War tables offer.
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
  (narrow fronts, many ranks), Werlé's 3,500 in reserve, 1,500 Polish lancers and hussars
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
- Fair. Most of the fighting was at night, which the field map does not have: the GM may
  treat it as fog.
- The evening's opening: Scott's 800 in front of the hill, Jesup's 25th working round the
  British left, Towson's guns, and Ripley's brigade and Porter's volunteers coming up behind.
- On the hill: five British guns at the churchyard, the 89th, the 8th and 41st, the
  Incorporated Militia, the Glengarry Light Infantry on the west, the 19th Light Dragoons, and
  Drummond's 1,000 coming up behind the crest.
- The wound tables are the War of 1812's.

It is drawn by `tools/maps/make_lundys_lane_field.mjs`.

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
  men rallied behind, and Stuart's horse to the south-west.
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
- The relief column with its mountain howitzer, which came in the early afternoon, is not on
  the map: on its move the Army side can bring it on with **Add a unit**.
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
  behind, and a battalion of Infantry Regiment 86 coming out of the woods to the north-east.
- Fire support: six British 18-pounders against twelve German 77 mm field guns and six field
  howitzers.
- The wound tables are the First World War's.

It is drawn by `tools/maps/make_mons_field.mjs`.

**Hill 700, Bougainville, 8-12 March 1944** (`data/fields/bougainville-1944.yaml`). The field
is 120 × 100 hexes, about 1,310 yards (1,200 m) east to west and 950 yards (870 m) north to
south, north at the top: the ridge across the middle.
- Hill 700's crest (high ground) with a saddle between two knobs; a line of pillboxes
  (bunkers: −50% to shots at men in them) on the forward crest, a belt of barbed wire below
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
  short of the town, with the 3rd Reconnaissance Troop's platoon behind them on the road.
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
  round the west, in column on the highway, and coming down the railroad, with machine guns.
- Fire support: American 105 mm howitzers, 4.2-inch and 60 mm mortars; North Korean mortars and
  the T-34s of the 107th Tank Regiment firing over open sights. There are no vehicle rules: the
  tanks are on call as fire support, and the recoilless rifles and bazookas fight as riflemen.
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
  reserve.
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
- Fire support: Little Bird gunships.
- There are no vehicle rules: the relief column can be brought on as infantry with **Add a
  unit**.
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
  - the Afghan National Army platoon (green) on the west side.
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
  - the 4/6th Rajputana Rifles along the ridge for Point 593, with the Royal Sussex in reserve;
  - the 1/9th and 1/2nd Gurkhas down the slopes for Point 444 and the abbey's hill;
  - German paratroops (veteran, dug in) on the tops and in the ruins, with machine guns.
- May, a **dark night**: the 3rd Carpathian Rifle Division for Point 593 and along Snakeshead,
  and the 5th Kresowa Division for Phantom Ridge, against the paratroops on all three tops and
  in the abbey.
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
- The paratroops' cellars are **bunkers**.
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
- Chinese (veteran): battalions from the heights to the north, from the north-east and across
  the road, with machine guns.
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
- Chinese (veteran): battalions down the valley, onto the north spur and round the east of the
  hill, with machine guns.
- Fire support: the New Zealand 25-pounders and 3 RAR's mortars; Chinese mortars.

**Hill 931 on Heartbreak Ridge, October 1951** (`data/fields/heartbreak-1951.yaml`). The field
is 170 × 260 hexes, about 1,860 by 2,460 yards (1,700 by 2,250 m), north at the top.
- The narrow, rocky crest (high ground) runs north and south up the middle, with Hill 931 in
  the upper part and Hill 894 at the bottom. Spurs run off both sides, the slopes are steep,
  wooded and shattered, and the Mundung-ni valley (paddies, a stream and a dry track) lies
  along the west edge.
- The North Koreans' log-and-earth **bunkers** are dug into the crest. A fair day.
- United Nations: the 2nd Battalion, 23rd Infantry along the crest from 894, the French
  Battalion up the east spur, the 1st Battalion, 23rd Infantry up the west spur, and a company of
  tanks (**vehicles**) in the valley.
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
  200, and K Company coming up from the main line.
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
  Marines, attacking east, with machine guns and four M48 **tanks** on Highway 1.
- North Vietnamese (veteran, in cover): the provincial headquarters, the Treasury, the
  hospital and the prison held, with RPG teams that can knock out tanks, and machine guns.
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
  through the north wire).
- North Vietnamese (veteran): a battalion through the north wire, a company from the
  north-west, and machine guns.
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
- Darwin ridge runs across the middle, with the Argentine **trenches** and **bunkers** along
  its crest. The gorse gully lies below Darwin Hill on the right, and a gorse hedge crosses
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

**Grozny: the railway station, 31 December 1994** (`data/fields/grozny-1995.yaml`). The field
is 140 × 110 hexes, about 1,530 by 1,040 yards (1,400 by 950 m), north at the top.
- The station building is in the middle, with its square to the north and the platforms,
  tracks and freight yard to the south.
- Older houses (**buildings**) stand round the station, with five- and nine-storey apartment
  blocks (**tall buildings**) beyond and streets with wrecks and **rubble** between.
- **Dusk** on a winter afternoon.
- Russians (green): the 131st Brigade's 1st Battalion in the station and the freight yard,
  with its **infantry fighting vehicles** (BMPs) and **tanks** parked in the square.
- Chechens (veteran, in cover): **RPG** teams in the buildings on three sides of the square
  that can knock out the armour, fighters to the north and south, and machine guns.
- Fire support: Russian artillery and mortars; Chechen mortars.

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
rough, `F` woods, `m` marsh, `h` high ground, `T` buildings, `B` tall buildings, `x` rubble, `w` water (the `key` of each kind in `data/units.yaml`).
`up` (optional) is the compass point at the top of the map, if not north, and `weather` may
give the wind's direction as `dir` (where it blows from). `travel` (optional) is `{map, place, within, sides}`: the travel map and place it belongs
to, how many hexes from the place count as there, and the travel-map side names that stand
with each army. `works` has `hexes`, a list of `{type, at: [hexes]}`, and `edges`, a list of `{type, at:
[[hex, hex], ...]}` with the first hex the high or inner side. `units` lists `{name, side
(0 or 1), men, quality, weapon, kit, formation, width, pos (the middle of the front row),
facing, mounted}`. `support` (optional) lists each side's batteries on call, `{name, side
(0 or 1), kind (mortar, field or howitzer), tubes}`: loading the field fills the Fire support
panel. `python3 -m gravewounds check` makes sure every unit fits where it stands.

# Battles of hundreds {#battle}

When hundreds fight, rolling for every man every round would take all night. On the
[field map](field.html) the rank and file fight as **units**, resolved a minute at a time
through the same wound tables, and the team fights among them as **heroes** with the full
rules of [the fight](#fight).

## The field map {#field-map}

The field map is a grid of hexes {{f_hex}} across. One **exchange** is about a minute, some
{{f_rounds}} rounds. Each exchange, one side moves, then the other, and then every melee and
volley is resolved at once.

A **unit** is a block of hexes: its front row along its line, its men in rows behind. It
has a number of men, a quality (green, regular or veteran, as in
[How to play](#characteristics)), a weapon, armour and a **formation**:

{{table:formations}}

Mounted units move {{f_mounted}} hexes. A unit that ends its move touching the enemy may have
come up to {{f_charge_move}} times its move: a **charge**. A unit in contact cannot move. Units
cannot pass through each other, except that a steady unit charging may pass through its own
side's men to reach the enemy; the units it passes through lose half their move that exchange.

**Seeing.** To aim, to lay a gun on a target or to call fire, a man must see it. Woods and
buildings between block his sight unless they stand lower than he does; he sees
{{f_see_into}} hex into them, and out of them from their edge. Ground between that stands
higher than both him and his target is **dead ground**: a rise hides each from the other.
A crest within {{f_crest}} hex of either man does not count, so a man or a tank pulled up
just behind it sees over it and is seen, and a man on the top sees down both slopes.

## An exchange {#exchange}

1. **Who strikes.** In melee, the front rank of each hex touching the enemy, and one more
   rank for each hex of the weapon's reach past the first (spears and bills strike from two
   ranks, the pike from three). With missiles, the men who have the target in range.
2. **How many blows tell.** Most of a minute in a press is shoving and watching for an
   opening: about one striking man in {{f_tempo}} makes a real attempt each exchange. A
   longbowman looses {{f_bow_rate}} arrows a minute, and about one shot in {{f_aimed}} is aimed at
   a man rather than loosed at the mass.
3. **Each attempt is one attack**, at the unit's quality, exactly as in [the fight](#turn):
   +{{f_flank}} from the flank and +{{f_rear}} from the rear (and no parry from either),
   +{{f_charge}} and twice as many attempts for a mounted charge in its first exchange, −{{f_shaken}} for a shaken unit, +{{f_pikes}} for
   pikes in close order against horse to their front; range, weather and cover come off
   missiles. A tired unit loses its [fatigue](#fatigue) level's penalty off its attack and
   its parry.
4. **The wound** is rolled as for one man. A light wound or a graze: he fights on. Serious
   or critical: a stop check, and failing it puts him **down**. A wound that kills within
   rounds kills. A module can change who goes down: [Modern fire](#modern-down) puts more men
   down.
5. **Morale**, below; then the next exchange.

**Fatigue.** A unit tires as a character does. Each exchange it fights hand to hand counts
one toil, and so does each hex it goes in deep mud or snow. After 12 toil in heavy armour,
20 in medium, or 30 in light, it is a fatigue step worse, to Exhausted at most, and stays
so for the battle. Shooting costs none, and vehicles don't tire.

**Quick-play blows (a GM's choice).** Rolling every blow is exact but slow on a table. To
roll a group's blows in one go: count the tries as above, then find the men down per 100
tries in the era's quick-play chart (in the tables) for the weapon against the target's
armour, at the attack after all modifiers, times the quality factor printed with it, times
(1 − parry × 0.9) if the target can parry. Tries × that ÷ 100 is the average; roll d100 on
the spread chart for the men down. The field page's *Quick-play sheet* prints the exact
figures for the units on the field, and ticking *quick-play blows* makes the page roll this
way too. Blows that fall on a hero are still rolled one at a time. It gives the same losses
on average, with the same spread, as rolling every blow. Shellfire goes the same way (see
[fire support](#support)): one roll for one battery's fire on one unit.

## Morale and the rout {#morale}

After an exchange a unit checks its morale if it lost the exchange in contact (more of its
men down than it put down), has {{f_trigger}} of its men down, lost {{f_shock}} of its men in
this exchange, or was struck in the flank or rear. A unit of a side holding its ground (its
commander's stance) that stands in a position (in a bunker, dug in, behind works, in buildings or rubble, or lying down in woods or scrub), not
flanked, has lost the exchange only if it lost more men hand to hand than it put down hand to
hand, and counts its losses only in an exchange it lost men: a garrison does not break from the
passing of time, nor from fire it cannot answer. It rolls d100 against its quality's Nerve:

{{table:morale}}

- **Steady, fails:** it is **shaken**: it fights at −{{f_shaken}} and cannot charge. Failing
  by more than {{f_shaken_by}} while flanked, or with half its men down, it breaks at once. A unit
  of a holding side in a position is never flanked: its men there face every way.
- **Shaken, fails:** it **breaks**.
- **Shaken, passes out of contact:** it rallies to steady.

A broken unit runs. Every enemy man in reach strikes it at +{{f_rout}}, with no parry and
twice as often, as long as the pursuers keep up. This is where most of a battle's dead
fell, as at Towton and Agincourt, where the beaten side lost far more men in flight than in
the press.

On the field map it runs straight back as far as it can move. Its own side's units do not
stop it: it runs on through them to the first clear ground beyond, and each unit it runs
through loses half its move that exchange as the fugitives push through its ranks.

A broken unit with nowhere to run and an enemy touching it **surrenders** instead: the war's
quarter of its men standing are taken prisoner, the rest killed. Some armies fought to the end
and did not (the battlefield says so): they are struck as before.

!!! gm "For the GM"
    A melee of ten or twenty minutes, decided by morale more than by wounds, with the beaten
    side losing most of its men in the rout: that is the shape the records show, and the
    page is tuned to give it. Let the players' heroes break a line rather than kill it.

## Ammunition {#ammunition}

A unit that shoots carries only so much. Its load is counted in **exchanges of fire**: the
rounds, arrows or bolts a man carries (a machine gun's belts, for a gun), over the rate it
fires at, times {{ammo_burn}}% (men do not fire every round they could). Longbowmen have about
{{ammo_bow}} exchanges of shooting, riflemen of 1914-53 about {{ammo_rifle}}, a machine gun about
{{ammo_mg}}. Vehicles and guns count their own rounds.

- **Running low.** Each exchange it shoots uses one. At {{ammo_low}}% of a full load or less it
  shoots at half rate; with none it cannot shoot at all, still fights hand to hand, and has
  {{ammo_morale}} on morale.
- **Resupply.** An exchange out of contact, neither moving nor firing, within {{ammo_reach}}
  hexes of a supply source: its side's map edge (behind the way most of its men face), a
  lorry or armoured carrier of its side, or a **supply dump**. The GM places dumps before the
  battle (a battlefield may come with its own, as the stores in RIR 119's dugouts at
  Beaumont-Hamel); from the Second World War on, an **air drop** called on a side's move lands as a
  dump at the end of the exchange, a little off the mark, and from Vietnam on a helicopter
  can set one down on a landing zone ([Landing by air](#landing)).
- **The enemy commander** resupplies a unit that is out, or low with no enemy in its
  range, when a source is in reach. Attacking, a unit out of ammunition with none in reach
  falls back toward its edge; holding, it stays and fights hand to hand.

## Heroes {#heroes}

A team's characters go with units as **heroes**: in the front rank, shooting with it, or
behind it. A hero in the front makes {{f_tempo_h}} times a ranker's attempts with his own
attack, and blows on his unit's front fall on him {{f_exposure}} times as often as on a ranker
there. His wounds use the full rules, his own Blood and his own stop check. Two front-rank
heroes in contact fight each other: {{f_duel}} attempts each an exchange, instead of at the
rankers.

**Rank.** A hero brings his rank from the team builder. Leading his unit and up, each rank step
above the lowest adds {{f_rank_step}} to its morale (at most {{f_rank_cap}}). An officer (his rank
pays three times a private's or more) draws fire: the blows that fall on his unit's heroes fall on
him {{f_officer}} times as often. What a hero does is counted for the roller: his hits tick his
weapon skill, two or more enemies put down are a deed, and a Plains man's close-combat downs are
coups ({{f_coup}} honours each).

His wounds slow him as in [Wounds](#wounds): an arm hurt stops a two-handed weapon, and a
lamed hero halves his unit's move. In a quiet exchange his friends give first aid: the best
Leechcraft in the unit, or its medics, else his comrades at {{f_first_aid}}%. A lamed or down
hero can be **carried back** by {{f_bearers}} of his unit's men, or **left behind**. A wounded
hero who can still walk can **go back** alone. Where he goes depends on whether his side has
an aid post:

- **With an aid post** (the GM places one for each side), the party crosses the map
  {{f_post_pace}} hexes an exchange on open ground by the cheapest way (round water, walls and
  the enemy, slower through woods), and shells can catch it on the way. At the post he gets
  first aid every exchange at {{f_post_aid}}%, and his wounds come off the death clock. An
  enemy who reaches the post takes or kills the men there. On its side's move the GM can
  move the post; the men there go with it, and it gives no first aid that exchange.
- **With none**, he is carried off the map at once, and the bearers return after
  {{f_back}} exchanges.

A hero left behind lies on his unit's hex. A unit of his side that stands there picks him
up; an enemy unit takes him prisoner or kills him, by the war's custom of **quarter**. When
the battle ends, a hero still lying out there is found if his side holds the field; if not,
quarter decides.

!!! example "The retinue: at Towton"
    On the field map the retinue's followers fight as units: its archers in open order, its
    spearmen in close order. {{ex.lead}} goes with the spearmen in the front rank;
    {{ex.arch}} shoots with the archers, at his own {{ex.a_bow}}% rather than the unit's
    quality, and makes {{f_tempo_h}} times as many aimed shots as one of them. When the billmen close,
    blows on the archers' front can find him, and a wound there is his own: rolled in full,
    bled on his own {{ex.a_blood}} Blood, and carried back to the roller when the battle is over.

## The enemy commander {#commander}

The GM can hand one side to a scripted **enemy commander**, attacking or holding. At the start of
that side's move it orders each unit, and **Undo its orders** puts the move back for the GM to make
by hand. It knows only the enemies its units can see, or saw a few exchanges ago. In short, it:

- closes, takes cover, shoots from range or charges with the odds its quality wants; green units go
  for the nearest enemy and sometimes hesitate, better ones for an enemy that is hurt or dangerous;
- storms works as its weapons' module says, and fights by fire with archers and machine guns;
- keeps a reserve, and commits it when a unit of its own breaks, the enemy comes close, or its attack
  stalls;
- takes and holds the objective the GM marks, and a second if there is one;
- follows a battlefield's routes round a flank, and the accounts' orders: who held to the end, and
  who withdrew, when and where;
- turns its guns on the enemy, brings them into reach and pulls them back from a charge. The modules
  add its batteries, shellfire, vehicles, mines and aircraft.

**Both sides.** Each side is moved by the GM or by the commander. With the commander on both sides
the GM only watches: **Next** steps a move at a time, and **Run** plays on until the GM presses
**Stop** or the battle ends itself. Under the map the page tells the battle's turning points as they
happen, and can have a language model retell them in a voice for the war; the rules never depend on
it.

How it decides each of these, when a run ends, and what the modules add, is in
[How the pages work](#commander-full).

## After the battle {#after}

**End the battle** stops it. The page then sets the two sides' results side by side, and
says who holds the field and the objective. Then:

1. **The field.** A side with no unit still standing has lost the field: the men it had down
   there are left behind, and die; a hero left there is found, or not, by quarter.
1. **The pursuit.** If the other side still has units standing, the beaten side loses more as it
   flees, as a share of its killed and left on the field (each share rolled between its figures):

   {{table:pursuit}}

   The victor's fresh horse makes it 1.5 times, and no horse half (before 1850); the dark, half; a
   river or marsh at the beaten side's back, twice. Most of a beaten medieval army's dead fell in
   the pursuit; by the 20th century the pursuit takes prisoners.
2. **The death clock.** A wound that kills in minutes kills before help comes, unless he is
   bound in time ({{f_saved_min}}%). One that kills in hours kills unless his camp can treat it:
   {{f_saved_field}}% saved in a camp, {{f_saved_shelter}}% in quarters, none with no camp.
   **Medevac** does better where a side had it: ambulance wagons (the Civil War and the
   Indian Wars) save {{ev_wagon}}%, motor ambulances (the world wars) {{ev_motor}}%, and
   helicopters (Korea on) {{ev_heli}}%, and {{ev_heli_min}}% of those dying within minutes.
   Helicopters need a landing zone on the field and a helicopter of the side not lost, or
   it is motor ambulances; the GM can untick a side that had none.
3. **To camp.** The rest are carried to their force's camp and go onto the track, as in
   [Recovery](#recovery). A battle set up from the travel map sends its dead and wounded back
   to the forces there.

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
come up to {{f_charge_move}} times its move: a **charge**. A unit in contact cannot move.

## An exchange {#exchange}

1. **Who strikes.** In melee, the front rank of each hex touching the enemy, and one more
   rank for each hex of the weapon's reach past the first (spears and bills strike from two
   ranks, the pike from three). With missiles, the men who have the target in range.
2. **How many blows tell.** Most of a minute in a press is shoving and watching for an
   opening: about one striking man in {{f_tempo}} makes a real attempt each exchange. A
   longbowman looses {{f_bow_rate}} arrows a minute, and about one shot in {{f_aimed}} is aimed at
   a man rather than loosed at the mass.
3. **Each attempt is one attack**, at the unit's quality, exactly as in [the fight](#turn):
   +{{f_flank}} from the flank, +{{f_rear}} from the rear (and no parry), +{{f_charge}} for a
   mounted charge in its first exchange, −{{f_shaken}} for a shaken unit, +{{f_pikes}} for
   pikes in close order against horse to their front; range, weather and cover come off
   missiles.
4. **The wound** is rolled as for one man. A light wound or a graze: he fights on. Serious
   or critical: a stop check, and failing it puts him **down**. A wound that kills within
   rounds kills. Against **modern fire** (breech-loaders on, machine guns, shell, grenades),
   every serious or critical wound puts him down and a light one calls for the check: the
   casualty returns from 1914 on count nearly every man hit as out of the line.
5. **Morale**, below; then the next exchange.

## Morale and the rout {#morale}

After an exchange a unit checks its morale if it lost the exchange in contact (more of its
men down than it put down), has {{f_trigger}} of its men down, lost {{f_shock}} of its men in
this exchange, or was struck in the flank or rear. It rolls d100 against its quality's
Nerve:

{{table:morale}}

- **Steady, fails:** it is **shaken**: it fights at −{{f_shaken}} and cannot charge. Failing
  by more than {{f_shaken_by}} while flanked, or with half its men down, it breaks at once.
- **Shaken, fails:** it **breaks**.
- **Shaken, passes out of contact:** it rallies to steady.

A broken unit runs. Every enemy man in reach strikes it at +{{f_rout}}, with no parry and
twice as often, as long as the pursuers keep up. This is where most of a battle's dead
fell, as at Towton and Agincourt, where the beaten side lost far more men in flight than in
the press.

!!! gm "For the GM"
    A melee of ten or twenty minutes, decided by morale more than by wounds, with the beaten
    side losing most of its men in the rout: that is the shape the records show, and the
    page is tuned to give it. Let the players' heroes break a line rather than kill it.

## Heroes {#heroes}

A team's characters go with units as **heroes**: in the front rank, shooting with it, or
behind it. A hero in the front makes {{f_tempo_h}} times a ranker's attempts with his own
attack, and blows on his unit's front fall on him {{f_exposure}} times as often as on a ranker
there. His wounds use the full rules, his own Blood and his own stop check. Two front-rank
heroes in contact fight each other: {{f_duel}} attempts each an exchange, instead of at the
rankers.

His wounds slow him as in [Wounds](#wounds): an arm hurt stops a two-handed weapon, and a
lamed hero halves his unit's move. In a quiet exchange his friends give first aid: the best
Leechcraft in the unit, or its medics, else his comrades at {{f_first_aid}}%. A lamed or down
hero can be **carried back** by {{f_bearers}} of his unit's men, or **left behind**. A wounded
hero who can still walk can **go back** alone. Where he goes depends on whether his side has
an aid post:

- **With an aid post** (the GM places one for each side), the party crosses the map
  {{f_post_pace}} hexes an exchange, and shells can catch it on the way. At the post he gets
  first aid every exchange at {{f_post_aid}}%, and his wounds come off the death clock. An
  enemy who reaches the post takes or kills the men there.
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

The GM can hand one side to a scripted **enemy commander**, attacking or holding. At the
start of that side's move it orders each unit. It knows only the enemies its units can see
(or saw in the last {{c_remember}} exchanges, where they were then); green units go for the
nearest, better ones for an enemy that is hurt, shaken or dangerous to them. It closes,
takes cover, shoots from range or charges with the odds its quality wants, and green units
sometimes hesitate. With no enemy in sight, a unit holds.

- **Reserve.** Regulars and veterans hold back their rearmost units, and commit one when a
  unit of theirs breaks or the enemy comes close; veterans also commit to exploit an enemy
  rout. The GM can mark reserves instead.
- **Objective.** The GM can mark a hex as its objective. Attacking, its units advance on it
  when they have nothing better to do and hold it once there (within {{c_obj_radius}}
  hex); holding, units more than {{c_obj_hold}} hexes from it fall back to it. Enemies near
  it make better targets. The log says who holds it after each exchange. Most battlefields
  mark the place their battle was fought for, a hill, a bridge, an outpost, as theirs,
  taking in the whole position (a ring of trenches counts as the hill).
- **Minefields.** It steers round minefields it knows of. Its sappers, attacking, lift a
  lane through known enemy mines in the row ahead when those mines lie on the way to their
  target or the objective. Holding, or at the objective, with no enemy it knows of within
  {{c_sap_clear}} hexes, they lay mines in the row ahead: mixed if the enemy it knows of has
  vehicles, otherwise anti-personnel.
- **Guns.** It turns its guns to face the enemy and calls its off-map batteries on what it
  sees. In the dark it first has one battery fire illumination over the enemy it has lost
  sight of nearest its men, where it was last seen. Attacking, guns with no enemy in reach go forward: a battery limbers, moves and
  unlimbers once an enemy is in reach; anti-tank guns hook up to an empty tractor beside
  them, are towed, and are unhooked in reach. They stop in reach but no nearer than
  {{c_keep_off}} hexes. Holding, its guns unlimber or unhook where they stand. Attacking, it first has one battery smoke an enemy that is shooting at men who
  cannot reply (not in the dark, or in a gale). Then one battery fires counter-battery on
  a located enemy battery it can reach: the one with the best counter % on the one with the
  most guns still served.

**Undo its orders** puts the move back for the GM to make by hand.

## After the battle {#after}

**End the battle** stops it. The page then sets the two sides' results side by side, and
says who holds the field and the objective. Then:

1. **The field.** A side with no unit still standing has lost the field: the men it had down
   there are left behind.
2. **The death clock.** A wound that kills in minutes kills before help comes, unless he is
   bound in time ({{f_saved_min}}%). One that kills in hours kills unless his camp can treat it:
   {{f_saved_field}}% saved in a camp, {{f_saved_shelter}}% in quarters, none with no camp.
3. **To camp.** The rest are carried to their force's camp and go onto the track, as in
   [Recovery](#recovery). A battle set up from the travel map sends its dead and wounded back
   to the forces there.

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
   +{{f_flank}} from the flank, +{{f_rear}} from the rear (and no parry), +{{f_charge}} for a
   mounted charge in its first exchange, −{{f_shaken}} for a shaken unit, +{{f_pikes}} for
   pikes in close order against horse to their front; range, weather and cover come off
   missiles. A tired unit loses its [fatigue](#fatigue) level's penalty off its attack and
   its parry.
4. **The wound** is rolled as for one man. A light wound or a graze: he fights on. Serious
   or critical: a stop check, and failing it puts him **down**. A wound that kills within
   rounds kills. Against **modern fire** (breech-loaders on, machine guns, shell, grenades),
   every serious or critical wound puts him down and a light one calls for the check: the
   casualty returns from 1914 on count nearly every man hit as out of the line.
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

On the field map it runs straight back as far as it can move. Its own side's units do not
stop it: it runs on through them to the first clear ground beyond, and each unit it runs
through loses half its move that exchange as the fugitives push through its ranks.

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
  battle; from the Second World War on, an **air drop** called on a side's move lands as a
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

The GM can hand one side to a scripted **enemy commander**, attacking or holding. At the
start of that side's move it orders each unit. It knows only the enemies its units can see
(or saw in the last {{c_remember}} exchanges, where they were then; what a unit sees from where it has just moved, the units ordered after it know); green units go for the
nearest, better ones for an enemy that is hurt, shaken or dangerous to them. It closes,
takes cover, shoots from range or charges with the odds its quality wants (counting the
steady friends touching it, who go in with it), and green units sometimes hesitate. With no enemy in sight, a unit holds; attacking with no objective, it goes forward along its facing to find one. A unit with no room to move facing its goal (or a turn too dear) moves facing as near its goal as it can.

- **Storming works.** Attacking, infantry with muskets, rifle-muskets, breech-loaders, or
  modern rifles and sub-machine guns do not stop to trade fire with an enemy behind works (a
  parapet, trench or bank), dug in, or in buildings or rubble: they close without seeking
  cover, firing as they go, and charge it, with the same odds. Flintlock riflemen, archers
  and machine guns still fight by fire. Modern infantry storm in bounds: a unit that took
  fire in the last exchange goes to ground and fires this move, and goes on once a bound
  draws no fire, its target is pinned, or it can charge home. A wall or
  palisade that blocks hand-to-hand fighting stops them at its foot, unless they carry
  ladders: then they go up it (see [works](#works)). Breaching it is the GM's order.

- **Routes.** A battlefield can send a unit on a route round a flank, as its account tells:
  the commander moves it from waypoint to waypoint, turning aside only for an enemy in contact
  or across its way, then orders it as any other.
- **Orders from the accounts.** On the battlefields, units that the sources say held their
  ground fight where they stand rather than fall back, and units the sources say withdrew on
  orders fall back at the minute the accounts give, to a place or off the field.
- **Narrowing.** Attacking, a formed unit that the ground keeps from closing on its target
  closes in its front, a quarter at a time and deeper, until it can move nearer, but never to
  less than half the front it started with.
- **Pursuit.** Its horse ride down a broken enemy within a charge when no standing enemy is as
  near, and its foot go after one within their move that is nearer than any standing enemy.
  Veterans rally back to the fight after a couple of moves if the enemy still stands near.
- **Shooters give way.** Attacking, archers, crossbowmen and skirmishers in open order step
  aside when they stand in the way of their own formed men behind them, and the formed men go
  on.
- **In range** means the weapon reaches, the light lets it see, and nothing blocks the line
  from where it would stand.
- **Tanks.** A unit with a main gun counts the target in range where the gun reaches and it
  can see; a vehicle with one prefers a spot where the target can neither reach it nor see it.
- **Reserve.** Regulars and veterans hold back their rearmost units (not one on a route, nor tanks and other vehicles with a main gun), and commit one when a
  unit of theirs breaks or the enemy comes close; veterans also commit to exploit an enemy
  rout. Attacking, they also commit one when the attack has stalled: five moves without
  putting down any real share of the enemy or getting nearer. A unit committed because one broke goes to plug the gap where it stood. The GM can
  mark reserves instead.
- **Digging in.** Its foot units with modern weapons dig in where they stand when it is
  safe (not under fire, no enemy it knows of in their range): at the objective, holding
  with no objective, and in reserve while they wait.
- **Objective.** The GM can mark a hex as its objective. Attacking, its units advance on it
  when they have nothing better to do and hold it once there (within {{c_obj_radius}}
  hex); holding, units more than {{c_obj_hold}} hexes from it fall back to it. Enemies near
  it make better targets. The log says who holds it after each exchange. Most battlefields
  mark the place their battle was fought for, a hill, a bridge, an outpost, as theirs,
  taking in the whole position (a ring of trenches counts as the hill).
  The GM can also mark a second objective. Attacking, once it holds the first, the units on
  it stay and the rest go on to the second (and back to the first if the enemy retakes it);
  holding, once the enemy holds the first, its units fall back to the second.
- **Minefields.** It steers round minefields it knows of. Its sappers, attacking, lift a
  lane through known enemy mines in the row ahead when those mines lie on the way to their
  target or the objective, closing up to the belt first and working through it row by row. Holding, or at the objective, with no enemy it knows of within
  {{c_sap_clear}} hexes, they lay mines in the row ahead: mixed if the enemy it knows of has
  vehicles, otherwise anti-personnel.
- **Guns.** It turns its guns to face the enemy and calls its off-map batteries and its
  aircraft (when they can fly; a strafing run or napalm strip along a wide enemy front) on
  what it sees, first what its forward air controllers see, and closer to its own men there. A controller with nothing
  to do and no target in its sight moves up to where it sees one (attacking only), up to {{c_spot_moves}} moves away, a move at a time,
  preferring a spot out of the enemy's reach; not while it has a fight of its own (an enemy touching it or in its own reach, pinned, or men lost the exchange before). Attacking, one battery lays a creeping barrage ahead of a unit closing on the
  enemy. Its batteries under counter-battery fire displace (a placed one moves its place {{c_displace_shift}} hexes along its map edge, away from the battery firing). In the dark it first has one battery fire illumination over the enemy it has lost
  sight of nearest its men, where it was last seen. Attacking, guns with no enemy in reach go forward: a battery limbers, moves and
  unlimbers once an enemy is in reach; anti-tank guns hook up to an empty tractor beside
  them (an empty tractor drives over to fetch them), are towed, and are unhooked in reach. They stop in reach but no nearer than
  {{c_keep_off}} hexes. Holding, its guns unlimber or unhook where they stand. Attacking, its foot units get aboard empty carriers beside them while no known enemy is in reach, and get down once one is (or at the objective). Attacking or holding, guns an enemy could reach at a charge, with no steady friend on the line between, limber or hook up and pull back as far as they can from it. Attacking, it first has one battery smoke an enemy that is shooting at men who
  cannot reply (not in the dark, or in a gale). Then one battery fires counter-battery on
  a located enemy battery it can reach: the one with the best counter % on the one with the
  most guns still served.

**Undo its orders** puts the move back for the GM to make by hand.

**Both sides.** Each side has its own choice: moved by the GM, or the commander attacking or
holding. With the commander on both sides the GM only watches: **Next** steps a move at a time,
and **Run** plays on until the GM presses **Stop** or the run ends itself. It ends when a side
has no unit left standing and none still to come, when an attacking side has taken the
objective and held it {{c_sp_held}} exchanges running with no enemy standing within
{{c_sp_secure}} of it and none still to come (but not before the battlefield's last phase has
begun), or after {{c_sp_limit}} exchanges (on a
battlefield with phases, {{c_sp_after}} past the last phase's start, if later, but never more
than {{c_sp_most}}); then the battle
ends, as with *End the battle*. On a battlefield the side its objective names attacks and the
other holds, or the armies fight as the battlefield says they did (the choice marked *as
fought*); on open ground both attack. The GM can take either side back at any
time.

**The narrative.** Under the map, the page tells the battle's turning points as they happen: a
phase beginning (and who comes on), units breaking or fleeing, a reserve committed, the objective
taken or lost, and the end with each side's losses. With an API key of the player's own, a
language model retells each one in a short passage of at most {{n_words}} words, in a voice for
the war (a chronicle, a dispatch, a war diary or a situation report), or one the GM picks for the
battle (any of those, a soldier's account or a plain summary). It is told to use only the
facts the game gives it and to write original prose; the plain line stays under each passage.
The rules never depend on it.

## After the battle {#after}

**End the battle** stops it. The page then sets the two sides' results side by side, and
says who holds the field and the objective. Then:

1. **The field.** A side with no unit still standing has lost the field: the men it had down
   there are left behind.
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

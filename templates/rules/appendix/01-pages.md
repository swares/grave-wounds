# How the pages work {#pages}

The main chapters say what each rule means for play. This appendix holds the procedures the pages
compute for you, in full, so that the game can still be played on paper and checked by hand. Each
section belongs to the rule it is linked from.

## The enemy commander {#commander-full}

The GM can hand one side to a scripted **enemy commander**, attacking or holding. At the
start of that side's move it orders each unit. It knows only the enemies its units can see
(or saw in the last {{c_remember}} exchanges, where they were then; what a unit sees from where it has just moved, the units ordered after it know); green units go for the
nearest, better ones for an enemy that is hurt, shaken or dangerous to them. It closes,
takes cover, shoots from range or charges with the odds its quality wants (counting the
steady friends touching it, who go in with it), and green units sometimes hesitate. With no enemy in sight, a unit holds; attacking with no objective, it goes forward along its facing to find one. A unit with no room to move facing its goal (or a turn too dear) moves facing as near its goal as it can. A unit on the ground turns to face its target where it lies, and stays down.

- **Storming works.** Attacking infantry close on an enemy behind works (a parapet, trench or
  bank), dug in, or in buildings or rubble, as the module for their weapons says: with
  muskets, rifle-muskets and breech-loaders, [Black-powder guns](#storming); with modern rifles
  and sub-machine guns, [Modern infantry](#modern-storming). Archers, flintlock riflemen and
  machine guns fight by fire.

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
- **Reserve.** Regulars and veterans hold back their rearmost units (not one on a route, nor tanks and other vehicles with a main gun), and commit one when a
  unit of theirs breaks or the enemy comes close; veterans also commit to exploit an enemy
  rout. Attacking, they also commit one when the attack has stalled: five moves without
  putting down any real share of the enemy or getting nearer. A unit committed because one broke goes to plug the gap where it stood. The GM can
  mark reserves instead.
- **Objective.** The GM can mark a hex as its objective. Attacking, its units advance on it
  when they have nothing better to do and hold it once there (within {{c_obj_radius}}
  hex), but go on attacking while their target is on it too; holding, units more than {{c_obj_hold}} hexes from it fall back to it. Enemies near
  it make better targets. The log says who holds it after each exchange. Most battlefields
  mark the place their battle was fought for, a hill, a bridge, an outpost, as theirs,
  taking in the whole position (a ring of trenches counts as the hill).
  The GM can also mark a second objective. Attacking, once it holds the first, the units on
  it stay and the rest go on to the second (and back to the first if the enemy retakes it);
  holding, once the enemy holds the first, its units fall back to the second.
- **Guns.** It turns its guns to face the enemy. Attacking, guns with no enemy in reach go
  forward and stop in reach, but no nearer than {{c_keep_off}} hexes; holding, they stay where
  they stand. Attacking or holding, guns an enemy could reach at a charge, with no steady friend
  on the line between, pull back as far as they can from it.
- **Modules.** What it does with batteries, shellfire, vehicles, mines and aircraft is in the
  modules that bring them: [Black-powder guns](#bp-commander), [Modern fire](#fire-commander),
  [Armour and mines](#vehicles-commander) and [Air and night devices](#air-commander).

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
taken or lost, and the end with each side's losses. With an API key of the player's own (a
free one serves), or a model run on the player's own computer, a language model retells each one in a short passage of at most {{n_words}} words, in a voice for
the war (a chronicle, a dispatch, a war diary or a situation report), or one the GM picks for the
battle (any of those, a soldier's account or a plain summary). It is told to use only the
facts the game gives it and to write original prose; the plain line stays under each passage.
The rules never depend on it.

### With Black-powder guns {#bp-commander}

With this module, the [enemy commander](#commander) also moves its batteries: attacking, a
battery with no enemy in reach limbers, moves, and unlimbers once an enemy is in reach;
holding, it unlimbers where it stands; to pull back from a charge it limbers first.

### With Modern fire {#fire-commander}

With this module, the [enemy commander](#commander) also:

- **Digging in.** Its foot units with modern weapons dig in where they stand when it is
  safe (not under fire, no enemy it knows of in their range): at the objective, holding
  with no objective, and in reserve while they wait.
- **Shellfire.** It calls its off-map batteries on what it sees, closer to its own men first.
  Attacking, one battery lays a creeping barrage ahead of a unit closing on the enemy, and
  first has one battery smoke an enemy that is shooting at men who cannot reply (not in the
  dark, or in a gale). Its batteries under counter-battery fire displace (a placed one moves
  its place {{c_displace_shift}} hexes along its map edge, away from the battery firing). In
  the dark it first has one battery fire illumination over the enemy it has lost sight of
  nearest its men, where it was last seen. Then one battery fires counter-battery on a located
  enemy battery it can reach: the one with the best counter % on the one with the most guns
  still served.

### With Armour and mines {#vehicles-commander}

With this module, the [enemy commander](#commander) also:

- **Tanks.** A unit with a main gun counts the target in range where the gun reaches and it
  can see; a vehicle with one prefers a spot where the target can neither reach it nor see it.
  Any shooter counts a target in range only where the weather and light let it see that far.
  Attacking, a vehicle unit leaves its immobilised vehicles behind and goes on with the rest.
- **Minefields.** It steers round minefields it knows of. Its sappers, attacking, lift a
  lane through known enemy mines in the row ahead when those mines lie on the way to their
  target or the objective, closing up to the belt first and working through it row by row. Holding, or at the objective, with no enemy it knows of within
  {{c_sap_clear}} hexes, they lay mines in the row ahead: mixed if the enemy it knows of has
  vehicles, otherwise anti-personnel.
- **Towing and carriers.** Attacking, its anti-tank guns with no enemy in reach hook up to an
  empty tractor beside them (an empty tractor drives over to fetch them), are towed, and are
  unhooked in reach; holding, they unhook where they stand, and to pull back they hook up.
  Attacking, its foot units get aboard empty carriers beside them while no known enemy is in
  reach, and get down once one is (or at the objective).

!!! gm "For the GM"
    Armour is a problem the infantry must solve, not a fight it can win with rifles. Give
    the side without tanks rockets, anti-tank guns, mines, ground the tanks cannot cross,
    or the dark.

### With Air and night devices {#air-commander}

With this module, the [enemy commander](#commander) also:

- **Aircraft.** It calls its aircraft (when they can fly; a strafing run or napalm strip along a
  wide enemy front) on what it sees, first what its forward air controllers see, and closer to
  its own men there. A controller with nothing to do and no target in its sight moves up to
  where it sees one (attacking only), up to {{c_spot_moves}} moves away, a move at a time,
  preferring a spot out of the enemy's reach; not while it has a fight of its own (an enemy
  touching it or in its own reach, pinned, or men lost the exchange before).

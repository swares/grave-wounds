# How the pages work {#pages}

The main chapters say what each rule means for play. This appendix holds the procedures the pages
compute for you, in full, so that the game can still be played on paper and checked by hand. Each
section belongs to the rule it is linked from.

## An exchange in full {#exchange-full}

For [An exchange](#exchange).

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

## Ammunition in full {#ammunition-full}

For [Ammunition](#ammunition).

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

## The enemy commander {#commander-full}

For [The enemy commander](#commander).

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

## Batteries in full {#guns-full}

For [Guns of the black-powder wars](#guns).

A **battery** is a unit in battery order, {{g_per_hex}} men to a hex. Its men are the crews,
{{g_crew}} to a gun, so as crews fall fewer guns are served.

- **Its fire.** Each served gun fires a round an exchange at the nearest enemy in front of it,
  in sight and with a clear line of fire, out to {{g_range}} ({{g_rifled}} for rifled guns).
  The GM can name another target, split the guns into sections, or choose the shot.
- **Canister.** Within {{g_canister}} the guns fire canister: {{g_balls}} chances a round,
  each likely to hit at short range and less so beyond.
- **Round shot.** Beyond that range the guns fire round shot. A ball that strikes a unit
  ploughs through its ranks, and each man in its path is hit at {{g_file}}%, so a deep
  column suffers far more than a line. On firm ground the ball bounds on, and it can strike
  another unit up to {{g_ricochet}} beyond.
- **Shell.** Howitzers fire shell over anything in the way. Its fuse may burst it early, in
  the air over the men, on the ground, or not at all. Gunners who have found the range cut
  their fuses better.
- **Wounds.** Every man struck by a gun rolls a wound at {{g_attack}}%, with no parry.
- **Rounds.** Each gun carries {{g_ammo}} rounds into action. **Resupply** takes an
  exchange.
- **Limbering.** Changing between limbered and unlimbered takes an exchange. Unlimbered,
  the guns can only be pushed {{g_pushed}} hexes.
- **Losing the guns.** A battery that breaks loses its guns for good.
- **Canister at the charge.** Charged in front, a battery gives the first charger one
  round of canister at point-blank range before the melee.

## Knocking out in full {#knocking-out-full}

For [Knocking them out](#knocking-out).

- **Morale.** A vehicle unit's morale checks count whole vehicles lost, not crewmen hit in
  vehicles still fighting.
- **Damage short of that.** A hit that does not knock the vehicle out strikes the turret at
  {{v_turret}}%, else the hull.

    - On the turret it puts the main gun out at {{v_t_gun}}%, and immobilises the vehicle at
      only {{v_t_imm}}%.
    - On the hull it immobilises the vehicle at {{v_h_imm}}%, and puts the gun out at
      {{v_h_gun}}%.

    Immobilised vehicles can still turn. Their crews can abandon them and leave the fight
    unhurt.

- **Shells and bombs** bursting in a vehicle's hex knock it out at the kind's own chance: a
  heavy howitzer's {{i_how_knock}}%, a fighter-bomber's {{v_fb_knock}}%. Light armour is
  {{v_shell_light}} times as likely to go, soft-skinned vehicles {{v_shell_soft}} times.
- **Knocked out.** Its crew are out of the fight. Each is struck at {{v_crew_struck}}% and
  wounded as by shellfire; the rest bail out.

## Anti-tank guns in full {#at-guns-full}

For [Anti-tank guns](#at-guns).

In the Second World War and Korea, a unit can be **anti-tank guns**: towed guns such as
the British 6-pounder, the American 57 mm, the German Pak 38 and 40, the Soviet and North
Korean 45 mm and the Japanese 47 mm.

- **Crews.** Each gun has {{at_crew}} men. A gun fires while one of its crew is up, and its
  crews manhandle it {{at_move}} hexes.
- **Fire.** Each gun fires {{at_rate}} round an exchange, as a tank's main gun does. Out to
  {{at_range}}, it hits a vehicle at {{at_hit}}% (close, mid and full range), and the hit
  then knocks the vehicle out as a main gun's would. At men, its high explosive bursts as a
  tank's round does.
- **Towing.** Gun tractors and trucks tow a gun each, the crews riding. Hooked up beside
  them, the guns move with the tractors and do not fire; unhooked, they fire from the next
  exchange.
- **Rounds.** Each gun brings {{at_rounds}} rounds. A gun out of them is resupplied as a
  battery is: an exchange out of contact, neither moving nor firing.
- **Shields.** Anti-tank and anti-aircraft guns have shields: small arms fired at them from
  in front lose {{at_shield}}%. Shields do nothing against shells or fire from the flank or
  rear. Some machine guns had shields too (a Maxim on a wheeled mount, say), though most did
  not: in set-up the GM can mark a machine-gun unit **shielded**, and it gets the same cover.
- **Vulnerable.** Otherwise its crews are men: rifles, machine guns and shells strike them,
  and hand to hand they fight with bayonets.
- **Emplaced.** Before the battle the GM can dig in any gun unit (anti-tank guns,
  anti-aircraft guns, machine guns or a battery). While it stands it counts as gone to
  ground, −{{at_ground}}% and hidden, but it cannot move all battle, though it can turn. A
  unit that breaks leaves its pits.
- **The enemy commander** tows its anti-tank guns forward and unhooks them in reach (see
  [the enemy commander](#commander)).

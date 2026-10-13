# Guns and fire support {#fire}

The [field map](#field-map) uses the same exchange for every era. What changes after 1865
is the weight of fire, and how men live under it.

## Modern infantry {#modern-infantry}

- **Extended order.** {{x_ext_men}} men to a hex, a few yards apart. Shots at them count
  half, and they move {{x_ext_move}} hexes.
- **Rifles.** In a minute a bolt-action rifle fires {{x_bolt}} rounds, a self-loading or
  assault rifle {{x_assault}}, and a submachine gun or pistol {{x_smg}}. They are rolled as
  aimed shots at the same rate as a musket's: most rounds are fired at the enemy's line,
  not at a man.
- **Modern fire puts men down.** Against breech-loaders and later weapons, shell and
  grenades, every serious or critical wound puts a man down, and a light one calls for the
  stop check ([An exchange](#exchange)).
- **Going to ground.** On its own move a unit can **go to ground** in the folds of the
  ground. Shots at it lose {{x_ground}}% on top of its cover. It cannot move until it gets
  up, but it still shoots and fights hand to hand.
- **Hidden men.** Men gone to ground, in a trench or a bunker, or in buildings or rubble
  show little of themselves. Only {{x_seen}}% of the aimed shots at them find a man to aim
  at ({{x_mg_seen}}% of a machine gun's); the rest go at the smoke and the flashes.
  Dug-in men also hold better: +{{x_dug_in}} on morale.
- **Machine guns.** A machine-gun team serves one gun for every {{x_mg_crew}} men, and the
  gun fires while one of its crew is up. It fires {{x_mg}} rounds a minute, and one in
  {{x_mg_aimed}} is rolled as an aimed shot.
- **The beaten zone.** The cone of fire falls on past its target. The first other unit
  (friend or foe) within {{x_beaten}} beyond the target on the line of fire takes
  {{x_beaten_share}}% as many shots. Woods, rough ground and marsh stop it.
- **Pinned.** A unit near a shell burst, or under a machine gun's fire (in its beaten zone
  too), checks at the end of the exchange: d100 against its Nerve, +{{x_sup_prone}} if gone
  to ground. On a failure it is **pinned** for the next exchange: it cannot move, and it
  shoots at half its rate.

## Guns of the black-powder wars {#guns}

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

## Fire support {#support}

From the First World War on, a side can have **batteries** off the map: mortars, field
guns, heavy howitzers, and tanks or autocannon firing over open sights. Each is a number of
**tubes** with their rounds and crews.

{{table:indirect}}

- **Calling fire.** On its side's move a battery fires on a hex that one of the side's
  units can see. That means within the weather's sight and the light's, with no woods or
  smoke between. It can keep firing each exchange until stopped or out of rounds.
- **Where it lands.** Each shell scatters by a d6 for the direction and up to the kind's
  scatter in hexes.
- **What it does.** Every man in the burst is struck at the % for his distance from it,
  ×{{i_prone}} if gone to ground and less his cover. A struck man rolls a wound as one hit
  by shell fragments at {{i_attack}}%.
- **Tree bursts.** Over woods, shells burst in the branches. The woods give no cover, the
  chance is ×{{i_tree}}, and going to ground only brings it to ×{{i_tree_prone}}.
- **Smoke** spends the same rounds and wounds no one. No one sees or shoots into, out of or
  through it, and it drifts downwind:

{{table:smoke}}

- **Illumination** lights the ground round its aim as by day (see
  [Night and the air](#night)). It needs no one to see the hex.
- **A fire plan.** A creeping barrage lifts its aim 1 to {{i_creep}} hexes after 1 to
  {{i_each}} exchanges on each line, ahead of an advance kept to the same timetable. A
  plan can have up to eight legs, each going on the same way or turning.
- **Counter-battery.** A battery that has fired is **located**. Field guns and heavy
  howitzers can fire on it with no one needing to see it:
  - each shell lands among its guns at {{i_cb_field}}% (field guns) or {{i_cb_how}}%
    (heavy howitzers), knocking out a tube and striking {{i_cb_among}} of its crew;
  - at {{i_cb_near}} times that chance, it bursts close by and strikes one man.

  Counter-battery wears a battery down over a battle rather than ending it. **Displacing**
  silences a battery for an exchange or more and leaves it no longer located.
- **On the map.** A battery can stand on a hex of the map instead. From there it reaches
  only its range, and an enemy unit next to it **overruns** it.

## Trenches and bunkers {#bunkers}

A **trench** gives the men in it cover and hides them, but they fight hand to hand as
usual. A **bunker** shelters its men from shots and shellfire and from blows: no one
strikes them, and they strike no one, but they shoot out of it. A tank's shell bursting on
it knocks it out at {{i_tank_knock}}%, a heavy howitzer's at {{i_how_knock}}%.

To take a bunker, a unit next to it **storms** it with one of three means, once an exchange
for each enemy-held bunker across its front, +{{b_pinned}} if the bunker's men are pinned:

{{table:assault}}

A man reached by flame is out of the fight with critical burns, and {{b_flame_dead}}% of them
are killed outright. A knocked-out bunker is a hex like any other.

!!! gm "For the GM"
    Under modern fire the question each exchange is who can see whom. Units in the open in
    close order are cut down. Spread out and gone to ground, they are hard to hit but are
    pinned half the time. Let the players find a way to move: smoke, a fire plan, a covered
    approach, or the dark.

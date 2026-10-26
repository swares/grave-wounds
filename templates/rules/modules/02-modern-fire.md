# Modern fire {#fire}

For the wars of machine guns, quick-firing artillery and breech-loaders. The [field map](#field-map)
uses the same exchange for every era; what this module changes is the weight of fire, and how
men live under it. A period book may switch on only part of it, as the black-powder book does
for its breech-loaders.

## Modern infantry {#modern-infantry}

- **Extended order.** {{x_ext_men}} men to a hex, a few yards apart. Shots at them count
  half, and they move {{x_ext_move}} hexes.
- **Rifles.** In a minute a bolt-action rifle fires {{x_bolt}} rounds, a self-loading or
  assault rifle {{x_assault}}, and a submachine gun or pistol {{x_smg}}. They are rolled as
  aimed shots at the same rate as a musket's: most rounds are fired at the enemy's line,
  not at a man.
- <span id="modern-down"></span>**Modern fire puts men down.** Against breech-loaders and later weapons, shell and
  grenades, every serious or critical wound puts a man down, and a light one calls for the
  stop check ([An exchange](#exchange)): the casualty returns from 1914 on count nearly every man
  hit as out of the line.
- <span id="modern-storming"></span>**Storming in bounds.** Attacking, modern rifles and sub-machine guns
  storm works as black-powder infantry do ([Storming works](#storming)), but in bounds: a unit
  fired on in the last exchange (whether or not anyone fell) goes to ground and fires this
  move, and goes on once a bound draws no fire, its target is pinned, or it can charge home.
  From the Second World War on, every advance goes this way, not only against works.
- **Going to ground.** On its own move a unit can **go to ground** in the folds of the
  ground. Shots at it lose {{x_ground}}% on top of its cover. It cannot move until it gets
  up, but it still shoots and fights hand to hand.
- **Digging in.** A unit with a modern weapon, out of contact, can dig shell scrapes and
  foxholes: {{x_dig}} exchanges without moving or firing, and it is dug in where it stands.
  Dug in, it counts as gone to ground (and hidden, and steadier) while it stays there, but it
  can get up and move, leaving its holes. In set-up the GM can start units dug in.
- **Hidden men.** Men gone to ground, in a trench or a bunker, or in buildings or rubble
  show little of themselves. Only {{x_seen}}% of the aimed shots at them find a man to aim
  at ({{x_mg_seen}}% of a machine gun's); the rest go at the smoke and the flashes.
  Dug-in men also hold better: +{{x_dug_in}} on morale.
- **Machine guns.** A machine-gun team serves one gun for every {{x_mg_crew}} men, and the
  gun fires while one of its crew is up. It fires {{x_mg}} rounds a minute, and one in
  {{x_mg_aimed}} is rolled as an aimed shot.
- **The beaten zone.** The cone of fire falls on past its target. The first other unit
  (friend or foe) within {{x_beaten}} beyond the target on the line of fire takes
  {{x_beaten_share}}% as many shots. Woods, rough ground, marsh, buildings, tall buildings and
  rubble stop it.
- **Pinned.** A unit near a shell burst, or under a machine gun's fire (in its beaten zone
  too), checks at the end of the exchange: d100 against its Nerve, +{{x_sup_prone}} if gone
  to ground. On a failure it is **pinned** for the next exchange: it cannot move, and it
  shoots at half its rate.

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
  by shell fragments at {{i_attack}}%. With quick-play, add up each man's chance (men × their
  % for each burst) for the average and roll once on the spread chart for the men struck.
- **Tree bursts.** Over woods, shells burst in the branches. The woods give no cover, the
  chance is ×{{i_tree}}, and going to ground only brings it to ×{{i_tree_prone}}.
- **Smoke** spends the same rounds and wounds no one. No one sees or shoots into, out of or
  through it, and it drifts downwind:

{{table:smoke}}

- **Illumination** lights the ground round its aim as by day (see
  [Night](#night-air)). It needs no one to see the hex.
- **A fire plan.** A creeping barrage lifts its aim 1 to {{i_creep}} hexes after 1 to
  {{i_each}} exchanges on each line, ahead of an advance kept to the same timetable. A
  plan can have up to eight legs, each going on the same way or turning.
- **Counter-battery.** A battery that has fired is **located** (not tanks or autocannon
  firing over open sights). Field guns and heavy
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

## Fixed lines {#fixed-lines}

Before dark a machine gun can be laid on a fixed line. In the dark, with
no target it can see, it fires blind down the line at an enemy within {{n_fixed_width}}
hex of it, at −{{n_fixed}}%. The enemy commander, holding, lays its machine guns' lines by
day or at dusk on the nearest enemy it knows of in reach, or else ahead toward one (or
straight ahead) as far as it can reach and see, shifting such a line once onto an enemy
that comes into reach off it.

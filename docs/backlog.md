# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Deferred work

- **Works and ground on the field map.** Turning a unit in place pays nothing for the ground
  its ends sweep over, a unit's flanks and rear rows pay no ground on the move (only its
  front row), and high ground's edge in shooting is all or nothing (no slopes). See
  [units.md](units.md).
- **Heroes on the field map.** His sickness does not lower his attack and defence there
  (the GM can lower them by hand), his wounds' impairments (a useless arm, dazed) are left
  to the roller, and there is no first aid during the battle: he bleeds until it is over.
- **Indirect fire, simplified.** Batteries stay off the map, with no ground of their own:
  counter-battery fire finds a located battery wherever it is, its crews' wounds are counted
  but not named, and a displaced battery reappears unlocated with no new position to plot.
  A barrage's fire plan has one direction and one lift for the whole plan.
- **The travel clock, simplified.** The clock watches for meetings every quarter hour, so
  two fast forces passing in open country within one quarter hour can miss each other; and
  meetings are only between the forces' hexes (no scouting reach, no seeing a dust cloud).
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Agincourt (1415), Towton (1461), Lützen (1632), Albuera (1811), Cowpens (1781), Lundy's
  Lane (1814), First Bull Run (1861), Fort Phil Kearny (1866-67, with two battlefields), Mons
  (1914), Hill 700 on Bougainville (1944), Anzio and Cisterna (1944) and Osan (1950) have both a
  campaign map and a battlefield. The rest of Italy (Cassino), the rest of Korea, Vietnam and later
  still play on the generic valley and open ground (the unit rules for them are in: machine
  guns, extended order, artillery and mortars on call, suppression). Each needs the same work: a spec for `tools/maps/campaign_lib.mjs` (places,
  rivers and roads drawn through public-domain facts) and one for `field_lib.mjs` (the
  battlefield and its armies).
- **Modern rifle fire may be too deadly close in.** Playtesting Osan: left alone, the dug-in
  American line breaks in about 20 exchanges (minutes) against five times its numbers, where
  the real fight lasted about two and a half hours before the withdrawal. Veteran riflemen at
  150 yards hit prone men behind 17% cover with about 65% of their aimed shots. Worth a look at
  the missile tempo and range bands for service rifles before more modern battlefields.
- **Guns, still simplified.** A battery splits into at most one section, and its canister
  at a charge is counted at the end of the exchange like all fire, so it does not thin the
  blows the charge strikes that minute. The Thirty Years' War still borrows the Peninsula's
  gun wounds: no 1618-48 artillery wound counts were found.
- **Character generation, beyond the first cut.** The medieval tables are a first draft for
  a team playtest. Its characteristics now count in the roller (Agility, Endurance,
  Strength, Presence), and Leechcraft, Fieldcraft, Watch and Stealth work outside a fight.
  Followers have one-line stat blocks, and the gunpowder eras (1618-1876) and the world wars
  (1914-18, 1939-45) have their own tables. Still to come: Korea, Vietnam and later, and
  women's names where they served under arms (Soviet snipers and medics, for one).

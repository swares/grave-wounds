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
- **Indirect fire, simplified.** Batteries stay off the map: counter-battery fire wears
  their tubes down but never kills their crews, and a battery cannot move to escape it.
  Smoke does not drift with the wind, and a creeping barrage cannot be timed to lift.
- **One clock for all forces.** Each force on the travel map keeps its own clock (kept on
  purpose for now). A shared clock would let forces meet on the road.
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Agincourt (1415), Towton (1461), Lützen (1632), Albuera (1811), Cowpens (1781), Lundy's
  Lane (1814), First Bull Run (1861), Fort Phil Kearny (1866-67, with two battlefields), Mons
  (1914) and Hill 700 on Bougainville (1944) have both a campaign map and a battlefield. Italy
  1944, Korea, Vietnam and later
  still play on the generic valley and open ground (the unit rules for them are in: machine
  guns, extended order, artillery and mortars on call, suppression). Each needs the same work: a spec for `tools/maps/campaign_lib.mjs` (places,
  rivers and roads drawn through public-domain facts) and one for `field_lib.mjs` (the
  battlefield and its armies).
- **Guns, still simplified.** A battery splits into at most one section, and its canister
  at a charge is counted at the end of the exchange like all fire, so it does not thin the
  blows the charge strikes that minute. The Thirty Years' War still borrows the Peninsula's
  gun wounds: no 1618-48 artillery wound counts were found.
- **Character generation, beyond the first cut.** The medieval tables are a first draft for
  a team playtest. Its characteristics now count in the roller (Agility, Endurance,
  Strength, Presence), and Leechcraft, Fieldcraft, Watch and Stealth work outside a fight.
  Followers have one-line stat blocks, and the gunpowder eras (1618-1876) have their own
  tables. Still to come: tables for the eras after 1876, once they have unit rules.

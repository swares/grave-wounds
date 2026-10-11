# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Deferred work

- **Works and ground on the field map, simplified.** A unit's move pays only for what its
  middle hex crosses, the cover of a volley is taken at the nearest target hex only, and
  breaching is by order (it does not stop the unit fighting). High ground gives no edge to
  shooting. See [units.md](units.md).
- **Heroes on the field map, simplified.** A hero's earlier wounds and his sickness do not
  lower his attack and defence there (the GM can lower them by hand), he does not bleed during the battle
  (the roller takes it up afterwards), a failed stop check puts him down for the rest of
  the battle (no stunned or defend-only), and a duel between two heroes is left to the
  roller.
- **One clock for all forces.** Each force on the travel map keeps its own clock (kept on
  purpose for now). A shared clock would let forces meet on the road.
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Agincourt (1415), Towton (1461), Lützen (1632), Albuera (1811), Cowpens (1781), Lundy's
  Lane (1814) and First Bull Run (1861) have both a campaign map and a battlefield. The
  conflicts after 1865 in the tables (the frontier, the world wars and later) still play on
  the generic valley and open ground; their weapons need unit rules first (machine guns,
  modern artillery). Each needs the same work: a spec for `tools/maps/campaign_lib.mjs` (places,
  rivers and roads drawn through public-domain facts) and one for `field_lib.mjs` (the
  battlefield and its armies).
- **Guns, simplified.** A battery fires one kind of shot at one unit an exchange, and the
  fuse is rolled rather than set by the gunners. The Thirty Years' War still borrows the
  Peninsula's gun wounds: no 1618-48 artillery wound counts were found.
- **Scurvy for forces.** Camp disease covers flux, typhus, typhoid, ague and plague, and
  wound fever for the wounded from the field map. Scurvy needs food tracking (weeks
  without fresh food); it is in the design doc's disease table.
- **Named characters' wounds on the travel map.** A named man's battle wounds stay in the
  roller (bleeding, treatment) and do not turn septic or heal by the week as a force's wounded
  do. One way: hand his wounds to the wound track when he goes with a force.
- **Nursing and spread.** The design doc has nurses catching flux, typhus and typhoid from
  the sick. The force-level rules leave that out for now.
- **Character generation, beyond the first cut.** The medieval tables are a first draft for
  a team playtest. Still to come: tables for the other eras; characteristics feeding more
  rules (Endurance for blood and disease, Agility for initiative); named characters' skills
  outside a fight (Leechcraft for first aid, Fieldcraft and Watch on the travel map); and
  followers' one-line stat blocks for big teams.

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
- **Heroes on the field map, simplified.** A hero's earlier wounds do not lower his attack
  and defence there (the GM can lower them by hand), he does not bleed during the battle
  (the roller takes it up afterwards), a failed stop check puts him down for the rest of
  the battle (no stunned or defend-only), and a duel between two heroes is left to the
  roller.
- **One clock for all forces.** Each force on the travel map keeps its own clock (kept on
  purpose for now). A shared clock would let forces meet on the road.
- **Cover and elevation on the battle map**, beyond what works give.
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Agincourt (1415), Towton (1461), Lützen (1632) and Albuera (1811) have both a campaign
  map and a battlefield. The other conflicts in the tables (the American Revolution, 1812,
  the Civil War and later) still play on the generic valley and open
  ground. Each needs the same work: a spec for `tools/maps/campaign_lib.mjs` (places,
  rivers and roads drawn through public-domain facts) and one for `field_lib.mjs` (the
  battlefield and its armies).
- **Guns, simplified.** Batteries fire only at the nearest enemy in front, never over
  their own units' heads; round shot does not bounce on beyond its target or strike a
  second unit behind; there is no ammunition count, shell, or counter-battery fire at the
  crews in particular; and the Thirty Years' War borrows the Peninsula's gun wounds.
- **Scurvy for forces.** Camp disease covers flux, typhus, typhoid, ague and plague, and
  wound fever for the wounded from the field map. Scurvy needs food tracking (weeks
  without fresh food); it is in the design doc's disease table.
- **Disease for named characters.** The roller's fighters could carry conditions on the
  five-step track, with their own Endurance, and sick men could come to a fight weakened
  instead of staying out of it.
- **Nursing and spread.** The design doc has nurses catching flux, typhus and typhoid from
  the sick. The force-level rules leave that out for now.
- **Medieval character generation**, then a team playtest.

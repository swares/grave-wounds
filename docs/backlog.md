# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Camp fights (from PR #15)

### 3. A very large camp does not match the travel map's labour

**Now.** The battle map is capped at 80 × 60 hexes. A camp too big for that is shrunk to
fit, and the map says so. Its works, and the man-hours shown on the battle map, are then
smaller than the travel map's figure, which is costed on the full-size camp.

**Why it matters.** Only very large forces are affected, on the order of a thousand men or
more on foot. But it breaks the promise that the two maps agree.

**A way to fix it (pick one).**
- Show the travel map's figure on the battle map too, and say that the map shows only part
  of the camp. This is the cheapest fix.
- Lay out only the stretch of the camp facing the attackers, at full scale, so the fight
  takes place at the true size of the works.
- Raise the cap, if the page stays fast enough. Laying out a camp scans the whole map, and
  a large map costs time.

## Deferred earlier

- **One clock for all forces.** Each force on the travel map keeps its own clock (kept on
  purpose for now). A shared clock would let forces meet on the road.
- **Planned arrivals use today's ground.** The arrival estimate assumes today's mud or snow
  for later days too (see [weather.md](weather.md)). It could use the weather already
  rolled for those days, or show a range.
- **Cover and elevation on the battle map**, beyond what works give.
- **Campaign and battle maps** for each campaign or battle, to replace the generic valley.
- **Disease and camp hygiene.** The hooks are in place: each terrain's wet flag and the
  night's rest. The rules are not written yet.
- **Medieval character generation**, then a team playtest.

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

## Travel

### 4. Choose to march with the baggage train

**Now.** Every force on the travel map marches on its own route, at its own speed. A foot
band (4 km/h) leaves its baggage train (wagons, 3 km/h) behind and arrives first, unless
the player moves the two forces step by step. There is no way to say "these march
together".

**Why it matters.** Keeping the baggage close is a real choice with a cost either way.
Marching with it slows the whole column to wagon pace, and keeps it to ground wagons
can cross (no forest, marsh, mountains or heath). Going ahead leaves the train, with the
food and tools, open to raids, and it reaches camp after the fighting men.

**A way to fix it.**
- Give each force a **March with** choice: another force on its side, or none (the
  default, as now).
- Forces marching together share one route and one clock. The route avoids terrain any
  of them cannot enter, and the column moves at the slowest one's speed, after fatigue.
- They camp together. A camp sized for all their men can use the men of both forces for
  the work, and the train's tools count for everyone.
- In a fight, they already defend together if both are within reach of the camp
  (done in the allies change); marching together keeps them within reach.
- Leaving the column is one click, and each force keeps its own clock from there.

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

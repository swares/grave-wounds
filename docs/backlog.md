# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Camp fights (from PR #15)

### 1. An enemy who arrives early still fights a finished camp

**Now.** A fight starts at the later of the forces' clocks. If the enemy reaches the camp
while it is still being dug, the fight waits until the camp is done, and the battle map
lays out the camp complete. In testing, Enemy horse reached Our band's camp at 14:33 on
20 October; the fortified camp was finished at 19:25 on 24 October, and that is when the
fight starts.

**Why it matters.** Catching an enemy before his works are up is one of the main reasons
to march hard, and the rules currently take that away.

**A way to fix it.**
- Record when each camp's work started as well as when it will finish.
- If the attackers arrive first, start the fight at their arrival. Lay the camp out
  partly built, in proportion to the labour done by then. For example, finish the ditch
  first, then the bank, then the palisade, with the gate last. Or build the ring
  section by section from the gate.
- Ask the GM which: fight now against the unfinished works, or wait and watch.
- The labour figures are already shared (`works_labour` in `gravewounds/combat.py` and
  `templates/camp.js`), so a partial layout can be checked against them.

### 2. Friendly forces nearby do not join the defence

**Now.** One force defends. Another force on the defender's side within reach, such as
the baggage train camped beside Our band, is left out. You can bring its men in by hand:
**Add** puts new fighters on the attackers' side, so change each one's Side field on its
card.

**Why it matters.** Baggage trains, allied companies and garrisons camp together, and a
raid on one is a raid on all.

**A way to fix it.**
- Extend `fight_plan` (Python and the travel page) to return all defending forces within
  reach of the defender, as it already does for attackers.
- In the roller's `setupHandoff`, put the first force inside the camp and the others in the
  remaining hexes inside, or just behind the gate if the camp is full.
- Keep the 8-men-per-force cap, or make the cap a setting.

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
  purpose for now). A shared clock would let forces meet on the road, and would make
  item 1 simpler.
- **Planned arrivals use today's ground.** The arrival estimate assumes today's mud or snow
  for later days too (see [weather.md](weather.md)). It could use the weather already
  rolled for those days, or show a range.
- **Cover and elevation on the battle map**, beyond what works give.
- **Campaign and battle maps** for each campaign or battle, to replace the generic valley.
- **Disease and camp hygiene.** The hooks are in place: each terrain's wet flag and the
  night's rest. The rules are not written yet.
- **Medieval character generation**, then a team playtest.

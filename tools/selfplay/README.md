# Self-play tools

These scripts play every battlefield with the enemy commander on both sides, using the rules as
they run in the built field page (`dist/field.html`, from `python3 build.py`). They then report
how the runs compare with the battles as fought (`docs/selfplay-review.md`). They need Node and
Python 3, and nothing else.

| File | What it does |
| --- | --- |
| `play.js <field> <seeds> <out.json> [page] [first seed]` | Self-plays one battlefield, one run a seed (seed k rolls dice k × 101), with the stances the battlefield gives. |
| `quality.js <field> <seed> [page]` | One run, reporting how each side's commander used its units (below). |
| `run.sh <seeds> <out dir> [page] [workers] [first seed] [play\|quality]` | Every battlefield × seed as its own job, longest first (`times.txt`), shared among the workers. |
| `report.py winners <dir>` | Each battlefield's runs against the battle as fought (`actual.json`), and the total. |
| `report.py diff <before> <after>` | The battlefields whose results changed between two runs, and both totals. |
| `report.py quality <dir>` | The commander report, by battlefield and side. |
| `actual.json` | Each battlefield's winner as fought, and the losses, in brief. |
| `times.txt` | Milliseconds a run took on each battlefield (only orders the jobs). |

**A change measured.** Build the page on main and copy it aside. Build again on the branch. Then
run both and compare:

```sh
tools/selfplay/run.sh 4 /tmp/before /tmp/main-field.html 2
tools/selfplay/run.sh 4 /tmp/after dist/field.html 2
python3 tools/selfplay/report.py diff /tmp/before /tmp/after
```

All 37 battlefields × 4 seeds take well under an hour on two cores; Chipyong-ni is the longest.

**Who won a run.** If one side is gone, the side left standing wins. An attacker that took and
held the objective wins. Otherwise, on a battlefield with an objective, the side holding it at
the end wins. With no objective, the side with nobody standing loses, else the side that lost
the larger share of its men loses.

**The commander report.** A unit is *engaged* in an exchange when it fired, struck, or was struck
hand to hand. For each side the report gives:
- *idle%*: the share of its men in units never engaged.
- *peak%*: the most engaged in any one exchange.
- *spread*: the exchanges between its first and last units' first fight, which is large when the
  attack goes in piecemeal.
- *hitIdle%*: the share of its losses (not counting the rout) taken by units that could not hit
  back that exchange.
- The units that never fought.

`quality.js` also gives, for each idle unit, whether it moved, whether it was held in reserve and
until when, its state, and how near it ended to the enemy.

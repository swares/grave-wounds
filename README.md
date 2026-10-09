# Grave Wounds: blood, bivouac and weather

A d100 roleplaying game where wounds behave like real wounds. Where you are hit matters
more than how hard. Fights end in incapacitation far more often than death, and the dying
happens on a clock that first aid can stop. Off the battlefield, the team lives with what
the fight left behind: wounds to dress, sickness in camp, food to find, and weather that
makes a day's march easy or brutal.

Players lead a small team rather than a lone hero. The game spans historical eras, from
the Crusades to the modern day, and speculative ones in the spirit of Aftermath!, The
Morrow Project, Gamma World and Traveller.

**Status: early design.** The rules are not written yet. The design proposal is in
[docs/design.md](docs/design.md). It includes a comparison with Aftermath!, Rolemaster,
Gamma World, Traveller and The Morrow Project. The first playtest era is medieval.

**First playable piece:** the roller now runs the Grave Wounds stop check, graze and team
morale. Each fighter has a side, a leader flag and a Nerve rating. A hex battle map holds
the fighters' positions, with movement, leaving contact, and weapon reach and range. The
one-page rules are in [docs/combat.md](docs/combat.md).

**Travel map:** `dist/travel.html` marches forces from camp to the field across 1 km hexes
of terrain, with planned routes, marching days and terrain painting. See
[docs/travel.md](docs/travel.md).

**Camps and works:** forces make camp on the travel map, from a bivouac to a fortified
camp. A camp can be sent to the battle map as a fight, with its ditch, bank, palisade,
gate or stakes laid out. Works can also be built by hand on the battle map, and they
change movement, cover and close combat and can be breached. See
[docs/works.md](docs/works.md).

## Where this started

This repository began as a copy of [HitLoc](https://github.com/swares/HitLoc), the
historical hit-location and wound roller, taken at HitLoc PR #14 and renamed to the
`gravewounds` package. The two projects are separate and will diverge. HitLoc stays a
system-neutral wound tool, and this repo becomes the game.

Everything inherited from HitLoc is still here and still builds:

- d100 hit-location tables weighted by real wound records, with sources (`data/`)
- wound effects, armour, weapons and example combatants
- the web roller with its wounded-fighter tracker and turn order
- combatant figures, conflict maps and period pictures
- printable tables and the JSON data bundle

[docs/hitloc-reference.md](docs/hitloc-reference.md) documents all of this. It is HitLoc's
README, with commands updated for this repo. Parts the game does not need will be pruned
in later changes.

## Building

```
pip install -r requirements.txt
python build.py                  # rebuild dist/ and index.html
python -m gravewounds check      # validate the data
python -m gravewounds list
python -m gravewounds roll --table towton-1461-all-hits --weapon bill -n 3
```

`build.py` writes:

- `dist/roller.html` and `dist/travel.html`
- `dist/tables.pdf` and `dist/tables.md`
- `dist/gravewounds-data.json`
- the start page `index.html`

## Next steps

From the design proposal (the rule changes from the rulebook comparison are agreed and
written in):

1. Playtest the stop check, graze, morale and battle map in the roller and tune their
   numbers. Cover and elevation come next on the map.
2. Playtest the travel map, then add maps for each campaign and battle. Weather, forage and
   camp disease will use the terrain's cover, forage and wet notes.
3. Draft the medieval character generation tables and make a team in 20 minutes.
4. Playtest one fight with two teams, then a few weeks of camp, march and weather.

## Copyright and trademarks

Grave Wounds' rules, tables and text are its own. The design notes compare it with
Aftermath!, Rolemaster, Gamma World, Traveller and The Morrow Project, describing how those
games work in our own words; none of their rules text, tables or art is reproduced here.
Those names are trademarks of their owners, and Grave Wounds is not affiliated with or
endorsed by any of them. The wound data comes from published studies, cited in `data/`;
period pictures are linked from Wikimedia Commons, not copied; maps are drawn from
Natural Earth (public domain).

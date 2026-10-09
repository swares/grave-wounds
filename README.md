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

- `dist/roller.html`
- `dist/tables.pdf` and `dist/tables.md`
- `dist/gravewounds-data.json`
- the start page `index.html`

## Next steps

From the design proposal (the rule changes from the rulebook comparison are agreed and
written in):

1. Write the one-page combat rules and the stop check, and test them in the roller.
2. Draft the medieval character generation tables and make a team in 20 minutes.
3. Playtest one fight with two teams, then a few weeks of camp, march and weather.

## Copyright and trademarks

Grave Wounds' rules, tables and text are its own. The design notes compare it with
Aftermath!, Rolemaster, Gamma World, Traveller and The Morrow Project, describing how those
games work in our own words; none of their rules text, tables or art is reproduced here.
Those names are trademarks of their owners, and Grave Wounds is not affiliated with or
endorsed by any of them. The wound data comes from published studies, cited in `data/`;
period pictures are linked from Wikimedia Commons, not copied; maps are drawn from
Natural Earth (public domain).

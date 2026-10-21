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

**Travel map:** `dist/travel.html` marches forces from camp to the field across 0.6-mile (1 km) hexes
of terrain, with planned routes, marching days and terrain painting. It comes with a test
valley, the Agincourt campaign of 1415 (Harfleur to Calais, on 3-mile, 5 km hexes), the
Towton campaign of 1461 (Pontefract to York), Valdemar IV's invasion of Gotland in 1361
(the landing to Visby), the Lützen campaign of 1632 (Naumburg to Leipzig), the raid on
Sidon in 1253 (Banias to the coast), the Albuera campaign of 1811 (Badajoz to Santa
Marta), the Cowpens campaign of 1781 (the Pacolet to the Broad), the Niagara campaign of 1814
(Fort Erie to Fort George), the siege of Sevastopol in 1855 (Kamiesh to the Chernaya), the First Bull Run campaign of 1861 (Fairfax to Gainesville),
Fort Phil Kearny on the Bozeman Trail in 1866-67, Mons in 1914 (Condé to Binche), the
Bougainville perimeter in 1944, the Anzio beachhead in 1944 (to Cisterna), Osan in 1950 (Suwon to P'yongt'aek), Chipyong-ni in 1951 (Yangpyong to Wonju) and the Chosin Reservoir in 1950 (Yudam-ni to Hungnam), all on 0.6-mile (1 km) hexes; Cassino in 1944, Kapyong in 1951 (the Kapyong valley), Heartbreak Ridge in 1951, Pork Chop Hill in 1953,
the Ia Drang in 1965 (X-Ray and Albany), Hue in 1968 (the city and Phu Bai), Khe Sanh in 1968 (the base and its hills), Dak To in 1967 (the base to Hill 875), Hamburger Hill in 1969 (the A Shau valley), Goose Green in 1982 (the Darwin isthmus), 73 Easting in 1991 (the 2nd Armored Cavalry's last day), Grozny in 1995 (the New Year's assault), Fallujah in 2004 (Operation Phantom Fury), COP Keating in 2009 (the Kamdesh valley) and Wanat in 2008 (the Waygal valley) on 0.3-mile
(0.5 km) hexes; and Mogadishu in 1993 on 270-yard (0.25 km) hexes. See
[docs/travel.md](docs/travel.md).

**Camps and works:** forces make camp on the travel map, from a bivouac to a fortified
camp. A camp can be sent to the battle map as a fight, with its ditch, bank, palisade,
gate or stakes laid out. Works can also be built by hand on the battle map, and they
change movement, cover and close combat and can be breached. See
[docs/works.md](docs/works.md).

**Calendar and weather:** each map has a start date, latitude and climate. Days have real
dates and daylight, and the weather is rolled from climate normals (the GM can change
it). Mud, snow and floods slow the march; rain, wind and fog affect bows and firearms in
battle; and the night's rest and fatigue follow from the camp and the weather. See
[docs/weather.md](docs/weather.md).

**Camp disease:** forces on the travel map fall sick with bloody flux, camp fever,
typhoid, ague and plague. The risk depends on camp hygiene, the ground, the weather and how
long they stay. The sick slow the march, leave fewer men to dig and fight, and some die. See
[docs/travel.md](docs/travel.md).

**Unit combat:** for battles of hundreds, the rank and file fight as units, resolved in
bulk each minute through the same wound tables. Morale decides most fights, and the rout
does most of the killing. Named characters still fight one by one. The field map,
`dist/field.html`, puts units on 11-yard (10 m) hexes: each side moves, then every melee and volley
is resolved together, with flank and rear, morale and the pursuit, batteries of guns firing
round shot, canister and shell (bounding on over firm ground, at named targets, ordered shot, split sections, cut fuses and canister into a charge, until the rounds run out), machine guns, artillery and mortars on call with suppression, tanks, infantry fighting vehicles and carriers (with their riders) against rockets and guided missiles, on painted ground
with the battle map's works and weather, or on a real battlefield (Sidon, Visby, Agincourt, Towton, Lützen, Albuera, Cowpens,
Lundy's Lane, the Great Redan at Sevastopol (June and September 1855), First Bull Run, the Fetterman Fight, the Wagon Box Fight, Mons 1914, Hill 700 on
Bougainville, the Rangers at Cisterna, Task Force Smith at Osan, the perimeter at Chipyong-ni, landing zone X-Ray, the crash sites in Mogadishu, the patrol base at Wanat, Cassino's ridges and ruins, Fox Hill at Toktong Pass, Hill 504 at Kapyong, Hill 931 on Heartbreak Ridge, Pork Chop Hill, the new city at Hue, Hill 861A at Khe Sanh, Hill 875 at Dak To, Hamburger Hill, Darwin Hill at Goose Green, the rise at 73 Easting, the railway station in Grozny, the Jolan in Fallujah, or Combat Outpost Keating, with both armies drawn up). A fight on the travel
map can be fought there, and its wounded go back to camp, where wound fever can take
them. An optional scripted commander can play either side, attacking or holding (an objective
hex the GM marks if wanted, and a second to go on to or fall back to), with an Undo for each of its moves: it moves, digs in and lays or
lifts mines with its men, carries them up in its vehicles, limbers, tows and unlimbers its guns, and calls its batteries and
aircraft (smoke, illumination at night, counter-battery fire, and moving batteries that are
under it). See [docs/units.md](docs/units.md).

**Rule book:** `dist/rules.html` teaches the game: making a team, the fight, wounds, first
aid and recovery, battles of hundreds, the march and the camp, and weather and works,
following one team from the road to Towton into camp; then the other eras, guns and fire
support, vehicles, night and the air, with a rifle squad in Vietnam followed through one
night. GM notes are set apart, and an index of its terms closes it. It prints cleanly from
the browser, with page numbers in Chrome and Edge.

**Team builder:** `dist/team.html` makes a team of four to six in a few rolls each, from the
tables of eleven eras (medieval, the Thirty Years' War, horse and musket, the Crimean War, the Civil War and
frontier, the Plains nations of the 1860s and 1870s, the First and Second World Wars, Korea,
Vietnam, and the Falklands to Afghanistan): characteristics (3d6 x 5 or a fixed array), an origin with a
trait and a drawback, one to three career terms with their events, old wounds rolled on the
region's wound table, and kit, with what that kit is worth and a purse of savings. Prices come from
`data/equipment/<era>.yaml`, each army's coin with a common soldier's day's pay (a **Day**),
so a sheet reads "kit worth about 21 Days; purse 60 Days (£1 10s)". Between fights the team can find work: each era has its own
jobs (`data/jobs/<era>.yaml`), picked by where the team is, each with a skill check for the pay
and a chance of trouble. Women serve where the records show they did (French cantinières in the Crimea, Civil War women
disguised as men, Soviet women in 1941-45, the Vietnamese, and the Americans, British and
Russians since 1991), chosen or rolled at the army's share. Sent to the roller, each character's skills fill in his attack
and defence; a big team's followers get a line each. `python3 -m gravewounds team` makes one
on the command line. See
[docs/team.md](docs/team.md).

**Units:** every page has a **US | Metric** switch in its header (US by default), shared by
the roller, the travel map and the field map and remembered in the browser. The rules and
data stay metric inside; the printed tables and these docs give US units with metric in
brackets.

**Backlog:** known gaps and deferred work are listed in [docs/backlog.md](docs/backlog.md).

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
python -m gravewounds selfplay --field wanat-2008   # the enemy commander on both sides
```

`build.py` writes:

- `dist/rules.html`, the rule book: chapters in `templates/rules/*.md`, every number filled
  in from the data (`gravewounds/rulebook.py`, and `rulebook_later.py` for chapters 9-13);
  the index is gathered from the terms set in bold (`rulebook.index_terms`)
- `dist/roller.html`, `dist/travel.html` and `dist/field.html`
- `dist/tables.pdf` and `dist/tables.md`
- `dist/gravewounds-data.json`
- `dist/team.html`, the team builder (character generation)
- the start page `index.html`

## Next steps

From the design proposal (the rule changes from the rulebook comparison are agreed and
written in):

1. Playtest the stop check, graze, morale and battle map (with its ground, height and
   cover) in the roller and tune their numbers.
2. Playtest the travel map and the campaign and battle maps, then add maps for the other
   campaigns and battles.
3. Playtest the medieval character generation (the team builder) and make a team in 20
   minutes.
4. Playtest one fight with two teams, then a few weeks of camp, march and weather.

## Copyright and trademarks

© 2026 Scott Wares. All rights reserved.

Grave Wounds' rules, tables and text are its own. The design notes compare it with
Aftermath!, Rolemaster, Gamma World, Traveller and The Morrow Project, describing how those
games work in our own words; none of their rules text, tables or art is reproduced here.
Those names are trademarks of their owners, and Grave Wounds is not affiliated with or
endorsed by any of them. The wound data comes from published studies, cited in `data/`;
period pictures are linked from Wikimedia Commons, not copied; maps are drawn from
Natural Earth (public domain). The campaign and battle maps are drawn by us from
public-domain coastline and plain facts (where places are, what the accounts say), not
traced from any published map.

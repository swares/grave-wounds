# Morale and the rout: a redesign (proposal, for review)

This is a proposal, not the rules. It replaces the unit morale check and the rout strike
(docs/units.md, *Morale* and *The rout*) with a model built on what the sources support (the
project's `break-points-research.md`). Nothing here is built yet. Once agreed, it is built
alongside the present rules behind a setting, and kept only if it beats them on the tests at
the end.

## Why

The present rules:
- check every exchange once a unit is a quarter down, so any such unit breaks in the end;
- check a unit in contact whenever it loses more men than it puts down, however few of its men
  are touching the enemy;
- let every man of a unit beside a broken unit strike it in the rout, however few hexes touch.

Measured, these over-break long defences (Keating, X-Ray) and let a few dozen men at the edge
decide a battle of thousands (Agincourt). They also do a needed job: the drain is what breaks
the losers of short battles (Cowpens, the Monastery, Mons), and the rout strike is what gives
the losers most of their dead. Every piecemeal fix measured worse: 91 to 97 runs of 148,
against 96 to 98. So the model is replaced as a whole and tested as a whole.

## What the sources support (the targets)

These are the patterns a battle must show. Each is sourced; the numbers the rules use to get
there are not.

| | Target | Source |
|---|---|---|
| T1 | The losing side breaks having lost little: 5% or less in battles before 1914, most units under 10% after | Krentz; Sabin; McQuie (80 engagements, 1941-82) |
| T2 | Final losses about 2-3 to 1, loser to winner | Krentz (1:2.9); Helmbold; Bodart |
| T3 | Most of the loser's dead fall after it breaks, more so with horse to pursue | Clausewitz; Sabin; Krentz |
| T4 | Units quit mostly because they are outflanked, penetrated or left exposed, not because of their casualties | McQuie (manoeuvre 64%, casualties 10%); Rowland and Speight |
| T5 | The losses at breaking vary widely, from a few percent to most of the unit | Clark (43 WWII battalions: about 1% to nearly 100%) |
| T6 | Dug-in, cut-off small units can fight on far past any threshold | Wanat (about 75%), Keating |
| T7 | Losses follow the men actually engaged, not the whole unit | Osipov; Dupuy (company 21%, battalion 8%, brigade 1.8% a day); Lanchester fits |

No source gives losses a minute or an hour, so nothing below is fitted to a per-minute rate.

## The rules

### 1. A unit checks morale when something happens to it

A unit checks after an exchange in which any of these happened to it:

| Event | Was |
|---|---|
| **Hit hard:** a tenth of its men went down this exchange | the same |
| **Flanked:** struck in flank or rear | the same |
| **Losing the fight:** over its last three exchanges in contact, the men it lost exceed the men it put down by a twentieth of the men it has in contact (at least one) | lost more than it put down this exchange, by any amount |
| **A neighbour broke:** a unit of its own side within 2 hexes broke or fled this exchange | new (T4) |
| **Its leader fell:** its named leader went down this exchange | a modifier only |
| **A loss mark:** a quarter of its starting men are down for the first time, and again at half | every exchange once a quarter is down |

That is all. Nothing else makes it check, however many men it has lost. A unit a quarter down
that is not being pressed no longer drains away (T6). One that is being beaten still checks
every exchange through *losing the fight* or *hit hard*.

### 2. Its losses make each check harder, not more frequent

Nerve with modifiers, as now, but with the losses as a standing penalty:

| Modifier | |
|---|---|
| Still steady (ranks closed) | +20 (now) |
| A named leader with it, up | +10 (now) |
| Its leader down | −20 (now) |
| A quarter of its men down | −10 (new) |
| Half its men down | −20 (now; not added to the quarter) |
| Struck in flank or rear | −20 (now) |
| A steady friendly unit beside it | +10 (now) |
| Dug in: gone to ground or in a bunker | +10 (now) |
| Out of ammunition | −10 (now) |
| Losing the fight: for each twentieth of its men in contact more lost than put down (three exchanges) | −5, at most −30 (now: −5 a man) |

The modifier for losing is measured against the men in contact, so 10 men losing 3 to 1 count
for something, while 4,800 men of whom 10 are touching count only those 10 (T7).

### 3. What failing does (unchanged, with one fix)

- Steady, fails: shaken. It breaks at once instead if it fails by more than 20 while flanked
  or with half its men down.
- Shaken, fails: broken.
- Shaken, out of contact and not losing men: it checks each exchange to rally; passing, it is
  steady again; **failing, it stays shaken** (now it breaks).

### 4. The rout

A broken unit runs, as now. The pursuers strike it as now (+20, no parry, twice the tempo),
but only **the men of the pursuing unit in the hexes touching it** (its men a hex times those
hexes), not the whole unit (T7). Mounted pursuers strike at **twice** that again: horse ran
fugitives down (T3). In the dark, the pursuit strikes at half. The broken unit is struck each
exchange while pursuers keep contact, as now.

### 5. Holding a position (T6)

No new rule: dug-in units get +10 as now, and with the drain gone they no longer break from
the passing of time. If the tests show the small dug-in units still breaking where the
accounts say they held, a second step is a larger bonus for a unit in works or a bunker.

## The numbers, sourced or not

| Number | Value | Basis |
|---|---|---|
| Events that call a check | the six above | sourced in kind (T4); the list is ours |
| Losing window | 3 exchanges | ours: long enough that one exchange's luck does not decide |
| Losing margin | a twentieth (5%) of the men in contact | ours, set against T1 |
| Loss marks | a quarter, a half | the present thresholds |
| Neighbour range | 2 hexes | ours |
| Rout: mounted pursuit | ×2 | ours, set against T3 |
| Rout: in the dark | ×0.5 | ours |

Five numbers are ours. They are set by the tests below, against the targets, not against the
match count, and the rules say so.

## At the table

A GM running it by hand checks a unit when one of six things happens to it, and each has a
reason a player understands: they were hit hard, they were flanked, they are losing the fight,
the unit beside them broke, their leader fell, they have lost a quarter (or half) of their men.
That is fewer rolls than now, where every unit a quarter down rolls every exchange. Two things
to keep by hand: each unit's losses and kills over its last three exchanges (or the GM's
judgement of who is losing), and the hexes touching in a rout (already counted for who
strikes). The field page does both.

## How it is tested

Built behind a setting (`morale.model: events`, the present rules `drain`), both run on all 37
battlefields, twelve runs each, with the self-play tools. It is kept only if:

1. **Battles:** at least as many runs match as now (303 of 444).
2. **The targets**, from the runs:
   - T1: the median loss share of units when they break, by era;
   - T2: the loser-to-winner loss ratio, battle by battle;
   - T3: the share of the loser's dead that fell after breaking;
   - T4: how often a check came from being flanked or a neighbour breaking, against losses;
   - T5: the spread of loss shares at breaking;
   - T6: whether Keating, Wanat and X-Ray hold.
3. **The battles that need breaks** (Cowpens, Mons, the Monastery, Towton) still break.

The targets are reported beside the match count. Where they disagree, the targets win.

## What it does not change

The individual fight, wounds and stop checks; suppression and pinning; heroes; the commander,
except that it sees units break at different times.

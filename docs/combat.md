# Grave Wounds: one-page combat rules (playtest draft)

All the numbers below live in `data/wounds.yaml` (`combat:` and `tracking:`). The roller,
the Python engine and the printed tables read them from there, so change them there.

## A fighting turn (6 seconds)

1. **Initiative.** Fighters act from highest to lowest. A fighter who is down, out of the
   fight, or on a side that has broken does not act. A fighter who can only defend, or who
   is stunned, gets his turn but cannot attack.
2. **Move or stay.** See *The battle map* below. A fighter who runs does not attack.
   **Attack** only an enemy within the weapon's reach or range.
3. **Attack.** d100 against attack % minus the attacker's wound penalties and any range
   penalty. Equal or under hits. The margin is the effective chance minus the roll. A roll at or under a tenth of
   the effective chance is a critical, and a critical cannot be defended.
4. **Defence.** Optional: d100 against parry or dodge % minus wound penalties. Equal or
   under avoids the blow.
5. **Location and mechanism.** Roll on the era's hit-location table and the weapon's
   mechanism table.
6. **Severity from the margin.** Default: light below 20, serious from 20, critical from
   50 or on a critical roll. Firearms use their own bands by body zone.
7. **Graze.** A hit by a margin of 2 or less, if not a critical, only grazes. The wound's
   bleed and pain drop one step each, and it calls for no stop check.
8. **Armour.** The armour on the location lowers severity by its steps against the
   mechanism. A gap in coverage means no armour.
9. **Wound.** Record it. Its bleed, pain, impairments and lethality clock take effect.
10. **Stop check.** A serious or critical wound calls for d100 against the fighter's
    Nerve, if the wound is marked for one (most are; some limb wounds are not). The target
    is Nerve minus his pain and blood-loss penalties, and −10 more for a critical wound.
    - Equal or under: he fights on.
    - Failed by 1–20: **defend only** for 2 rounds.
    - Failed by 21–40: **stunned** for 2 rounds (cannot attack, −50% defence).
    - Failed by more than 40: **out of the fight** until helped or the fight ends.

    A worse result replaces a milder one. The round a result happens in counts as the
    first of its rounds: a fighter who fails on round 3 is defend only for rounds 3 and 4.

## End of the round

- **Bleeding.** Every casualty loses Blood at his bleed rate. Blood thresholds bring
  penalties, then collapse, then unconsciousness.
- **Results wear off.** Defend-only and stunned results count down a round.
- **Pain.** A fighter whose total pain is above the cap (3 steps, −30%) makes a stop
  check every round, as for a serious wound.
- **Team morale.** A side with at least a quarter of its fighters down rolls d100. The
  target is the best Nerve among its fighters still up (its leader's, if he is up), then:
  - +10 if a leader is up
  - −20 if a leader is down
  - −20 once half the side is down

  Over the target: the side breaks and runs or surrenders. A side keeps checking each round
  while a quarter or more is down.

## The battle map

The battle map is at the top of the roller page. Once an attacker and a defender are
chosen, its bar has **Roll the hit** and, after a hit, **Apply hit**, with the last roll in a
few words; the Strike panel below keeps the attack and defence figures and the full result.

One hex is about 2 yards (2 m) and a round is 6 seconds. On his turn a fighter may:

- **Stay** where he is.
- **Advance** up to 4 hexes and still attack.
- **Run** up to 12 hexes and not attack this turn.

He may pass through friends but not stop on them, and cannot enter an enemy's hex.

**Wounds and movement.**

- A leg or move impairment halves both distances, rounding down: advance 2, run 6.
- Collapse or cannot stand: he can only crawl 1 hex.
- Winded (the breath impairment): he cannot run.
- Stunned or out of the fight: he cannot move.
- Defend only: he may move, but not attack.

**Leaving contact.** If he moves more than 1 hex and ends no longer next to an enemy he
started beside, that enemy gets one free attack on him, if the enemy is up and able to
attack. Stepping back 1 hex is a careful withdrawal and draws no free attack.

**Reach and range.**

- Close-combat weapons strike enemies within their reach. Reach 1 is the next hex;
  spears, bills and lances have reach 2.
- Missile weapons have short, medium and long range in hexes: +0, −20% and −40% to hit.
  There is no shot past long range.
- Artillery, mines and stakes are not aimed on the map; the GM decides whom they hit.
- The printed tables list every weapon. The ranges are design estimates from each
  weapon's effective range in its period.

## Works

Ditches, banks, palisades, gates, stakes, wagons and other works change movement, cover
and close combat on the battle map. A fighter can spend his attack breaching one. See
[works.md](works.md).

## Weather

Rain, wind and fog affect missile attacks, wet weather makes firearms misfire, deep mud
or snow slows movement, and fatigue costs attack and defence. See [weather.md](weather.md).

## Nerve

Set by experience: green 35, regular 50, veteran 65, or any number your game prefers.
Nerve is used for the stop check and for team morale.

## In the roller

- Each fighter card has **Side**, **Leader** and **Nerve**.
- **Apply hit to defender** rolls the stop check. Type your own die in **Stop d100** or
  leave it blank.
- **Next round** and **Next fighter** count results down and roll morale. Type your own
  die in **Morale d100** or leave it blank.
- **Clear** removes a stop-check result, for example after first aid or a rally.
- **Reset count** also rallies broken sides.
- **Battle map.** New fighters are placed near their side's edge. Before the turns start,
  click a fighter and then an empty hex to move him; **Free placement** does the same at
  any time.
  - Once **Next fighter** starts the turns, the acting fighter's hexes are shaded: green to
    advance and still attack, sand to run.
  - Enemies his weapon can reach are ringed; click one to make him the defender. The roller
    refuses an attack out of reach, or after a run, and takes the range penalty off the
    attack.
  - **Stay** keeps him in place; **Undo move** takes a move back.
  - A free attack is set up for you: roll the hit and apply it, or **Skip** it. The token
    has moved already, so if the free attack stops him, use Free placement to put him
    back where he was hit.

These are first-draft numbers for playtesting. The design notes in
[design.md](design.md) say what they should be calibrated against: how often wounded men
really stopped fighting.

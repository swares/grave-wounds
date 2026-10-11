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
- **In the way.** Each fighter standing on the line between a shooter and his target
  (friend or foe, not down) costs the shot 10%, at most 30%. If the shot misses, it goes into
  the first man in the way at 50%: the Strike panel and the map's bar offer **Roll the hit on**
  him, which rolls his hit with no attack roll and the severity table. Bows and crossbows
  loose high over the men in the way: they take the penalty but never strike them.
- Artillery, mines and stakes are not aimed on the map; the GM decides whom they hit.
- The printed tables list every weapon. The ranges are design estimates from each
  weapon's effective range in its period.

## Ground and height

The GM can paint the battle map with **Paint ground**: rocks and rubble, woods and brush,
marsh, deep water, road, bridge, and hexes raised a level at a time (0 to 3). Painted hexes
show a small mark; raised hexes are shaded, darker the higher they are.

**Laying out ground.** A fight sent from the travel map lays out its ground to match the
defenders' travel hex: irregular clumps of woods, rocks and marsh, and a rise or two, in the
shares the terrain gives (for example, about half the hexes wooded in forest, a tenth rocky
and up to three levels high in hills, a third marsh in marsh, a fifth rubble in a town).
Inside a camp's works the ground is cleared and levelled to the camp's middle. The same
fight always lays out the same ground. In the Paint ground bar, **Ground like** and **Lay out
ground** do the same for any fight; pressing it again for the same country gives another
layout. Paint any hex to change it. The shares are design estimates, in `data/wounds.yaml`
under `combat.ground.seed`.

**Roads and rivers through the hex.** A force in a road, ford or bridge hex (or a village or
town on a road) is on the road or at the crossing. So the road runs through the middle of
the battle map toward each neighbouring road, bridge, ford, village or town hex, 2 to 3 hexes
wide; there is a junction where more than two meet. At a ford or bridge hex the river runs
through the middle too, 8 to 25 hexes wide, toward the neighbouring river, ford, bridge or
lake hexes. At a ford the road crosses by a ford 3 to 6 hexes wide (marsh to wade), or straight
across the middle when no road comes; at a bridge it crosses by a bridge as wide as the road.
A road is clear, open going, no faster than open ground at 2 yards a hex. A camp at a crossing
is cleared inside its works, so the river shows only outside them.

**The hexes around.** A travel hex is 0.6 to 3 miles (1 to 5 km) across and the battle map at
most about 175 by 115 yards (160 by 105 m), so the fight stands at a fixed spot inside its
travel hex. Where the map reaches past a side of the hex, the ground beyond that side is laid
out like the neighbouring hex: woods beyond a forest edge, rises beyond a hill edge. A lake
beyond is deep water. A river beyond is a band of deep water 8 to 25 hexes wide with open
ground on the far bank, and when a ford or bridge is next to the hex, a ford 3 to 6 hexes wide
(marsh to wade) crosses it near the middle of the map's side. The map's message gives how far
the fight is from each side it reaches. In a large hex this happens seldom, as it should.

**Where the attackers come in.** Attackers arrive on the map's edge facing the way they came
on the travel map, on the dry hexes nearest it: across a river they stand on the far bank or
at the ford. Attackers already in the defenders' own travel hex come in at their side's far
edge.

- **Movement.** Entering rocks or woods costs 1 extra hex of movement, marsh 2; each level
  climbed costs 1 more. No one enters or stands in deep water, but shots cross it.
- **Cover.** A shot at a man in rocks is −10% and the rocks hide his legs, so the table's
  *behind cover* situation applies. In woods the shot is −20%. Where a work also gives cover,
  the better of the two counts.
- **Higher and lower.** An attacker above his target gets the *attacker higher* situation
  (blows and shots come down on the head and shoulders); one below gets *attacker lower*.
- **Fighting uphill.** A close-combat attack on a man higher up is −10% for each level,
  at most −20%.
- **Shooting downhill.** A shot from higher ground reaches 10% further for each level.
- **Line of sight.** Higher ground rising above the straight line between a shooter and his
  target blocks the shot. Men in the way who stand below that line are shot over and do not
  count.
- **Take cover.** Instead of moving or attacking, the acting fighter can **Take cover**. Until
  he moves or strikes in close combat, shots at him are −20% (or the ground's cover, if
  better) and hit as *behind cover*, and blows at him hit as at a man *down*. His token gets a
  dotted edge. **Undo move** takes it back.

The roller sets these situations and penalties itself once the turns start; they show in
the Strike panel's line under the result.

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
  - **Stay** keeps him in place; **Take cover** puts him to ground for the turn; **Undo
    move** takes a move or the cover back.
  - A free attack is set up for you: roll the hit and apply it, or **Skip** it. The token
    has moved already, so if the free attack stops him, use Free placement to put him
    back where he was hit.

These are first-draft numbers for playtesting. The design notes in
[design.md](design.md) say what they should be calibrated against: how often wounded men
really stopped fighting.

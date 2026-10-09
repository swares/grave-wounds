# Grave Wounds: one-page combat rules (playtest draft)

All the numbers below live in `data/wounds.yaml` (`combat:` and `tracking:`). The roller,
the Python engine and the printed tables read them from there, so change them there.

## A fighting turn (6 seconds)

1. **Initiative.** Fighters act from highest to lowest. A fighter who is down, out of the
   fight, or on a side that has broken does not act. A fighter who can only defend, or who
   is stunned, gets his turn but cannot attack.
2. **Attack.** d100 against attack % minus the attacker's wound penalties. Equal or under
   hits. The margin is the effective chance minus the roll. A roll at or under a tenth of
   the effective chance is a critical, and a critical cannot be defended.
3. **Defence.** Optional: d100 against parry or dodge % minus wound penalties. Equal or
   under avoids the blow.
4. **Location and mechanism.** Roll on the era's hit-location table and the weapon's
   mechanism table.
5. **Severity from the margin.** Default: light below 20, serious from 20, critical from
   50 or on a critical roll. Firearms use their own bands by body zone.
6. **Graze.** A hit by a margin of 2 or less, if not a critical, only grazes. The wound's
   bleed and pain drop one step each, and it calls for no stop check.
7. **Armour.** The armour on the location lowers severity by its steps against the
   mechanism. A gap in coverage means no armour.
8. **Wound.** Record it. Its bleed, pain, impairments and lethality clock take effect.
9. **Stop check.** A serious or critical wound calls for d100 against the fighter's
   Nerve, if the wound is marked for one (most are; some limb wounds are not). The target
   is Nerve minus his pain and blood-loss penalties, and −10 more for a critical wound.
   - Equal or under: he fights on.
   - Failed by 1–20: **defend only** for 2 rounds.
   - Failed by 21–40: **stunned** for 2 rounds (cannot attack, −50% defence).
   - Failed by more than 40: **out of the fight** until helped or the fight ends.

   A worse result replaces a milder one.

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

These are first-draft numbers for playtesting. The design notes in
[design.md](design.md) say what they should be calibrated against: how often wounded men
really stopped fighting.

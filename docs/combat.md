# Grave Wounds: one-page combat rules (playtest draft)

All the numbers below live in `data/wounds.yaml` (`combat:` and `tracking:`). The roller,
the Python engine and the printed tables read them from there, so change them there.

## A fighting turn (6 seconds)

1. **Initiative.** Fighters act from highest to lowest. A fighter who is down, out of the
   fight, or on a side that has broken does not act. A fighter who can only defend, or who
   is stunned, gets his turn but cannot attack. Nor can a fighter with an arm hurt (an arm
   wound, a lost grip, a useless hand or arm, on either side) attack with a two-handed
   weapon: a bow, crossbow, musket, rifle, machine gun, rocket launcher, bill, pike, halberd,
   poleaxe, bayonet or clubbed musket. He can only defend until he takes up a one-handed weapon.
2. **Move or stay.** See *The battle map* below. A fighter who runs does not attack.
   **Attack** only an enemy within the weapon's reach or range.
3. **Attack.** He may first declare an aim: at a zone (head, body, arms, legs), at a gap
   in the armour, or both. d100 against attack % minus the attacker's wound penalties and any range
   penalty. Equal or under hits. The margin is the effective chance minus the roll. A roll at or under a tenth of
   the effective chance is a critical, and a critical cannot be defended.
4. **Defence.** Optional: d100 against parry or dodge % minus wound penalties. Equal or
   under avoids the blow.
5. **Aim.** On a hit, each aim paid costs 20 of the margin (nothing on a critical); one he
   cannot pay fails. A zone paid for rolls the location within that zone only; a gap is paid
   for only where the armour covers part of the place hit, and the blow finds it. Severity
   and graze come from the margin left.
6. **Location and blow.** Roll on the era's hit-location table. A cut-and-thrust weapon
   (sword, spear, bill, halberd, poleaxe, dagger, sabre, bayonet) strikes the blow the
   attacker declares: cut, thrust, or a crushing blow with a bill, halberd or poleaxe. Any
   other weapon strikes with its main mechanism. Unnamed fighters strike with the main
   mechanism on paper; the roller and the field map roll their mix.
7. **Severity from the margin.** Default: light below 20, serious from 20, critical from
   50 or on a critical roll. Firearms use their own bands by body zone.
8. **Graze.** A hit by a margin of 2 or less, if not a critical, only grazes. The wound's
   bleed and pain drop one step each, and it calls for no stop check.
9. **Armour.** The armour on the location lowers severity by its steps against the
   mechanism. Where it covers only part of the location (a sleeve to the elbow, a plate on the
   chest), the attack roll's units digit (0 is 10) says whether the blow met it: at or under
   its cover in tens (a 70% sleeve on 1-7) it did; above, it found a gap and there is no armour.
   No extra roll.
10. **Wound.** Record it. Its bleed, pain, impairments and lethality clock take effect.
11. **Stop check.** A serious or critical wound calls for d100 against the fighter's
    Nerve, if the wound is marked for one (most are; some limb wounds are not). The target
    is Nerve minus his pain and blood-loss penalties, and −10 more for a critical wound. A player
    character's lethality setting may add to his Nerve or spare him the check below critical, and
    his fate points can lower a wound a step or roll the check again (rule book, Lethality).
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
  - while a leader is up, (Presence − 50) ÷ 5 more, rounded down: +4 at Presence 70, −3
    at 35 (50 without a team-builder sheet)

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
  spears, bills, halberds and lances have reach 2, the pike 3.
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
A road is clear, open going, no faster than open ground at 2 yards a hex.

**A camp at a crossing.** A camp with works at a ford or bridge stands on one bank, not
astride the river: the river passes it at least 3 hexes beyond its outer works, on the side
toward the way the attackers came, so they must cross by the ford or bridge. When they came
along the river, the bank is fixed for the fight. The road still runs out of the camp to the
crossing. The battle map grows to make room, up to 80 by 60 hexes, and the camp moves back
from the middle, away from the river, just as far as the river at its widest and 2 hexes of
its far bank need, keeping 2 hexes of map behind its works. If the river still does not fit,
it is narrowed, to no less than 8 hexes, and the rest runs off the map. The camp's gate faces
the crossing (toward where the road meets the river, or straight at the river when no road
goes that way), and the road to the river leaves by it. A camp too big for the whole map moves
back as far as the river needs, and only the stretch facing the river and the crossing, with
its gate, is shown. (Camps away from a crossing keep their main gate on the east, and a camp too
big for the map shows the stretch with its gate, facing the attackers.)

**Gates on the roads.** A camp with works on a road (in a road, ford, bridge, village or town
hex) has a gate, or a gap in its stakes, wherever a road leaves it, besides its main gate; the
roads run out from the camp's middle through them. At a crossing the road to the river
leaves by the main gate.

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
at the ford. Attackers who have marched into the defenders' own travel hex come in from the
side of the hex they last left. Only when that is not known (a game saved before this, or a
force that has not marched) do they come in at their side's far edge.

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
  dotted edge. **Undo move** takes it back. Getting up again takes 2 hexes of his move: moving
  out of cover, everything costs 2 more, and a blow in close combat from cover spends those 2
  hexes first (a man who can only crawl cannot get up and strike). He may shoot from cover,
  kneeling or lying, without getting up, and stays in cover.

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

## Characteristics in the fight

A fighter from the team builder brings his sheet's characteristics. Anyone else counts as
50 in each, which changes nothing. All are design estimates, rounded down (Toil to the nearest):

| Characteristic | In the fight |
| --- | --- |
| Agility | **Roll initiative** gives d10 + Agility ÷ 10 (the GM can still type any number) |
| Endurance | Blood pool 20 + (Endurance − 50) ÷ 10: 16 at 15, 24 at 95. The Endurance on his card sets it |
| Strength | Toil: each hand-to-hand exchange he attacks or defends in counts. After 30 in light kit, 20 in medium or 12 in heavy, times Strength ÷ 50 (rounded to the nearest), he is a fatigue step worse, to Exhausted at most. Shooting costs none |
| Presence | A leader who is up adds (Presence − 50) ÷ 5 to his side's morale |

**Load and Strain.** A team-builder man's load band (the **Load** select on his card) costs
Dodge: 10 Light, 20 Medium, 35 Heavy, 50 Overloaded, 75 Immobile; Overloaded or Immobile, he
cannot run (`data/loads.yaml`; [travel.md](travel.md), *Loads*). His Strain state costs attack and
Nerve: shaken −10, strained −20; broken down, he is out of the fight (`data/stress.yaml`
`results`; [team.md](team.md), *Strain*).

**First aid.** On a side with any team-builder character, the best Leechcraft among them
still up rolls d100 for each **Bind**, **Tourniquet** or **Cauterise**. Success: a bind stops
two steps of bleeding instead of one, and cautery adds no pain. Failure: nothing happens;
try again. A side with no sheets treats as before, unrolled. The note under the strike
panel says who rolled what.

**Surprised.** A fight set up from the travel map may catch the defenders unawares (see
[works.md](works.md), *Surprise*). Then the defenders and their friends start **Surprised**:
they cannot attack or move in round 1.

Heavy kits are full plate and the transitional harness, the Danish man-at-arms, the 1630
cuirassier, the First World War sentry's armour, the aircrew flak suit and the Interceptor
vest. Mail, jacks, brigandines, the 1630 harquebusier and pikeman, the Napoleonic
cuirassier, the Gotland armoured man, the Marines' Vietnam vest, PASGT, the Rangers' 1993
kit and the plate carrier are medium. The rest are light, unarmoured included. The fatigue select on the card still lets the GM set it by hand, and the toil
count goes on from there.

## In the roller

- Each fighter card has **Side**, **Leader** and **Nerve**, and **Endurance** with **With**:
  put him with a force on the travel map, and its days run his own sickness, which weakens
  him here (see [travel.md](travel.md), Disease).
- **Apply hit to defender** rolls the stop check. Type your own die in **Stop d100** or
  leave it blank.
- **Roll initiative** rolls every fighter's initiative and puts them in order.
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
- **Event log** (under the cards) records each strike and each wound applied, in order,
  with every die it used: the ones the player typed in are marked \*, the rest were rolled.
  **As seen by** shows the log as the GM sees it (everything) or as one side does. A side
  sees its own men's wounds in full; of the other side's it sees only what the table would:
  the outcome, where a blow landed, the attack and defence rolls, and whether the man fell.
  It also records initiative (for all), each side's Blood lost at the round's end (for that side),
  morale checks (the roll for that side, whether it held or broke for all), first aid, the stop
  checks for pain at the round's end, hazards (swimming, climbing, falls, chases), words across
  tongues, deeds and loot (each for the man's side). **Save this view** downloads that side's view as a file. The log is kept with the fight in
  the browser (the last 500 events); the examples on a fresh page and the roll the page opens
  with are not logged.
- **Run the fight** (above the round log) lets the page run the turns. Tick it and choose, for
  each side, who plays it: **Player**, **GM by hand**, or **GM's script**. A side with team-builder
  men starts as Player, the rest as the script. Solo play is your side as Player and the enemy
  as the script; GM assist is the players' sides as Player and the enemy as GM by hand.
  - On a scripted fighter's turn the script moves him (or puts him to ground), picks whom to
    strike and strikes, rolling his dice for him. It strikes the most hurt enemy in reach, then
    the easiest, then the nearest; closes when no one is in reach; and a shooter keeps his
    distance. A named man declares a thrust at an armoured enemy and a cut at an unarmoured one;
    unnamed men strike their weapon's mix. He aims for a gap only in part-covered armour and with
    attack to spare.
  - **How boldly** the script plays each side: *cautious* men fall back when they have lost
    four tenths of their Blood, or when their side is near breaking, and never run to close;
    *steady* men fall back at about a third of their Blood left; *reckless* men never fall back.
  - **Quality** gives men with no team-builder sheet their attack, defence and Nerve (green,
    regular or veteran, as units.yaml); men with sheets use their sheets.
  - While the fight is run, a hit goes on the defender at once (no Apply to click), and there is
    no parry or dodge against a shot.
  - **Step** plays one step of the script (a move, a strike, or handing on to the next fighter);
    **Play to my turn** plays on until a person must choose; with **Play the script by itself**
    ticked, the script plays on after each Next fighter. **Undo the script** puts the page back as
    it was before the script's last step.
  - In the event log the script's moves are public; why it chose them is for the GM.
- **Screen** (in the Run the fight panel) shows the page as the GM sees it (everything) or as one
  side does. On a side's screen an enemy's card shows his name, side, kit, weapon, where he has
  been hit and whether he is down or shaken, but not his Blood, his wounds' effects, his
  penalties or his Nerve. His attack and defence % are blurred in the roll form; a blow on him
  shows where it landed, not how badly; the Apply message says only where he was hit and whether
  he fell; the round log leaves out his Blood, wounds and stop checks; and the event log shows
  that side's view only. In solo play (one side yours, the rest the script's) Run the fight
  starts on your side's screen. It is a screen filter, not a lock: the rules do not change, and
  the GM can switch back. Online (below), a player's page is sent only this view.
- **Play online** (under Run the fight) lets players join from their own computers, with the GM's
  page as host. There is no server: the GM clicks **Invite a player for** a side and sends the
  player the link it gives; the player opens it, and his page shows a reply code he sends back;
  the GM pastes it under that side and clicks **Connect**. The side is then a player's (Run the
  fight turns on if it was off), and the GM's page stays on the GM's screen.
  - After every change the GM's page draws the fight as that side's Screen shows it and sends
    that drawing to the player: the enemy's Blood, wounds' severity and effects, penalties and
    stop checks never leave the GM's page. While the enemy acts, the player sees that he acts, not
    how far he could have gone.
  - On his page the player clicks hexes and enemies on the map, uses Stay, Take cover, Undo move
    and Next fighter, and rolls his strike with his own aim, gap, blow and any dice he types.
    The GM's page makes each choice only if it is his to make (his side's fighter on its turn, or
    his free attack), through the same functions as its own buttons. The GM's script plays on
    after his Next fighter.
  - He gives first aid to his own side's men from their cards (Bind, Tourniquet, Cauterise), on his
    side's turn, as the GM's buttons give it (his side's best Leechcraft rolls). First aid, by anyone,
    goes into the event log for that side and the GM.
  - **Use a public STUN server** (on by default) lets the pages find each other across the
    internet through stun.l.google.com; on one network it is not needed. There is no relay
    (TURN), so a few strict networks (some offices, some mobile networks) will not connect.
  - A short drop (the network blinks) mends itself, and the player gets his screen again. A
    player lost for good (his page closed, the network gone) shows as lost on the GM's page with
    **Invite again**: a new link for the same side, in the same row; his side waits for him on its
    turns meanwhile (or the GM plays it: Run the fight, GM by hand). His page keeps his side's last
    screen, says he is lost, and takes the new link pasted into **Rejoin** (or opened in that tab);
    reloaded, it shows that last screen at once while it rejoins. If the GM's page is reloaded,
    Play online remembers which sides had players (in that browser tab) and offers Invite again for
    each. Every rejoin still passes a link and a reply by hand: no server. The GM's page sends his
    whole screen when he connects (tens of kB), then only the panels that changed, each as its
    changed tags (a few hundred bytes for a wounded man's card; a map that lights every hex for his
    turn still goes nearly whole); his page puts them over the last screen, and shows only what it is sent.
  - `node tools/net/test.mjs` tests the codes, the message pieces and the changes; `python3 tools/net/twopages.py`
    connects a GM's page and a player's page in a headless browser, plays a turn from each, then
    checks that after the first screen only changes go and that they add up to the GM's screen for his side,
    loses the player and brings him back (Invite again, Rejoin, a reload on either side)
    (in CI, with the other browser tests: `.github/workflows/browser.yml`).
  - The script's choices are design guesses, not calibrated against any record.
    `python3 tools/gm/selfplay.py` plays it against itself on a spread of tables and checks every
    fight runs to an end (in CI too); `node tools/gm/test.js` checks its choices one by one.
  - In the campaign console's frame, the console can work Run the fight (on, Step, Play to my turn,
    Undo, a person's turn ended) and mark the winner; the roller tells it how the fight stands
    (`docs/campaign.md`).

**How the roller decides a strike.** The attack, defence, location, blow, severity and armour
are worked out in `templates/strike.js`, which never touches the page: the page measures the
situation (range, cover, wounds, armour), passes what the player declared and any dice he
typed, and shows the result. The log is `templates/gamelog.js`. This is the start of the
virtual GM: the same rules can then be driven by a scripted GM, or by a host sending each
player only his side's view. `python3 tools/strike/parity.py` plays thousands of strikes through
it and through `gravewounds.engine.roll_hit` on the same dice and checks they agree, then runs
its tests (`tools/strike/test.js`).

These are first-draft numbers for playtesting. The design notes in
[design.md](design.md) say what they should be calibrated against: how often wounded men
really stopped fighting.

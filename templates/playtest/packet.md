<!-- page -->
# Grave Wounds {.cover}

## Playtest packet: one fight and a week in camp

Version {{pt_version}}, for 3 to 5 people and about 3 hours. One person is the GM.

**What this is.** Grave Wounds is a d100 game built on real wound records. Where a man is hit comes from
the graves and surgeons' returns of his own war. A fight usually ends with men stopping, not dying, and
what happens afterwards can kill them just as well. This packet sets four men of a Yorkist retinue at a
crossing of the River Aire on 28 March 1461, the day before Towton. They fight once, and then have to
get through a week in camp.

**What we want to learn.** Are the fights tense and quick enough? Do wounds feel fair? Are the camp's
decisions interesting, or a chore? Nobody has played this at a table yet, so a blunt "this dragged" is
the most useful thing you can tell us.

**What you need.** Pencils, two ten-sided dice for d100, scissors, and these pages. Everything to play on
paper is here, with a hex map of the ford and counters to cut out at the back. If you'd rather, a phone or
laptop can run the fight: **the wound roller does the arithmetic**. Open
[{{pt_link_short}}]({{pt_link}}). It sets up the four men against Clifford's five, and the GM's script
can play the enemy. Please tell us which way you played.

| Pages | Who needs them |
| --- | --- |
| The fight, Wounds, Where it lands, What it does | Everyone |
| The camp | Everyone |
| Four character sheets, and a blank one | One to a player |
| The crossing, The week | The GM only |
| Camp log and session log, Feedback | The GM fills these in, with the table |
| At the back: the quick reference, the map, the counters, the enemy's roster | On the table. Print the reference once for each player, and the map and counters at actual size (100%) |

**What's where.** Printed on both sides, a page marked *own sheet* has a blank back, so it can be handed out or cut up alone.

@@contents@@

**Which setting?** Play **Standard** first. If you play again, try **Gritty**. The sheets show both.

**After you play.** Send the feedback pages, or a photo of them, to [{{pt_email}}](mailto:{{pt_email}}). To
hear about later versions, sign up on the [start page]({{pt_site}}). For a quick comment, use [the feedback form](https://docs.google.com/forms/d/e/1FAIpQLSfGgYKRfBpDth3odGXHWHI1iXSNCmscYczxBW7BE_2Pv9-Hwg/viewform).

**This packet** is free to copy and share for playtesting. It is an early version: please don't sell it or
post it as finished. The numbers and tables are generated from the game's own data.

<!-- page -->
# The fight {#fight}

A round is 6 seconds. Every fighter gets one turn, highest **initiative** first. Each man rolls once at the
start: d{{init_die}} + Agility ÷ {{init_per}}, rounded down.

**The one roll.** Roll d100. Equal to or under the number succeeds, and how far under is the **margin**. A roll
at or under a tenth of the number is a **critical**.

**On his turn**

1. **Move.** Stay, **advance** up to {{advance}} hexes and still attack, or **run** up to {{run}} and not attack.
   Walking away from an enemy beside you gives him a free attack.
2. **Attack.** d100 against Attack, less your penalties. You may first declare an **aim** at a zone, at a gap in
   the armour, or both. Each costs {{aim_cost}} of your margin on a hit, and is free on a critical.
3. **Defence.** The defender rolls d100 against Defence, less his penalties. Success turns the blow. A critical
   can't be defended.
4. **Where it lands.** d100 on *Where it lands*, under the attacker's weapon. With a sword, bill or dagger, the
   attacker chooses **cut** or **thrust** before he rolls. A longbow pierces.
5. **How bad.** Margin under {{band_serious}}: **light**. {{band_serious}} or more: **serious**. {{band_critical}}
   or more, or a critical: **critical**. A margin of {{graze}} or less only **grazes**, unless it is a
   critical: a step less bleeding and pain, and no stop check.
6. **Armour.** Armour lowers the severity by steps. See *Where it lands*.
7. **The wound.** Read it from *What it does* and write it on the sheet.
8. **Stop check.** A serious or critical wound marked **S** needs d100 against the wounded man's Nerve, less his
   pain and blood penalties, and {{crit_stop}} more for a critical. Players' men add their setting's bonus.

{{table:stop}}

**End of the round.** Everyone bleeds. Then a side with {{morale_trigger}} or more of its men down rolls d100 against
the best Nerve among those still up: +{{leader_present}} while a leader is up, −{{leader_down}} if he is down, −{{heavy_losses}} once
{{morale_heavy}} of the side is down. Over the target, the side breaks: it runs or surrenders.

**Lethality.** Standard: Blood ×1.5, +20 to Nerve on stop checks, and one **fate** point, which lowers a wound a
step, or rerolls a stop check, recovery or fever roll. Gritty: Blood ×1, no bonus, no fate.

!!! example "A worked blow"
    Gilbert shoots at {{pt_gil_attack}}% and rolls 31: a margin of {{pt_gil_margin}}, **serious**. The billman dodges
    at {{pt_foe_def}}% and rolls 72, so it hits. On the longbow column, a 40 is the right chest. His jack would lower
    the wound a step, but the war bow takes a step off armour, so it stays serious. The thrust table gives bleed 2,
    pain 2, and **S**, so he loses 1 Blood a round and makes a stop check: Nerve {{pt_foe_nerve}}, less {{pt_foe_pain}} for pain.

<!-- page -->
# Wounds {#wounds}

A wound has five parts, and they add up across all of a man's wounds.

**Bleeding.** Every man has a **Blood** pool, on his sheet.

{{table:bleed}}

{{table:blood}}

**Pain.** −{{pain_step}}% to attack and defence for each step, counted to {{pain_cap}} steps. Above that, a stop check every round.

**Impairments.** Each counts once. Attack and defence penalties are capped at −{{cap}}%.

{{table:impair}}

**The clock.** How long the wound takes to kill if left untreated: days, hours, minutes, rounds or instant.

**A man with an arm hurt** can't use a two-handed weapon: a bow, a bill or a poleaxe. He can only defend until he
takes up something else.

**First aid.** A friend beside him may treat a wound on his turn. Roll d100 against the side's best Leechcraft:

- **Bind:** one step less bleeding, {{bind_skilled}} steps on a success.
- **Tourniquet:** an arm or leg only. The bleeding stops. Left on for hours, the limb is lost.
- **Cauterise:** the bleeding stops, at one more step of pain. A success adds no pain.

<!-- page -->
# Where it lands {#where}

Roll d100 under the attacker's weapon. These odds come from the Towton table, adjusted from the bone evidence for
wounds that leave no mark on bone.

{{pt:hit}}

**Armour.** Each kit below gives steps off the severity, Critical to Serious to Light to Stopped. A stopped blow
is only a bruise. Where a place is only partly covered, read the **units digit of the attack roll**, with 0 as 10.
At or under the cover shown in tens, the blow met the armour.

{{pt:armour}}

A longbow's arrows take 1 step off the armour's pierce figure, so a jack gives them nothing and a brigandine only 1.

**Range.** A longbow reaches {{pt_bow_range}} hexes: short, medium and long. Each hex is {{hex_yd}} yards. On paper take −20 at medium range and −40 at long; the roller does it for you. On the map, count the hexes between the two men; to a man still on the approach track, count the hexes to the map's north edge and add his box number.

<!-- page -->
# What it does {#effects}

Find the place and the blow. Each entry gives **bleed** and **pain**, then **S** if it calls for a stop check, then how long it
takes to kill and any impairments. Fever is the risk of wound fever in camp. A longbow's wound uses the thrust columns. A knee or
foot may not bleed at all.

{{pt:effects}}

<!-- page -->
# The camp {#camp}

After the fight, each day runs the same way. Use the camp log.

1. **Evening council.** The four roles decide, in this order. A role with nothing to decide is skipped.
    - **Leader:** stay, move, and what kind of camp.
    - **Scout:** where to go, and how the watch is set.
    - **Quartermaster:** what the men eat, and what they try to find.
    - **Leech:** who gets the medical stores, and how clean the camp is kept.
2. **The day's weather** is on the GM's page, and it can make a night hard.
3. **The night.** A man in camp gets back {{blood_night}} Blood.
4. **Wound fever.** On the {{fever_lo}}rd to {{fever_hi}}th day after the fight, roll once for each wound: {{fever_low}}%
   for low risk, {{fever_medium}}% medium, {{fever_high}}% high. Add {{fever_nocamp}} with no camp, take off {{fever_quarters}}
   in quarters, and take off a leech's Leechcraft ÷ 10. A septic wound moves a step worse, and is checked every night.

**Every 7 days: the recovery check.** Each wound rolls d100 against the man's **Endurance**, plus:

{{table:recovery}}

Succeed by {{big}} or more: two steps better. Succeed: one step better. Fail: it holds, and at *deadly* he dies. Fail
by {{big}} or more: one step worse. A wound starts on the track at its severity: light is **mending**, serious is
**serious**, critical is **grave**. A wound that would kill in days starts at serious at least, and one that would
kill in hours or less at grave.

{{table:track}}

**Every 7 days: sickness.** Each well man rolls d100. At or under the chance, he has the flux. A day or so later, roll d100 for how bad: 1–3 **deadly**, 4–15 **grave**, otherwise **serious**.

{{pt:sickness}}

**Food.** A man carries {{pt_rations}} days' rations. With none left he goes hungry, so forage, buy or move while you can. **Hunting** in open
country or woods: the Quartermaster rolls Fieldcraft at nightfall. A deer feeds {{hunt_deer}} men for a day.

**Camps.** A **bivouac** needs nothing, and is poor hygiene. A **watched camp** needs nothing. **Quarters** in houses need
the quartermaster to roll Persuade, and he must find somewhere that will take them.

{{pt:sheets}}

<!-- page -->
# The crossing {#crossing}

*For the GM.*

**Where and when.** Ferrybridge, on the River Aire, before dawn on 28 March 1461. The Lancastrians broke the bridge, and
Warwick's men forced the crossing on the 27th. Before dawn Lord Clifford's men fall on the Yorkist camp there. Lord
Fitzwalter is mortally wounded rallying his men. That much is history. Our four men, and the small ford they hold just
upstream, are ours.

**Read this out.** *It is dark and bitterly cold. You've been set to watch a ford a bowshot from the broken bridge, in case
anyone tries to come round. Then the shouting starts behind you at the bridge, and men with no badges you can see come
wading out of the dark.*

{{pt:map}}

**The enemy.** Five of Clifford's men, all regulars. They are on foot here. On the roller they are already set up.

{{pt:foes}}

**How it runs.**

1. **Set-up (10 minutes).** Hand out the sheets and pick the setting. Each player places his man south of the water, on the map at the back. Clifford's men start on box {{pt_track}} of the approach track, 30 hexes away; the GM keeps their numbers on the roster.
2. **Arrows (2 rounds).** Gilbert may shoot as they come on and wade, and Clifford's archer shoots back.
3. **The fight (45 to 60 minutes).** They close. Keep a note of the time.
4. **The end.** The side's nerve check decides it (*The fight*). A man who surrenders is a prisoner, and the Leader decides what happens to him. **If the four lose,** the game goes on: Yorkists come up from the bridge at sunrise, Clifford's men fall back north, and anyone left alive is found and carried to camp.

**The ford, for this fight.** The Aire is too deep to cross except at the ford, the three pale columns in the middle of the river. A man in the ford may advance but not run.

**After the fight (10 minutes).** Bind what can be bound. Carry the wounded back. Each of the four who can stand rolls d100 on the field:

{{table:finds}}

The medieval captain's third goes to the lord. For this test, ignore pay and money otherwise.

<!-- page -->
# The week {#week}

*For the GM.*

**The news.** Edward's army crosses and marches north. The four are left behind with whoever can't walk. On Palm Sunday,
29 March, snow falls all day, and there's a noise far to the north that the wounded take for the wind. The next day the
carts begin to come back. Towton was the bloodiest day anyone can remember, and Pontefract and every village round it are
full of hurt men.

**The week's weather.** Use this table, so nobody rolls for it. It is from the game's weather rules for this place and date,
and the snow of the 29th is from the record.

{{pt:weather}}

**The decision that costs something.** Where do they wait?

| Choice | What it means |
| --- | --- |
| Stay at the crossing | No march. But the dead lie unburied within reach for {{dead_days}} days, unless the four spend a day burying them. |
| Move to Pontefract, about 3 miles | Each man who can't walk takes 2 men to carry him, so the four may not be able to take everyone. −20 on any recovery check rolled on the march day. Then quarters, if the Quartermaster can find any. |
| Bury the dead, then stay | A day's work for every fit man, and no one forages that day. The sickness chance drops. |

**Events.** Use one on a slow day, or roll d6. Each should make someone decide something.

| d6 | Event |
| --- | --- |
| 1 | A cart of wounded stops at the camp and asks for food. The Quartermaster must say yes or no. |
| 2 | A local man says the well by the camp has a dead horse in it. The Leech may move the water, at a day's work. |
| 3 | A stranger comes in with a Lancastrian badge under his coat, begging for a surgeon. |
| 4 | A priest offers to bury the dead for what the team found on the field. |
| 5 | Forage: the Quartermaster rolls Persuade or Fieldcraft. On a success, 2 days' rations. |
| 6 | A rider says Warwick wants every man who can walk at York. The Leader may send someone, or lie. |

**The end of the week.** Make the recovery checks and the sickness rolls, then the feedback. Who is alive, and who can walk?

**If you're using the roller only for the fight**, that's fine. Keep the week on paper. The travel map can run a camp, but it isn't
part of this test.

<!-- page -->
# Camp log and session log {#log}

{{pt:camplog}}

**Session log, GM**

| Item | Note |
| --- | --- |
| Packet version | {{pt_version}} |
| Date, number of players | |
| Players' usual games (d100, D&D, OSR, other) | |
| Setting (Standard or Gritty) | |
| Fight run on (roller or paper) | |
| Minutes for the fight, and rounds | |
| Lookups during the fight (tally) | |
| Minutes for the week | |
| Wounds taken, by man, place and severity | |
| Down, dead or crippled at the end of the week | |
| Decisions the council argued over | |

<!-- page -->
# Feedback {#feedback}

Score 1 (no) to 5 (yes), and add a comment if you can. Send it to {{pt_email}}.

{{pt:feedback}}

**Which rule did you have to read twice?**

<div class="blank"></div>

**What would you cut?**

<div class="blank"></div>

**What did you expect the game to do that it didn't?**

<div class="blank"></div>

<!-- page -->
# Quick reference {#reference}

*Cut out or print one for each player.*

**The round.** 6 seconds. Initiative d{{init_die}} + Agility ÷ {{init_per}}, rolled once; highest first. Every fighter takes one turn.

**The one roll.** d100 at or under the number. **Margin** = number − roll. **Critical** = at or under a tenth of the number.

**On his turn.** **Move:** stay, advance {{advance}} and attack, or run {{run}} and not attack. Leaving an enemy's side gives him a free attack. **Attack:** d100 against Attack. **Aim** at a zone or a gap: {{aim_cost}} off the margin each, free on a critical. **Defence:** d100 against Defence turns it; not against a critical.

**How bad.** Margin under {{band_serious}}: light. {{band_serious}}+: serious. {{band_critical}}+ or a critical: critical. Margin {{graze}} or less: a **graze** (a step less bleed and pain, no stop check), unless a critical.

**Where and what.** d100 on *Where it lands* under the weapon; cut or thrust is the attacker's choice before rolling (a longbow pierces). Armour takes steps off: Critical → Serious → Light → Stopped. Part-covered: the attack roll's units digit (0 = 10) at or under the cover's tens met the armour. Read the wound on *What it does*.

**Stop check (S).** d100 against Nerve, less pain and blood penalties, {{crit_stop}} more for a critical. Fail: he stops.

**Range (longbow).** Short to {{pt_short}} hexes, medium to {{pt_medium}} (−20), long to {{pt_long}} (−40). Off the map: hexes to the north edge plus the box.

**End of the round.** Everyone bleeds: {{pt_bleed_rates}}. A side with {{morale_trigger}} or more down rolls d100 against its best Nerve still up: +{{leader_present}} with a leader up, −{{leader_down}} if he's down, −{{heavy_losses}} once {{morale_heavy}} are down. Over: the side breaks.

**Pain.** −{{pain_step}}% a step, to {{pain_cap}} steps; above that, a stop check every round. **Impairments** cap at −{{cap}}%.

**First aid** (a friend beside him, his turn, d100 against the side's best Leechcraft). Bind: a step less bleeding, {{bind_skilled}} on a success. Tourniquet: arm or leg, bleeding stops. Cauterise: bleeding stops, +1 pain, none on a success.

**Lethality.** Standard: Blood ×1.5, +20 Nerve on stop checks, 1 fate. Gritty: Blood ×1, no bonus, no fate.

**The ford.** Too deep elsewhere. In the ford, advance only.

<!-- page -->
# The ford at Ferrybridge {#battlemap}

{{pt:battlemap}}

<!-- page -->
# Counters {#counters}

{{pt:counters}}

<!-- page -->
# Clifford's men {#roster}

*For the GM.* All regulars, on foot. Roll each man's initiative at the start: d{{init_die}} + 5. Blood is not multiplied for the setting: only the four's is.

{{pt:roster}}

**When a man is down,** turn his counter over or put a *Down* marker on it. The side checks its nerve at the end of the round once {{morale_trigger}} of it is down.


# How to play {#playing}

Grave Wounds is a roleplaying game about small bands of fighting men and women in real
wars, and about what wounds do to them. There are no hit points. A wound is a place on the
body, the way it was made and how bad it is, and those three things decide whether it
bleeds, hurts, stops a hand gripping or a leg bearing weight, and how long it would take
to kill without help. Most wounds do not kill. They stop a fighter, and then the question
is whether his friends can stop the bleeding, carry him to camp and keep the fever off.

## What you need {#need}

- **Dice.** Everything is rolled on **d100**: two ten-sided dice, one for tens and one for
  units, 01 to 00 (00 is 100). A few rolls use a single d10.
- **The pages.** The [wound roller](roller.html), the [team builder](team.html), the
  [travel map](travel.html) and the [field map](field.html) run on any browser and keep
  your game in it. They roll the dice, look up the tables and keep the count, so the table
  can play quickly. Everything they do is written here, and the
  [printed tables](tables.pdf) hold every table, so the game can be played on paper too.
- **A GM and players.** One person runs the world and the enemy (the GM). Each player runs
  a **team** of four to six characters, not a single hero, so losing one is a loss and not
  the end of the evening.

## The one roll {#roll}

Every test is the same: roll d100, and **equal to or under** the number you are rolling
against succeeds. That number is a skill or a characteristic, less any penalties. How far
under you rolled is the **margin**, and in a fight the margin matters: a hit by a wide
margin is a worse wound.

Out of a fight the GM calls for a roll only when failing would matter and the outcome is in
doubt; a man with time and the right skill simply does the thing. The GM sets the
**difficulty**:

{{table:difficulty}}

A roll of {{chk_crit}}% of the chance or under is a **critical**: the best result. A failed
roll of {{chk_fumble}} or more is a **fumble**: the worst.

**One man against another.** When someone resists (a sentry watching for a man sneaking past,
a seller holding out on a price), both roll, the resisting side at Ordinary. The man acting
wins only by beating them: a success over a failure, a critical over a plain success, or the
wider margin between two of the same. A tie, or both failing, goes to the side resisting, and
nothing changes. Where the GM has no sheet for the other side, it counts as 50.

!!! example "The running example"
    This book follows one team from start to finish: a lord's retinue on the road to
    Towton in 1461, led by {{ex.lead}}. Each chapter picks up the story where the last
    left it: the team is made, {{ex.arch}} the archer shoots and is cut down, his friends
    stop the bleeding, and he is carried to camp to heal or die. The numbers in the example
    are the game's own; where a die is rolled, the book says what came up.

## Time {#time}

The game's clock changes with what the team is doing:

| Scale | How long | For |
|---|---|---|
| Round | 6 seconds | One action in a fight; bleeding; stop checks |
| Minute | 10 rounds | Binding wounds; the end of most fights |
| Day | | Marching, camps, the weather, sickness |
| Week | | Wounds healing in camp; catching disease |
| Season | about {{xp_season}} days | Experience: ticked skills roll to rise |

## Lethality {#lethality}

Before play the GM sets how hard the game is on the **player characters**: the men made in the
team builder, and the heroes they become on the field map. Followers, enemies and bystanders are
never spared: they stay as fragile as real people, and the wound tables never change. One setting
holds for the whole game; every page has a **Gritty | Standard | Heroic** switch in its header,
and they share it.

{{table:lethality}}

**Fate.** A player character has the setting's fate points each season; the ones he spends come
back at End of season. One fate point, spent after the dice:

- lowers a wound he has just taken one severity step (a light wound turned is no wound at all);
- rolls again a stop check, a recovery check or a wound-fever roll he has just failed;
- spares him a capture or captivity roll that would kill him (he is held instead).

In the roller the player chooses, with the buttons under the hit. The pages that run on their own
(the travel map's nights, the field map's heroes, the team builder's captives) spend one only to
save a life, and say so in the log.

The examples in this book are at Gritty: a player character's Blood and stop checks as anyone's.

!!! gm "For the GM"
    Gritty is the game the wound records describe. Standard is the place to start a first
    campaign: a team that has a little luck and a little more blood learns the game before it
    loses its leader. Heroic suits a story about the team rather than about the war.

## Characteristics and skills {#characteristics}

Every character has six **characteristics**, from {{stat_lo}} to {{stat_hi}}:
**Strength**, **Agility**, **Endurance**, **Wits**, **Nerve** and **Presence**. Fifty is an
ordinary person. **Skills** (Bow, Blade, Dodge, Leechcraft and the rest) start from a
characteristic and grow with experience, up to {{skill_max}}. A character's **attack** is
the skill his weapon is fought with, and his **defence** is the better of Parry and Dodge.

## Using skills {#skills}

What each skill and characteristic is for out of a fight, its usual difficulty, who resists
it, and what follows (the GM decides when a case is easier or harder):

{{table:skill_uses}}

A skill check that succeeds (or wins against someone) ticks the skill for experience; a
characteristic is not ticked. **A hurt man checks worse:** out of a fight a check (a job's
included) takes the same penalty his attack would in the roller, from pain, blood lost, wounds,
fatigue (a hungry day is a step of it), sickness and Strain; with no fight to go by, his Strain
alone.

**Bargaining.** Buying from the price list, selling goods taken as loot (not money, prize money
or a ransom) or hiring a replacement, a man may haggle: his Persuade against the other man's (a
seller's is {{haggle_seller}}). Buying, a win takes {{haggle_win}}% off the price ({{haggle_crit}}%
on a critical); selling, a win gets {{sell_win}}% more ({{sell_crit}}% on a critical). On a fumble
there is no deal today, and a man selling has been cheated of {{sell_fumble}}% by a fence.

## Tongues {#tongues}

A man speaks his own **tongue** at {{lg_native}}, which never changes (Letters is the separate
skill of reading and writing). Any other is a figure read in bands:

{{table:tongue_bands}}

**Talking in a tongue.** Persuade and Command in another tongue are at most his figure in it: a
fine talker with twenty words of French is a man with twenty words of French.

**Words across tongues.** An order to a man of another tongue, a call on a foe to surrender (or
his own surrender), a question to a prisoner or a villager: d100 at the best tongue the two share
(the lower of their figures). A critical is understood in full; a success, understood; a failure,
only the gist (an order half done, a surrender not understood); a fumble, a dangerous error, the
wrong thing understood (at the Grattan fight of 1854 a drunk interpreter's broken Lakota began a
war; in Afghanistan "fire an illume" was heard as "fire mortars").

Related tongues, phrase books, passing as a native, the travel map's tongues, learning a tongue
and hiring an interpreter are in [Tongues in full](#tongues-full).

## Age and wear {#age}

The [team builder](team.html) ages a man for the terms he served before play. In play, each term
he serves ages him the same way: his characteristics decline with his age band, and to 40 or 45
he gains a little Presence, Nerve and Wits with maturity. Service also **wears** him: hard seasons
on the march, hungry, sick or wounded, add Wear, which ages him faster. From 35, or with 8 Wear,
he may be **worn out**, and the GM may send him home. Enlisting under or over age, the ageing
table and the Wear and worn-out rolls are in [Age and wear in full](#age-full).

## Experience {#experience}

**Training.** A week's teaching, from a master for hire or a teammate at least 20 better, ticks a
skill if the teacher's roll succeeds; an army drills its men in camp; and courses (an
apprenticeship, Sandhurst, Officer Candidate School) take a man away for set gains. The fees,
drill and courses are in [Training in full](#training-full).

A skill used well is **ticked**: a job's check that succeeds (lawful or not; a
failed or fumbled check, or a job with no check, teaches nothing), a hit, a parry or dodge that
works, first aid that works, Fieldcraft that finds fresh food on the march, a week nursing the
sick (the best Leechcraft with the force), Stealth that surprises an enemy and Watch that stops
one surprising his. A skill is ticked once however often it is used. At the **end of a season**
(about {{xp_season}} days, when the GM calls it) each ticked skill rolls d100: over the skill,
it rises {{xp_lo}}-{{xp_hi}}, never past {{skill_max}}; then the ticks clear. Low skills rise
quickly and high ones slowly.

**Time served.** Days at a job with a skill check (not fumbled) and every day with a force on the
travel map count toward a **term**, as long as one of his career terms ({{age_term}} years in
most eras). Each term served gives a later term's gains ({{term_main}} to his career's main skill
and {{term_second}} to its second) and its years of age, at the next end of season, and rolls on
his career's term table as at the making of a character: its event (+{{event_gain}} to its skill,
and a line of his story) and its wound chance (a scar, or a lasting hurt). His starting purse is
not changed.

Anyone without a sheet (a bystander, an enemy the GM has not written up) counts as 50 in
every characteristic, and fights at his **quality**:

{{table:qualities}}

!!! gm "For the GM"
    Quality is the quickest way to make an enemy: decide whether he is green, regular or
    veteran, and the table gives his attack, defence and Nerve. The followers of the
    players' teams use the same table, and so do whole units on the field map.

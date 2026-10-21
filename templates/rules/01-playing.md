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

**Haggling.** Buying from the price list, a man may haggle: his Persuade against the
seller's ({{haggle_seller}}). If he wins he pays {{haggle_win}}% less ({{haggle_crit}}% on a
critical); if not, the list price; and if he fumbles the seller will not deal with him today.

A skill check that succeeds (or wins against someone) ticks the skill for experience; a
characteristic is not ticked.

## Experience {#experience}

**Training.** A skill can also be ticked by a week's teaching: from a master for hire where the
team is (a riding master, a master of defence, a schoolmaster, a surgeon, a craftsman; his skill
counts as 60, and he charges a fee by the week), or from a teammate at least 20 better (who gives
up the week too). The teacher rolls his skill; a success ticks the pupil's skill, a failure wastes
the week. The pupil pays the fee and his keep. An army drills its men: a week in which a force
its army feeds spent four days or more not marching, the best Command with it (or the army's own
sergeants, 50) rolls, and on a success each named man's weapon skill is ticked. Riding lessons
in London in 1879 cost about six days of a private's pay each; the other fees are estimates.

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
and {{term_second}} to its second) and its years of age, at the next end of season. His starting
purse is not changed.

Anyone without a sheet (a bystander, an enemy the GM has not written up) counts as 50 in
every characteristic, and fights at his **quality**:

{{table:qualities}}

!!! gm "For the GM"
    Quality is the quickest way to make an enemy: decide whether he is green, regular or
    veteran, and the table gives his attack, defence and Nerve. The followers of the
    players' teams use the same table, and so do whole units on the field map.

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

**Haggling.** Buying from the price list, a man may haggle: his Persuade against the
seller's ({{haggle_seller}}). If he wins he pays {{haggle_win}}% less ({{haggle_crit}}% on a
critical); if not, the list price; and if he fumbles the seller will not deal with him today.

A skill check that succeeds (or wins against someone) ticks the skill for experience; a
characteristic is not ticked. **A hurt man checks worse:** out of a fight a check (a job's
included) takes the same penalty his attack would in the roller, from pain, blood lost, wounds,
fatigue (a hungry day is a step of it), sickness and Strain; with no fight to go by, his Strain
alone.

**Selling and hiring.** Loot that is goods (not money, prize money or a ransom) may be sold
haggling: his Persuade against the buyer's; a win gets {{sell_win}}% more ({{sell_crit}}% on a
critical), a fumble lets a fence cheat him of {{sell_fumble}}%. A man hiring a replacement may
haggle his price as at the price list; on a fumble the man will not sign today.

## Tongues {#tongues}

A man speaks his own **tongue** at {{lg_native}}, which never changes (Letters is the separate
skill of reading and writing). Any other is a figure read in bands:

{{table:tongue_bands}}

A tongue he lacks he knows at a share of a related one he has (half of German from Low German,
three quarters of English from Scots). Pidgins rise no higher than {{lg_pidgin}} (Bamboo English
in Korea, GI Vietnamese), the Plains sign language no higher than {{lg_sign}}, and a learned tongue
no higher than {{lg_max}}.

**Talking in a tongue.** Persuade and Command in another tongue are at most his figure in it: a
fine talker with twenty words of French is a man with twenty words of French.

**Words across tongues.** An order to a man of another tongue, a call on a foe to surrender (or
his own surrender), a question to a prisoner or a villager: d100 at the best tongue the two share
(the lower of their figures). A critical is understood in full; a success, understood; a failure,
only the gist (an order half done, a surrender not understood); a fumble, a dangerous error, the
wrong thing understood (at the Grattan fight of 1854 a drunk interpreter's broken Lakota began a
war; in Afghanistan "fire an illume" was heard as "fire mortars"). From the Crimea on, armies
issued phrase books: a yes or no, a number or a pointed direction is then Easy at no worse than
{{lg_book}}.

**Passing as a native.** His figure against the listener's Watch (both roll): Ordinary in his
own tongue, Hard fluent without the idiom (76+), Very hard a good speaker (51-75), and below that
he cannot pass. In 1944 Skorzeny found ten men with perfect English and idiom for Operation
Greif, thirty or forty good speakers, and over a hundred moderate ones; those caught in American
uniform were shot.

**Taken and escaping.** A man who asks for quarter in his captors' tongue is a little safer (the
capture roll is 10 better: a surrender had to be accepted to protect him). Escaping, his Fieldcraft
to get home is +10 if he converses in their tongue and +20 if it is his own.

**On the travel map** the people where a force stands speak a tongue, or in mixed country several:
the nearest town, village or landmark within {{lg_place_km}} decides (its own, if it names them),
and everywhere else has the map's. A force with no named man who gets by in any of them forages Hard, its talk is in the best
of them he has, and a month among them ticks their main tongue. The map shows a place's tongues
when you point at it.

**Learning.** A tongue used well is ticked and rolls to rise at End of season like a skill (one at 0
always rises). A month among its speakers on the travel map, or a season held prisoner, ticks it;
so does a week with a language master, a teammate who speaks it well, or (from 1943) an army
course. The army's courses took three months for the better students to order a meal or rent a
room; the Foreign Legion's recruits answered in French within ten days.

**Interpreters.** The team may hire an interpreter for a season: a man of the other army who speaks
the team's tongue and his own at {{int_lo}} to {{int_hi}} (rolled). He costs {{int_wage}} Day a day
({{int_wage_modern}} for the modern wars, where Iraqi interpreters began at $600 a month in 2005). A
man who talks through him uses the interpreter's figure in that tongue, not his own. Of those
hired {{int_unrel}}% are unreliable (a whistleblower said 28% of one firm's Afghan hires failed the
language standard): his roll of {{int_err}} or more is a dangerous error. Each End of season he may
be killed ({{int_hazard}}%, {{int_hazard_modern}}% in the modern wars: in Iraq some fifteen times a US
soldier's rate), and his season is up. On the travel map, where the people speak his tongue and
the team's named men march with the force, he forages and talks for it: the force does not forage
Hard for want of the tongue, and its billeting and talk go through him at his figure.

Who speaks what, by army (the shares are estimates, not muster counts):

{{era:tongue_armies}}

## Age {#age}

**Enlisting.** A man enlists at his era's starting age, raised to his army's legal least (15 to
60 under the Statute of Winchester; 17 to 25 for Victorian recruits; 18 to 37 in the American
draft of 1942). Then d100: a few are **boys under age** (about a tenth of the Union army was under
18), enlisted at up to {{en_under}} years below the least, and a few **older recruits**, from
{{en_older}} up to {{en_over}} years past the most (over it, he lied). A man under or over age is
found out at {{en_found}}% each End of season and sent home, until he is of age (a boy) or has
served out his first term (an older man). Most characters are made after their terms, so a boy's
lie matters only in the eras of one-year terms. A recruit who enlisted at {{en_older}} or more
takes {{en_wear}} times the Wear for his service: Union men enlisting at about 39 had 1.8 times the
odds of dying of disease of men of 20 in their first year, and 2.4 after.

A man ages with his terms. For every 4 years of his life past the start of his service (at the
making of a character, the years of his terms; in play, each term served) he rolls his age band's
decline, taken from his characteristics as a lasting hurt is (his skills that rest on them fall
with them), and, from 20, gains a step of maturity: +1 Presence and +1 Nerve until 40, +1 Wits
until 45 (at most +5 each). Each promotion adds +{{pres_rank}} Presence, to +{{pres_cap}} in all (a
design estimate: a man who leads grows into it). Endurance goes first, then Agility, then Strength; Wits slows from
50:

{{table:ageing}}

**Wear.** Service wears a man: +1 Wear for each 4 years, and +1 for each hard season (a month of
hard nights on the travel map, hungry, sick or wounded, or colder and wetter than his shelter; or
the GM's word for a siege, a famine or a tropical station). Each 4 Wear makes him 2 years older
for his decline, and from 6 Wear his Endurance rolls twice and takes the worse.

**Worn out.** For each term he serves from 35, or with 8 Wear or more, he rolls d100: at or under
3 × Wear + 2 × (his age − 35) − (Endurance − 50) ÷ 2, he is worn out (a 1-year term rolls a
quarter of that). From 40, Endurance under 30, or Strength, Agility or Endurance under 25, wears
him out at once. The GM may send him home (with a pension where his army gave one) or keep him
on. British soldiers discharged "worn out" were mostly 41 to 44, after 21 to 25 years.

## Experience {#experience}

**Training.** A skill can also be ticked by a week's teaching: from a master for hire where the
team is (a riding master, a master of defence, a schoolmaster, a surgeon, a craftsman; his skill
counts as 60, and he charges a fee by the week), or from a teammate at least 20 better (who gives
up the week too). The teacher rolls his skill; a success ticks the pupil's skill, a failure wastes
the week. The pupil pays the fee and his keep; a teammate who teaches loses the week from his
next job term. An army drills its men: a week in which a force
its army feeds spent four days or more not marching, the best Command with it (or the army's own
sergeants, 50) rolls, and on a success each named man's weapon skill is ticked. Riding lessons
in London in 1879 cost about six days of a private's pay each; the other fees are estimates.

**Courses.** Some training takes him away for weeks or a year, for set gains: a year as an
apprentice or in a knight's household, two weeks at a Civil War camp of instruction, eighteen
months at Sandhurst, four and a half at a 1916 officer cadet battalion, seventeen weeks at an
American Officer Candidate School (22 in Korea, 23 in Vietnam, 12 today), Ranger School, the
Special Forces course. An army's course counts as service, and an officer's course makes him
eligible for its rank at the next vacancy, whatever his rank and years:

{{era:courses}}

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

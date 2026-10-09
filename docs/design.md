# Grave Wounds: blood, bivouac and weather

Snapshot of the design proposal, Oct 8, 2026. The working copy lives in Claude Docs.

Design proposal. Grave Wounds is a d100 roleplaying game where wounds behave like real wounds: where you are hit matters more than how hard, fights end in incapacitation far more often than death, and the dying happens on a clock that first aid can stop. It is built on HitLoc's historical wound data and spans historical eras and post-apocalyptic and spacefaring settings.

## The pitch

Players lead a small team through fights that feel like the real thing: brief, lopsided and decided by position, armour and nerve, with every wound telling you what it does to the body. The game keeps the grit of Aftermath! and the vivid criticals of Rolemaster, but resolves a hit in one roll and one lookup instead of a flow chart.

Design goals:

1. **Real effects, not abstract damage.** No hit points. A wound is a location, a mechanism (cut, pierce, crush, gunshot, blast, burn) and a severity, and those decide bleeding, pain, lost function, shock and how long until it kills.
2. **Fast at the table.** One d100 for the hit, one for the location, one for the wound; everything else is read off a single result line. The HitLoc roller can do it all in one click.
3. **Lethality the GM chooses.** The same wound data serves gritty and heroic games through a few dials, not a different rulebook.
4. **Teams, not lone heroes.** A player runs a squad, a crew or a household, so losing one character is a loss, not the end of play.
5. **Era colour from real records.** Each era gets hit-location tables from real wound data where it exists, and clearly labelled estimates where it doesn't.
6. **Weather that matters.** A mild day's march is easy; rain, mud, heat and cold tire the team, spoil powder and bowstrings, and feed sickness. One roll a day decides it.

## Lessons from the games that inspired it

Each of the six games got one part of this right; the common failure was paying for realism with time at the table.

| Game | Keep | Avoid |
| --- | --- | --- |
| [Aftermath!](https://en.wikipedia.org/wiki/Aftermath!) (FGU, 1981) | d100 roll over 30 hit locations; armour worn piece by piece on any location; damage set by the weapon (bullet damage by muzzle energy) | Flow charts and arithmetic every action; reviewers called it "nearly unplayable" |
| [Rolemaster](https://en.wikipedia.org/wiki/Arms_Law) (ICE, Arms Law 1980; Unified 2022) | Attack results read against the target's armour; criticals graded A-E with named effects: bleeding, broken bones, severed limbs | Dozens of tables (Unified: 39 attack, 15 critical); location fixed by the critical's text; one armour type for the whole body |
| [Traveller](https://necropraxis.com/?p=3127) (GDW, 1977) | Lifepath generation: careers, terms, survival rolls, mustering out; damage to physical characteristics instead of hit points, so one hit can drop you | Characters dying during generation; 2d6 too coarse for this game |
| [The Morrow Project](https://en.wikipedia.org/wiki/The_Morrow_Project) (Timeline, 1980) | A team as the premise (recon, military, science teams); detailed real firearms and vehicles | Many separate rolls to find a wound's location and effect |
| [Gamma World](https://fanlore.org/wiki/Gamma_World) (TSR, 1978) | Random mutations make a character in minutes and give it a story | Wildly uneven characters; a drift into the absurd |
| [Fallout tabletop](https://roll20.net/compendium/fallout/Rules:Damage%20and%20Injury) (Modiphius, 2021) | Located injuries with plain effects until treated: arm drops what it holds, leg goes prone, torso bleeds, head is dazed | Still hit points underneath; injuries only on big hits |

## Core resolution

Everything is d100 roll-under a skill, and in a fight a hit takes at most three rolls, read off one result line.

- **Skill roll:** d100 at or under skill succeeds. Wounds, cover, position and fatigue subtract from skill, as HitLoc's attack and defence penalties already do.
- **Margin matters:** how far under the skill you rolled grades the result. In a fight the margin raises the wound's severity, so skill buys clean hits, not just more of them.
- **Opposed fights:** attacker rolls, defender may roll to parry, dodge or take cover. A defence success turns the hit into a near miss or a glancing blow.

A fighting turn runs in this order:

1. **Initiative:** fighters act from highest to lowest, the order HitLoc's tracker already keeps.
2. **Attack:** d100 against weapon skill, minus situation and wound penalties.
3. **Defence:** optional d100 against parry, dodge or cover.
4. **Location:** d100 on the era's hit-location table (HitLoc), shifted by aimed shots and the situation.
5. **Armour:** the armour on that location lowers the severity by its steps against the mechanism; a gap in coverage means no armour.
6. **Wound:** severity plus location gives the effects line: bleed, pain, lost function, shock and the lethality clock.
7. **Status:** the target checks whether he can keep fighting (below), then the round's bleeding and the next fighter.

**Time scales.** As in Aftermath!, the clock the game runs on changes with what the team is doing; the combat turn is 6 seconds, the same round HitLoc's tracker already bleeds by.

| Scale | Length | Used for |
| --- | --- | --- |
| Combat turn | 6 seconds | One action; bleeding per turn; stop checks |
| Minute | 10 turns | First aid, the end of a fight (HitLoc's "+1 minute") |
| Exploration turn | 10 minutes | Searching, moving through a site, careful work |
| Day |  | Weather roll, travel, foraging; recovery checks for fever and poison |
| Week |  | Recovery checks for wounds and slow illness; training, crafting |

## The wound model

There are no hit points: each wound is recorded on its own and its effects add up, so a character is described by what is wrong with him, not by a number going down.

A wound is three things, each from a roll or a table:

- **Location:** one of 26 (skull left and right, face, neck, chest, abdomen, groin, back, and each shoulder, upper arm, forearm, hand, thigh, knee, lower leg and foot), weighted by the era's real wound records.
- **Mechanism:** cut, pierce, crush, gunshot, blast fragment or burn, from the weapon.
- **Severity:** light, serious or critical, from the attack's margin, reduced a step at a time by armour.

Together they give an effects line, the same five effects HitLoc already uses:

| Effect | What it does in play |
| --- | --- |
| Bleeding (B0-B3) | Drains a Blood pool each round; falling Blood brings weakness, then fainting, then collapse |
| Pain (P0-P3) | A penalty to every action; past a limit, a shock check each round |
| Lost function | A useless hand or arm, a leg that cannot bear weight, blinded, winded |
| Shock, fracture, severed | Immediate stop checks; bones that need setting; limbs that are gone |
| Lethality clock | Instant, rounds, minutes, hours, days or none: how long until it kills untreated |

**Most hits stop a fighter without killing him.** In the Peninsular War records, 4,129 French officers were wounded against 230 killed outright or dying of wounds; at Bougainville about one gunshot hit in five killed. So every wound forces a **stop check**: d100 against the character's nerve, harder for worse wounds, pain and blood loss. Fail and he goes down, breaks or can only crawl, even if the wound itself is not fatal. That is what ends real fights, and it keeps them short.

**Death runs on the clock, and treatment stops it.** A bind slows bleeding; a tourniquet stops a limb bleed; surgery and later medicine change the clock. Days-long clocks bring infection in eras before antibiotics. Recovery takes weeks and can leave a permanent impairment, which is good story for a team game.

## Lethality dials

The GM sets lethality with four dials before play; the wound data never changes, only how much of it reaches the player characters.

| Dial | Gritty | Standard | Heroic |
| --- | --- | --- | --- |
| Severity shift on PCs | None | Critical wounds to PCs drop to serious on a lucky roll (01-10) | Every wound to a PC drops one severity step |
| Fate points per PC | 0 | 1 per session | 3 per session |
| Stop checks for PCs | As for anyone | +20 nerve | Only on critical wounds |
| Lethality clock | As rolled | One step slower (minutes become hours) | Two steps slower; instant kills only from the skull and heart |

A **fate point** spent after the wound is rolled lowers its severity one step or moves the hit to the next location on the table. Fate points belong to PCs only, so named enemies and bystanders stay as fragile as real people. The dials mix freely: a gritty clock with heroic fate points makes a tense but survivable campaign.

## Recovery, sickness and downtime

Wounds, disease and poison share one simple model: each is a condition on a five-step track, checked once per day or week, and a team that pushes on with its sick and wounded pays for it. Aftermath!'s disease model was detailed but slow; this keeps one roll per condition per check.

**The track.** Every condition sits on one of five steps, each with its own penalty to actions:

| Step | Meaning | Penalty |
| --- | --- | --- |
| Deadly | Will die without help, on its lethality clock | Cannot act |
| Grave | Bedridden; needs care to improve | -50% |
| Serious | Can ride or be carried, light work only | -30% |
| Mending | Can march and fight, carefully | -10% |
| Healed | Gone, or a permanent mark or impairment | None or the impairment |

A fresh wound enters by severity (critical at Grave or Deadly, serious at Serious, light at Mending); a disease enters at Mending once its incubation ends and climbs from there.

**The recovery check.** Once per day for poison and fever, once per week for wounds and slow illness: d100 against Endurance, modified by care, activity and conditions.

- Care: none -20, field dressing 0, nursed in shelter +10, surgeon or hospital +10 to +30 by era.
- Activity: marching or fighting -20, light work -10, full rest +10.
- Conditions: cold, wet or filth -10; short of food or clean water -10.
- Result: success by 30 or more moves two steps toward Healed; a success moves one; a failure holds; a failure by 30 or more moves one step worse. A wound that worsens rolls for infection, using the infection risk HitLoc already gives each location.

**Disease and poison** come as short profiles, each one line: how it is caught (wound, water, food, contact, air, bite), incubation, how fast it climbs, and whether nursing spreads it. A handful covers most play: wound infection and gangrene, dysentery, camp fever, plague, radiation sickness, and venom or poison. Their numbers are design estimates, labelled as such. The history behind them matters: in the American Civil War about two of every three soldiers who died, died of disease.

**Medieval diseases for the first playtest.** Seven profiles cover what killed medieval armies off the battlefield. All are checked daily once caught, except scurvy, which is checked weekly. Onset times follow modern medicine; the game numbers built on them are design estimates.

| Disease | Caught from | Shows after | Spreads to nurses | In play |
| --- | --- | --- | --- | --- |
| Wound fever (sepsis, gangrene) | A dirty or untreated wound, rolled with HitLoc's infection risk for the location | 1-3 days | No | Climbs fast once it starts. Richard I died of an infected crossbow wound to the shoulder in 1199, eleven days after he was hit |
| Bloody flux (dysentery) | Dirty water or food, latrines dug near the water | 1-3 days | Yes, unless the nurse keeps clean | Dehydration; can lay low much of a camp at once. Killed King John (1216), Louis VIII (1226) and Henry V (1422) on campaign |
| Camp fever (typhus) | Lice in crowded, unwashed camps | 1-2 weeks | Yes, through lice | High fever and delirium; no chance to wash clothes counts as filth (-10) |
| Plague | Flea bites, worst in sieges and towns full of rats | 2-6 days | Rarely (only the lung form spreads by breath) | Climbs fastest of all: high fever, delirium, swollen buboes. The Mongol army besieging Kaffa in 1346 was struck by it |
| Ague (malaria) | Mosquitoes in marshes and low wetlands | 1-4 weeks | No | Fevers every second or third day (tertian, quartan) leave a man too weak for armour; a healed case can relapse |
| Scurvy | Months without fresh food, in long sieges and winter camps | 1-3 months | No | Bleeding gums, aching joints, and old wounds reopen: each old wound from character generation comes back at Mending. Only fresh food heals it |
| Typhoid | Dirty water or food, often from a carrier in camp | 1-3 weeks | Yes, unless the nurse keeps clean | Weeks of fever and weakness. Medieval chroniclers did not tell it apart from other camp fevers, but army records show it was one of the great killers |

**What the records show.** Before antibiotics, disease, not battle, emptied armies. The medieval sources are chronicles and a few sick lists, so the rates come from later armies that counted cases and deaths:

- Union army, 1861-66: about 10 million cases of illness, and roughly two deaths from disease for every death in battle.
- Corunna retreat, 1809: 14% of Moore's army was listed sick on one morning, and more than 20% came home sick. Of 241 deaths at Plymouth, only 25 were from wounds.
- Harfleur, 1415: of about 11,000 men, the surviving sick lists name 1,330 sent home. Estimates of the dead run from 36 (the lists alone) to up to 5,000 (the chronicles).
- Granada, 1489: a chronicle gives 17,000 dead of typhus against 3,000 killed by the enemy.

| Disease | Deaths per case in the records |
| --- | --- |
| Bloody flux | Union army 1,739,135 cases, 44,558 deaths (2.6%); chronic dysentery 12.6%; Corunna hospital cases 26% |
| Camp fever (typhus) | Untreated 10-60%, usually about 40%; Union army 37% (2,624 cases); Corunna fever cases 13% |
| Typhoid | Union white troops 75,368 cases, 27,050 deaths (36%) |
| Ague (malaria) | Union army 1,315,955 cases, 10,063 deaths (0.8%): it disabled far more than it killed |
| Scurvy | Union army about 47,000 cases, 771 deaths (1.6%); far deadlier with no fresh food at all, as at Andersonville |
| Plague | Untreated bubonic 30-60%; the lung form nearly always fatal |
| Wound fever | Union pyaemia 97% fatal. Union amputations: forearm 14%, upper arm 24%, lower leg 38%, mid-thigh 54%, hip 88%; done at once 23%, delayed 52% |

**Catching a disease.** Once a week in camp or on the march, the GM rolls d100 for each disease the surroundings allow, against its outbreak chance. On an outbreak, every team member rolls Endurance to resist; a failure catches it and starts the incubation. The outbreak chance is set by four things, all design estimates:

| Factor | Raises | Lowers |
| --- | --- | --- |
| Camp hygiene | Poor (fouled water, crowding, no washing): flux +20, typhoid +5, typhus +5 | Good (latrines downstream, clean water, washing): flux, typhoid and typhus -5 each |
| Staying put | A siege or a camp held over 4 weeks: flux +10, typhus +10, plague +5 where it is about | Moving to fresh ground resets it |
| Location | Marsh or low wetland: ague 15 in the warm season, flux +5. Town or crowded river camp: typhoid +5, plague +5 where it is about | Dry upland: ague 0, flux -5 |
| Weather | Hot summer: flux +10, typhoid +5. Cold and wet: typhus +10 (huddling, unwashed clothes) | Winter: ague 0 |

**Already sick or wounded.** The resist roll is harder for anyone already on the track: -10 at Mending, -20 at Serious or worse, and -10 more if short of food. A nurse tending a disease that spreads to nurses rolls to resist again each week. So a team that camps badly with its wounded gets sicker, which is the decision the downtime rules are meant to force.

**Draft numbers.** When a disease takes hold, a d100 peak roll sets how bad it gets; it then climbs daily to that step before recovery checks begin. Deadly chances follow the deaths per case above; outbreak chances are for a fair camp, before the factors.

| Disease | Outbreak chance per week | Peak roll | Notes |
| --- | --- | --- | --- |
| Bloody flux | 10 | Deadly 01-03, Grave 04-15, else Serious | Turns chronic (stays at Serious) on a failed recovery check by 30 or more |
| Camp fever (typhus) | 2 | Deadly 01-30, Grave 31-70, else Serious | Mostly a cold-weather and siege disease |
| Typhoid | 2 | Deadly 01-30, Grave 31-60, else Serious | Long: recovery checks start only after two weeks |
| Ague (malaria) | 0, or 15 in warm marsh | Deadly 01-02, Grave 03-30, else Serious | A healed case relapses to Serious on a weekly 01-05 while in marsh country |
| Plague | 0, or 5 where an outbreak is about | Deadly 01-50, Grave 51-80, else Serious | The GM decides when plague is in the region |
| Scurvy | Not rolled: after 6 weeks without fresh food, each week resist or catch it | Starts at Mending, climbs a step each week without fresh food | Fresh food heals a step a week |
| Wound fever | Per wound, from HitLoc's infection risk | Deadly chance by location, from the amputation figures | Worse when treatment is delayed |

As a check on the numbers: a fair camp gives a man about a 1 in 20 chance a week of catching the flux, more than double the Union army's average (about one bout per man per year, or 1 in 50 a week), which suits a team on campaign rather than in garrison. A poor camp in summer gives about 1 in 5, near the 14% sick seen at Corunna. The playtest should test both.

**Food and sunlight.** What the team eats, and how much daylight it gets, is tracked once a week as a few marks on the team sheet, not counted meal by meal. Calories decide strength; a handful of key nutrients decide the slow conditions. The weekly forage downtime action is how a team finds what it lacks.

| Mark | What sets it | If it is missing |
| --- | --- | --- |
| Calories: Fed, Short or Starving | Rations against work: a marching or fighting man needs roughly 3,000-4,000 calories a day (design estimate) | Short: -10 to resist and recovery rolls. Starving: -20, and every member drops a step of fatigue each week until fed |
| Fresh food (vitamin C): fruit, greens, fresh meat, onions | Any fresh food in the week | After 6 weeks without it, scurvy rolls begin (above) |
| Sunlight (vitamin D) | Days spent outdoors; lost in a long siege inside walls, in a dungeon or mine, below decks, or a northern winter | After 8 weeks with little sun: tiredness and dull wits (-10 to Endurance and Wits rolls), and broken bones take a week longer per recovery step. A week of sun, or fish, liver or eggs, starts to clear it |
| Greens, liver or milk (vitamin A) | Any in the month | After 3 months without: night blindness, -20 to sight and fighting in the dark |

Later eras add their own diet diseases: beriberi on polished-rice rations, pellagra on maize, and in the speculative eras whatever a vault or a ship's stores lack.

**Weather.** Each morning the GM rolls d100 on the season's table for the region; on a second roll of 01-50 yesterday's weather holds instead, so wet and dry spells last. The effects feed the checks the team already makes: fatigue on the march, water, the disease outbreak roll, and recovery. The tables below are for temperate Europe in the first playtest; all numbers are design estimates, and the mud rule follows Aftermath!'s.

| Season | Fair | Hot | Rain | Storm | Cold | Snow | Fog |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Spring | 01-45 | - | 46-75 | 76-80 | 81-90 | - | 91-00 |
| Summer | 01-50 | 51-80 | 81-92 | 93-97 | - | - | 98-00 |
| Autumn | 01-35 | - | 36-70 | 71-78 | 79-88 | - | 89-00 |
| Winter | 01-25 | - | 81-92 | - | 26-60 | 61-80 | 93-00 |

| Weather | March | Body | Fighting and camp |
| --- | --- | --- | --- |
| Fair | Full pace | Normal fatigue and water | - |
| Hot | Full pace | Water doubled; marching in armour costs double fatigue; an Endurance check each hot march or a step of fatigue from heat exhaustion, and heatstroke on a bad failure | Flux +10 on the outbreak roll |
| Rain | Three-quarters pace; unmade roads turn to mud, half pace the next day, back to normal the day after | Without shelter, the cold-and-wet -10 on resist and recovery rolls | Matchlocks and flintlocks misfire on 01-30, bowstrings left strung slacken (-10 and shorter range); sight and hearing shortened |
| Storm | Half pace; mud as rain | As rain, and no fires | Gunpowder useless in the open; sight a few tens of metres |
| Cold | Full pace, frozen roads firm | Without warm clothing, fatigue one and a half times; a night unsheltered needs an Endurance check or chills, frostbite to hands and feet, and a pneumonia roll | Typhus +10; ague 0 |
| Snow | Half pace, a quarter in drifts; slow to clear as Aftermath!'s snow days | As cold | As cold; tracks easy to follow |
| Fog | Three-quarters pace off the road; easy to get lost | Damp: as rain if it lasts all day | Sight about 20 metres; surprise much more likely |

History gives the weather its weight: chroniclers say rain slackened the Genoese crossbow strings at Crécy in 1346, the French advanced through deep mud at Agincourt in 1415, and rain-soaked ground delayed the start of Waterloo in 1815.

**Downtime.** Every day or week the team stops, each member who is not recovering takes one downtime action: nurse a patient (the patient's care bonus comes from that skill), train a skill, craft or repair, forage or scavenge, scout, earn money, or stand guard. A team that moves on instead travels at its slowest member's pace, carries the Grave on litters, and every condition rolls with the activity penalty, so recovery becomes a real decision rather than a rest button.

## Leading a team: fast, rich character generation

Each player runs a team of four to six, and a whole team should be made in under 20 minutes: about three minutes a character, five for the leader.

A character is built in five rolls:

1. **Characteristics:** six of them (Strength, Agility, Endurance, Wits, Nerve, Presence), each 3d6 x 5 for a 15-90 range, or a fixed array for speed.
2. **Origin:** one d100 roll on the era's origin table: where he comes from, a starting skill and a trait.
3. **Career terms:** Traveller's idea, kept short. Each term is one d100 roll on the career's table and gives a skill, an event and a chance of an old wound. Leaders take three terms, others one or two. Nobody dies in generation.
4. **Old wounds:** an old wound is rolled on the era's HitLoc table and leaves a healed mark or a small permanent impairment. The Towton and Sidon skeletons show many men with healed wounds from earlier fights; here they become history you can see on the character sheet.
5. **Kit:** a package from the team template: armour kit, weapons and gear, as HitLoc's example combatants already define them.

For post-apocalyptic eras, a Gamma World-style **mutation or implant roll** can replace one career term.

**Team templates** set the shape of the team and its kit: a man-at-arms with his archers and servants, a Morrow Project recon team in its vehicle, a merchant crew, a vault scavenging party. **Followers** get a one-line stat block (one skill rating, nerve and kit) so that a team of six stays fast to run in a fight.

## Eras and settings

Historical eras use real wound records; speculative eras reuse the closest real data and label every extrapolation, as HitLoc does today.

| Era | Wound data | What gives it colour |
| --- | --- | --- |
| Crusades and the Middle Ages | Sidon, Visby and Towton mass graves | Mail and plate, shields, mounted charges, sieges, arrows |
| Pike and shot | Lutzen mass grave plus blends | Matchlocks and wheellocks, cuirassiers, pike blocks |
| Musket era | Revolution pension rolls, Peninsular officers' records | Volleys, bayonets, sabres, surgeons with saws |
| Civil War and the frontier | Union surgeons' records, Army arrow reports | Rifle-muskets, revolvers, bows, field hospitals |
| World wars to today | Hospital and killed-in-action studies, WWI to Afghanistan | Machine guns, shells, body armour, medevac |
| After the bomb (Aftermath!, Morrow Project, Fallout, Gamma World) | Modern gunshot and close-combat tables; radiation and disease added | Scavenged weapons, failing medicine, mutation, rebuilding |
| Among the stars (Traveller) | Modern tables extrapolated; burn and vacuum effects new | Lasers, vacc suits, ship decks, frontier medicine |

The era sets three things: the hit-location table, what medicine can do (which changes the lethality clock and infection), and the kit available to teams. That keeps one rulebook and many settings, and every era's notes say how directly its numbers come from records.

## What HitLoc already provides and what is new

About half of the combat engine already exists in HitLoc; the new work is the character side and the rules text.

| Part | Status |
| --- | --- |
| Hit-location tables, 37 tables across 17 eras and groups, with sources | Exists |
| Wound effects: bleed, pain, lost function, shock, lethality clock | Exists |
| Armour by slot and coverage, severity steps per mechanism | Exists |
| Attack and defence roll with margin, wound penalties | Exists |
| Casualty tracker: Blood, rounds, treatment, initiative order | Exists |
| Combatant figures, example fighters per era, period pictures | Exists |
| Stop checks and nerve | New |
| Lethality dials and fate points | New |
| Characteristics, skills, origin and career tables, old wounds | New |
| Team templates and follower stat lines | New |
| Radiation, disease, burns and vacuum for speculative eras | New |
| Recovery track, disease and poison profiles, downtime actions | New (each HitLoc wound already has an infection risk) |
| The rulebook itself, written to be fast to read at the table | New |

## Checked against the Aftermath! rules

Read from the FGU boxed rules (Basic Rules and Gamesmaster's book). Aftermath! makes its tests on a d20 (skill and saving throws) and uses d100 for hit location and effect tables. The draft already follows it on the 6-second turn and on recovery; it differs most in replacing the damage-point pool with located wounds.

| Topic | Aftermath! | This draft | Take from it |
| --- | --- | --- | --- |
| Time scales | Strategic (a day split into a day turn and a night turn), Tactical (10 minutes to 1 hour, set by the GM), Detailed Action (6-second combat turn), Real Time, and Down Time between adventures (about a month of game time per week of play) | Combat turn, minute, exploration turn, day, week | Confirmed. Add a Down Time scale for between adventures |
| Who acts when | Each turn counts down action phases from the fastest fighter's Speed/2; fast fighters act more than once | Initiative order, one action each | Keep ours; it is far faster at the table |
| Hit location | d100 over 30 locations; facing decides the side (50% front or back, 70% the side facing the attacker); ±5 for attacks from above or below | 26 locations weighted by real wound records | Borrow the facing rule for which side is hit |
| Damage | Damage points minus the armour on the location, added to a pool against a Damage Resistance Total. Wounded past half (Deftness and Speed -25%), seriously past three quarters (-50%), out past the total, dead when lethal damage passes it by more than the Healing Rate. Lethal, subdual, crushing and mixed damage | No pool; each wound is a location, mechanism and severity | Keep ours. Their crushing split (mostly bruising, some lethal) matches our crush mechanism |
| Shock | Damage over the Shock Factor (10, plus Healing Rate for PCs) needs a Health save or the victim is unconscious for 50 minus Health turns | Stop check against Nerve on every wound | Use a threshold like theirs: only serious and critical wounds force a stop check |
| Criticals | d100 plus damage done: daze, stun, disable, trauma (severs; bleed to death in Health Group + 1d6 turns unless bandaged or cauterised), lethal. PCs may save to drop one step. Missiles add flesh wound, knock-back and stopping effects | Severity from the margin; effects line; fate points | Confirmed: their sever bleed-out is our lethality clock, their PC save is our fate point |
| Healing | Bruising heals in 10 minutes of rest; lethal and critical damage heal by the Healing Rate each dawn, -2 for a full day's travel, -1 for a fight, +1 each for rest, good care, a medic's roll and hospital. First aid right after a fight takes off a point. Bones take 100 minus Health days and must be set | Weekly track step, care and activity modifiers | Confirmed: the same factors. Add the first-aid window right after a fight and bone-setting time |
| Infection | From bites, dirty or rusty weapons, or not keeping clean (sleeping in armour for days). A secret Health save; an infected wound does not heal; a natural 20 on the daily save brings gangrene, which grows worse every day until it kills or is cut out | Infection roll when a wound worsens | Add their triggers (dirty weapon, bite, sleeping in armour) and the rule that an infected wound does not heal |
| Disease | Each disease coded as vector (air, wound, food or water, skin), course (acute, recurring, chronic), the attribute it attacks, incubation, virulence and cycle. Resist on exposure; drains an attribute each cycle to a crisis save. Wounded -1 and seriously wounded -2 on disease saves. Optional immunity after surviving a strain. Water is foul 80% of the time in swamp, 50% in rubbled cities, 5% in open country; boiling allows a reroll | Five-step track, one roll per check, weekly outbreak roll from camp factors | Keep our track. Add the foul-water chance by terrain and boiling, and immunity for typhus and plague survivors (not flux or ague). Their wound penalty on disease saves matches ours |
| Food, water and weather | Safe days on half rations, then starvation advances like a disease to fatigue and death; thirst is twice as fast. Rations assumed balanced; deficiency diseases left to the GM. Heat doubles water need; cold without proper clothes brings fatigue, and a night exposed risks pneumonia | Calories, fresh food, sunlight and vitamin A marks | Add their thirst rule and cold exposure leading to pneumonia |
| Poison | Works like a disease: two stages (attributes -25%, then -50%), then a crisis save | Poison as a disease profile | Confirmed |

The proposed changes above wait for your decision; none are written into the rules sections yet.

## Checked against Rolemaster's Arms Law

Read from Arms Law & Claw Law (ICE, 2nd edition). Rolemaster resolves a blow in two d100 rolls: the attack roll, open-ended on 96-00, plus offence minus defence, read against the target's armour type, gives concussion hits and a critical of severity A to E; a second d100 on that critical's table (slash, puncture, krush and others) gives the named effect.

| Topic | Arms Law | This draft | Take from it |
| --- | --- | --- | --- |
| Time | 10-second battle round, 6 rounds to a 1-minute turn; phases in order: spells, fire, movement, fire again, melee | 6-second turn, initiative order | Keep ours. Their fire-before-melee order is worth an optional rule for volleys |
| Attack | d100 open-ended + OB - DB against one of 20 armour types for the whole body; the table gives hits and critical severity | d100 under skill; margin sets severity; armour by location | Keep ours: one roll fewer, and armour by location |
| Location | Set by the critical roll's band: legs and body in the middle, head, neck and vitals at 96-100, so the worst criticals land on the head | Location from the era's real wound records, independent of severity | Keep ours; theirs makes head wounds follow luck, not the records |
| Critical effects | Extra hits, hits per round (bleeding), cumulative penalties (fights at -10 to -90), stunned, must parry, down for N rounds, broken or useless limbs, severs, and death in N rounds | Bleed, pain, lost function, shock, lethality clock | Confirmed. Add their action states as the results of a failed stop check: must defend only, stunned, down for N turns |
| Damage pool | Concussion hits against a limit; unconscious past it; death at about twice it | No pool | Keep ours |
| Recovery | Concussion hits heal 1 an hour resting, 1 per 3 hours active. Injuries heal by type of tissue: a d100 + Constitution roll gives days for a light injury (about 1-10 by type), x5 for medium and x10 for severe; hospital care halves it | Weekly steps on one track | Add tissue type: bone, tendon, organ and head wounds take longer per step than muscle and skin |

The proposed changes above wait for your decision; none are written into the rules sections yet.

## Checked against Rolemaster's Character Law & Campaign Law

Read from Character Law & Campaign Law (ICE): the healing, death, injury, disease, poison and exhaustion rules, and character generation.

| Topic | Character & Campaign Law | This draft | Take from it |
| --- | --- | --- | --- |
| Degrees of injury | Light: penalty up to -20 or bleeding 1-5 a round. Medium: -21 to -50, bleeding 6-10, or a fracture. Severe: -51 or worse, bleeding over 10, a shattered bone, or an organ destroyed or out for more than a day | Light, serious, critical | Confirmed. Use their bands to define our three severities |
| First aid | Heals light injuries with the right kit (bandage, splint); slows medium and severe ones (bleeding cut by 5 a round, more with a tourniquet; a medium fracture set). No use on serious nerve or organ damage. Straining the wound (fighting, faster than a walk) undoes it | Bind, tourniquet, surgery change the clock | Add: first aid fixes light wounds, only slows worse ones, and fighting or hurrying undoes it |
| Recovery | Days by tissue type (burn, bone, muscle, head, organ, tendon), x5 for medium and x10 for severe, halved in care. Several wounds take the worst one's time plus half of the rest. The penalty falls evenly day by day | Weekly track steps | Add tissue type to wound recovery, and the worst-plus-half rule for several wounds |
| Permanent harm | Only after a severe wound: open-ended d100 + Constitution; over 100 means none, and the shortfall sets how bad | Healed may leave an impairment | Adopt: one roll when a critical wound heals |
| Dying | Past the hit limit plus Constitution, the victim dies in Constitution/10 rounds unless brought back under; a fatal critical kills at its stated time unless someone intervenes | Lethality clock | Confirmed |
| Disease and poison | A resistance roll (Constitution and race bonuses) against the disease's level; how badly it fails sets the course: mild, moderate, serious or extreme. Grouped by how they spread (flea-borne, airborne, and others); effects stack | Resist roll, then a separate peak roll | Fold the peak into the resist roll: fail by a little, a mild case; fail by a lot, a deadly one. One roll fewer |
| Exhaustion | Exhaustion points spent by pace and fighting, multiplied by heat or cold, rough ground, bog, wounds over 25% (x2) and 50% (x4), and going without sleep | Fatigue mentioned, not defined | Add a simple fatigue track that heat, cold, bad ground, wounds and lack of sleep speed up |
| Characteristics and background | Ten stats from 1 to 100, each with a current and a potential value. Background rolls give a special ability that comes with a drawback | Six characteristics, origin roll | Give each origin roll a trait with a matching drawback, for colour |

The proposed changes above wait for your decision; none are written into the rules sections yet.

## Checked against Gamma World and a Morrow Project conversion

Gamma World read from the first edition (TSR, 1978). The Morrow Project material is a fan conversion to the Genesys system (Thomas Clegg, on GM Binder), not Timeline's original rules, so it shows how the team setting can be run but does not confirm the original wound procedure.

| Topic | Source | What it does | Take from it |
| --- | --- | --- | --- |
| Time | Gamma World | Route move about 4 hours; search move 10 seconds; melee round 10 seconds | Our scales already cover these |
| Combat and damage | Gamma World | Side-wide d6 initiative; hit points from Constitution d6s; no hit locations; a creature killed with little overkill gets a dying stroke | Keep ours. The dying stroke is a nice optional rule: a man struck down can still finish his blow |
| Fatigue | Gamma World | Long fights tire fighters after 11 to 18 rounds (about 2 to 3 minutes), sooner in heavy armour with heavy weapons; a penalty to hit | Add to the fatigue track: heavy armour and weapons tire a fighter after a few minutes of fighting |
| Poison and radiation | Gamma World | Intensity 3-18 cross-indexed with Constitution in one lookup: no effect, dice of damage, or death; an antidote within 2 rounds saves the victim. Radiation can also bring a mutation a week later | Use the intensity-against-Endurance idea as the resist roll's modifier for poison and radiation |
| Radiation dose | Morrow conversion | Radiation accumulates as a dose that lowers what the body can take; a resist roll reduces each exposure; potassium iodide removes some once a day; protective suits block it | Track radiation as an accumulating dose that pushes the sickness track, for the after-the-bomb era |
| Characters and followers | Gamma World | Three kinds of character (pure human, mutated human, mutated animal); random mutations, some of them defects; Charisma sets the number of followers and their morale | Confirmed: mutation with defects for the speculative eras. Let Presence set how many followers a leader can keep and their morale |
| Succession | Gamma World | When a character dies, a relative or the most loyal follower inherits and the player can carry on with them | Adopt for team play: a follower can step up when the leader falls |
| Teams | Morrow conversion | Recon teams of 5-6 (up to 8); military teams with a medic, mechanic and negotiator; science teams; specialist teams; a frozen reserve that replaces casualties | Use as team templates for the after-the-bomb era |

The proposed changes above wait for your decision; none are written into the rules sections yet.

## Checked against Classic Traveller

Read from the Classic Traveller facsimile (GDW, 1981 edition): character generation and Book 1 combat.

| Topic | Classic Traveller | This draft | Take from it |
| --- | --- | --- | --- |
| Time and range | 15-second combat rounds; five range bands (close, short, medium, long, very long) on a simple line grid; each fighter declares evade, close, open range or stand | 6-second turn | Keep ours. The four movement statuses are a fast way to run movement without a map |
| To hit | 2d6, 8+ to hit, with modifiers for weapon against armour, range, skill and strength or dexterity | d100 under skill | Keep ours |
| Wounds | Each damage die is a separate wound taken off Strength, Dexterity or Endurance; the first wound all goes on one physical characteristic chosen at random, so first blood can drop or kill. One at zero: unconscious; two: seriously wounded; three: dead | Located wounds; stop check | Confirmed: one hit can end a fight, which is the point of our stop check |
| Recovery | Unconscious for 10 minutes, then back at half way; full recovery with a medic's kit (Medical-1) or 3 days' rest. Seriously wounded: out 3 hours, and full recovery needs a medical facility and Medical-3 | Care modifiers by medic and hospital | Confirmed: the level of medical skill and facility decides what can be healed at all |
| Fatigue | Endurance sets how many blows and swings a fighter can make before resting 30 minutes; after that, blows are weakened. Guns are not limited | Fatigue track | Add: hand-to-hand fighting spends fatigue, shooting does not |
| Morale | When a party has 25% unconscious or dead, it throws 7+ each round to stand; +1 military unit, +1 leader present, +1 leader with tactics, -2 leader killed, -2 over 50% casualties | Individual stop checks | Add a team morale check at 25% casualties, with the same leader and loss modifiers. It matches what ends real fights |
| Characters | Six characteristics on 2d6; four-year terms in a service, each with enlistment, survival, commission, promotion, skills, and aging later; mustering-out benefits. An optional rule turns a failed survival roll into an injury instead of death | Origin, career terms, old wounds; nobody dies in generation | Confirmed, including the optional injury rule, which is our old-wound roll |

## Checked against The Morrow Project (4th edition)

Read from The Morrow Project 4.0 rulebook: timing, combat, damage and recovery, disease and radiation. Of all the games checked, it is the closest to this proposal in what it models, and the furthest in how much bookkeeping it asks for.

| Topic | Morrow Project 4.0 | This draft | Take from it |
| --- | --- | --- | --- |
| Time | 3.6-second combat turn; 10 make a 36-second tactical turn; 100 a 6-minute game turn | 6-second turn | Keep ours; theirs confirms that bleeding and treatment need a minute-scale step |
| Rolls | d100 under a task base (ability x2 plus skill); degrees of success can shift the hit location or add damage; zero degrees is a graze at half damage | d100 under skill; margin sets severity | Confirmed. Add the graze: a hit by the barest margin does half |
| Hit location | d100 over 30 human locations (head 6%, neck 2%, arms 24%, torso and groin 32%, legs 36%); called-shot and partial-cover tables (head-and-shoulders in a window, legs only, and so on) | Era tables from real records | Add cover tables: when only part of a man shows, roll on the part that shows |
| Damage | Bullet damage from calibre and velocity; armour subtracted per location, with blunt trauma through soft body armour; structure points per location; head, neck or torso at zero is fatal without aid | Severity steps, armour by location | Confirmed: blunt trauma behind soft armour is worth adding for the modern era |
| Shock | A Constitution check whenever damage passes a threshold (any limb hit; head and torso above Mass/5); the result sets endurance loss, bleed rate, and the chance of impairment, critical bleeding, a severed limb or death | Stop check | Confirmed, including the threshold idea from Aftermath! |
| Bleeding | Blood points; each wound bleeds its damage every 36 seconds, a critical bleed every 3.6 seconds; slash and blunt wounds bleed less than gunshots (x0.5 and x0.2). Pressure or a tourniquet each turn cuts it; a man lying still can stop it himself; moving reopens it. Heavy blood loss saps endurance; below a critical level, a check every 6 minutes to stay alive | Blood pool B0-B3 and the lethality clock | Confirmed. Add self-help (lie still and press) and the rule that exertion reopens a wound |
| Recovery | Blood back at about 1% a day; structure 1 point per 2.5 days, with a recovery check every 10 days that can bring an infection; joints may be left with a lasting penalty | Weekly steps | Confirmed; joint wounds should be the likeliest to leave a lasting impairment |
| Disease and poison | Route (air, food or water, contact, vector, injection), infectivity, incubation, then virulence drains Constitution daily during an active phase; wound infection shows after 3-5 days, worse for belly and head wounds and bites | Track with daily checks | Confirmed. Wound infection risk higher for belly and head wounds and bites; shows after 3-5 days |
| Radiation | Dose in rads, cut by shielding (a basement to 1/10, a tank to 1/25); real dose bands from no effect under 100, through bone-marrow sickness, to death above 3000; dose is permanent and cumulative | Not yet defined | Use their dose bands for the after-the-bomb era |
| Panic | Focus check with modifiers; NPCs rated green, regular or veteran | Stop check and morale | Confirmed: rate NPCs by experience for morale |
| Fatigue | Endurance points spent by pace, load, terrain, combat and blood loss; tired at 5 or less (-10%), stunned at zero; rest restores 1 an hour, sleep 3 | Fatigue track | Use as the model for the fatigue track |

## Open questions and next steps

Six decisions shape everything else; a playtest of one era can answer the rest.

- [x] **Name and first era.** Decided: the game is Grave Wounds: blood, bivouac and weather, and the medieval era leads the first playtest, for its wound data (Sidon, Visby, Towton).
- [x] **Six characteristics or fewer?** Decided: six (Strength, Agility, Endurance, Wits, Nerve, Presence), because six gives colour.
- [x] **Margin or separate severity roll?** Decided: the attack's margin sets severity, so a hit needs no extra roll.
- [ ] **How much the book reads from the roller.** Undecided. A paper-only game needs printed tables; a roller-first game can hide the arithmetic. The medieval playtest can show how much players lean on the roller.
- [ ] **Stop check thresholds.** Agreed approach: calibrate against the records, how often a wounded man really stopped fighting. Still to do: find those figures for the medieval era.
- [x] **Recovery time step.** Decided: daily checks for fever and poison, weekly for wounds and slow illness. The medieval disease set is drafted above. Draft numbers for each medieval disease are in, with the weekly outbreak check. Still open: the disease sets for later eras.

Next steps:

1. Settle the roller question and playtest the draft disease numbers over a few weeks of camp.
2. Write the one-page combat rules and the stop check, and test them in HitLoc's tracker.
3. Draft the character generation tables for the first era and make a team in 20 minutes.
4. Playtest one fight with two teams, then adjust the dials.
5. If you find the Aftermath! or Rolemaster books, compare their turn structure and critical layout with this draft.

## Sources

- [Aftermath! (Wikipedia)](https://en.wikipedia.org/wiki/Aftermath!) and [Vintage RPG review](https://www.vintagerpg.com/?p=19014)
- [Arms Law (Wikipedia)](https://en.wikipedia.org/wiki/Arms_Law) and [Rolemaster Unified Core Law release (Iron Crown)](https://ironcrown.co.uk/rolemaster-unified-core-law-out-now/)
- [Traveller: characters and combat (Necropraxis)](https://necropraxis.com/?p=3127)
- [The Morrow Project (Wikipedia)](https://en.wikipedia.org/wiki/The_Morrow_Project)
- [Gamma World (Fanlore)](https://fanlore.org/wiki/Gamma_World)
- [Fallout tabletop: Damage and Injury (Roll20 compendium)](https://roll20.net/compendium/fallout/Rules:Damage%20and%20Injury)
- [Union army disease table (Montana State)](https://montana.edu/historybug/civil_war_disease_table.html) and [Civil War medical services, with disease and amputation tables (ACWRTA)](https://www.americancivilwar.asn.au/meet/2003_10_mtg_medical_services.pdf), both from the Medical and Surgical History of the War of the Rebellion
- [Germs Deadlier Than Bullets (HistoryNet)](https://historynet.com/germs-deadlier-than-bullets/)
- [Howard 1991, Medical aspects of Moore's Corunna campaign (JRSM)](https://journals.sagepub.com/doi/reader/10.1177/014107689108400517)
- [Epidemic typhus](https://en.wikipedia.org/wiki/Epidemic_typhus), [case fatality rates](https://en.wikipedia.org/wiki/List_of_human_disease_case_fatality_rates) and [Siege of Harfleur](https://en.wikipedia.org/wiki/Siege_of_Harfleur) (Wikipedia)
- [Scurvy at Andersonville (US Deadly Events)](https://usdeadlyevents.com/?p=3144)
- [HitLoc](https://github.com/swares/HitLoc): wound tables, sources and the roller

Aftermath! rules checked against the FGU boxed set. Rolemaster checked against Arms Law & Claw Law (2nd edition) and Character Law & Campaign Law; Rolemaster Unified not seen. Gamma World checked against the first edition (TSR, 1978); Traveller against the Classic Traveller facsimile (1981 edition). The Morrow Project checked against the 4th edition (Morrow Project 4.0) rulebook, and a fan Genesys conversion for its team types.

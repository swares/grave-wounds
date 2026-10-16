# Self-play review: the enemy commander against the battles as fought

October 2026. Every battlefield on the field map was played with the enemy commander on both
sides (`python -m gravewounds selfplay`, or Run on the page), with the stances the armies fought
with, and the result set against what happened. This note says what went wrong, why, what was
changed, and what is left for later. It is a design review, not a validation: a few runs per
field, judged by eye against short accounts of each battle.

## How it was done

- Each battlefield was played with the commander on both sides, the side its objective names
  attacking and the other holding (or the stances the battlefield gives; else both attack).
- Before the changes: 10 runs a field for the first sixteen, 6 or 3 for the rest (the big fields
  are slow), each stopping after 60 exchanges at most.
- After the changes: 3 runs a field for the first few, 1 for the rest (the runs are now much
  longer, up to 240 exchanges, and the big fields take minutes each). One run is a weak sample:
  read the "after" column as a direction, not a rate.
- A run's winner: the side left standing if the other has nothing; the attacker if it took and
  held the objective; else, with an objective, the side holding it at the end; with none, the
  side with fewer losses (in share of its men).
- "As fought" is each battlefield's own account (the header of its file in `data/fields`),
  boiled down to who won and roughly at what cost.

## What went wrong, by kind

1. **No fight at all** (Towton, Visby, Sidon before; Cassino; Khe Sanh and Kapyong before).
   - With no objective and no enemy in sight, an attacking unit stood still, so two armies
     ordered to attack each other on a snowy plateau never met. *Fixed:* an attacking unit with
     no objective and no enemy it knows of goes forward along its facing to find one ("move
     forward to find the enemy").
   - Approaches that take longer than 60 exchanges (Khe Sanh's battalion starts 40 hexes off
     through jungle at night) ended before contact. *Fixed:* a battlefield with phases runs at
     least 30 exchanges past its last phase's start, at most 240. Khe Sanh is now fought (the
     North Vietnamese lose a fifth of their men and the hill holds).
   - At Kapyong the two Chinese battalions (500 and 600 men, 30 hexes wide) never move in 240
     exchanges: the commander turns each unit to face its objective before moving, and turned,
     the deep blocks do not fit ("no room there") from where they start. *Fixed in the retest
     (below):* the commander now tries other facings when the one toward its goal does not fit.
   - At Cassino the Indian, British and Polish battalions (450-900 men in extended order, 100-300
     hexes of ground each) cannot fit along the narrow, rough ridge; after a move or two every
     hex is "no room there" or "too far". *Fixed in the retest (below)* by the same change as
     Kapyong: they now climb the ridge facing as near their goal as the ground allows.
2. **The run stopped too soon or on the wrong thing**.
   - Fetterman ended at once: the warriors' side had only its ten decoys on the field, and they
     broke, with the thousand still to come. Pork Chop ended when E Company was overrun, before
     K and L Companies (still to come) could counter-attack. *Fixed:* a side with units still to
     come (a later phase's, or a lift in the air) is not "gone".
   - Grozny's battlefield opens with the Russians in the station; the run ended "taken and
     held" after five exchanges. *Fixed:* holding the objective from the start is not taking it
     (it counts once it has changed hands), and a hold with a standing enemy within 10 hexes does
     not count. (Grozny still goes the wrong way: see below.)
3. **Wrong stances.** Agincourt, Cowpens, Sidon and Fallujah have no objective, so both sides
   attacked: the English left their stakes, the insurgents came out of the houses. *Fixed:* a
   battlefield with no objective can say how its armies fought (`stances`), and does for these four.
4. **The commander's habits.**
   - Tanks went to ground under fire (73 Easting) and lay still for the rest of the battle.
     *Fixed:* vehicles never go to ground.
   - Modern infantry attacking men in trenches, bunkers or buildings stopped at range and traded
     fire, going to ground under fire, and almost never hit them (Goose Green: 2 Para lost a
     third of its men; the Argentines in their trenches about one in ten). *Changed:* modern rifles
     and sub-machine guns now storm works as black-powder infantry do: they close, firing as they
     go, and charge with their quality's odds. The battles where this mattered still go the wrong
     way (below), but they are now fought at close quarters, as they were.
5. **Beyond the commander** (not fixed: the combat model and the battlefields' data).
   - *Agincourt:* 1,600 longbowmen put down only a handful of plate-armoured men an exchange,
     and the French vanguard routs an archer wedge; the arrow-storm, the dead and maddened horses,
     the mud and the crush are not modelled.
   - *73 Easting:* the game has one tank kind, so an M1A1 and a T-72 are equals gun for gun (no
     fire control, no armour difference), and tank units break after losing a few crewmen; the
     dug-in T-72s win.
   - *Grozny:* the Chechen RPG ambush of armour in the streets at night is not reproduced: the
     Russians hold the station and the Chechens lose more.
   - *Cassino town:* the paratroops in the rubble are shot out within 30-45 exchanges; in fact
     they held the south of the town for eight days. Men in rubble and cellars are too easy to
     hit, or too few on the map.
   - *Lundy's Lane:* the guns were taken in the dark; the field map has no darkness there (the
     battlefield says to treat it as fog).
   - *Cassino:* the battalions are too big for the ridge (above).
6. **Plans the commander cannot make** (not fixed).
   - *Cowpens:* Morgan's double envelopment (the militia falling back and coming round, the horse
     from behind the rise).
   - *Osan, Mons:* a holding commander never falls back; Task Force Smith withdrew under orders
     when the North Koreans worked round both flanks, as the Fusiliers did at Mons in the afternoon
     (Mons now goes the right way by attrition).
   - *Hue, Heartbreak Ridge, Goose Green:* days-long or hours-long clearing with heavy fire
     support; within a run the attackers bleed and stall.

## Each battlefield

Matched: how many runs the self-play winner was the historical winner. Casualties: the median
share of each side's men killed, dead of wounds, left on the field or carried off wounded (side A
is the battlefield's first side). "Before" is the commander as it was; "after" is with every
change below.

| Battlefield | As fought (winner first) | Before: matched; casualties A / B | After: matched; casualties A / B |
| --- | --- | --- | --- |
| Agincourt (English / French) | English: English win; French vanguard cut down in the mud; rearguard never came on | 2 of 10; 26.9% / 13.9% | 0 of 3; 25.8% / 8.9% |
| Albuera (Allies / French) | Allies: French columns take the heights' edge; Allies stand and Cole drives the French off | 3 of 3; 16.5% / 32.8% | 3 of 3; 16.5% / 32.8% |
| Hill 700 (Americans / Japanese) | Americans: Japanese seize pillboxes at the saddle; Americans restore the line over days | 10 of 10; 7.2% / 45.5% | 3 of 3; 4.9% / 35.9% |
| First Bull Run (Confederates / Union) | Confederates: Henry Hill changes hands; late Confederate brigades break the Union line | 8 of 10; 15.6% / 19.2% | 1 of 1; 21.0% / 14.6% |
| Snakeshead Ridge and the abbey (Allies / Germans) | Germans: Indian Division's night attack on Point 593 fails with heavy loss | 10 of 10; 0.0% / 0.0% | 3 of 3; 0.0% / 0.0% |
| The Poles at Point 593 and Phantom Ridge (Allies / Germans) | Germans: Poles take 593 and are thrown off it the same day | 3 of 3; 0.0% / 0.0% | 1 of 1; 6.6% / 35.1% |
| Cassino town and Castle Hill (Allies / Germans) | a draw: New Zealanders take Castle Hill; paratroops hold the south of the town (stalemate) | 0 of 10; 29.6% / 69.7% | 0 of 3; 28.5% / 65.1% |
| The perimeter at Chipyong-ni (United Nations / Chinese) | United Nations: Chinese break into G Company's hill; the perimeter holds until the tanks come | 3 of 3; 12.4% / 26.1% | 1 of 1; 18.2% / 28.3% |
| The Rangers at Cisterna (Americans / Germans) | Germans: Rangers pinned in the open short of the town; of 767, six got back | 3 of 3; 36.4% / 9.4% | 1 of 1; 39.5% / 7.3% |
| Cowpens (Americans / British) | Americans: Morgan's double envelopment: the British line surrenders | 5 of 10; 12.9% / 9.9% | 0 of 1; 8.6% / 8.3% |
| Hill 875 (United States and ARVN / North Vietnamese) | North Vietnamese: First day: the paratroopers are stopped below the crest and cut off (crest taken four days later) | 7 of 10; 58.8% / 34.4% | 1 of 1; 46.7% / 14.6% |
| 73 Easting (Coalition / Iraqis) | Coalition: Eagle Troop destroys the dug-in tank company in 23 minutes without loss | 0 of 10; 15.1% / 14.8% | 0 of 1; 10.3% / 10.6% |
| Fallujah (Coalition / Insurgents) | Coalition: Marines and tanks clear the Jolan house by house; insurgents fall back south | 10 of 10; 1.8% / 40.5% | 1 of 1; 22.1% / 56.1% |
| The Fetterman Fight (US Army / Lakota, Cheyenne and Arapaho) | Lakota, Cheyenne and Arapaho: Decoys draw the relief over the ridge; about a thousand warriors kill all 81 | 0 of 10; 0.0% / 90.0% | 1 of 1; 100.0% / 10.5% |
| Fox Hill at Toktong Pass (United Nations / Chinese) | United Nations: Chinese overrun forward squads; the Marines hold the crest (26 killed, 89 wounded of 240) | 10 of 10; 6.0% / 19.6% | 1 of 1; 7.1% / 13.7% |
| Darwin Hill (British / Argentines) | British: 2 Para pinned for the morning, then breaks into the Darwin Hill line | 0 of 10; 30.8% / 11.3% | 0 of 1; 41.1% / 11.1% |
| Grozny (Russians / Chechens) | Chechens: The brigade takes the station, is cut off overnight and destroyed breaking out | 0 of 10; 1.4% / 22.8% | 0 of 1; 6.2% / 39.5% |
| Hamburger Hill (Dong Ap Bia) (United States and ARVN / North Vietnamese) | United States and ARVN: After ten days the summit is taken about noon | 10 of 10; 26.3% / 71.8% | 1 of 1; 43.5% / 54.4% |
| Hill 931 on Heartbreak Ridge (United Nations / North Koreans) | United Nations: Night attack along the crest; Hill 931 taken before noon | 0 of 3; 31.5% / 45.7% | 0 of 1; 33.7% / 27.0% |
| Hue (United States and ARVN / North Vietnamese) | United States and ARVN: Marines take the provincial headquarters building by building after two days | 0 of 6; 18.2% / 13.2% | 0 of 1; 51.8% / 17.5% |
| Hill 504 and the valley at Kapyong (United Nations / Chinese) | United Nations: Australians hold the hill all night (32 killed, 59 wounded), then fall back in order | 3 of 3; 0.0% / 0.0% | 1 of 1; 0.0% / 0.0% |
| Combat Outpost Keating (Coalition / Insurgents) | Coalition: Insurgents break in from the east; the Americans retake the outpost by the afternoon | 10 of 10; 28.1% / 28.5% | 1 of 1; 26.0% / 37.4% |
| Hill 861A (United States and ARVN / North Vietnamese) | United States and ARVN: NVA break into E Company's trenches; Shanley's counter-attack throws them out (7 Marines killed, 100+ NVA dead) | 10 of 10; 0.0% / 2.0% | 1 of 1; 0.0% / 19.5% |
| Lundy's Lane (Americans / British) | a draw: Americans take the guns in the dark and hold the crest against three counter-attacks; both exhausted | 0 of 6; 66.6% / 27.5% | 0 of 1; 43.2% / 39.7% |
| Lützen (Swedes / Imperialists) | Swedes: Swedes storm the windmill battery late; the Imperialists withdraw in the night | 1 of 3; 1.1% / 4.1% | 1 of 1; 1.3% / 6.0% |
| Mogadishu (United States / Somali National Alliance) | United States: The force holds round the crash site through the night until relieved | 6 of 6; 5.9% / 7.4% | 1 of 1; 35.6% / 45.5% |
| Mons (British / Germans) | Germans: Rifle and machine-gun fire cut down the Germans; the British fall back by afternoon | 0 of 3; 11.1% / 18.8% | 1 of 1; 51.0% / 11.7% |
| Task Force Smith at Osan (United Nations / North Koreans) | North Koreans: Tanks drive through; infantry work round both flanks; Task Force Smith withdraws | 0 of 3; 27.5% / 10.5% | 0 of 1; 35.6% / 9.2% |
| Pork Chop Hill (United Nations / Chinese) | United Nations: Chinese overrun the trenches; K and L Companies take the hill back | 0 of 3; 13.7% / 40.0% | 1 of 1; 13.5% / 45.4% |
| The Great Redan (British / Russians) | Russians: British reach the salient, stall on the parapet, and are thrown back | 3 of 3; 24.8% / 17.8% | 1 of 1; 29.9% / 10.1% |
| The Great Redan (British / Russians) | Russians: The columns are swept by grape in the open; the attack is called off | 2 of 3; 35.6% / 20.8% | 1 of 1; 43.7% / 25.7% |
| Sidon (Franks / Damascenes) | Damascenes: The Damascenes break into the unfinished walls and cut the garrison down | 0 of 3; 0.0% / 0.4% | 1 of 1; 6.6% / 0.5% |
| Towton (Yorkists / Lancastrians) | Yorkists: Hours of fighting; Norfolk arrives; the Lancastrian line breaks and is slaughtered in the rout | 0 of 3; 0.0% / 0.0% | 1 of 1; 1.2% / 14.2% |
| Visby (Gotlanders / Danes) | Danes: The Danish professionals crush the Gotland levies | 3 of 3; 2.8% / 0.0% | 1 of 1; 2.6% / 0.0% |
| The Wagon Box Fight (US Army / Lakota, Cheyenne and Arapaho) | US Army: Breech-loaders hold the corral against mounted and foot attacks | 3 of 3; 0.0% / 10.2% | 1 of 1; 0.0% / 18.3% |
| Wanat (United States / Insurgents) | United States: The post is nearly overrun; reinforcements hold it until the fighters are driven off | 3 of 3; 47.4% / 25.7% | 1 of 1; 28.6% / 36.3% |
| Landing zone X-Ray (United States / North Vietnamese) | United States: The landing zone holds under assault from three sides | 3 of 3; 27.5% / 49.9% | 1 of 1; 32.4% / 49.9% |
| **Battlefields where most runs matched** | | **21 of 37** | **27 of 37** |

Notes on the ones that still go wrong after the changes are in the list above. Some read as
"matched" without much of a fight: Cassino in February and Kapyong (the defenders hold because
the attackers cannot move), and Visby and Sidon (the attackers win on fewer losses, a handful of
men each, before the limit). Albuera ran before the changes that matter to it and was not rerun
(it takes about half an hour a run).

## The changes made (all in the rules, Python and JavaScript alike)

| Change | Where | Why |
| --- | --- | --- |
| An attacking unit with no objective and nothing in sight goes forward along its facing | `commander._search`, `units.js search` | Towton, Visby, Sidon: no contact |
| A self-played battle with phases runs 30 exchanges past the last phase, at most 240 | `commander.self_play.after_phases`, `most` | Khe Sanh, Kapyong, Lützen: ended before contact |
| A side with units still to come is not gone | `battle.to_come` | Fetterman, Pork Chop |
| Holding the objective from the start is not taking it; a hold needs no standing enemy within 10 hexes | `battle.stop_reason`, `self_play.secure` | Grozny |
| Battlefields with no objective can give their stances | `stances` in `data/fields` (Agincourt, Cowpens, Sidon, Fallujah) | wrong stances |
| Vehicles never go to ground | `commander._stay`, `_unsteady` | 73 Easting |
| Modern rifles and sub-machine guns storm works | `commander.storm` | Goose Green, Hue, Heartbreak: stalled at range |
| The air controller counts losses last exchange as under fire | units marked `hit` after an exchange in which they lost men | the design asked for it |
| A shot is not looked for beyond twice a weapon's range | `units._beyond_reach` | speed only: the same results, ten times faster on big fields |

## Recommended, not built

- **Cassino's battalions** (both battles) might better come on as companies: they now move, but
  as 100-300-hex blocks on a narrow ridge. This is the battlefields' data. *Tried, 16 October: see
  "Followed up" below; the Poles now come on as companies, February stays as battalions.*
- **Tank kinds by era** (an M1A1 is not a T-34 or a T-72): fire control and armour by generation,
  and vehicle units' morale (a tank troop does not break on losing a few crewmen).
- **Archery against armour and horses** at Agincourt: the arrow-storm's effect on horses and on
  men struggling in mud is missing.
- **Men in rubble and cellars** (Cassino town): harder to find and to hit, or more of them.
- **A holding commander that withdraws** when outflanked and outnumbered (Osan, Mons), and a
  plan for an envelopment (Cowpens): these are plans, beyond a unit-by-unit commander. *Measured,
  16 October, and not built: see "Followed up" below.*
- **Darkness at Lundy's Lane** (the battlefield's light).
- **Faster exchanges** on the biggest fields (Albuera takes about 3 seconds an exchange even now:
  the ground and sight look-ups dominate).

## Retesting

`python -m gravewounds selfplay --field <id> -n 5 --story` plays a battlefield five times and
prints each battle's turning points; on the page, put the commander on both sides and press Run.
The scripts used for this review (all battlefields, winners against the accounts) are not in the
repository; the numbers above are from them.

Since 16 October the rules remember sight lines, the ground and step costs (see units.md, Both
sides): the same battles, move for move, about five times faster. Both runs of all 37
battlefields now take about 13 minutes of computing, against about 70, with Chipyong under a
minute and a half a run instead of nine and a half.

## Retest, 16 October 2026

The merged build (with every change above) was played again on all 37 battlefields, two runs
each, and so was a build with one more change: **a unit that cannot stand facing its goal (no
room for its ranks, or the turn costs more than its move) moves facing as near its goal as it
can** (a point either side, then two, then the way it faces now), and **a hold of the objective
is not secure while the enemy still has units to come**.

| | Merged build | With the facing change |
| --- | --- | --- |
| Battlefields where most runs matched the winner | 24 of 37 | 23 of 37 |
| ... of those, with a real fight (both sides lost 2% or more) | 17 | 20 |
| Runs matched | 52 of 74 | 47 of 74 |

What the facing change did:

- **Better:** Kapyong, Cassino (February) and Khe Sanh, where the attackers could not move or
  arrived too late, are now fought; Kapyong's Chinese lose about half their men against the
  hill, as they did. Osan now goes the North Koreans' way (Task Force Smith is overrun), Mons
  and Mogadishu more consistently match. Lützen is a hard fight on both sides (about a quarter
  of each army) instead of a Swedish walkover at 1%.
- **Worse, or no longer a match:** Hamburger Hill becomes a coin-flip (both sides lose about
  half; in both runs the attackers broke first). Lützen ends with the Imperialists still on the
  windmill hill at 240 exchanges (in 1632 it fell late in the day). The Poles at Cassino take
  Point 593 and hold it (in May 1944 they took it and were thrown off it that morning; the
  throwing off comes long after this run). Pork Chop ends with the Chinese still on the hill
  (the counter-attack companies come, but do not retake it).
- The headline count is flat (24 to 23), but battles that were won by default because one side
  never moved are now fought; the change fixes a fault rather than tuning results, and it stays.

## Followed up, 16 October 2026

**A holding commander that withdraws: measured, not built.** Before writing any rule, each
exchange of a self-play run of every battlefield was measured for two triggers a holding side
might use (the rules unchanged):

- *Outflanked and hurt* (standing enemy past either end of its line, level with it or behind it,
  near its units, and a share of its men lost): it never fires at Mons or Osan, where the attackers
  come straight on and never work round a flank, but it would fire at Mogadishu, Wanat, Pork Chop,
  Keating, Albuera and Lützen, all defences that held.
- *Losses alone* (30-50% of the side's men no longer standing): 15-17 holding sides, most of them
  defences that held at heavy cost (X-Ray, Mogadishu, Wanat, Pork Chop, Kapyong).

Meanwhile Mons and Osan already end close to the day: the defenders break and leave the field
after losing about a quarter to a third of their men, near what they lost; it is a rout rather
than an ordered withdrawal, and it comes earlier. Neither trigger tells the defences that held
from those that went, so nothing was built. A withdrawal the battlefield orders (Osan's 14:30 and
Mons' 13:10 are in their phases) would change no result today, since both break first. Working
round a flank, and Cowpens' envelopment, remain to do.

**Cassino as companies.** Each battalion was split into companies of equal strength (the same
men, the same men per hex of front, so a company is a narrow, deep block), standing side by side
across its battalion's old front:

- *February:* the Rajputanas and the Sussex took Point 593 in all four runs, by exchange 25 to 50
  (with battalions the paratroops held in every run). The accounts give no progress that night
  (the defence held, at a cost of 196 Rajputanas, 149 of the 1/9th Gurkhas and 96 of the 1/2nd), so
  the companies made the battle less like the day, and February stays as battalions. Why small
  units take 593 so easily is still open; the accounts describe attacks along the narrow ridge
  (the Sussex started one from about 70 yards off) under fire from the tops round it, which the
  map and the night may not make hard enough.
- *May:* the Polish battalions (and the Kresowa's 900) now come on as four companies each. The
  result is unchanged in four runs: the Poles take 593 and hold it, by exchange 28 to 41. They took
  it about 02:00 and were thrown off it in the morning by the paratroops' counter-attacks
  (Heilmann's 4th Parachute Regiment, about 800 men on the massif). No source found gives the
  counter-attacks' number, strength or times, so they are not on the map; until they are, the
  run ends with 593 in Polish hands.

Sources: [Battle of Monte Cassino (Wikipedia)](https://en.wikipedia.org/wiki/Battle_of_Monte_Cassino),
citing Holmes (2001) and Whiting; the battlefields' own accounts.

**Darkness at Lundy's Lane.** A phase can now set the light from then on, and Lundy's Lane's
phases bring dusk at sunset (about 19:30, exchange 31) and a moonlit night from about 20:00
(exchange 61): sunset and a moon about eight days old, more than half lit, worked out for the
place and day. In four runs the darkness cut the Americans' losses (about 250-320 down against
330-560 by day) but they still do not take the guns: the British hold them at the limit in every
run, as before. In 1814 Miller's 21st took them with a rush in the dark.

**Routes round a flank.** A battlefield can now give a unit waypoints (`via`) from its account,
and its commander marches it round by them, turning aside only for an enemy in contact or
across its way. Four battlefields have them (the waypoints are our reading of the accounts on
our maps): Osan (the battalion round the west, the one down the railroad), Lundy's Lane (Jesup's
25th round the British left), Kapyong (the Chinese battalion round the east of the hill to
battalion headquarters) and the Poles at Cassino (the Kresowa's companies for Phantom Ridge).
Mons was left out (the canal can be crossed only at the bridges on this map), and so was the
Poles' 1st Battalion (Albaneta is not on the map). In four runs each against the build without
routes, no winner changed:

- *Lundy's Lane:* Jesup now goes round the east end of the hill and comes at the guns from behind
  (a first try showed the commander holding him back as its reserve, the rearmost unit; a unit on
  a route is now never held back), but the British still hold the guns at the limit.
- *Kapyong:* the battalion round the east goes down its route and breaks on the hill's east side
  in every run; the Australians hold, as before and as they did.
- *The Poles:* the Kresowa's companies go for Phantom Ridge first; the Poles still take and hold 593.
- *Osan:* unchanged: Task Force Smith breaks by exchange 26-31, before either flanking battalion
  comes on (46 and 166).

**Cassino town: measured, not built.** The paratroops are not shot out by rifle fire: in a trace
of two runs, shellfire put down most of them (125-130 of about 325), the rout after they broke
most of the rest, and the New Zealanders lost as many to the German mortars (130-155 of 600). Two
fixes were measured over every battlefield with rubble (four runs each), and neither was kept:

- *A morale check once, when a quarter of a unit is down,* instead of every exchange after it
  (all 37 battlefields, two runs each): 45 of 74 runs matched against 47, 21 battlefields against
  23. Cassino town's paratroops stood and died (75% lost) instead of breaking; Cisterna's Rangers
  lost 94%; Mons stopped matching. The repeated check stays.
- *Men in rubble sheltered from shells as in a bunker* (the cellars): no winner changed on any
  rubble battlefield. Cassino town's paratroops lasted about 40 exchanges instead of 28 and
  still went (68% lost); Grozny's Chechens held to the limit instead of going under.

Shellfire still does most of the killing in both.

**Shellfire: measured, not changed.** Batteries already have a rate of fire and a battle's
ammunition (field guns 2 rounds a minute a tube, 80 rounds), within the 25-pounder's published
rates (1 to 5 rounds a minute by the manual's scales, 32 rounds in its trailer and more with the
section; in big operations a gun fired some 100 to 335 rounds a day). What decides Cassino town is
how deadly a shell is against men in cover. The one sourced figure found: British wartime findings,
as summarised on a Royal Artillery history site, put 0.1 lb of shell a square yard (25-pounder
terms) at about 20% casualties to troops in the open and 2% to troops in weapon pits. By that, our
field and mortar shells are about two and a half times too deadly in the open (a 25-pounder shell
for every 2.4 hexes, against the equivalent of about 1.2 hexes struck a shell here). Scaling them
to 40% over all 37 battlefields, four runs each: 93 of 148 runs matched against 97, 22 battlefields
against 24 (better: Pork Chop, Heartbreak, Hamburger; worse: Mons, from 4 of 4 to 1, Wanat, Cassino
in February, Osan, Keating), and Cassino town unchanged (the paratroops still lose about 60%, more
of it in the rout). One secondary figure and a mixed, slightly worse result: not applied.
Other anchors found: Operation Cobra's bombardment caused "less than 10 percent" casualties to the
Germans under it, and losses ran "in inverse proportion to the extent units were dug in" (the Army's
Combat Studies Institute report on concentrated artillery).

Sources: [Royal Artillery methods in WW2](https://nigelef.tripod.com/maindoc.htm);
[Ordnance QF 25-pounder (Wikipedia)](https://en.wikipedia.org/wiki/Ordnance_QF_25-pounder);
[CSI Report 13, Tactical Responses to Concentrated Artillery](https://www.armyupress.army.mil/Portals/7/combat-studies-institute/csi-books/tactical.pdf);
[Tank Archives, 25 pounds of death](https://www.tankarchives.com/2018/09/25-pounds-of-death.html).

**Grozny: the night as it was fought.** The battlefield's objective named the Russians as its
attacker, so in self-play they "attacked" a station they already held and the Chechens sat in
their buildings and were destroyed (gone in 3 of 4 runs). The objective is now the Chechens' (the
night was their attack on the station), and phases bring the dark at about 17:05 (sunset about
16:30, the moon a day from new, the sky overcast). In four runs the Russians are harder hit (67-123
of 290 down, against 32-76) and the Chechens survive in three, but they do not take the station
within the run (61 exchanges, the first hour of the night), so every run now scores as a Russian
win (one of four went the Chechens' way before). The brigade broke out of the station about 18:00
the next day, some 25 hours on: a self-play run cannot reach it, and Grozny is recorded as not
matching for that reason.

**Tanks by fire control, and 73 Easting.** Every tank used one gun table (75% to 200 m, 25% to
1,000 m, nothing beyond), so Eagle Troop's M1A1s and the dug-in T-72s were equals, and the troop
broke over a few wounded crewmen. Now, from sourced figures (approved before building):

- A tank's gun hits and reaches by its **fire control**, its war's unless the battlefield gives
  its own: an optical sight (WWII, Korea: as before, plus one sourced point, about 5% a round at
  1,500 m), a stadia reticle (Vietnam: an M48's 98% / 35% / 4% at 500 / 1,000 / 2,000 m), a laser
  rangefinder (the late 20th century: a 125 mm's 98% / 94% / 75% / 55% / 35% to 3,000 m), and a
  thermal fire control (an M1A1: no published figure, so the laser figures as its floor; the GAO
  found it hit at 3,000 m and more and beat the projections). Isby; GAO NSIAD-92-94.
- **Thermal sights see through a sandstorm** to about 900 m (others 400 m): Eagle Troop's first
  kill was at about 1,000 yards in the storm, and the GAO found thermal sights saw through haze
  and smoke.
- **Composite armour** (the M1A1s at 73 Easting and Fallujah): a main gun's round from the front
  does not knock one out (the GAO: no T-72 round reported through an M1A1's front, even from
  2,000 m, and no Abrams destroyed by enemy fire); flank and rear as heavy armour.
- **Vehicle morale** counts whole vehicles lost, not crewmen hit in vehicles still fighting.
- Kill chances once hit were to change only where sourced; the sourced figures (Isby: 1960s-70s
  guns against 1960s tanks, 54-81%) match no battlefield, so none changed.

73 Easting, four runs: no longer a massacre of Eagle Troop (losses about 14% a side, against the
troop gone in 2 of 4), but it still matches 0 of 4: the commander drives the north platoon into
the Iraqi position, where it is shot from the flanks and rear, and the Iraqis hold the position
at the limit. Historically the troop fought from the ridge at 1,000 to 3,000 m. Of the other tank
battlefields only Grozny changed (1 of 4 to 0; it does not match for the reason recorded above).
How the commander handles tanks (standing off at range when it outranges the enemy) is a new
backlog item.

Sources: [Historical PHit and PKill (from Isby)](https://www.generalstaff.org/BBOW/Weapons/Hist_PHitsPKills.htm);
[GAO NSIAD-92-94](https://www.gao.gov/assets/nsiad-92-94.pdf);
[HistoryNet, 73 Easting](https://historynet.com/learned-battle-73-easting/);
[FAS, T-72](https://man.fas.org/dod-101/sys/land/row/t72tank.htm).

**Tanks placed by their main gun.** The commander counted a shooter "in range" by its own weapon,
so tanks (whose own weapon is the machine gun) were taken to machine-gun reach. Now a unit with
a main gun counts the gun's reach where it can see the target, and a vehicle with a main gun
prefers a spot where the target can neither reach it nor see it there. Over all 37 battlefields
(two runs each, against main): 47 of 74 runs matched either way, and no winner changed. At 73
Easting the T-72s are in dead ground behind the rise: Eagle Troop loses sight of them, advances
on the objective and fights at the crest at close range, as it did in 1991, but takes the BMPs'
and T-72s' fire there in the flank; what made that close fight one-sided in 1991 is not in the
model.


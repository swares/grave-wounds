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


**Units tire (Agincourt).** Whole units now tire by the individual toil rule. Each
hand-to-hand exchange a unit fights counts one toil, and so does each hex it goes in deep mud
or snow. Twelve toil in heavy kit makes a step, 20 in medium and 30 in light, up to Exhausted.
Each step's fight penalty comes off the unit's attack and parry. Over all 37 battlefields, four
runs each against main, 96 of 148 runs matched the actual winner, against 95. Only Agincourt
changed, from 0 of 4 to 1 of 4: the French reach the English line Tired and soon become
Exhausted. The English now have units standing at the end of all four runs; before, two runs
ended with the whole English army gone. Cassino town's German losses rose from 54% to 64%
(still 0 of 4, for the reason recorded above), and nothing else moved by more than a few tenths.

The other three Agincourt runs still go to the French on the share of men lost, because an
English archer block of about 1,500 breaks and is cut down in the rout. The cause is the morale
check a unit in contact takes whenever it loses more men than it deals in an exchange. Only 10
to 50 men of a block of thousands are touching, so one exchange lost 1 to 0 can call a check,
and a run of them breaks the block. It broke the English on main and broke the French battles
in the prototype after they had lost about 10 men. That check is the next item to measure.

**The contact-scale morale check, measured and not built.** The losing check (a unit in
contact that loses more men than it deals in an exchange) counts a handful of men touching as
the whole unit, and so do the flank check and the rout strike, in which every man of the
pursuing unit strikes. Four variants, all 37 battlefields, four runs each, against main's 96 of
148:

| Variant | Runs matched |
| --- | --- |
| The losing check and its penalty counted per 1% of the unit, not per man | 91 |
| No losing check at all | 93 |
| The rout strike by the pursuers' men in the hexes touching the broken unit | 93 |
| Both scaled | 91 |

The losing check is what decides the big medieval melees (scaled, Towton fell from 4 of 4 to 1
of 4), and the whole-unit pursuit is what makes most of a battle's dead fall in the rout (with
it scaled, Towton's Lancastrians lose 8.5% instead of 13.6%). Nothing was built.

## The commander's own faults, 16 October 2026

The match count mixes the rules, the battlefield and the commander, so a report on the
commander alone was added to self-play (every battlefield, two runs). For each side it gives the
share of men who never fired or fought, the most fighting at once, how far apart in exchanges
its units first fought, the share of losses taken while they could not hit back, and which
units broke and why idle units sat out. The largest fault on the attacking side was formed
men held up behind their own shooters: the shooters went forward until in range and stood,
and the close-order men behind could pass through them only to charge, and never went round.
At Visby, 75% of the Danes and 84% of the Gotlanders never fought; the battle was a shoot-out
at long range. The second was a reserve that never came in when an attack stalled with
nobody breaking (Cowpens' Legion dragoons, Sidon's heavy horse, Visby's men-at-arms).

Two changes (see docs/units.md, *The enemy commander*):

- **Shooters give way.** Attacking, open-order shooters standing on the ground a formed unit
  behind them would cross step aside to their best spot off it, and the formed unit goes on.
- **A stalled attack commits a reserve**: five moves in a row without putting down 1% of the
  enemy or getting any nearer.

All 37 battlefields, four runs each: **100 of 148 runs matched, against 96.**

- Better: Cowpens 0 → 4 of 4 (the British attack now goes in and is beaten: British losses
  36%, Americans 19%; before, about 8% each and a stand-off); Heartbreak Ridge 2 → 3. Visby
  still matches, but now as fought: the Danes break the Gotlanders, who are gone in all four
  runs at about exchange 20, Gotlanders 29.5% lost (2.9% before).
- Worse: the Redan (September) 4 → 3; the Russians now lose 42% (10% before).
- Moved without changing the winner: Wagon Box's soldiers now lose 62% counted as hurt
  (light wounds included) against 0.8%, though few go down (the Lakota's stalled attacks now
  bring in their reserve); historically the corral lost a handful. Albuera's Allies 37%
  (24%).
- Agincourt does not change: the French main battle is held up behind the vanguard, a
  formed unit, which this does not cover.

The commander report: on attacking sides the share of men who never fought fell from 13.5% to
10.0% on average (Visby 75% and 84% to 0; Cowpens' British 21% to 9%), and on holding sides
more of their men fight too, because the attacks now reach them (the Redan's Russians 48% idle
to 0, Khe Sanh 61% to 30%). Grozny's
Chechens idled more in one of the two runs, which went another way by the dice from early on.
The Poles at Cassino idled more (25% to 38%) because in one run they held Point 593 six
exchanges sooner, before the second battalion's companies came up.

**A formed unit held up behind another, measured and not built.** The next fault after the
shooters was a formed unit stuck behind a formed unit of its own side (Agincourt's French
main battle behind the vanguard). Two answers were measured, each on all 37 battlefields,
four runs, against main's 100 of 148:

- *Extend, else relieve*: come up in line beside the front unit where there is room, else,
  when the front unit in contact is shaken or a quarter down, change places with it. 100 of
  148; only Towton and Visby moved, by a point or two of losses. At Agincourt neither ever
  happened: there is no room beside the vanguard, and it is never shaken or a quarter down.
- *Narrowing*: the real block at Agincourt is the ground. The field narrows between the woods
  toward the English line, and the vanguard's 60-hex front cannot fit nearer than 4 rows
  from it (only the GM's *Narrower* changes a unit's width). A formed unit that would stand
  closed in a quarter at a time, deeper, to the widest front that let it move nearer its
  target, and moved. The vanguard then reached the English line, but 98 of 148: Agincourt
  1 to 0 of 4 (the English lose more, 31% against 25%, most of it in the rout in the run looked at; the
  French still put down few men hand to hand) and Lützen 1 to 0; Albuera's Allies lose 48% (37%).

Neither was built. At Agincourt the French reaching the line does not help them, because what
breaks the English is the morale check and rout strike counted on the whole unit when a few
dozen men touch, measured above. That, not the commander, is what stands between Agincourt and
its result.

**Runs long enough for every phase, 17 October 2026.** Self-play stopped at 240 exchanges, which
ended runs before the last phase began on fifteen battlefields (the Poles at Cassino's last phase
is at 1,111, Chipyong-ni's at 1,156), unless the battle ended sooner. Runs are now fast enough
(Lützen, the longest, about 77 seconds) to go to 1,200. All 37 battlefields, four runs each:
101 of 148 runs matched, against 100. Pork Chop went from 1 to 2 of 4 and Heartbreak Ridge from 3
to 4. Lützen went from 1 to 0: it now runs to 451 exchanges, and in three runs of four it ends with
the Imperialists still on the windmill hill. Mogadishu's American losses fall from 70% to 25% once
the relief column's phase comes; why has not been looked into. A battle that went on for days after
its last phase (Cassino town) is still cut short, and a battlefield cannot yet run as long as its
own account says when that is past its last phase (Lundy's Lane was fought until near midnight,
about 300 minutes, but a run ends at 180).

The scripts behind these measurements are now in `tools/selfplay` (see its README): self-play,
the commander report, a runner for every battlefield and seed, and a comparison of two runs.

**Runs as long as the accounts say, 17 October 2026.** Thirteen battlefields now give `ends`: how
long their account says the fight went on, in exchanges, the earliest the words allow ("the next
afternoon" is 12:00; "at dawn" the sunrise worked out for the place and day). A run lasts at least
that long, within the 1,200 cap. Lundy's Lane runs 271 (180 before), the Monastery 418, Keating
361 (60), Lützen 541, Mogadishu 783, Kapyong 871, Heartbreak Ridge 901, and X-Ray, Pork Chop,
Grozny, Bougainville, Dak To and Cassino town to the cap. All 37 battlefields, four runs each: 98
of 148 matched, against 101. It was kept, because the runs are now the length of the battles they
stand for, and the three runs lost are faults the short runs hid:

- **Keating** 4 → 3: in one run the outpost falls at exchange 63, just after the old stop at 60
  (Coalition losses 56% to 68%).
- **X-Ray** 4 → 3: in one run the Americans are gone at exchange 296; two run to the cap.
- **Pork Chop** 2 → 1 (American losses 8% to 13%).
- Lundy's Lane stays 0 of 4 at 271 exchanges (Americans 59% lost, against 49%); Grozny now runs
  640 exchanges (61), still 0 of 4.

The short runs had stopped some battles with the defenders close to breaking; why they break,
where the accounts say they held, is the next thing to look at.

**Morale only under pressure, measured and not built.** Traced at Keating: once a unit is a
quarter down it checks morale every exchange from then on, whatever is happening to it. B Troop's
machine guns held at 5 of 8 men from exchange 21 to 31, losing no one, checking at 95% each time;
shaken at 26, and still a quarter down so unable to rally, they checked at 75% until they broke at
31. Over a long run any unit a quarter down breaks in the end. Measured on all 37 battlefields,
four runs each, against main's 98 of 148:

| Variant | Runs matched |
| --- | --- |
| A: the quarter-down check only in an exchange the unit loses men | 96 |
| B: a failed rally leaves a unit shaken, not broken | 97 |
| A and B | 96 |

A gains Keating, Mogadishu, Pork Chop, Hamburger Hill and Goose Green (+5) but loses the Monastery
(3 to 1), Cowpens (4 to 2), Chipyong-ni, Mons and the Redan (−7): the same drain that wears down
the long defences is what breaks the losers of the short, decisive fights. Neither was built.

A third variant kept the check while the unit is under pressure: losing men that exchange, or a
standing enemy within a charge of it (twice the enemy's move, edge to edge). 96 of 148 as well: 73
Easting 0 to 1 and Pork Chop 1 to 2, but the Monastery 3 to 1 and Mons 4 to 2, and Keating
unchanged. At the Monastery and Mons the side that should fail is fighting at rifle range,
beyond any charge, and the constant drain is what broke it. The drain carries the outcome of too
many battles to take out piecemeal; it was left as it is.

**The Monastery's Gurkhas, measured and not built.** The commander report on main showed the two
Gurkha battalions at the Monastery (February) often never fighting. Traced: they come on at
exchange 121, go to ground under fire within a couple of moves, and then score staying in the
scrub's cover above closing on the only enemy they know of, the paratroops on Point 593, far off;
they never get up. Their accounts name where they went, so they were given routes (the 1/9th
across the slopes for Point 444, the 1/2nd straight down for the abbey's hill). They then went,
but found the hills empty: the holding German commander pulls every unit more than a few hexes
from the one objective (593) back to it, so the paratroops on 444 and the Germans in the abbey
leave in the first hour. Marking those Germans to hold their own ground (`stand`) made it worse:
over twelve runs, main matches 5, routes 4, routes and `stand` 1. With 444 and the abbey holding,
593 is left to its own paratroops and the Rajputana take it in most runs; on main it is the
Germans who abandon 444 and the abbey to reinforce 593 that let it hold at all. The fight for 593
itself is too easy for the attackers. Nothing was built; that fight is the thing to look at next
at the Monastery. (Twelve runs also show main's four-run 3 of 4 there was luck: 5 of 12.)

## Morale against the sources, 17 October 2026

A research report (the project's `break-points-research.md`) found no sourced share of losses at
which units break, in any era, but a set of patterns the sources agree on: the loser breaks having
lost little; final losses run about 2-3 to 1, loser to winner; most of the loser's dead fall after
it breaks; units quit mostly because they are outflanked or left exposed; the losses at breaking
vary widely; and losses follow the men engaged, not the whole unit. Those became targets T1-T7
(`docs/morale-redesign.md`), measured by `tools/selfplay/targets.js` and `targets.py`.

The present rules meet T2 (2.5 to 1) and T5 (7% to 67% down at breaking), but miss T1 (units
break at a median 18% down before 1914 and 37% after, against 5% or less and mostly under 10%) and
T3 (7% of the loser's men go down after it breaks, against most).

A redesign that checks morale only when something happens to a unit (hit hard, flanked, losing
the fight, a neighbour broken, its leader down, a quarter or half down), with losses a standing
penalty and the rout struck only by the pursuers touching it, was built behind a setting and
measured twice (four runs each, all 37 battlefields): 87 and 90 of 148 runs matched, against 98;
units broke less often and later, and none of the loser's men went down after breaking. Not
adopted. The finding: a flank or a neighbour breaking called only a tenth of the breaking checks.
The battles rarely produce the situations the sources say break units, so morale cannot be put
right on its own; the present rules break units on their losses instead. The full tables are in
`docs/morale-redesign.md`.

A 12-run baseline of main was also taken: 303 of 444 runs matched (68%). Twenty-three
battlefields match in 11 or 12 runs of 12; the Monastery (5), X-Ray (7), Keating and Hamburger
Hill (9), Mogadishu (10), Pork Chop (4), Goose Green and 73 Easting (3) and Lützen (2) are
coin-flips; Agincourt matches once, and the Poles at Cassino, Cassino town, Grozny, Hue, Lundy's
Lane and the June Redan never.

**Pursuit, 17 October 2026.** Looking into why so few of the loser's men go down after it breaks
(target T3) found that the commander never went after a broken unit: its units choose targets
only among enemies still standing, so the rout struck only while the fugitives happened to stay
in contact. Now a steady unit that fights hand to hand goes after a broken enemy (horse one within
a charge when no standing enemy is as near, foot one within its move nearer than any standing
enemy; veterans rally back after two moves if a standing enemy is in reach). Four runs each, all
37 battlefields: 101 of 148 matched, against 98; Lützen 0 to 3 of 4, the Swedish horse running
down the broken Imperial units. T3 did not move (a median 14-20% of the loser's men after it
breaks before 1914, none after): the losers still lose most of their men in the line before they
break (T1). Pursuit is in; breaking too late is the open problem.

## Flanking, 17 October 2026

The sources say units mostly break because they are outflanked or left exposed (T4), and the
morale redesign found that self-play rarely puts a unit there. So the flanking itself was
measured first (`tools/selfplay/flanks.js` and `flanks.py`, four runs of each of the 37
battlefields). After every exchange, for each side, it counts the spare units: steady, not guns
or vehicles, and not in contact. It checks whether each one could reach an open hex on the flank
or rear of an enemy unit fighting one of its own, within one move or three, and strike from it
with a facing it can still turn to on a charge.

| | Before 1914 | 1914 on |
| --- | --- | --- |
| Spare unit-exchanges, while some enemy was in hand-to-hand contact | 2,772 | 4,815 |
| ... that could reach an open flank within one move | 2% | 0% |
| ... within three moves | 12% | 1% |
| Flank or rear strikes, against front strikes | 69 / 1,460 | 87 / 864 |
| Flank strikes by a unit that had such a chance in the five exchanges before | 4 (all at Lützen) | 0 |
| Volleys fired from off the target's front | 18% | 23% |

The flank and rear strikes there were came mostly from units already in contact, wrapping round
the end of a line: 43 at Agincourt and 49 at Mogadishu. From 1914 on, the fighting is almost all
by fire, so the chances to flank are fire from a flank. That fire was already happening, but the
rules gave it no effect except against vehicles. Two changes were built in the page behind a
setting and measured against the present rules (with pursuit) over twelve runs of every battlefield.

**Fire from a flank counts as flanked for morale (`morale.flank_fire`).** A volley that put men
down from off a unit's front counted as striking its flank: a morale check at −20, and breaking
at once on a failure by more than 20. A unit gone to ground, dug in or in a bunker faces all
round and was exempt.

| | Present rules | Flank fire |
| --- | --- | --- |
| Runs matched | 307 of 444 | 299 |
| T1: share down at breaking before 1914 (median) | 18% | 12% |
| T1: breaks under 10% down, 1914 on | 1% | 9% |
| T2: loser's share lost against the winner's (median) | 2.6 | 2.6 |
| T3: loser's men down after breaking (median) | 4% | 2% |

It moved T1 toward the sources, but cost eight runs, and T3 got worse. The Monastery fell from
5 to 1 of 12: German paratroops who left their holes to shift or counter-attack took fire from
the flank and broke. Kapyong and Wanat lost two runs each. Not adopted.

**The commander sends spare units round an open flank (`commander.flanking`).** A steady unit
that fights hand to hand, not in contact, looks for the nearest open hex on the flank or rear of
an enemy fighting its own, within three of its moves (holding, one). Within a charge it charges
there; otherwise it advances toward it. A reserve with such a flank in reach is committed to it.
Traced first on the fifteen battlefields before 1914, two runs each, it never charged:
- 47 of the 62 chances it found were refused by the charge odds, which set the charging unit
  against the whole enemy unit. A small unit of horse never has those odds against a battalion.
- The rest had no legal charge. A block 25 hexes wide pays 13 to turn, more than its whole
  charge of 12, so it can only strike a flank it already faces.

For a flank charge the odds were then counted against the enemy men in the hexes it would strike
(T7: losses follow the men engaged). Twelve runs: 302 of 444 matched, against 307. Lützen fell
from 6 to 3, as the Imperial horse struck the Swedish flanks, and Albuera and Cowpens lost one
each. T1 hardly moved (a median of 17% down at breaking before 1914, against 18%), and T3 went
from 4% to 3%. Not adopted.

Neither change brings the battles nearer the sources. Before 1914 the flanks are seldom open
within reach, and the big blocks can't wheel onto the few that are. After 1914 fire from a flank
is common, but counting it breaks the defenders the accounts say held. Both prototypes are kept
on the branch `flank-prototypes`, and `flanks.js` stays to measure the next attempt. The open
problem stands: units break too late (T1), so few of the loser's men fall in the rout (T3).

## The battlefields that never matched, 18 October 2026

Six battlefields matched none of twelve runs: Lundy's Lane, the Poles at Cassino, Cassino town,
Grozny, Hue and the June Redan. Each was traced. The faults found, and what was done:

- **Scoring and stopping.**
  - **Draws.** Lundy's Lane and Cassino town were fought to a draw, and a run could score one
    only if both sides were gone, so neither could ever match. A battle fought to a draw in
    which the attacker took the objective now matches a draw, or a run that ends with the
    attacker holding the objective: on the field the fight went the attacker's way, and the
    draw came after.
  - **Runs ending early.** Holding the objective no longer ends a run while any of the
    battlefield's phases are still to come. The Poles at Cassino used to stop on taking
    Point 593 at about exchange 40, hours before the account has them forced off it.
  - Neither change moved the total, scored either way.
- **Works drawn off the units meant to hold them.** Five battlefields drew their bunkers or
  trenches a hex or more from the units their accounts put in them, so no one stood in them:
  - Cassino town's cellars;
  - Bougainville's pillbox line;
  - Goose Green's ridge trenches;
  - 73 Easting's trenches;
  - Hue's strongpoints.

  Their generators now lay each work under the front row of the unit meant to hold it
  (`frontRow` in `tools/maps/field_lib.mjs`). Goose Green fell from 3 to 0 of 12: with the
  Argentines really in their trenches, 2 Para's attack breaks within about 21 exchanges. Its
  matches before came partly from the misplaced works. 73 Easting rose from 3 to 4. Dak To,
  Hamburger Hill, Heartbreak Ridge, Khe Sanh and Pork Chop have rings of works their
  defenders partly fill, as drawn.
- **The June Redan.** The centre column never left the trenches: Engels, writing in 1855, says
  so, and the losses fell almost all in the two flank columns' brigades. So it is off the map,
  and the battle went from 0 to 2 of 12. The fault the trace found is in the rules. The
  600-man Russian battalion at the salient breaks with 3% of its men down: it fights a
  46-man ladder party across the bank, loses one man to none, and checks as losing the fight.
  The losing check counts the whole unit at any margin. That is the morale redesign's first
  fault (`docs/morale-redesign.md`), still open.
- **Hue.** The field had no length, so a run lasted 60 exchanges, for an attack the sources
  put at about 55 hours. It now ends at 3,301 (07:00 on 4 February to the flag a little past
  14:00 on the 6th), capped at 1,200. It still never matches. The Marines lose about 200 men to
  the North Vietnamese's 120, while the sources have about 1,000 North Vietnamese dead south of
  the river against 38 Marines killed. The headquarters fell to tanks and tear gas, with
  recoilless rifles and Ontos; the field has none of these, and the rules have no gas.
  No unit strengths were found.
- **Cassino town.** With their cellars now under them, the paratroops still go by about
  exchange 28. The holding commander walks them off their cellars toward Castle Hill: holding,
  it pulls every unit to the objective, here the New Zealanders' objective, not the ground the
  Germans held. That is the "units that hold their own ground" problem the Monastery showed.
  The opening barrage also puts down a quarter of a company in one exchange; the sources say
  the bombing killed about half the garrison.
- **Lundy's Lane.** The guns were taken by Miller's 21st Infantry rushing them in the dark,
  but the commander never lets a unit with a missile weapon charge, except when storming
  works. Two versions of a bayonet charge for black-powder foot were measured and not
  built:
  - charging any target it had the odds against: 288 of 444, from 307. Lundy's Lane went to
    5 of 12, but Albuera fell from 12 to 2 and Bull Run from 12 to 5, because the musketry
    that decided them never fired;
  - charging batteries only: 304. Albuera fell to 9, and Lundy's Lane did not move, because
    the guns are never the target chosen.
- **The Poles at Cassino.** The field has no German counter-attacking force. The Polish
  Institute's account has the battalion beating off all six counter-attacks and worn down by
  mortar and artillery fire to one officer and 17 men. No source found gives the German fire
  strength or the counter-attacks' strength.
- **Grozny.** One survivor's memoir puts about 1,200 Chechens near the station, against the
  field's 380. Sources also place a battalion and tank company of the 81st Regiment there,
  which the field lacks. These rest on a single witness and were not built.

Twelve runs of every battlefield on the branch: 307 of 444 matched, against 308 for the
same runs before it, scored the same way:
- Goose Green −3 and Cassino town −1;
- 73 Easting +1 and the June Redan +2.

The targets hardly moved: T1 before 1914 is 17%, from 18%, and T2 is 2.8, from 2.6.

**Holding units that keep their own ground, 18 October 2026.** At Cassino town the holding
commander walks the paratroops off their cellars toward Castle Hill. That is the attackers'
objective, and holding, every unit more than 3 hexes from it falls back. A unit dug in, gone
to ground or in a bunker was let fight where it stood instead. Twelve runs of every
battlefield: 285 of 444 matched, against 307. Not adopted.
- **Defenders that gave way stood instead:**
  - Mons, 12 to 0;
  - Osan, 12 to 5;
  - the Monastery, 5 to 1;
  - Hamburger Hill, 9 to 6.
- **Gains:** X-Ray, 7 to 12, and Mogadishu, 10 to 11.
- **Unchanged:** Cassino town still lost its paratroops, later (about 55 exchanges, from 28).
- **T3:** the loser's men down in the rout fell from 6% to 1%, since the losers no longer ran.

Which units should stand and which should give way is a question of their orders and the
account, not of whether they are in cover.

## The blocked advance at Agincourt, 19 October 2026

At Agincourt the French main battle, 4,800 men 60 hexes wide, stood a hex behind its own
vanguard for the whole battle and never struck a blow. The vanguard in front of it was not
fighting either: from exchange 12 it stood 2 hexes from the English, because the field narrows
between the woods and its front could not fit nearer. Feeding men forward from the main battle
into the vanguard was built and dropped, because the vanguard was never in contact to be fed.

Three changes were screened, four runs of every battlefield each, against the present rules'
102 of 148:

| Change | Runs matched | Agincourt | T1 before 1914 (median down at breaking) | T3 (loser's men down in the rout) |
| --- | --- | --- | --- | --- |
| Present rules | 102 | 1 of 4 | 18% | 5% |
| Narrowing the front | 104 | 4 of 4 | 16% | 9% |
| The losing check counted in twentieths of the men in contact, and the rout strike by the pursuers' touching men | 101 | 0 of 4 | 28% | 2% |
| Both | 101 | 0 of 4 | 27% | 2% |

Counting only the men in contact made units break far later, away from the sources. It also
cost Towton and Lützen, though it fixed the June Redan (0 to 4 of 4). It was not built.

**Narrowing is in** (`commander.narrow`). Attacking, a formed unit out of contact that cannot
move nearer its target closes in its front a quarter at a time, deeper, to the widest front
that lets it move nearer. Twelve runs of every battlefield: 309 of 444, from 307. But Towton
fell from 12 to 8. The trace showed Norfolk's 5,000, coming on late, closing again each
exchange, from 30 hexes to 23, 18, 9, 7 and 4. A column 4 hexes wide broke at 5% down and was
cut down in the rout. With a floor of half the front it started with (`narrow_to`), twelve
runs: 313 of 444. Agincourt went from 1 to 8 and Lützen from 6 to 5; Towton is back at 12 and
nothing else moved. T1 before 1914 went from 17% to 15%, T3 from 6% to 9%, and T2 stays 2.8.
At Agincourt the unit that narrows is the French western mounted wing, which closes from 10
hexes to 5 and charges home.

## The runs' own spread, and quick-play blows, 19 October 2026

**How much do twelve runs vary?** The present rules, run again on seeds 13 to 24 instead of 1
to 12, matched 290 of 444 runs against 313: about 20 runs of difference from the dice alone.
The sourced targets T1, T2 and T5 held steady between the two sets; T3 (the loser's men down
in the rout) moved from 6% to 9%. So several earlier verdicts made on a difference of a dozen
runs or fewer (narrowing 309 against 307; the elite tier 304 against 303; flank fire 299 and the
flank order 302 against 307) were within the noise. From here a change is judged on 24 runs of
every battlefield pooled (seeds 1 to 24: 603 of 888 for the present rules) and on the morale
targets, and a battlefield's change counts only when it moves well outside its own spread.

**Quick-play blows** (`quick` in `data/units.yaml`; docs/units.md, Quick-play blows) roll a
group's blows on the rankers as one d100 on the per-blow rules' own curve, for a GM who wants a
faster table. With it on for every blow, twelve runs: 285 of 444 against 313, within the spread
above, and the share of blows of each kind putting a man down matched the per-blow rules (a
volley at North Vietnamese, 0.243 a try against 0.235). Two faults were found and fixed on the
way: rounding a group's men down to whole men biased small groups (now a d100 on the binomial
curve), and lightly wounded men were rounded away (now rounded at random, right on average).
It is off by default: a GM's choice, with a chart for each era in the tables and an exact sheet
for the field from the field page.

## The defenders' orders from the accounts, 19 October 2026

Several battlefields failed because the commander pulled holding units off their ground to the
objective, or kept units fighting that the accounts say were ordered out (the traces under *The
battlefields that never matched*). The accounts were read for each battlefield's defenders
(the project's hold-or-give-way notes): which units held to the end of the fight the set-up
covers, and which gave way on orders, when and where to. `data/orders.yaml` carries what they
say, with its source; a unit the sources say was driven off, or that they do not cover, has no
entry.

- **hold**: the unit fights where it stands; it does not fall back to the objective.
- **withdraw**: from the minute given it falls back to a hex (and holds it) or off a map edge.
  Mons (the Fusiliers), Osan (the hillock platoon, then the rest), X-Ray (A and B Companies to
  the landing zone) and Kapyong (the HQ and Shermans, then B Company).

On twelve runs, Bull Run fell from 12 to 5. Its brigades held Henry Hill, but Henry Hill is the
objective: marked to hold where they stood, they let the Union walk onto the empty summit. Its
hold entries were taken out (the summit is where a holding unit goes anyway).

Twenty-four runs of every battlefield, against the present rules on the same seeds:

| | Runs matched | 73 Easting | Lützen | X-Ray | Agincourt | Monastery |
| --- | --- | --- | --- | --- | --- | --- |
| Present rules | 603 of 888 | 7 | 9 | 12 | 11 | 5 |
| With the orders | 620 of 888 | 19 | 17 | 15 | 8 | 2 |

The two large gains are on battlefields with orders; the two losses are within a battlefield's
spread over 24 runs (about 2 to 3 runs). The morale targets did not move: T1 before 1914
5/15/26% (from 5/15/27), from 1914 29/37/53%, T2 3.1 (2.8), T5 6/68%; T3 went from 8% to 5%,
the target that varies most between seed sets. The orders are in.

## Lopsided losers: Goose Green and the June Redan, 19 October 2026

**The June Redan** (2 of 24). The trace: the 600 Russians in the salient lost one man more than
they put down in contact, which calls the losing check (35% to fail when steady); shaken, they
broke at the next. A block of hundreds checks over a single man. Built and measured: the check
called only when the unit lost at least 1% of its men more than it dealt (one man for a unit
under 100). The June Redan went from 2 to 24 of 24, but before 1914 units then broke far later:
the median share down at breaking from 15% to 27% (5% of breaks under 10% down, from 41%),
away from the sources. Towton fell from 23 to 3, Agincourt from 8 to 0, the September
Redan from 22 to 16 and Lützen from 17 to 12: 610 of 888 against 620. The one-man trigger is
what breaks the older armies early, as the accounts have them break; counting the men in contact
(measured on 17 October) failed the same way. Not built. The salient's fault is still open.

**Goose Green** (0 of 24). The trace: the Argentines hold trenches, so 2 Para's riflemen storm,
and storming they walked upright across open ground into two machine guns; A Company lost 22
of 74 in two minutes and broke. In 1982 A Company went to ground and took the hill by fire
and movement over hours. Built: storming in bounds (`commander.bounds`; docs/units.md, Storming
works): a storming modern unit hit or pinned in the last exchange goes to ground and fires,
and goes on once a bound draws no fire, its target is pinned, or it can charge home. A first
version let it walk on if the target was within a charge's distance (16 hexes), which was
across the open; it now goes on only if the charge itself can be made. Twenty-four runs: 628
of 888 from 620. Hamburger Hill went from 18 to 23, Pork Chop 7 to 9, Grozny 2 to 3, Keating
16 to 17, the Monastery 2 to 1; the battlefields before 1914 are unchanged run for run, and so
are the morale targets. Goose Green itself does not match: down after the first fire, A
Company loses one or two men a minute rather than twenty, but its next bound still goes into
machine guns nothing has pinned (British losses 63% to 55%). Suppressing them first, as the
accounts have it done in the end (Milan and 66 mm rockets on the trenches), is to do.

## The Cassino battlefields, 19 October 2026

Three battlefields at 0 to 2 of 24 (the Poles, the town, the Monastery). The traces:

- **The Monastery.** The Rajputana stop 12 hexes short of Point 593 and trade fire for half an
  hour; the paratroops lose 34 of 120, then break with 86 left and no assault. Past a quarter of
  their men down, a unit checks morale every exchange whether hit or not, and a long defence
  sooner or later fails one.
- **The Poles.** The Phantom Ridge paratroops walk off their ridge toward Point 593 (the
  objective), and two artillery groups catch them in the open: 111 of 122 down in one minute.
  On 12 May the Kresowa men took the first bunkers but withdrew, and the paratroops ended the
  day holding the ridge. The paratroops' counter-attacks that threw the Poles off 593 that
  morning are not on the map: the times are sourced, the strengths are not (the project's
  point593-counterattacks notes).
- Starting the massif's defenders dug in would change little: lying down already gives the
  same cover, hiding, shellfire cut and morale.

Built and measured together: the quarter-down check only in an exchange the unit lost men, and
Phantom Ridge holding. Twenty-four runs: 614 of 888 against 620. The Cassino battlefields did not
move (the Poles 0, the town 0, the Monastery 2 to 1). The long defences that held gained (Pork
Chop 7 to 17, Grozny 2 to 9, Keating 16 to 21), but Cowpens fell from 23 to 15, 73 Easting 19 to
12, Mons 23 to 18 and the September Redan 22 to 18, and from 1914 on units broke at a median 45%
down, from 37% (the sources put most quits under 10%). The standing check is what makes many
attacks and defences give way when they did. Not built (branch cassino-drain). Cassino needs its
counter-attacks (strengths unsourced) and a look at its shellfire.

## Hue: the armour, and the line of fire, 20 October 2026

Hue (0 of 24) had none of the supporting weapons the accounts credit. Research from the command
chronologies (the project's hue-supports notes) gave counts for some: the two gun tanks named in
the assaults (the four on the map were cut to two), and two Ontos (six 106 mm recoilless rifles
on a light tracked carrier) with H Company, now a vehicle kind. The 106s on mules, the 3.5-inch
launchers and CS gas have no counts and stay off; gas worked at the Treasury and failed in the
wind at the provincial headquarters, with no numbers.

The traces then showed two faults, not just Hue's:

- **Vehicles in reserve.** The tanks and Ontos, the rearmost units, were held back, then sent
  to plug a broken company's place inside the blocks, where vehicles cannot go, and stopped.
  Vehicles with a main gun are now never held back.
- **In range without a line.** Once forward, they stopped 25 hexes out behind houses: the
  commander counted the Treasury in range (the gun reached, the light was good) though the
  buildings blocked every line, and they never fired. In range now needs a clear line from the
  hex, for every shooter, as firing itself does.

Twenty-four runs (measured before storming in bounds was merged): 641 of 888 from 620, the
morale targets unchanged. Cassino town 0 to 22, Pork Chop 7 to 16, Hamburger Hill 18 to 23,
Grozny 2 to 6, Chipyong 23 to 24; Hue only 0 to 1. Two fell: X-Ray 15 to 1 and 73 Easting 19
to 12. At X-Ray the North Vietnamese used to stop in the elephant grass "in range" of Americans
they could not see; now they close until they can, and the American line fails though the
artillery, rocket helicopters and air strikes of the account are on the field. The fix is
right; what holds X-Ray up is to be traced, with 73 Easting's tanks and Hue itself.

## X-Ray: a line that cannot turn, and the rally, 21 October 2026

With the line of fire checked (#248), X-Ray fell to 1 of 24. The trace: C Company, south of the
clearing, a line 26 hexes wide, could make no turn toward the North Vietnamese, and the commander
then gave it no order at all, which also skipped going to ground. It stood in the open trading
volleys with a battalion at 6 to 9 hexes, lost 46 of 105 in five minutes, and broke. A unit that
cannot turn now stays facing as it is and goes to ground under fire where it stands. Measured on
GitHub Actions (the selfplay workflow, 24 runs of every battlefield) against main as it now
stands (620 of 888, Hue 3 of 24, X-Ray 1): 628 of 888. X-Ray 1 to 7, nothing else more than a
run either way, the morale targets unchanged. X-Ray still breaks too often.

**A failed rally leaving the unit shaken** (it breaks now: a shaken unit out of contact that fails
its rally) was measured again, since the traces at Hue and X-Ray showed companies going from
shaken to broken: 613 of 888 against 620, nothing moving outside its spread (X-Ray 15 to 14, Hue 0
to 0, 73 Easting 19 to 15). The failed rally is not what holds those battlefields back. Not built
(branch rally-shaken), as on 17 October.

**Measuring.** The 24-run measurements now run on GitHub Actions (`.github/workflows/selfplay.yml`,
16 parallel jobs, well under an hour) and are compared there (`selfplay-compare.yml`); runs in a
Claude session died whenever the session went idle.

## Two kinds of break: holding a position, 21 October 2026

X-Ray, Keating, Pork Chop and the Monastery lose because their garrisons, a quarter down, check
morale every exchange and fail one in the end; at X-Ray the fire support did its job (in one run
323 of 367 North Vietnamese down came from artillery, mortars, rockets and air) and the American
companies still broke at 25-35% down, most of their losses then coming in the rout. Taking the
standing check away for everyone was measured on 20 October (614 of 888) and cost the attacks and
defences that gave way on time. The research (the project's breakpoints-pre1914 notes) points to
two kinds of break: cheap ones from flanks, charges and neighbours, late ones from frontal
attrition, with dug-in units holding far past any threshold. The design (morale-two-kinds notes)
kept the present rules and measured two changes on GitHub Actions, 24 runs of every battlefield,
against main (628 of 888):

| | Runs matched | Notes |
|---|---|---|
| Holding a position (posture), both sides | 637 | Keating 12 to 20, Pork Chop 10 to 16; but Wanat 23 to 16 |
| A neighbour within 2 hexes broke calls a check | 627 | no effect |
| Both | 633 | |
| Holding a position, the holding side only | 642 | Keating 12 to 20, Pork Chop 10 to 16, X-Ray 7 to 9, Cassino town 17 to 19; Wanat 23; Hue 3 to 1 |

At Wanat the first version let the Taliban fighters in the draw and their machine guns, lying in
cover, stop breaking too; they kept their fire on Observation Post Topside, whose teams of two and
three broke instead. Limited to the side holding its ground (the commander marks each unit with
its side's stance), Wanat is back to 23 of 24. The battlefields that need breaks keep them
(Cowpens, Mons, Towton, Osan unchanged; 73 Easting 12 to 11), and the targets did not move. Built,
on by default (`morale.posture`). The neighbour check, which seldom fires because units seldom
break beside each other in these battles, was not built.

## X-Ray and Hue traced, 22 October 2026

**X-Ray.** In 12 of 24 runs the Americans were gone at exchange 241-242, a red herring: by the
time B Company of the 2nd Battalion flies in at dusk (211), every other American unit has already
broken, and the run is scored once it breaks too. Traced, each company broke after checking on
being a quarter down: no American unit counted as holding a position, because they lay in the
trees, the elephant grass and the dry creek bed (woods, scrub and rough ground), not in works,
dug in or in buildings. Built: a unit gone to ground in ground that gives cover holds a position
too (`morale.posture_cover`). The trace also found a fault: a lift kept landing men into its unit
after the men already down had fled (B Company of the 2nd Battalion went from 40 fled to 83).
Fixed: the rest of the lift turns back.

**Hue.** The Marine companies broke at 10-20% down from the losing check: a unit in contact that
loses more men than it puts down checks, and most such checks were over one or two men (often to
the North Vietnamese mortars) against none, in companies of 120 to 160. Counting only losses hand
to hand was measured: the Marines then broke from losing the hand-to-hand fights they met storming
the buildings, so Hue did not improve. Its next cause is the storming rule, which sends modern
infantry in to fight hand to hand where the Marines cleared rooms with fire (recoilless rifles,
rockets, the tanks, then grenades).

Measured on GitHub Actions, 24 runs of every battlefield, against main after #281 (642 of 888, the same total as before
#276 to #279):

| | Runs matched | Notes |
|---|---|---|
| A lift for a routed unit turns back | 640 | X-Ray 9 to 7, within its spread; a fault fixed |
| With lying in cover holding a position (built) | **652** | X-Ray 9 to 18, Hamburger 19 to 20; the targets unchanged |
| With the losing check hand to hand only (not built) | 645 | the June Redan 2 to 13, Hamburger 19 to 22; but Agincourt 8 to 3, Keating 20 to 18, the September Redan 22 to 20, Hue 1 to 0; before 1914 breaks under 10% down 41% to 31% |
| All three | 657 | |

Built: lying in cover and the lift turning back. Still to trace: Hue's storming (the Marines
fighting hand to hand in the buildings), Agincourt and the June Redan under the losing check.

## Hue's storming, and suppression, 22 October 2026 (measured, not built)

**The trace.** With hand-to-hand losses no longer a separate cause (above), Hue still matched 1 of
24. The Marine companies storm whenever their numbers give the odds (`commander.storm`), against a
garrison nothing has suppressed: in one run 83 of their 93 hand-to-hand strikes went in against
unpinned North Vietnamese veterans in the buildings, and those strikes put down 19 men against 31.
The Marines in fact made the breach first, with 106s, 3.5-inch rockets, tanks and CS, and went in
at small cost (the Treasury 8 wounded against 6 killed; the hospital bunkers 3 wounded against 25;
2/5's February chronology).

**Suppress, then assault** (branch suppress-first): a modern storming unit goes in only on a
target that is pinned, shaken or broken, and till then closes, takes cover and fires. 666 of 888
from 652: Hue 1 to 4, Mogadishu 19 to 24, Cassino town 19 to 23, Hamburger 20 to 23; Dak To 24 to
20. But the rout's share of the loser's losses (T3) fell from a median 7% to 0, and the town
fights stalled: Mogadishu's losses fell from 24% and 30% to 7% and 10%, Khe Sanh's to about a third.

**Why they stall.** Almost nothing can suppress a garrison in buildings. Only shellfire and
machine-gun fire pin, after a Nerve check that veterans lying down usually pass: at Hue the North
Vietnamese were pinned in about 1% of unit-exchanges. Men in buildings are hidden and the
buildings screen sight, so small arms rarely find them (at Hue the Marines' 306 volleys put down
19 men in a run; at Mogadishu the Somalis' 185 volleys none), and the tanks and Ontos often have
no line of fire (3 shots at men in one Hue run, 93 in another). Storming was what made the town
fights bleed.

**Suppression rules**, from the research (the project's suppression notes: US Army field
experiments of the 1960s-70s, Vietnam weapons evaluations, the Hue chronologies), measured with
suppress-first: heavy direct fire (a main gun's rounds, a rocket or recoilless round) on a unit
holding a position pins it with no roll, and a pinned unit kept under fire stays pinned. 659 of
888: Grozny 3 to 7, Hue 5, Goose Green 0 to 1; but Mons 23 to 16 (a guess, not traced: pinned
British units under German machine guns could not make their ordered withdrawals), X-Ray 18 to
16, and T3 still 0. Not built.

Still open: fire in towns (how men in buildings are seen and hit, and what lines of fire armour
gets), which storming has been standing in for; then suppress-first can be measured again.

## Fire in towns, 22 October 2026

Measured on main: in the town battlefields units fire in most exchanges while within 50 m of an
enemy (at Hue 33 of 36 and 58 of 72 unit-exchanges in two runs; at Mogadishu 115 of 164), less from
60 to 100 m, and seldom farther; the idle exchanges at long range came mostly after one side had
broken. What little lands per shot is what the rules intend: men in buildings are hidden (10% of
aimed shots find a man, 5% for machine guns) behind 30-40% cover. The research (the project's
town-fire notes: British street-fighting trials of 1944, The Dupuy Institute's urban studies
and their re-analysis, JRTC and doctrine) does not contradict those figures: about one occupant
in five was killed for every 100 Bren rounds that got into a room. It does show HE that got into
a room was far deadlier than the game had it: a 2-inch mortar bomb through a window put out
about half the occupants, a PIAT bomb three-quarters, where a tank's round bursting on men lying
in a building struck each at about 6%. Rockets and recoilless rifles fired at men were single
aimed shots, with no burst.

Built: a main gun's round or a rocket bursting in a building hex strikes each man there at 50%,
with no cut for cover or lying down; a rocket or recoilless round fired at men is aimed at the
hex and bursts there if it hits. 652 of 888, as before; the targets unchanged. Keating 20 to 23,
Mogadishu 19 to 21; Wanat 23 to 19, Hue 1 to 0. Only the side whose rockets are on the map gains:
Hue's and Wanat's RPG teams are; the Marines' 3.5-inch rockets, LAWs and 106s at Hue are not,
for want of sourced counts (only expenditure: F/2/5 fired 35 rockets and 15 LAWs in one
afternoon).

Still open from the research: defenders in towns lost about three times as much a day as in the
open (much of it as prisoners) once the attackers closed, which nothing in the rules gives; and
attackers were hurt mostly in the streets, from buildings other than the one being assaulted.

## Cornered units surrender, 22 October 2026

The town research found defenders losing about three times as much a day in towns as in the
open, much of it as prisoners, once the attackers closed. The game had no surrender on the field:
a broken unit ran straight back, and one that could not (no clear ground behind it) stood broken
and was struck again and again. Traced: most broken units get away within 4 to 10 exchanges;
those cornered were cut down almost to the last man (two Somali militia bodies at Mogadishu, over
79 and 187 exchanges, 294 to 3 and 199 to 3 men: nearly all of Mogadishu's rout deaths).

The research (the project's surrender notes): a defender's prisoners rise six times or more once
it is penetrated and again once enveloped (The Dupuy Institute's capture-rate study); being cut
off was the cause veterans gave most for units giving way; men trapped in cellars and bunkers gave
up as a group (Shils and Janowitz); and how readily an army gave up sets the level, from Iraqis in
1991 (93% of their losses prisoners) to the Japanese and North Vietnamese (about 1 prisoner for 50
to 80 killed).

Built: a broken unit that is cornered (an enemy touching it, nowhere to run) surrenders at the
start of the exchange: the war's quarter % of its men taken prisoner, the rest killed, its heroes
on their feet taken. Sides the accounts show fighting to the end do not (data/orders.yaml
fight_on: the North Vietnamese, the Japanese at Bougainville, the Chechens at Grozny). The
self-play tools now count prisoners as losses. Measured: 658 of 912 from 657 (main, with the Babuna
pass); the targets about as before. Visby 23 to 24, X-Ray, Grozny, Lützen and Agincourt +1;
Mogadishu 21 to 19, Wanat and the September Redan -1. Still open: no source gives how often a
cut-off unit surrenders, so the rule makes every cornered unit of a side that gives up do so.

## The June Redan and Agincourt under the losing check, 22 October 2026

The June Redan (2 of 24): the 600 Russians in the salient, holding behind the parapet, checked
because they lost more men than they put down in an exchange they were in contact: 5 against 0,
3 against 2, 2 against 0. Their losses were mostly to the British covering riflemen about 180 m
off, which their smoothbores could not answer (in one run the Russian infantry fired 17 volleys
all battle and put down 10; the British Left column fired 86 at them and put down 28), while the
hand-to-hand fight with the ladder party at the parapet was even. They failed twice and broke.
Agincourt (9 of 24) needs the check as it is: the French Vanguard, 4,800 men, checks over one
man lost to the archers while at the English line, and those checks are what break the French,
as in 1415. Counting only hand-to-hand losses for everyone (measured on 22 October) stalled
Agincourt; requiring a margin (19 October) made the older armies break far too late.

Built: a unit holding a position (as the posture rule: the holding side, in works, buildings or
cover, not flanked) has lost the exchange only by its hand-to-hand losses; attackers and units in
the open count every loss as before (`morale.posture_hand`). 671 of 912 from 658: the June Redan
2 to 14 (British losses 25% to 60%: the assault cut down at the salient, as fought), the September
Redan 21 to 22, Babuna 5 to 6, Lützen 18 to 17; Agincourt, Towton, Mons and Cowpens unchanged.
Before 1914 units break at a median 20% down (from 17%; 37% of breaks under 10% down, from 39%),
within the sources (broken brigades lost a median of about 21% over the whole action); the rout's
share of the loser's losses 8% (from 4%).

## Goose Green and 73 Easting traced, 22 October 2026

**Goose Green** (0 of 24; 2 Para lost about 55% to the Argentines' 8%). Two Argentine
machine-gun teams of two men put down 86 of 2 Para in one run, while 2 Para's riflemen, about
1,700 man-volleys at the platoons in their trenches, put down none. Lying down, a company lost
almost no one (the guns find a hidden man at 5%); on its feet it lost 5 to 14 men an exchange.
Two faults stood it up: storming in bounds counted "drew fire" as "lost men", so a company that
lay under the guns and lost no one got up into them; and a company moving as shooters on a
target not in works was not storming, so it walked upright across the open under fire.

**73 Easting** (11 of 24; the Iraqis lost 26% where they were destroyed). Eagle Troop's M1s
stopped 500 m out and never fired: the commander counted the Iraqi trenches in range of their
machine guns without asking whether the sandstorm let them see that far (their thermal sights
saw 450 m). And a platoon with one tank immobilised stood for the rest of the battle: the
commander never abandoned a disabled vehicle.

Built: a unit fired on, hit or not, has drawn fire; from WWII on (by the wound table's war),
every attacking modern foot unit fired on goes to ground and fires rather than walking on
(commander.bounds_all); small arms count a target in range only where the weather and light
let them see it; and an attacking vehicle unit leaves its immobilised vehicles and goes on
(commander.leave_disabled). Measured on 24 runs of every battlefield against main (692 of 936):

| | Runs matched | Notes |
|---|---|---|
| All, "every advance" in every era | 695 | Hue 0 to 6, Babuna 6 to 11; Mons 23 to 15 (the Germans of 1914 going to ground), Keating 23 to 19 |
| All, "every advance" off | 692 | Hue 0 to 5, Lützen 17 to 20; Pork Chop 16 to 11, Keating 23 to 20, Wanat 18 to 15 |
| **All, "every advance" from WWII on (built)** | **700** | Hue 0 to 6, Grozny 4 to 7, Hamburger 20 to 23, Lützen 17 to 20, Babuna 6 to 8, Cassino town 19 to 21, Goose Green 0 to 1, 73 Easting 11 to 12, Khe Sanh 23 to 24; Keating 23 to 19, Wanat 18 to 15, Chipyong-ni 24 to 22, the Monastery 2 to 0, Cisterna, X-Ray and Mogadishu -1 |

The morale targets about as before (1914 on, 3% of breaks under 10% down; the rout's share 10%).
Still open: Goose Green (2 Para still loses about half: its bounds go in before the guns are
pinned) and 73 Easting (once the tanks close inside the 200 m the Iraqis see in the sandstorm,
BMP and T-72 flank shots knock them out); Keating and Wanat, which lose in both variants, to
one of the other fixes.

## Keating and Wanat after the fire-and-movement fixes, 22 October 2026

Both lost runs to the fixes of #302 (Keating 23 to 19, Wanat 18 to 15) with or without "every
advance goes to ground". Each of the other fixes was undone in turn and measured on 24 runs of
every battlefield, against main after #302 (704 of 984):

| Undone | Runs matched | Keating | Wanat | Elsewhere |
|---|---|---|---|---|
| (main) | 704 | 19 | 15 | |
| A unit fired on has drawn fire | 695 | 22 | 13 | Hue 6 to 0, Grozny 7 to 4, Babuna 8 to 6, Pork Chop 16 to 14 |
| Small arms in range only within sight | 705 | 20 | 13 | Lützen 20 to 17 (fog); Chipyong-ni 22 to 24, Mogadishu 18 to 20 |

Keating's loss is the drawing-fire rule: the insurgents storming the outpost now go to ground
when fired on even if no one fell, and break in less often. The rule is worth nine runs elsewhere
(all six of Hue's), so it stays. Wanat's is no single fix: undoing either makes it a little worse,
and a swing of three in 24 runs is within the runs' own spread (about two either way). Kept as
built; Keating's insurgents and their bounds are left to a later look.

## Keating's insurgents traced: the contested outpost, 22 October 2026

The insurgents' bounds are not what costs Keating. Over 24 runs on main they were given about
5,100 orders to move or advance; about 410 (8%) were turned into going to ground and firing,
nine in ten of those after fire that hit no one. The drawing-fire rule keeps them alive (27% lost,
against 33% without it), so more of them reach the outpost. The note above, that they break in
less often, was wrong.

What the trace found was two faults once they are inside the wire. Six runs in 24 ended with
the outpost contested, held by no one, which the report counts as the Coalition's.

- **Attackers stopped attacking at the objective.** A unit within the objective's radius was
  ordered as if holding, so riflemen neither stormed nor charged. In seed 20 the north-slope
  company (79 men) lay 30 m from the guard post (15 men) from exchange 10 to the end and fired
  64 volleys, about 2,700 rounds, for no one down: men gone to ground in buildings are seen 10%
  of the time. Now a unit at the objective holds it only once its target (where last seen) is
  off it; until then it goes on attacking.
- **Units on the ground never turned.** The order to stay where it is kept a unit on the
  ground as it lay before looking at its facing, so the guard post faced east all battle while
  it was shot at from the west, and never fired back. Now it turns toward its target and stays
  down.

Measured on 24 runs of every battlefield against main after #303: 705 of 984 from 704 (the
battlefields in common; main's artifact held an extra 24 runs this time, 1,008 in all).

| Battlefield | Before | After |
|---|---|---|
| Dornach | 3 | 8 |
| Goose Green | 1 | 5 |
| Wanat | 15 | 19 |
| Lützen | 20 | 17 |
| Keating | 19 | 17 |
| Hamburger Hill | 23 | 21 |

Twelve others moved by one either way. Chipyong-ni's runs now end at a median exchange 175
rather than running to the cap, still 21 of 24. The Wagon Box's soldiers lose about 31% rather
than 61%. The rout's share (T3) rose from 9% to 13% down, nearer the sources.

Keating falls as expected: the insurgents now clear the outpost, and nothing yet models what
the account says came next, the Americans retaking it by the afternoon. A holding side never
counter-attacks into its own objective. The stalemates had been scoring as held by accident.
To do: the retake, with sourced timing and strength, or a general rule for holders retaking a
lost objective.

## Lützen after the contested objective: run-to-run spread, 22 October 2026

Lützen went from 20 to 17 of 24 with #305. Measured again on 96 runs of Lützen alone (seeds 1
to 96), from main before and after #305, and with each of its two fixes alone:

| Page | Runs matched |
|---|---|
| main before #305 | 76 of 96 |
| attackers go on attacking a contested objective | 82 |
| units on the ground turn to their target | 76 (no unit at Lützen lies down) |
| main after #305 (both) | 82 |

The contested-objective fix is what changes Lützen, and over 96 runs it gains six. Seeds 1 to 24
lost three, so the rest gained nine: that drop was the runs' own spread. With the fix the Swedes
clear the windmill battery and the run ends once they hold it with every phase begun (exchange
424), where before many runs went on to the limit with Imperial men still on the hill. The
Imperialists lose about 27% rather than 34%, since the run ends sooner. Nothing to change.

## Keating's retake, and holders flanked, 23 October 2026

**The retake (researched, not built).** The sources (the project's keating-retake-research notes)
have the Americans pull back into two or three unburned buildings once the wire was breached
(about 06:48) and hold them; then two small parties retook the outpost: Romesha and five men
to the ammunition point, the shura building and the gate, Hill and three men across the burned
east side. No source gives a clock time for either; "about 5.5 hours in" is the only clue, and
the official summary says control was regained in the afternoon. With no times, a dated
counter-attack order is not built.

**What Keating's misses were.** On main after #305 (17 of 24), six of the seven misses ended with
the Coalition gone or the outpost held by no one: a retake would have had no one to make it. In
four of them the barracks (B Troop, holding, steady, 10 to 21 men) broke the first time one to
three insurgents reached its flank hand to hand, having lost no one or one man. A flanked unit
checks every exchange at -20, and a bad failure while flanked breaks it at once.

| Version | Runs matched (common battlefields) | Keating | Elsewhere |
|---|---|---|---|
| A failure while flanked only shakes a unit holding a position | +3 | 17 (unchanged) | Mogadishu 17 to 20, Chipyong-ni 21 to 22, Goose Green 5 to 4 |
| A unit holding a position is not flanked (built) | +3 | 17 to 20 | Chipyong-ni 21 to 23, Mogadishu 17 to 19, the Monastery 1 to 2; Goose Green 5 to 3, Hamburger Hill, Khe Sanh and Pork Chop one fewer each |

The first did nothing at Keating: shaken and still flanked, the barracks checked again at 40
and broke the next exchange. Built: a unit holding a position (in a bunker, dug in, behind works,
in buildings or rubble, or gone to ground in cover) is not flanked (`morale.posture_flank`). The
morale targets did not move. Mogadishu's Somali losses fell from 27% to 13% (their militia hold
buildings): to look at. Measured against main after #306, with Beaumont-Hamel (#307, not on the
branch) left out.

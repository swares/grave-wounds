# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Deferred work

- **The rule book, beyond the third part.** `dist/rules.html` covers the whole game in
  thirteen chapters, with a medieval retinue and a Vietnam rifle squad followed through.
  It summarises rather than repeats the docs: the black-powder guns' fire (sections, fuses,
  ricochet), the travel map's battle set-up and the battlefields are covered in the docs and
  on the pages, not in the book. It ends with an index of the terms set in bold, each linked to its sections, and prints page numbers (in Chrome and Edge; other browsers may leave them off). The index has no page numbers of its own, only section names.
- **The enemy commander, beyond the second cut.** A scripted commander moves one side on
  the field map. It attacks or holds by its units' quality, knows only what its units see
  (remembering last sightings for a few exchanges), picks targets by threat and weakness,
  holds back and commits a reserve (sending it to plug the gap a broken unit left), steers round minefields it knows of, turns its guns and
  calls its off-map batteries, limbers, tows, moves up and pulls back its guns, puts its men aboard its carriers and sets them down, storms works with black-powder infantry, charges through its own waiting units, sets its sappers to lay or lift mines, and takes or holds an
  objective hex the GM marks (and a second it goes on to, or falls back to); Undo puts
  its move back. What a unit sees from where it has just moved, the units ordered after it know. Attacking, it smokes enemies
  shooting at men who cannot reply, calls its aircraft, puts one battery on counter-battery fire and displaces batteries under it (moving a placed one along its map edge), and in the dark lights an enemy it has lost sight of. Its sappers lay one row at a time (no deep belts), and work a lane through a known belt
  row by row along their straight way, one lane as wide as their front; the other units are not held back for it. Its creeping barrages start on the enemy and lift a fixed 3 lines, and it plans none
  for riflemen who stop at range. Its foot units ride its carriers up and get down once an enemy is in reach. Its aircraft prefer a target its air controllers see and come closer there. Holding, by day or at dusk, it lays its machine guns' fixed lines on the nearest enemy it knows of in reach, or else ahead toward one (or along its facing), shifting a line laid ahead once onto an enemy that comes into reach. It digs its foot units in where they stand when safe: at the objective, holding with none, and in reserve. Attacking, an air controller with nothing better to do moves up to see a target for its aircraft (up to three moves away; holding, it stays). An attacking air controller with nothing better to do goes up to three moves to see a target, preferring a spot out of reach, and not while it has a fight of its own. Still left out: a controller moving past three moves, fixed lines across its front or interlocking with each other, and works other than digging in (no field works are built during a battle); any plan beyond two
  objectives (phase lines across the front, feints, scouting; no battlefield marks a second); ladders only where the GM or a battlefield marks them (the Great Redan's ladder parties are marked, but ladders do nothing on its ditch and bank). It does
  not play the travel map. Later, by the choice made: an optional narrator, using a model
  with a key the player supplies, to explain its orders in prose.

- **Works and ground on the field map.** Height has three steps (flat, slope, high) and no
  contour lines, so dead ground comes only from those steps: a fold of ground lower than a
  slope hides no one, and a long gentle rise is drawn as a strip of high ground. Tall buildings give a view and a height, but
  not separate floors: there is no fighting room to room or stair by stair, and men upstairs
  are not safer from shells. Scrub and orchards thin aimed fire and block sight past 3 hexes,
  but calling fire has no roll for them to cost (only the block), and the roller's 2-yard
  battle map does not thin sight at all (its woods and brush only give cover). There is no
  seeing through a building's open windows.
- **Heroes on the field map.** First aid comes from the unit's best Leechcraft or its
  medics, with tourniquets and (before 1914) cautery. A lamed hero slows his unit until he
  is carried back or left behind. Bearers carry him to his side's aid post across the map
  (or off it, with none), walking wounded go back alone, and a hero left lying is picked up
  by a friendly unit or found by an enemy one. Still left out: only shellfire can catch parties, not aimed
  fire (no figures for it); the rank and file have no aid post (their wounded are reckoned after the battle);
  prisoners have no exchange, ransom or
  escape; and there is no two-handed great sword among the weapons, so no sword is barred
  to a one-armed hero.
- **Indirect fire, simplified.** A battery placed off the map stands straight out from the
  edge nearest where it was placed, not anywhere behind it. Counter-battery fire does not need to see a placed battery: it
  finds it by flash and sound once located, wherever it stands within range.
- **The travel clock, simplified.** Meetings are only between the forces' hexes: no
  scouting reach, and no seeing a dust cloud or campfires from further off.
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Agincourt (1415), Towton (1461), Lützen (1632), Albuera (1811), Cowpens (1781), Lundy's
  Lane (1814), Sevastopol (1855, two battlefields), First Bull Run (1861), Fort Phil Kearny (1866-67, with two battlefields), Mons
  (1914), Hill 700 on Bougainville (1944), Anzio and Cisterna (1944), Osan (1950), Chipyong-ni
  (1951), the Ia Drang (1965), Mogadishu (1993), Wanat (2008), Cassino (1944, three battlefields), the Chosin Reservoir (1950), Kapyong (1951), Heartbreak Ridge (1951), Pork Chop Hill (1953), Hue (1968), Khe Sanh (1968), Dak To (1967), Hamburger Hill (1969), Goose Green (1982), 73 Easting (1991), Grozny (1995), Fallujah (2004) and COP Keating (2009) have both a campaign map and a battlefield. The rest of Italy, the rest of the Gulf War (1991) and Northern Ireland
  still play on the generic valley and open ground (the unit rules for them are in: machine
  guns, extended order, artillery and mortars on call, suppression). Each needs the same work: a spec for `tools/maps/campaign_lib.mjs` (places,
  rivers and roads drawn through public-domain facts) and one for `field_lib.mjs` (the
  battlefield and its armies).
- **Night, second cut.** Muzzle flashes, night vision, fixed lines, slower moves and losing
  direction are in. Night-vision devices (Starlight scope, goggles, thermal sight) are a
  unit's whole: a Starlight scope stands for the few rifles that had one. A vehicle firing by its
  infrared searchlight shows itself to enemy infrared and intensifier devices out to about
  1 km, through the next exchange (not while it only moves or watches), and image
  intensifiers and infrared sets wash out for a unit standing in a flare's light (not when the
  light only lies between it and what it looks at). A fixed line is laid on one hex, with no traverse limits or
  final protective fire called by flare. A lost unit strays only a hex along its wrong
  facing, never into its friends or the enemy, and no further. How long a lost unit stays put
  is decided (October 2026): it cannot move the next exchange (`light.lost_for: 2` counts the
  exchange it lost its way in), the same for every quality and light. Its chance of losing its
  way already depends on the light and its quality; we have no good figures for how much longer
  a lost unit took to recover on a darker night or with greener men, so that is not built. The moon is a simple model, good to an hour or so.
- **Air support, third cut.** Ground fire hits aircraft (bringing some down, sending the
  rest home damaged), anti-aircraft guns add to it, forward air controllers and smoke on the
  target cut the scatter, and an attack can be a round burst, a strafing run or a napalm
  strip along a line. Still left out: surface-to-air missiles; anti-aircraft guns firing at
  aircraft passing elsewhere (only those near the aim); a run's line passing over the men
  between its start and the target; napalm burning on, setting woods alight or reaching
  men in bunkers; heroes struck by napalm (only the rank and file are); and strafing or
  napalm against parties on their way back. Numbers are design estimates.
- **Landing by air, second cut.** Each side has a set number of helicopters with a load and a
  turnaround, at most 8 land at a zone in an exchange, hot zones hit them (damaged or
  downed, a wreck placed on the zone), and they bring supplies in and lift units out. Still
  left out: helicopters on the map as units (they are only ever landing or away), a downed
  crew to rescue, door gunners firing as they come in, landing zones that move or are cut by
  the GM mid-battle other than by hand, and battlefields setting their own helicopter
  numbers (all use the defaults, which are X-Ray's).
- **Medevac, first cut.** A side's wounded get better after-the-battle figures from its war's
  ambulance wagons, motor ambulances or helicopters (helicopters needing a landing zone and a
  helicopter left), unless the GM unticks it. Still left out: medevac flights during the
  battle (using lift and landing zones, at risk at a hot zone), the wounded of the rank and
  file carried back during the battle at all, ambulances before 1860 (Larrey's flying
  ambulances of the 1790s, the Crimean War's few), and a side's medevac failing under fire.
- **Ammunition, beyond the first cut.** Units count their ammunition and resupply from their
  edge, a supply vehicle or a dump (air drops from 1944, helicopters from 1965). Still left out: riders resupplying
  aboard their carrier, food, water and medical stores, and carrying a force's ammunition on
  the travel map from one fight to the next.
- **A narrator, first cut.** The field page tells each exchange's turning points (phases,
  units breaking or fleeing, reserves committed, the objective taken or lost, the end) in plain
  words, and with the player's own key (Anthropic, or any OpenAI-compatible service) a model
  retells each in a short passage in a voice for the war, using only the facts given. The key
  is kept only while the page is open unless the player ticks Remember. Still left out: only what changed
  over a whole exchange is told (a unit that broke and rallied within one is missed), no rally or hero turning points, no narration on the travel map, no streamed or
  regenerated passages. The GM can pick the voice for a battle (the war's by default); passages already written are
  not retold in a new voice.
- **Self-play against the battles as fought, first review** (`docs/selfplay-review.md`). Every
  battlefield was played with the commander on both sides and set against what happened; the
  commander now searches forward when it knows of no enemy, tanks no longer go to ground,
  modern infantry storm works, battlefields can give their stances, and self-play runs past the
  last phase and does not end on units still to come or an objective held from the start; a
  unit with no room to face its goal moves facing as near it as it can (Kapyong, Cassino). To
  do, from the review: 73 Easting's fight at the crest (tanks now placed by their main gun and standing off, but the T-72s are in dead ground until the crest); the morale check a unit in contact takes when it loses more than it deals, however few are touching (it breaks blocks of thousands after a handful of losses: Agincourt, see the review); men in rubble harder to shift (Cassino town: measured, see the review; shellfire decides it, and batteries' rate and ammunition are already within published figures; a sourced lethality figure scaled to 40% was measured and not applied); the Chechen
  ambush at Grozny (the night now fought as it was, the dark at 17:05; the breakout 25 hours on is beyond a run); an envelopment plan (Cowpens); the American
  rush on the guns at Lundy's Lane (dark now, but the guns still hold); the German counter-attacks on Point 593 (no sourced figures yet) and why small
  units take 593 so easily in February. Measured and not built: a holding commander that
  withdraws (no trigger tells the defences that held from those that went). Done: self-play runs to 1,200 exchanges, so every battlefield's phases come (101 of 148 runs, from 100), and its scripts are in tools/selfplay. Done: a run as long as the battlefield's own account says (ends, thirteen battlefields; 98 of 148, from 101). Measured and not built: a quarter-down unit checking morale only when it loses men, and a failed rally leaving it shaken (96 and 97 of 148, from 98), and only while an enemy is within a charge (96); see the review. Measured and not built: morale checked only on events (docs/morale-redesign.md: 87 and 90 of 148, from 98; it misses the sourced targets, because the battles rarely produce the flanks and broken neighbours the sources say break units). Done: the commander pursues broken units (101 of 148, from 98; Lützen 0 to 3 of 4). To do: units breaking at lower losses (T1), which the rout's share (T3) waits on. Done: a formed unit that the ground keeps from closing narrows its front, to half at least (313 of 444 from 307; Agincourt 1 to 8 of 12). Done: quick-play blows, a GM's option, off by default, with an era chart in the tables and a sheet for the field (285 of 444 with it on, within the runs' own spread: the same rules on seeds 13 to 24 match 290 against 313; changes are judged from here on 24 runs pooled, 603 of 888, and the morale targets; see the review). Done: a unit of the holding side holding a position counts its losses only in an exchange it lost men (642 of 888 from 628; Keating 12 to 20, Pork Chop 10 to 16, X-Ray 7 to 9). Measured and not built: a check when a neighbour within 2 hexes broke (no effect). Done: a unit that cannot turn toward its target still goes to ground under fire (628 of 888 from 620 on main; X-Ray 1 to 7, still to trace further). Measured and not built: a failed rally leaving the unit shaken (613 of 888 from 620). Self-play measurements run on GitHub Actions (selfplay and selfplay-compare workflows). Done: Hue's two tanks and two Ontos (a new vehicle kind); vehicles with a main gun never held in reserve; a shooter counts a target in range only with a clear line from the hex (641 of 888 from 620; Cassino town 0 to 22, Pork Chop 7 to 16; but X-Ray 15 to 1 and 73 Easting 19 to 12, to trace; Hue only 0 to 1; 106s on mules, launchers and gas have no counts; see the review). Measured and not built: the quarter-down morale check only in an exchange the unit lost men, with Phantom Ridge holding (614 of 888 from 620; Pork Chop 7 to 17, Grozny 2 to 9, Keating 16 to 21, but Cowpens 23 to 15, 73 Easting 19 to 12, Mons 23 to 18; the Cassino battlefields unchanged; see the review). Done: modern infantry storm works in bounds, going to ground after a bound that drew fire (628 of 888 from 620; Hamburger Hill 18 to 23 of 24; Goose Green still 0: its bounds still go into machine guns nothing has pinned). Measured and not built: the losing check called only by a share of the unit's men (610 of 888 from 620; before 1914 units broke at a median 27% down, from 15%, Towton 23 to 3; the June Redan 2 to 24). Done: the defenders' orders from the accounts (data/orders.yaml): units the sources say held fight where they stand, and units that withdrew on orders go at the accounts' minute (620 of 888 from 603; 73 Easting 7 to 19 of 24, Lützen 9 to 17; see the review). Measured and not built: the losing check and rout strike counted by the men in contact (101 of 148 from 102; units broke later, T1 28%); a second line feeding men into the first (Agincourt's vanguard was never in contact to be fed). Done: a battle fought to a draw in which the attacker took the objective matches a run with the attacker holding it; holding the objective ends a run only once every phase has begun; works laid under the units their accounts put in them (Cassino town, Bougainville, Goose Green, 73 Easting, Hue: Goose Green 3 to 0 of 12); Hue runs its account's length; the June Redan's centre column, which never went out, is off the map (0 to 2). Measured and not built: black-powder bayonet charges (any target 288 of 444, batteries only 304, from 307). To do, from the traces: the losing check breaking a whole battalion over one man (the June Redan); holding units pulled off their ground to the attackers' objective (Cassino town; measured and not built: units dug in, gone to ground or in a bunker holding their own ground, 285 of 444 from 307, Mons 12 to 0 and Osan 12 to 5, where the defenders gave way); Hue's missing tanks, recoilless rifles, Ontos and gas; the German fire and counter-attacks on Point 593; Grozny's strengths (one witness); see the review, The battlefields that never matched. Measured and not built: fire from a flank counting as flanked for morale (299 of 444, from 307; T1 nearer the sources, the Monastery 5 to 1 of 12), and the commander sending spare units round an open flank, with the odds against the men it would strike (302 of 444; Lützen 6 to 3); before 1914 the open flanks are seldom in reach and wide blocks cannot wheel onto them (see the review, Flanking; branch flank-prototypes). Measured, held: an elite quality for selected formations (304 of 444, from 303; branch elite-tier). Measured and not built: routes for the Monastery's Gurkhas and its Germans on 444 and the abbey holding their ground (5 of 12 runs, 4, 1; see the review). To do: why Point 593's paratroops alone lose to the Rajputana; defenders that break in the longer runs where the accounts say they held (the constant morale drain, which the short decisive battles depend on) (Keating, X-Ray and Pork Chop each lose a run; see the review); Mogadishu's American losses falling to 25% once the relief comes; the September Redan, 4 of 4 to 3 since the shooters give way. Done: the commander's shooters give way to their own formed men behind them, and a stalled attack commits a reserve (100 of 148 runs, from 96; see the review); measured and not built: the losing check, flank check and rout strike counted by the men touching rather than the whole unit; measured and not built: a formed unit held up behind another coming up beside it or relieving it (no change), and a formed unit narrowing its front to fit the ground (Agincourt's funnel; 98 of 148, from 100); see the review. Done: units tire by the toil rule, from hand-to-hand fighting and deep going (Agincourt, 0 of 4 to 1 of 4; see the review); the Poles at
  Cassino as companies (February stays as battalions; see the review); phases that change the
  light, and Lundy's Lane's sunset and moonlit night; tanks by fire control, composite armour,
  thermal sights in a sandstorm and vehicle morale by vehicles lost (73 Easting still does not match); routes round a flank from the accounts
  (Osan, Lundy's Lane, Kapyong, the Poles; no winner changed, see the review). Done since: faster exchanges (sight lines, the ground and
  step costs remembered, the same battles about five times faster on the page).
- **The enemy commander against itself, first cut.** Each side has its own commander choice;
  with both, Run plays on until Stop, a side with nothing left standing, an attacking side
  holding the objective 5 exchanges running, or 60 exchanges, then ends the battle; Python
  plays the same (`python -m gravewounds selfplay`), the turn now shared in the rules. Still
  left out: a search plan when no enemy is in sight and no objective is marked (both sides
  stand until the limit), many-battle statistics beyond running `-n` battles, and a narrated
  summary (see the narrator).
- **Cold, first cut.** Frostbite is a sickness on the force's track (and a named man's), not a
  wound on a body part, and cold-weather clothing, warming tents and fires are only the camp's
  shelter. In battle, only automatic weapons jam; mortars, grenades and vehicles do not freeze.
- **Vehicles, third cut.** Flank and rear shots, turret and hull hits, immobilised vehicles
  and guns put out of action, riders, rockets and guided missiles, anti-tank guns (1939-53)
  and minefields (1939 on), gun shields (anti-tank and anti-aircraft guns, and machine guns
  the GM marks shielded; small arms from the front), guns emplaced before the battle, anti-tank guns' own rounds and gun tractors
  towing them, lorries, tank riders and sappers laying and lifting mines in battle are in. Field guns with shields (about
  1900 on) only fire from off the map, so no battery on the map has one. Sappers lay or lift
  only the row just ahead of them, and a unit that turns in place onto mines sets them off
  as if it had moved into them (except its own side's). The way a unit went is reckoned as
  the cheapest round known mines within its move, not the hexes actually clicked through (a
  hand move is a destination, not a route). No battlefield has minefields yet:
  to be laid only where the accounts name them. Crews who bail out simply leave the fight.
- **Fire at hidden men, first cut.** Men gone to ground, in bunkers or in buildings are now hit
  at 10% of aimed shots (machine guns 5%), and dug-in men hold better. Osan, left alone, lasts
  about an hour where the real fight took two and a half; the rest of that time went in the
  North Koreans moving round the flanks, which the static test does not play. Worth a second
  look once Osan has been played through by hand.
- **Siege warfare tables, first cut.** The Crimean War now has a wounded table for the siege
  of Sevastopol (British rank and file, April 1855 to the end of the war, from the 1858
  official medical history) and an all-hits blend, with the earlier period beside it in the
  conflict notes. Still left out:
  - siege tables for the other wars: the Peninsular War database's Zaragoza wounded (159) are
    not published by action, and no Civil War split between sieges and open battle was found;
  - the earlier Crimean period as its own table (its limb wounds are not split into arms and
    legs, and a third of its wounded have no record of region);
  - a French table: Chenu's Crimea report (1865) has no count of all wounded by region, only
    case notes on the pensioned wounded, by region (disabled survivors, so not used; see
    `docs/hitloc-reference.md`);
  - the `behind_cover` modifier's torso and leg factors, which whole-army totals cannot set
    (the head factor of 1.5 agrees with the Crimean returns);
  - on the Great Redan battlefields, the siege guns of both sides, the French attack on the
    Malakhov and the flanking fire of the batteries further along the line (only the guns in
    the work and, on 18 June, a battery either side are on the map);
  - a deep ditch that needs ladders: the Redan's ladder parties are marked, but the ditch
    (15 to 20 feet deep) and its bank are crossed without them, as no figures were found for
    how much slower or costlier it was to get in without ladders.
- **Guns, still simplified.** The Thirty Years' War still borrows the Peninsula's gun wounds,
  because no 1618-48 artillery wound counts were found.
- **Character generation, beyond the first cut.** The medieval tables are a first draft for
  a team playtest. Its characteristics now count in the roller (Agility, Endurance,
  Strength, Presence), and Leechcraft, Fieldcraft, Watch and Stealth work outside a fight.
  Followers have one-line stat blocks, and the gunpowder eras (1618-1876) and the world wars
  (1914-18, 1939-45), Korea, Vietnam and the later wars (1982-2014) have their own tables.
- **Rank, pay and loot, first cut.** Ranks, promotion by vacancy, pay by rank, loot, prize money,
  ransom and the Plains nations' honours are on the team builder. Still left out:
  - the field map now counts a hero's hits and downs (a deed at two) and a Plains hero's
    close-combat downs as coups, but not who struck first, nor a hero of the roller's own;
  - the deed suggestion (two downs, or the enemy's leader) is a design choice, and a down
    credited is only one made by a wound applied in the roller (bleeding out later is not);
  - a raid for horses is rolled after a fight, not played on the travel map;
  - rank shows on the roller's card and the field map's heroes; the highest rank leads; a
    leader's rank steadies his unit and officers draw fire, but the step and the officers'
    exposure are design estimates, and only team-builder heroes carry a rank to the field map;
  - many figures are estimates: pay below the British and American ladders (the Thirty Years'
    War, the medieval vintenar's rises, German, French and Soviet armies by region), the share
    of pay kept after stoppages, the loot finds and ransoms, and the honours tiers;
  - no figures for demotion (it is the GM's), for how often looters were punished (only
    Seringapatam's four hanged), for the Soviet parcels (described, not rolled), or for Plains
    raiding (Ewers' pages on dividing horses and how often raids went out were not read);
  - every career draws the soldier's wage when fed by the army, the medieval clerk and servant
    included.
- **Skill checks, first cut.** The team builder rolls any check, opposed or not, and haggles at
  the price list. Still left out:
  - billets, hunting for the pot and finding the way now work on the travel map (data/uses.yaml),
    but Mend kit has no kit that wears out, and getting lost at night on the travel map is not
    rolled (only fog, snow and storms, and off the road);
  - the roller and the travel map have no checks panel of their own (only their built-in rolls:
    first aid, foraging, surprise);
  - a check out of a fight takes the roller's last word on the man (pain, blood, wounds,
    fatigue, sickness, Strain), so a man not seen in the roller since he healed still carries it
    until the roller is opened again;
  - haggling covers buying, selling loot and hiring, but not selling anything else (no
    inventory of goods is kept).
- **Patrons, first cut.** Standing per patron, favours, events, rival claims, the patron's fate
  and his clients' lot. Still left out: the fate chances and the Standing moves are design
  estimates; British commission prices (the 1837 regulation table, £450 an ensigncy to £4,500 a
  lieutenant-colonelcy) and private-income needs are in the research but not priced into the
  commission favour, which is a +20 and the GM's word; patrons are not yet named people with their
  own rank, side and purse, nor do they appear on the field map or the roller; thirds (the captain's
  third of his men's winnings) are not taken from loot automatically; no drift without events
  (Pendragon's winter check); and Visby, the Napoleonic marshals, Korea, Vietnam, the Falklands and
  Chechnya had no patronage sources.
- **Tongues, first cut.** Own tongue, others by army, bands, related tongues, talk caps, words
  across tongues, passing, phrase books, capture and escape, learning by use, lessons and living
  among speakers. Still left out: the shares of who spoke what are estimates throughout (no muster
  counts by tongue were found); the Thirty Years' War's camp German is inferred, not sourced, and
  the King's German Legion's language of command, Crimean interpreters, Peninsula Spanish among the
  British rank and file and interpreters' pay before 1990 were not found; interpreters are not hired
  men with their own figure, reliability and pay (the research has Iraqi rates from $600 a month in
  2005); dialects (Dari against Waziri, Flemish against French) are not told apart; the field map's
  orders do not yet check a shared tongue between a leader and a mixed unit; and reading a foreign
  hand is left to Letters and the GM.
- **Period money, first cut.** Every page shows money in the man's army's coin first, then Days;
  the rule book's money chapter has each army's Day, pay by rank and every era's price list; 13 more
  coins have a Day (project doc "coin-days-research"). Still left out: five coins have no Day and
  their prices stand in coin alone (buffalo robes, North Korean won, North Vietnamese đồng, the 1982
  Argentine peso, AMG lire); several Days are stand-ins (the French livre of 1434 for 1415, a
  Swedish labourer's öre for Gotland, the 1850s franc for the Napoleonic, the WWI poilu's 5 sous
  unconfirmed, a Chinese Volunteer's pocket money below an officer's, the 1995 rouble as a ceiling);
  the Confederate dollar keeps its 1861 Day though it was worth a cent a day in gold by 1865; job
  pay is worked from Days, not each job's sourced wage; and Iraqi militia pay ($300 a month, Sons of
  Iraq 2008) is not a second Day.
- **Water, heights and pursuit, first cut.** Swimming and drowning, cold water, fords, climbing,
  falls and chases in the roller; fords on the travel map. Still left out: no era has a sound
  count of who could swim (the shares are estimates); drowning counts for the Rapido, Omaha, the
  Ebro and the Berezina, fording limits from the modern field manuals, swimming in armour, ladder
  climbing under fire and cavalry fall rates were not found; the travel map's fords have one depth
  (ordinary, or flooded), with no current or temperature of their own, and horses are not swept
  away; a fall's death is a critical head wound for the GM to rule on; and the pursuit on the
  field map (units.yaml aftermath.pursuit) takes its killed and prisoners from the units' men,
  but its shares are the research's ranges, not counts, the Python self-play does not apply it,
  and no named man runs his own chase from it.
- **Prisoners, first cut.** Capture, captivity by era and situation, release, escape, death,
  ransom, parole and service. Still left out: the release chances, escape modifiers and capture
  bands are calibrations, not figures (the death hazards are worked from the sourced totals); the
  1743, 1759 and 1780 cartels' tariffs were not found, nor Napoleonic parole-breakers' numbers,
  WWI deaths in Russian hands or the Plains nations' adoption of captives (deliberately left
  unnumbered); exchange values are shown but not traded (a release roll stands for them); the
  team cannot take and hold prisoners of its own beyond the loot's ransom; and a man's captivity
  does not touch the travel map.
- **Strain, first cut.** Strain and Toll, Nerve checks, results by era name, treatment, rotation
  and homecoming, lasting-effect notes. Still left out: the calibration rests on Appel and Glass
  and Jones (Appel and Beebe 1946 and Swank and Marchand 1946 were not read in the original); no
  figures before 1850 (the medieval, Thirty Years' War and Crimean rates are the same rules, not
  data); cohesion, a trusted leader, a replacement and being on the move change a combat day's
  Strain (the research's quarter and half), but a leader killed is a source of its own, not a
  one-off +3 to everyone, and "trusted" is a Command of 60, not a record of how he led; the field map's units have
  no Strain (their morale is their own), and its heroes take only the fight's when they come back
  to the roller; treatment takes no time on the travel map; and the Plains nations' homecoming is
  deliberately abstract.
- **Loads, first cut.** Load orders by era, bands by body weight and Strength, march pace and
  fatigue, blisters, Dodge and the run, dropped and lost packs. Still left out: no item has a
  weight, so what a man buys adds to his load only as the extra kg the GM writes on his sheet;
  a force's load is its average man's, with no armour for its rank and file; the band steps,
  blister rule and the hardening of feet are design choices; the Plains nations' loads and most
  medieval and 17th-century body weights are estimates; pack animals and carts that take the load
  off the men are not modelled; the field map's units do not carry loads; and the terrain's extra
  cost to a loaded man (Pandolf's terrain factors) is left to the map's existing going.
- **Ageing, first cut.** Decline, maturity, Wear and the Worn Out check. Still left out: the
  decline dice are design choices scaled to the physiology (no game-scale figures exist); the best
  sources for British invaliding by age (Tulloch's tables, 1838-53; Nielsen's Chelsea
  applicants) and for breakdown by age in WWII (Stouffer vol. II; Beebe and Appel) were not read;
  enlistment age limits by era, and older recruits wearing out faster (Civil War men enlisting at
  about 39 had 1.8 then 2.4 times the odds of dying of disease), are not applied; Presence does
  not rise with promotion; followers and men without a sheet do not age; age does not count in a
  fight beyond the characteristics it has changed.
- **Experience, first cut.** Skills used well are ticked (job checks, hits, parries and
  dodges, first aid, foraging, nursing, Stealth and Watch at a surprise) and roll to rise at
  End of season; days served add a career term (`docs/team.md`, *Experience*). Still left out:
  - the field map's battles tick a hero's weapon skill for his hits, but not his parries or the
    first aid he gives;
  - characteristics never change in play, and age brings no decline;
- **Training, first cut.** Masters for hire, teammates and drill in camp tick a skill. Still left
  out: the masters' fees are estimates apart from riding lessons (London, 1879), and a master's
  skill is always 60; a teammate who teaches is not stopped from working that week (the page says
  he gives it up, but does not hold him to it); drill ticks only the skill of the weapon a man
  carries in the roller, and only for named men; courses (data/training.yaml `courses`) are a
  set of examples with estimated gains and fees, the man is not missing from the team while away,
  and an apprenticeship is a year of its seven.
- **Women under arms, first cut.** Women serve as cantinières with the French in the Crimea, in the Civil War (disguised), the Soviet
  Union of 1941-45, Vietnam (the ARVN, the North and the Viet Cong) and the later wars (the US,
  Britain and Russia), chosen or rolled at the army's share. Still left out: the earlier eras
  (women in medieval sieges, the Revolution's and 1812's few, the Napoleonic cantinières, Russia's women's battalions of
  1917 and Flora Sandes in Serbia), careers outside the fighting units (nurses, auxiliaries,
  anti-aircraft gunners, pilots, the Female Engagement Teams of Afghanistan), the Plains
  nations' women who fought, and shares by career rather than by army. The Viet Cong's and the
  North's women have no reliable share, so they are chosen, never rolled.

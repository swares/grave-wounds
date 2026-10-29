# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Deferred work

- **The campaign, first cut** (`docs/campaign.md`). A console page over the others: the phase,
  what to do, where things stand, the campaign's log, and save and load of the whole game as a
  file. Still left out: it runs the travel map's day, the roller's script and the field map's
  moves, but a person's moves and strikes are made on the roller, and units placed and ordered by
  hand on the field map; it notices fights sent and won, named men felled, units broken, deaths, prisoners,
  outbreaks, supplies running out, new ranks and the end of a day or season; the pages' state is
  still per page (campaigns are kept side by side as whole sets of it, in IndexedDB); players online join the campaign on one link each (their men, their force, the public news, their fights on the console's roller, and orders they propose for the GM to accept). The travel map's
  rules and its day are now out of the page (`templates/travelrules.js`, checked against the
  Python; `templates/travelday.js`, played with no page), and the console runs the march's clock
  (Run the march), gives routes, orders and camps, sets up the fights on offer and takes a
  battle's result back. Still on the travel map: columns, the forces' own settings, adding forces
  and painting. A travel map open in another tab follows the day when it changes elsewhere; the
  roller and the team builder open in another tab still keep what they loaded until reloaded.
  The day still keeps the named men, purses and experience in the browser's storage as the other
  pages do, and the stress rolls in ranks.js take the browser's dice, not the day's.
- **Virtual GM, first cut.** The roller's strike is decided with no page (`templates/strike.js`),
  each strike, wound and scripted move goes into an event log tagged with who may see it
  (`templates/gamelog.js`), and Run the fight plays each side as a player, the GM by hand, or the
  GM's script (`templates/fighter.js`), with Step, Play to my turn and Undo. Its men give first
  aid out of contact (themselves when bleeding badly; comrades by the side's stance) and surrender
  (a man down beside an enemy asks for quarter; a broken side's cornered and down are taken, the
  rest run). Still left out: the script does not aim at a zone, use works, drop packs, swim or
  climb, and its priorities are guesses with nothing to calibrate them against; men with no
  sheet take their side's quality, with no per-man setting; a side's Screen hides the enemy's
  state on the cards, roll form, result, messages and logs, but it is a filter anyone at the
  page can switch off, and the after-fight, hazards and tongues panels still show whoever is
  chosen in full; every roll on the roller now
  goes into the event log (strikes, wounds, initiative, bleeding, morale, first aid, pain stop
  checks, hazards, tongues, deeds, loot); the log is a record, not yet the save (the last 500 events); a strike's
  public part is fixed, not a GM setting; the field and travel pages have no log. Play online
  (first cut): the GM's page is the host over WebRTC; the campaign console's players can use
  room codes through a small Cloudflare Worker (`worker/`, to be deployed), others pass codes by hand. Still left out: a
  TURN relay for strict networks, room codes for the roller's own Play online,
  rejoining without passing a new link and reply by hand (a lost player is invited again to the
  same seat, his page keeping his last screen; a blinked connection mends itself), sending changes of the whole picture (the panels that changed go as their changed tags, but a turn that lights every hex still sends them all), a player's
  works and the other panels from his page (first aid he gives, on his side's turn), and the field
  and travel pages online.
- **Fog of war on the travel map, second cut** (`docs/travel.md`, `docs/fog-of-war-research.md`).
  A side sees enemy forces within a distance in km (3 on foot, 8 mounted, 2 with wagons; cut by the
  weather, dusk and the dark; outposts find any enemy within 1 km; woods and towns hide a force
  beyond that) and remembers where it last saw them; a player's map online shows only that, and the
  GM's travel map can show any side's view. Still
  left out: campfires at night, dust, height, optics and aircraft (the 20th-century maps get
  naked-eye sight: a per-period factor is next), scouting orders and patrols, and the delay of
  reports; the weather factor (5) and several distances are judgments, not sourced.
- **Lethality, first cut.** Gritty | Standard | Heroic for player characters (wounds.yaml
  lethality): fate a season, Blood and the stop check, on every page. Still left out: fate does
  not save a man from drowning, a fall or the other hazards; the roller offers fate only on the hit
  just applied (not on old wounds or a pain check); the field map's heroes spend it only on a
  killing wound or a death when found, never on a stop check; and the CLI and self-play use the
  default setting with no flag to change it.
- **The rule book, still left out.** `dist/rules.html` covers the whole game in
  eleven core chapters and four modules, with a medieval retinue followed through. Five period
  books hold every era's figures and battlefields (`dist/book-medieval.html`,
  `dist/book-black-powder.html`, `dist/book-world-wars.html`, `dist/book-korea-vietnam.html` and
  `dist/book-late-wars.html`). Each but the medieval book ends with a worked example (the
  medieval retinue runs through the Rules), worked by `gravewounds/book_examples.py` and
  `rulebook_later.example`. Still to come: the pictures' files, and Sources and Methods.
  It summarises rather than repeats the docs: the travel map's battle set-up and the
  battlefields are covered in the docs and on the pages, not in the book. It ends with an index of the terms set in bold, each linked to its sections, and prints page numbers (in Chrome and Edge; other browsers may leave them off). The index has no page numbers of its own, only section names.
- **Playing alone, first cut.** The Rules' *Playing alone* chapter (`templates/rules/15-alone.md`)
  says how one person runs a session with the pages, and adds **Ask the dice**, a yes-or-no table
  on the one roll with a d10 of complications for the GM's judgement calls. Still left out (the rules
  audit of 26 October 2026): no solo campaign has been played through end to end, and the printed
  tables do not carry Ask the dice. (Done since: the virtual GM's first aid and surrender, and Beat
  history on the field map with its scorecard.)
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
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Jacob's Ford (1179), Crécy (1346), Aljubarrota (1385), Agincourt (1415), Towton (1461), Dornach (1499), Lützen (1632), Albuera (1811), Cowpens (1781), Lundy's
  Lane (1814), Sevastopol (1855, two battlefields), First Bull Run (1861), Fort Phil Kearny (1866-67, with two battlefields), Mons
  (1914), Beaumont-Hamel (1916), Snipe at El Alamein (1942), the Serbian retreat (1915-16, the Babuna pass, Topolčani and Mojkovac), Hill 700 on Bougainville (1944), Anzio and Cisterna (1944), Osan (1950), Chipyong-ni
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
  the GM mid-battle other than by hand, and helicopter numbers of each battlefield's own (a
  field can set them, `field.helos`, but none does: all use the defaults, which are X-Ray's).
- **Medevac, first cut.** A side's wounded get better after-the-battle figures from its war's
  ambulance wagons, motor ambulances or helicopters (helicopters needing a landing zone and a
  helicopter left), unless the GM unticks it. Still left out: medevac flights during the
  battle (using lift and landing zones, at risk at a hot zone), the wounded of the rank and
  file carried back during the battle at all, ambulances before 1860 (Larrey's flying
  ambulances of the 1790s, the Crimean War's few), and a side's medevac failing under fire.
- **Ammunition, beyond the first cut.** Units count their ammunition and resupply from their
  edge, a supply vehicle or a dump (air drops from 1944, helicopters from 1965). Still left out:
  riders resupplying aboard their carrier.
- **Reliability, first cut** (units.yaml `reliability`, weather.yaml misfires; project docs
  "reliability-weapons-research" and "reliability-vehicles-research"). Flintlocks misfire 15% even
  dry and percussion caps 0.6% (Woolwich, 1834); automatic weapons lose a share of their fire to
  stoppages by war (the M16 in Vietnam 10%); vehicles the GM or the travel map brings may be unfit
  as the battle begins (Cambrai's 15% for WWI, 5% after), a battlefield's armies as fought only by
  its own `unfit` %; WWI vehicles break down on the move. Self-play 422 of 576 (from 423): Albuera
  9 to 7, Mogadishu 8 to 12. Still left out:
  - wagons and harness breaking (horses already wear out by era on the travel map, events.yaml:
    four times as fast when hungry, and a force fed by its army is remounted at its depot);
  - no dry figure for matchlocks or wheellocks; the wet steps are design estimates;
  - no battlefield yet has the models the sources single out (the Panther's final drives, the
    Tiger's gearbox, the T-34's clutches of 1941) to carry its own `unfit`;
  - artillery duds and worn bores, radios and their batteries, bows and crossbows (the Crécy
    strings rest on one 1875 source).
- **Supplies between fights, first cut.** A travel-map force carries ammunition, rations, water
  and medical stores; a field battle takes its ammunition and sends back what is left; it refills
  at its depot, from its baggage train in the hex, and by buying rations in a village or town
  (project doc "supplies-research"). Still left out: the days carried are sourced for some eras
  only (medieval, Thirty Years' War, Plains and modern are estimates), the water needed by heat and
  the medical stores' reach are design figures (no dressings-per-wounded rule was found), a
  baggage train's stock is one size whatever its wagons and does not refill itself, the maps mark each side's depots
  where a source names one (project doc "depots-research"; many rest on Wikipedia, and a side that
  lived off the land, or whose base lay off the map, has only its starting place: the Chinese in
  Korea, the North Vietnamese, the Germans at Mons, the British at Cowpens, the Plains nations,
  Gotland's levy; the Hamburger Hill and Ia Drang maps were widened to take in Firebase Airborne and Plei Me camp, though the land drawn there is only the maps' plain forest), a force's own pack animals and the named men's
  carts do not carry its rations, the field map's own units do not eat or drink, rations bought
  are priced at the first army's keep for the era, and hunger and thirst only add to desertion,
  straggling, fatigue and the hard nights (no march-rate or heat-casualty rule).
- **A narrator, first cut.** The field page tells each exchange's turning points (phases,
  units breaking or fleeing, reserves committed, the objective taken or lost, the end) in plain
  words, and with the player's own key (Anthropic, or any OpenAI-compatible service, Gemini's
  free tier among them), or a model on the player's own computer with no key, a model
  retells each in a short passage in a voice for the war, using only the facts given. The key
  is kept only while the page is open unless the player ticks Remember. Still left out: only what changed
  over a whole exchange is told (a unit that broke and rallied within one is missed), no rally or hero turning points, no narration on the travel map, no streamed or
  regenerated passages. The GM can pick the voice for a battle (the war's by default); passages already written are
  not retold in a new voice.
- **Tumbledown and Pork Chop, fixed by planned fire** (27-28 October 2026; claude/tumbledown-study-2).
  Planned fire (`indirect.planned`): an attacker's guns may fire, unseen, within 3 hexes of a place
  the defenders held when the battle began (Tumbledown 0 to 8 of 12 as fought); a battery the
  battlefield marks with a defensive fire plan (`df: true`) may fire, unseen, within 12 hexes of
  its own side's start positions (Pork Chop's flash fire: 4 to 12 of 12). Given to every
  defender, the fire plan put Tumbledown back to 0 (and Grozny 2 to 7, Hue and Chipyong-ni -1), so
  it is marked by battlefield where a source gives one. 443 of 576 runs now match the battle as
  fought (Mojkovac and Topolčani added; reliability, 423 to 422; a bayonet front against horse,
  Albuera 7 to 12, Lundy's Lane 1 to 0; a closing volley before a charge home, both Redans +1;
  Cassino's sangars, the Monastery 0 to 3; trenches against shellfire at a fifth of lying, after
  Evans, and Snipe's six-pounders with no HE round, 431 to 435: Snipe 0 to 3, Babuna 6 to 10, the
  Monastery 3 to 6, Pork Chop 10 to 12, Mojkovac 11 to 12, but Tumbledown 8 to 3 and 73 Easting 4
  to 0; project doc "snipe-study"; proof armour takes no harm, a T-72's frontal hit neither
  immobilising an M1A1 nor putting its gun out, 435 to 443: 73 Easting 0 to 8). Still behind: Snipe 3 of 12, Rommel's evening tanks driving
  into the hollow (in fact they drew back to 800 yards); Tumbledown 3, the Argentines in their
  trenches outlasting the British guns, and their mortars then hitting the Guards; Chipyong-ni 10 of 12; Lundy's Lane 0, studied (project doc "lundys-lane-study"):
  Ripley's brigade stops 140 m off the guns and trades fire ("a shooter never charges"); made to
  storm them, it breaks 7 men down to the per-man rule for losing the exchange, and capping that
  rule by share cost Agincourt more than it gained. A closing volley before a charge home is
  now in (missile.closing_volley), but with the storm order it still gives 1 of 12: Ripley's
  brigade still loses the melee by the per-man rule.
- **Self-play against the battles as fought, first review** (`docs/selfplay-review.md`). Every
  battlefield was played with the commander on both sides and set against what happened; what has
  been changed since, and what was measured and not built, is in the review. To do, from the
  review and its traces:
  - 73 Easting: the fight at the crest (the T-72s are in dead ground until the crest), and tanks
    closing inside the Iraqis' sight in the sandstorm;
  - the morale check a unit in contact takes when it loses more than it deals, however few are
    touching (it breaks blocks of thousands after a handful of losses: Agincourt), Agincourt and
    the June Redan under the losing check, and the losing check breaking a whole battalion over
    one man (the June Redan);
  - units breaking at lower losses (T1), which the rout's share (T3) waits on, and defenders that
    break in the longer runs where the accounts say they held (the constant morale drain, which
    the short decisive battles depend on: Keating, X-Ray and Pork Chop each lose a run);
  - Cassino town: men in rubble harder to shift, and holding units pulled off their ground to the
    attackers' objective;
  - Grozny: the Chechen ambush (the breakout 25 hours on is beyond a run) and its strengths (one
    witness);
  - an envelopment plan (Cowpens), and the American rush on the guns at Lundy's Lane (the guns
    still hold);
  - Point 593: the paratroops now hold sangars and bunkers (the Monastery 0 to 3 of 12); May's
    counter-attacks are on the map with strengths of our own (none sourced) and are too weak to
    throw the Poles off (0 of 12); the Allied guns still put down hundreds of paratroops over the
    day's eighteen hours, against "sat out the bombardment under cover";
  - Goose Green (bounds still go in before the guns are pinned), Keating (traced: not the bounds;
    and the Americans retaking the outpost, researched but with no clock times in the sources) and
    Wanat (no single fix; within the runs' spread);
  - Hue: the Marines' rockets (3.5-inch, LAW, 106), recoilless rifles and gas (no sourced counts);
  - Mogadishu: the Somali losses falling from 27% to 13% once a unit holding a position was no
    longer flanked for morale, and the American losses falling to 25% once the relief comes;
  - the September Redan, 4 of 4 to 3 since the shooters give way;
  - a sourced rate for how often a cut-off unit surrenders (none found; every cornered unit of a
    side that gives up does).
- **The enemy commander against itself, first cut.** Each side has its own commander choice;
  with both, Run plays on until Stop, a side with nothing left standing and none still to come,
  an attacking side holding the objective 5 exchanges running once every phase has begun (taken
  from the other side, with no standing enemy within 10 hexes of it), or the exchange limit, then ends the battle. The limit is 60
  exchanges, or for a battlefield with phases 30 past its last phase's start, or its account's
  length if longer, but never more than 1,200 (units.yaml `commander.self_play`). Python plays
  the same (`python -m gravewounds selfplay`), the turn now shared in the rules. Still left
  out: many-battle statistics beyond running `-n` battles, and a model-written summary
  (`selfplay --story` prints each battle's turning points; see the narrator).
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
  at 10% of aimed shots (machine guns 5%), and dug-in men hold better. A dug-in line left alone
  is tuned to hold for an hour and a half to two against five times its numbers (Osan) where
  the real fight took two and a half; the rest of that time went in the North Koreans moving
  round the flanks, which the static test does not play. Worth a second look once Osan has
  been played through by hand.
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
- **Presence and followers, first cut.** A leader's Presence now caps how many of the
  template's followers stay (data/followers.yaml, a design table, as no period source gives
  one): shown on the team builder, with a warning over the cap, and half the excess, rounded up,
  drifting away at each End of season (deserting or going home). Still left out: the field
  map and the roller do not apply it.
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
  - billets, hunting for the pot, finding the way (by day and, marching on by night, by night) and
    Mend kit (boots and clothing that wear out) work on the travel map (data/uses.yaml,
    data/kit.yaml; project doc "kit-wear-research"); but the night march's extra fatigue and the
    boot and clothing lives for the medieval, Thirty Years', Crimean, Civil War and later eras are
    estimates, a night march gives no concealment of its own (the dark cuts every side's sight
    alike, marching or not), only the named men's kit wears (a force's men are not shod or clothed), weapons, harness and radios do
    not wear, and Mend kit is rolled only on a day the force does not march;
  - the roller and the travel map have no checks panel of their own (only their built-in rolls:
    first aid, foraging, surprise);
  - a check out of a fight takes the roller's last word on the man (pain, blood, wounds,
    fatigue, sickness, Strain), so a man not seen in the roller since he healed still carries it
    until the roller is opened again;
  - haggling covers buying, selling loot and hiring, but not selling anything else (no
    inventory of goods is kept).
- **Patrons, first cut.** Standing per patron, favours, events, rival claims, the patron's fate
  and his clients' lot. Still left out: the fate chances and the Standing moves are design
  estimates; British commissions can now be bought and sold at the 1837 regulation prices (ranks.yaml
  `purchase`): the ensign's £450 is confirmed in a journal, the captain's £1,800 rests on Wikipedia
  alone, and the ladders have no lieutenant, major or lieutenant-colonel to buy; the over-regulation price is the GM's to ask, and
  private-income needs are not priced; the commission favour is still a +20 and the GM's word;
  patrons are not yet named people with their own rank, side and purse, nor do they appear on the
  field map or the roller; the medieval third of loot and of a captive's ransom now goes to a patron who takes thirds as
  a gift, but only to the first such patron, and a prisoner of rank is not handed up to the captain
  or the king (the team keeps him); no drift without events
  (Pendragon's winter check); and Visby, the Napoleonic marshals, Korea, Vietnam, the Falklands and
  Chechnya had no patronage sources.
- **Jacob's Ford and the Ayyubids, first cut.** The siege of 1179 on a 1 km map and the storm of
  the castle as a battlefield, on Sidon's tables, and the Ayyubids as a medieval army (project doc
  "jacobsford-research"). Still left out: no Ayyubid pay or dinar-dirham rate was found (the Acre
  crossbowman's third of a bezant a day stands in), no strength for Saladin's army or his camp's
  place, no source for how far Baldwin's relief came; the siege before the storm (the outer
  works, the mangonels, the two mines) is not played, nor the timber wall that burned behind the
  breach; the mine's place at the north-east corner rests on secondary sources; Raphael's full
  excavation report (the siege, the bones, the arrowheads) and Mitchell, Nagar and Ellenblum's
  paper were not read in full; the Ayyubid ranks (amir, mamluk, halqa) are not a ladder of their
  own; Kurdish and Persian are new tongues with estimated shares. In self-play the storming column
  does not go in through the breach.
- **Snipe and Italy, first cut.** The El Alamein map of the northern sector (1 km, from 26 October
  1942), the Snipe battlefield (27 October, first light to dark, the 19 six-pounders by company
  sector against the German and Italian armour, 24th Armoured Brigade coming and going), a new
  Egyptian coast climate, and Italy (1940-1943) as a Second World War army: Italian names, the Owens
  WWII table, lire at about 0.96 a day (a private's $1.51 a month in the US Intelligence Bulletin of
  December 1942, at 5.26 cents a lira: our arithmetic), the next draft class as replacements, Italian
  as its tongue (project doc "snipe-research"). Still left out: no grid reference or survey for Kidney,
  Snipe or Woodcock (derived from Wikipedia's distances to Aqqaqir; Wikipedia's own Snipe point is 24
  km off); the guns one by one (only by company sector), the hollow's depth and the ridges; which way
  each Axis attack came and the strength of those the accounts do not number (ours); whether the
  armies moved their clocks back to GMT+2 at midnight on 26/27 October (the field keeps GMT+3,
  which the sources' times fit); the friendly fire of 47th RTR and the 11th RHA's Priests, the
  British artillery (its observer lost at 04:00), Toms's jeep run and the ammunition crisis (the
  rules' 40 rounds a gun, never refilled here); the Italian names and ranks are our reading, its ages
  take the British 18 to 41, its pay steps the American, its war supplement and any prices were not
  found; the M13s, M14s and Semoventi play as light armour and the Panzers as heavy, all with the
  tank kind's one gun; the camelthorn is not drawn (the rules' scrub keeps tanks out). No desert or
  tank-crew wound table yet: Chute's 1942 Eighth Army report on tank casualties (every casualty of
  one regiment by crew position, injury and cause; about 30% flash burns; 15-25% hit after bailing
  out) would make one, but it lies in an archive not reached; until then the Owens table stands.
  In self-play the battalion does not hold (0 of 3: every British unit gone by about 10:30, 40% of
  its men down to the Axis 14%; in fact 72 of under 300 hit and some 37 tanks and SP guns burnt
  out): the first use of anti-tank guns on a battlefield, a lead for the self-play review, not
  tuned here.
- **Beaumont-Hamel and the Newfoundland Regiment, first cut.** The Somme map from Doullens to
  Bapaume (1 km, from 30 June 1916), the battlefield on the ground of the Newfoundland Park (the
  87th Brigade at 07:30, the Newfoundlanders at 09:15, the Essex at 09:55), and Newfoundland as a
  First World War army (outport names, $1.00 a day, a draft from home, ages 19 to 35, VAD nurses;
  a Logger origin for every army) (project doc "beaumont-research"). Still left out: RIR 119's
  companies and machine guns opposite the park, their places and count (none found: ours); the
  British battalions' strengths but the Inniskillings' and the Newfoundlanders'; St John's Road,
  the Danger Tree and the Mary Redan have no coordinates, and the lines are drawn to the sources'
  distances, not from a trench map; spot heights (the elevation services were blocked); whether
  RIR 119 had the Stahlhelm on 1 July; a German private's pay in 1916 (the game's 50 pfennigs stays
  an estimate); RIR 119 is the generic German army, not a Württemberg one (Swabian names, all
  German-speaking, hardened by twenty months in the line); the Hawthorn Ridge mine and the 86th
  Brigade (a second board) are not played; no wound locations for this sector were found (the
  First World War table stands, and no field weights machine-gun fire above the 1916 average of
  39% bullet); the Newfoundland ranks take the British pay steps; an Irish share of its tongues
  and the number of its nurses were not found. The Newfoundland Day is his $1.00, though his pay
  was about four times a British private's: the purse counts every army's Days alike, so his British-priced kit
  (the SMLE, the Mills bomb, the Brodie) shows at a shilling to his dollar, about four times too dear.
  In self-play the Germans hold but the British lose about 14% (in fact over half, the
  Newfoundlanders 88%): the first wave, gone to ground in no man's land, draws the German fire as
  the nearest target and screens the waves behind it (no unit shoots through another, even one
  lying down), so the Newfoundlanders cross almost untouched. A lead for the self-play review, not
  tuned here. No man's land plays as open ground (a slope hex would hide the forward slope). Done
  with it: a battlefield file can place supply dumps (`dumps`), and RIR 119's dugouts hold its
  ammunition.
- **Crécy, first cut.** The campaign map from the Somme to Crécy (1 km, from the crossing at
  Blanchetaque on 24 August 1346) and the battlefield on the traditional site (Cassini's, 1757)
  with Preston's steep bank along the east side of the Vallée des Clercs (project doc
  "crecy-research"). Only the battlefield's units wear 1346 kit (the coat of plates and mail,
  padded aketons, Genoese crossbows without pavises); the team builder's England and France are
  still c.1415. Still left out: the 1346 pay is not in the purse. The Calais muster roll (Todd,
  after the 1346 roll) has an earl at 6s 8d a day, a banneret 4s, a knight 2s, an esquire 12d, a
  mounted archer or hobelar 6d, a foot archer 3d and a Welsh spearman 2d; no French daily gages
  under Philip VI, no Genoese pay per man, and no sterling-tournois rate for 1346 were found. The
  battle: the bank plays as an earth bank (the rules have no edge that horses cannot cross, so it
  slows the French rather than stopping their horse); which way the French came into the valley is
  our reading of Preston, whose chapter was not read; the terraces on the English slope are from
  an unsourced guide; the English guns (about 100 ribalds under the carts, by Sumption) are not
  on the field; the Genoese are 6,000 by Villani and Sumption, against Schnerb's doubt of about
  2,000; the battle is cut at 21:00, where Knighton has the charges go on to midnight; no
  capture rule keeps prisoners near none while the Oriflamme was up; the fight on 27 August in
  the fog, against the late levies of Rouen and Beauvais, is not played; Livingston's site (2015),
  about 5 km south by Domvast, is a place on the map but not a battlefield; Wadicourt, the
  windmill and the ford have only approximate coordinates, and the 1346 coast, forest edge and
  roads are drawn by hand.
- **Dornach, the Swiss and the Landsknechte, first cut.** The medieval era runs to c.1500 for
  the Swabian War: the Dornach campaign map and battlefield, the ossuary crania as a bone-evidence
  table (Cooper 2010: 417 skull wounds by kind and side, the region of each our tally from her
  catalogue), a Dornach gameplay table (Towton's body, the skulls' left and right), and the Swiss
  Confederates and the Swabian League's Landsknechte as armies (project docs "dornach-research",
  "dornach-wounds-research"). Still left out: no Swiss pay for 1499 (papal pay of 1485 stands in;
  the Swiss and Rhenish gulden taken as equal), no prices for pikes, halberds, handguns or armour,
  St. Gallen prices for the rest, no ransom sums, no name counts (the names are our reading), no
  Landsknecht ages; the halberd and the handgun are their own weapons, with design-estimate figures (no wound count separates them); the ranks
  are the medieval ladder, not Hauptmann, Venner and Rottmeister. The battle: the imperial army's
  strength is 10,000 to 16,000 by source and its split among its parts is ours, the Ramstel and
  Blood Hill are not located, when the Welsche Garde and the Bernese main body came in is our
  reading, and the field does not play the camp's surprise or the rout over the Birs (in
  self-play the Swiss lose more men).
- **Portugal and Castile, first cut.** Two medieval armies for the Aljubarrota campaign
  (project docs "iberia1385-research", "aljubarrota-research"), its 1 km map and its battlefield,
  and the São Jorge ossuary as a bone-evidence table. Still left out: no Portuguese soldier's pay
  for 1383-85 was found (a blacksmith's day of 1380 stands in, and Portuguese prices are turned
  into 1380 money by the silver mark, the libra having lost two-thirds of its silver in 1384-85);
  Castile's day is a crossbowman's of 1338; no food, lodging, mule, sword or mail-coat prices for
  either kingdom in 1370-1400; Portugal's service ages are borrowed from 1468; no Castilian women
  recorded; the replacements' waits are guesses; no Galician, Catalan or Gascon tongue
  (Portuguese and French stand in); the ranks are the medieval ladder, not the Constable's,
  anadel's or almocadén's. The battle: Jardoeira, the first position and Chão da Feira have no
  coordinates; which valley is the Vale da Mata, which way the ginetes went and the Castilian
  wings' sides are our reading; the 52 cuts and stab wounds in the ossuary are not located by
  bone in what was published (its table is the 58 leg fractures only), and the paper's table of
  bone by side was not seen; the field plays the attack and not the rout and pursuit, where
  most of the Castilians died.
- **Tongues by place, first cut.** A map place can list its people's tongues (main first) and
  the map keeps a default (one or a list); the nearest place within `place_km` decides.
  Places set so far (project doc "tongues-research"): Serbia 1915 (38 towns), Calais and Guînes
  (English, Flemish, French), Olivenza and Elvas (Portuguese), Balaklava (Greek) and the Tatar
  villages by Sevastopol, Sidon's Franks, Visby's Low German, Grozny (Russian and Chechen), Tan Canh
  and Khe Sanh village (Vietnamese), Pashto in the Pech and Kamdesh valleys, Picard round Mons and
  Walloon at Binche, Chinese at Gia Hoi, and the Lakota, Cheyenne and Arapaho with the Plains sign
  language at Fort Phil Kearny. The map defaults: Picard and French at Crécy, Agincourt (its
  Norman towns French, standing in for Norman), Beaumont-Hamel and Mons, Portuguese at
  Aljubarrota, German at Dornach, Arabic at Jacob's Ford and Snipe (the coast's Bedouin), and
  Albanian on the Serbia map where no town names its own. Still left out: the Crow (towards the Bighorn, off the map), the
  Mohawk (the Grand River, off the Lundy's Lane map), German among the Niagara Mennonites (no source
  it was still spoken), Gujari in Kamdesh's herders' hamlets (none named on the map), Norman in the Caux and on the
  Seine (French stands in); the Picard and Walloon line at Binche is our reading,
  and Gia Hoi's Chinese in 1968 has no source for its size; Grozny's districts and Visby's German share are not sourced, nor Vietnamese in
  the highland district towns (inference); the Kosovo and Macedonian shares are from before the
  killings and flight of 1912-13, which made the towns more Serbian and Slavic by 1915 by an
  unknown amount; one tongue list a place, no shares within it.
- **Tongues, first cut.** Own tongue, others by army, bands, related tongues, talk caps, words
  across tongues, passing, phrase books, capture and escape, learning by use, lessons and living
  among speakers. Still left out: the shares of who spoke what are estimates throughout (no muster
  counts by tongue were found); the Thirty Years' War's camp German is inferred, not sourced, and
  the King's German Legion's language of command, Crimean interpreters, Peninsula Spanish among the
  British rank and file and interpreters' pay before 1990 were not found; a team hires one
  interpreter at a time, for a season, at an estimated wage before 1990 (Iraqi rates from $600 a
  month in 2005 set the modern one), with no Python mirror of the hire; he forages and talks for a
  force on the travel map, but the field map does not use him; dialects (Dari against Waziri, Flemish against French) are not told apart; the field map's
  orders do not yet check a shared tongue between a leader and a mixed unit; and reading a foreign
  hand is left to Letters and the GM.
- **Period money, first cut.** Every page shows money in the man's army's coin first, then Days;
  the rule book's money chapter gives the rules, and each era's Day, pay by rank and price list
  are in its period book (or the Rules' Other periods); 13 more
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
  climbing under fire and cavalry fall rates were not found; each travel-map ford now has its own depth and
  current (fixed by its place within its water's span, which are estimates, as are the horses'
  drowning chances; the Kabul River's 46 men and 13 horses is the one anchor), and its water is as
  cold as the week's air (no river temperatures were found); baggage wagons are stopped by a ford deeper than 2 ft 4 in on
  maps before 1914 (later the wagons type stands for tanks and lorries, which have no fording depth
  of their own yet), a map may set a ford's own depth and current but none does yet (no sourced
  depths for the fords on the maps), and only a mounted force's horses can drown; a fall's death is a critical head wound for the GM to rule on; and the pursuit on the
  field map (units.yaml aftermath.pursuit) takes its killed and prisoners from the units' men,
  but its shares are the research's ranges, not counts, the Python self-play does not apply it,
  and no named man runs his own chase from it.
- **Prisoners, first cut.** Capture, captivity by era and situation, release, escape, death,
  ransom, parole and service. Still left out: the release chances, escape modifiers and capture
  bands are calibrations, not figures (the death hazards are worked from the sourced totals); the
  1743, 1759 and 1780 cartels' tariffs were not found, nor Napoleonic parole-breakers' numbers,
  WWI deaths in Russian hands or the Plains nations' adoption of captives (deliberately left
  unnumbered); the cartels' exchange values are shown but not traded between armies (a release roll stands for
  them); the team now keeps captives of its own (keep, escape, ransom, exchange one for one, parole,
  release and questioning), and the field map's pursuit offers its prisoners to the team when the
  team's side chased (taking any other is the GM's word); the escape and keep figures are estimates, and the questioning results
  are design choices; and a man's captivity does not touch the travel map.
- **Strain, first cut.** Strain and Toll, Nerve checks, results by era name, treatment, rotation
  and homecoming, lasting-effect notes. Still left out: the calibration rests on Appel and Glass
  and Jones (Appel and Beebe 1946 and Swank and Marchand 1946 were not read in the original); no
  figures before 1850 (the medieval, Thirty Years' War and Crimean rates are the same rules, not
  data); cohesion, a trusted leader, a replacement and being on the move change a combat day's
  Strain (the research's quarter and half), and a leader killed now strikes each of his men (twice
  over for a trusted one: a design estimate), and "trusted" is a Command of 60, not a record of how he led; the field map's units have
  no Strain (their morale is their own), and its heroes take only the fight's when they come back
  to the roller; treatment away from the force is counted off on the travel map, but the roller and field map do not yet know he is away; and the Plains nations' homecoming is
  deliberately abstract.
- **Loads, first cut.** Load orders by era, bands by body weight and Strength, march pace and
  fatigue, blisters, Dodge and the run, dropped and lost packs. What a man buys now weighs
  (data/weights.yaml: sourced weights where found, the rest by name pattern and category
  estimates), and so does his coin; pack animals and carts bought from the price list carry kit off
  him, wheels slow the force off the road and in mud, and fodder or fuel is paid nightly where the
  army does not feed it. Still left out: kit he started with weighs only as his era's orders, not
  item by item; sourced transport prices are now on the price lists where found (a medieval cart and ox, Spanish
  mules for the Crimea, Union and Confederate mules, a horse at Bent's Fort, a Ford ambulance, a
  Japanese army remount, the Marines' Korean packhorse), but no wagon is priced in any era, nor any
  donkey or camel, nor anything for the Thirty Years' War, the Latin East or the Baltic (the US
  Quartermaster's price lists of 1861-76 and 1920 are the best leads);
  an animal that goes short of fodder is only logged; a force's load is its average man's, with no armour for its rank and file; the band steps,
  blister rule and the hardening of feet are design choices; the Plains nations' loads and most
  medieval and 17th-century body weights are estimates; the field map's units do not carry loads; and the terrain's extra
  cost to a loaded man (Pandolf's terrain factors) is left to the map's existing going.
- **Ageing, first cut.** Decline, maturity, Wear and the Worn Out check. Still left out: the
  decline dice are design choices scaled to the physiology (no game-scale figures exist); the best
  sources for British invaliding by age (Tulloch's tables, 1838-53; Nielsen's Chelsea
  applicants) and for breakdown by age in WWII (Stouffer vol. II; Beebe and Appel) were not read;
  enlistment ages by army now bound a new man's age, with boys under age and older recruits
  (found out at 10% a season: an estimate, as are the shares but the Union's tenth under 18 and
  Britain's WWI boys), and older recruits take twice the Wear (the Civil War's disease odds, not
  a measure of wear itself); the Thirty Years' War's limits are borrowed, the Plains nations have
  none, and the Python self-play does not send a boy home; Presence rises with promotion by a
  design estimate (no source); followers and men without a sheet do not age; age does not count in a
  fight beyond the characteristics it has changed.
- **Experience, first cut.** Skills used well are ticked (job checks, hits, parries and
  dodges, first aid, foraging, nursing, Stealth and Watch at a surprise) and roll to rise at
  End of season; days served add a career term (`docs/team.md`, *Experience*). Still left out:
  - the field map's battles tick a hero's weapon skill for his hits, but not his parries or the
    first aid he gives;
  - characteristics change in play only by ageing, wounds and the Presence a promotion adds: no
    training raises Strength or Endurance;
- **Training, first cut.** Masters for hire, teammates and drill in camp tick a skill. Still left
  out: the masters' fees are estimates apart from riding lessons (London, 1879), and a master's
  skill is always 60; drill ticks only the skill of the weapon a man
  carries in the roller, and only for named men; courses (data/training.yaml `courses`) are a
  set of examples with estimated gains and fees, the man is not missing from the team while away,
  and an apprenticeship is a year of its seven.
- **Austria-Hungary and Bulgaria in the First World War, first cut.** Both on the team builder,
  as Russia and Serbia are (project doc "central-armies-research"). Still left out: no wound table
  of their own (none by region or cause was found for either); rank pay for neither (Austria-
  Hungary's Day is a private's 36 Heller from one secondary source, Bulgaria's the poilu's, an
  estimate); prices only for Vienna's bread, meat, wine and beer in 1914, none for Bulgaria; the
  wartime Landsturm ages (the 50-55 often given is the war-labour law's) and the 1912 Wehrgesetz's
  terms unconfirmed; the Bulgarian army's tongues (Bulgarian, Turkish; Pomaks and Macedonians as
  Bulgarian) and its name for shell shock are estimates; Bulgarians in Entente hands have no
  death rate; an Austro-Hungarian's first name, surname and tongue are rolled apart, so a Polish name may come with a Hungarian tongue (no nationality is rolled first); and the Ottoman army is not an army here.
- **Russia and Serbia in the First World War, first cut.** Both armies are on the team builder
  (and so the roller, travel and field pages): names, careers, women, money, pay, prices,
  prisoners, tongues, enlistment ages and replacements (project doc "eastern-armies-research").
  Still left out: both fight on the shared WWI wound table (a Petrograd hospital series and a 1915
  Kiev Red Cross report count only survivors, and nothing was found for Serbia); no Serbian pay at
  any rank (the Day is the French poilu's, the dinar at par with the franc), and the Russian
  corporal's pay is an estimate; Russian stoppages (kit was issued free) are not modelled, so the
  era's kept share applies; prices are a handful for Russia (bread, meat, shoes, a suit, an army
  horse) and none for Serbia, and every era row is offered to both, as to every army; the
  prisoner hazards are worked from totals that conflict (Russians 8% or 20%) or lack a count of
  those taken (Austro-Hungarians in Serbian hands); the Russian army's tongues are the 1897
  census's (no muster counts); Serbia's boys of 1915 and old men of the third ban use the era's
  under- and over-age shares, not their own; the Russian and Serbian names for shell shock are not
  shown (the era's are British); and no Russian campaign map or battlefield.
- **Women under arms, first cut.** Women serve as cantinières with the French in the Crimea, in the
  Civil War (disguised in the ranks, openly as nurses and vivandières), the Soviet Union of
  1941-45, Vietnam (the ARVN, the North and the Viet Cong) and the later wars (the US, Britain and
  Russia); and now in the earlier eras and other roles: townswomen at medieval sieges, the Thirty
  Years' War's camp women, French vivandières, British soldiers' wives and the Continental Army's
  women (Margaret Corbin at the guns, Deborah Sampson in the line), nurses (Crimea, Civil War, both
  world wars, Korea, Vietnam), auxiliaries (WAAC and QMAAC, ATS and WAC), the Female Engagement
  Teams, and the Lakota and Cheyenne women who fought. A career may have its own share. Still left
  out: no women nurses for the Confederacy or Russia at Sevastopol (not
  in the research); the career shares of 100% are design choices (men nursed and sutled too); nurses and auxiliaries draw their army's recorded rates (project doc "prices-nurses-research"),
  but Nightingale's nurses' pay rests on an uncited figure and is not used (they draw a private's),
  the Commonwealth's WWII nurses take the American rate, and the Russian Sisters of Mercy (120 at
  Sevastopol, 17 dead) are not yet a career; their term events are written from the research, not
  rolled from records; and the Viet Cong's and the North's women have no reliable share, so they
  are chosen, never rolled.

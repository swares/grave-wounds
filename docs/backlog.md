# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Playtests and release

Work that is not a rule or a page. Most of the detail is kept elsewhere; this section says where,
so that the backlog is the one place to start. Items in a project doc are in the Claude project,
not this repository.

- **Ways to play: where each stands** (reviewed 7 November 2026; revisit after the first table playtest).
  More ways to play reach more people. Five are aimed at:

  | Way to play | Support | What works | The main gap |
  | --- | --- | --- | --- |
  | Online: commander against commander (simulation) | Not yet | Two people on one screen, each side under its own commander; the commander against itself to check a battlefield | The field and travel maps are not online, so two commanders cannot play from two computers |
  | Online: you against the commander (solo) | Strong | The enemy commander on the field map (sees only what its units see, reserves, guns, objectives), Beat history and its scorecard, the GM's script on the roller, the rules' chapter on playing alone, the commander running the travel map's day | Runs in the browser with no connection needed; the commander does not yet notice some campaign events |
  | Online: a GM and his party (VTT) | First cut | The GM hosts from the roller or the campaign console; players join by room code and see their men, the public news and their fights, propose orders, and see only what their side has seen | The field and travel maps are not shared online; no TURN relay for strict networks; no voice or chat (groups bring their own); tested only with scripted players |
  | At the table: an RPG with a GM | Good on paper, untested | The rule book and five period books, the team builder's sheets, the roller as the GM's aid, the council card, the tables | The 309-page tables PDF is a reference, not a table booklet; making a man by hand is not checked for pencil and dice; never played at a table |
  | At the table: print-and-play modules | One module | Ferrybridge (the playtest packet 0.2.2): characters, map, counters, roster and reference, laid out for printing on both sides | The only module, and not yet played; the plan for more is under *Print-and-play modules* |

  What would widen the reach most, in order: the Ferrybridge playtest (it tests both table rows);
  the field map online (opens commander against commander and the field for a GM's party, building on the
  roller's and console's rooms); a TURN relay before strangers are asked to play online. Solo is the
  strongest today, which suits itch.io's Solo RPG category.
- **Table playtests.** None has been recorded: every result so far is self-play. The four to run
  are in the README's *Next steps*, and `design.md` has the disease numbers to try over a few weeks
  of camp. The playability review (project doc `claude/playability-review.md`) ranks this first.
- **The playtest packet, version 0.2** (`dist/playtest-packet.html`, built by `gravewounds/playtest.py`
  from `templates/playtest/packet.md`). Wars of the Roses, four pregenerated men with camp roles, a
  fight at the Aire crossing and a week in camp, played on the roller or on paper, with feedback by
  email. Version 0.2 adds the kit to play it on paper, at the back: a one-page quick reference, a hex map
  of the ford printed true to size (2 yards a hex, with an approach track for the enemy's first 18 hexes),
  counters to cut out (the nine men, and Down, Stopped, Bound, Prisoner, Bleed, Aimed, Fate and Round
  markers), the GM's roster of Clifford's five with Blood to tick off, and a blank character sheet. The
  ford's rule (the river too deep elsewhere; advance only in the ford) is the scenario's own. Not yet run by people. Its scenario pages are ours and untested at the table; the weekly
  rules are simplified for paper (the flux alone, at Endurance 50, and a fixed week's weather). Project
  doc *Grave Wounds: playtest packet outline* holds the three rounds of testing, the publishing path
  and the formats to consider (itch.io, Foundry VTT, desktop, Android).
- **Phones.** The roller, team builder and campaign console have a phone layout with full-size taps, checked in a phone-sized browser (`tools/campaign/phone.py`), not yet on a real phone. The field and travel maps have full-size taps and zoom (−, +, Fit and two-finger pinch; `templates/mapzoom.js`). On a phone the field page has an order bar at the foot of the screen for the selected unit (◀ ▶ through the units, Show, More, Turn left and right, Undo, and Start the battle / Next). Zoomed in, the field map follows the fighting: after each exchange it scrolls to the units in contact nearest the view (a "follow the fighting" tick under the map turns it off). On a phone the field page is in four tabs (Map, Battle, Units, Story), with the phase or latest message under them. The travel map is in four tabs too (Map, Forces, Camp, Day), with a bar for the selected force and the clock. Not done: a watch mode for spectators on a phone.
- **Print-and-play modules.** More ways to play reach more people: the plan is to publish print-and-play
  adventures like the old modules, each a scenario with its pregenerated men, map, counters, roster, the
  tables it needs and a quick reference, playable on paper or on the pages. Ferrybridge (the playtest
  packet) is the first. Still to come: a short table booklet of the common weapons and armour (the
  packet carries only its own fight's), Ask the dice on the printed tables, paper rules for making a man
  without the team builder, and further modules; field battles, travel and the campaign on paper are
  further off, since the pages do their arithmetic. The plan, if the Ferrybridge playtest goes well:
  - **Fix the shared parts first.** What the playtest finds slow or unclear on paper is fixed in what every
    module shares (the quick reference, the table booklet, the counters and map style) before it is copied.
  - **Skirmish modules next**, like Ferrybridge: a small action at the edge of a battle already researched,
    with four pregenerated men, a hex map, counters, the enemy's roster and a quick reference. One or two
    more, from other periods, so the series reaches medieval, Napoleonic and modern players (candidates:
    the baggage raid at Agincourt, a breach at Badajoz, a patrol on Tumbledown, the ditch at Dornach).
    Before the second, `gravewounds/playtest.py` becomes a module generator: each module a data file
    (men, enemies, map, ford-style local rules) and its own pages, rather than a copy of Ferrybridge's code.
  - **Then a battle module:** a battle such as Towton or Albuera on paper, with unit counters, a printed
    battlefield and paper rules for formations, morale and losses, which the field page now works out.
    Start small, a wing or a few units a side, to learn whether battle-scale play is quick enough at a table.
- **Comments from visitors.** A private Google Form, linked from the signup block, the Rules and books, and the packet. There is no public comment section yet.
- **Feedback on the core rules.** The review's next step after a table playtest: post the core
  rules, not the whole book, to r/RPGdesign, BRP Central and the Hârn community, then the wider
  wargame, solo and video-game audiences. Check each community's self-promotion rules first.
- **Crowdfunding preparation, paused on purpose** (November 2026). The human work ledger, the
  mailing-list signup, Kickstarter planning and the title art. The state and to-do list are in
  project doc `claude/human-ledger-handoff.md`, with the evidence in
  `claude/human-ledger-evidence.md`.
  The visit counter is in (Cloudflare Web Analytics, on the start page, How to play and the books; see
  `templates/privacy.html`). The news signup (`templates/signup.html`) is on the start page, under a battle's Beat history result and at the end of How to play, posting straight to Kit with no script; the books and the printed tables link to it.
- **The email to The Fat Electrician: yet to send.** The draft, the one-page overview and the World
  Wars book copy were made on 25 October 2026. Before sending, rebuild the book from current main
  and fill in its share link. Then one follow-up after about two weeks.
- **Battlefield source disputes** (`docs/battlefield-open-questions.md`). Each is a dispute no
  official history settles, or a point resting on one report; the data stands until better
  evidence turns up. New ones go there, not here.
- **The book pictures' licences.** None of the 68 picture slots in `data/pictures/` has its file
  yet, and each licence must be checked before its picture goes in.
- **Sources and Methods: the infringement check.** Before release, check every source for what may
  be reprinted and what must be cited or re-derived. The play books can ship without waiting for it.

## Deferred work

- **Camp roles, first cut** (`data/council.yaml`; docs/campaign.md, *The council*). Roles and the
  evening council are on the campaign page. Still left out: the travel map played on its own has no
  council and does not stop for one, the council records decisions by word only (its orders and
  settings are still given in the usual places), and only human play can say if it is worth the
  table's time.
- **Campaign frames for the other books.** The Medieval Wars has four (`templates/books/medieval/frames.md`).
  The other four books have none, and each frame needs its own sourcing.
- **Visby's evidence table is still a placeholder** (`data/tables/visby-1361-evidence.yaml`). Its
  weights are fitted to published summaries. Replace them with Ingelmark's per-bone counts
  (Thordeman, *Armour from the Battle of Wisby 1361*, vol. I, ch. IV, p. 149ff.), which have not
  been read. The adjusted table derives from it, so it needs refitting too. A library copy, or the
  Chivalry Bookshelf reprint of 2001, is the likeliest route.
- **Overfitting to the benchmark.** The self-play benchmark is also what gets tuned against. Track
  the match rate separately on the battlefields added most recently, which were tuned least. If it
  stays near the overall rate, the gains are real.

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
  pages do (a campaign's slot and save file carry every one of those keys, so nothing is lost; the
  pages simply share them). The Strain checks on the march and at a ford now take the day's dice
  (1 November 2026; before, the browser's own, which mattered only to a seeded day run with no page).
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
  room codes through a small Cloudflare Worker (`worker/`, deployed), others pass codes by hand. Still left out: a
  TURN relay for strict networks, room codes for the roller's own Play online,
  rejoining without passing a new link and reply by hand (a lost player is invited again to the
  same seat, his page keeping his last screen; a blinked connection mends itself), sending changes of the whole picture (the panels that changed go as their changed tags, but a turn that lights every hex still sends them all), a player's
  works and the other panels from his page (first aid he gives, on his side's turn), and the field
  and travel pages online.
- **Fog of war on the travel map, third cut** (`docs/travel.md`, `docs/fog-of-war-research.md`).
  A side sees enemy forces within a distance in km (3 on foot, 8 mounted, 2 with wagons; cut by the
  weather, dusk and the dark; outposts find any enemy within 1 km; woods and towns hide a force
  beyond that) and remembers where it last saw them; a player's map online shows only that, and the
  GM's travel map can show any side's view. By period: a map lists the sides with aircraft up
  (by day in fair or overcast weather they see every enemy force in the open on the map) and the
  sides' night sights (a thermal sees 3 km in the dark, goggles 1.5, a Starlight scope 1), set
  battle by battle on the 27 20th-century maps (project doc fog-of-war-period-research). Still
  left out: campfires at night, dust, height, field glasses (by day the ground limits sight, not
  the eye), scouting orders and patrols, and the delay of reports; the weather factor (5), the
  flying weather and several distances are judgments, not sourced, and several maps' air notes
  are our reading.
- **Lethality, first cut.** Gritty | Standard | Heroic for player characters (wounds.yaml
  lethality): fate a season, Blood and the stop check, on every page. Fate now saves a man from
  drowning (the roller's **Spend fate: pulled out**; a ford on the travel map spends it at once) and
  lowers a fall's wound as a blow's (1 November 2026), and `python3 -m gravewounds team --lethality`
  sets the CLI's sheets. Still left out: the roller offers fate only on the wound just applied (not
  on old wounds or a later pain check). By design, not a gap: the field map's heroes, like every
  page that runs on its own, spend fate only to save a life, so never on a stop check (design.md);
  self-play has no player characters, so it needs no setting.
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
  objectives (phase lines across the front, feints, scouting; no battlefield marks a second;
  plans give phase lines, pinning, envelopments, reserves and withdrawals on a trigger where a
  battlefield's plan says so: units.md, *Plans*; six battlefields have one so far; a procedural planner writes
  the commander's own plan for battles with no account, once, from five templates: units.md,
  *The procedural planner*; measured one side at a time, a plan helps holding sides (14 better, 5 worse of 43);
  the attacks it made worse were traced and fixed (the plan left units in reserve alone), which also
  took away most attacking gains: when a plan should send the reserve in is open (by the odds was
  tried and refuted on open ground, tools/selfplay/odds.js: it likely turns on the ground; on that open ground a plan
  wins no more than no plan, and less at even odds, a figure the planner should not make worse; by
  whether the enemy holds works was tried too and not kept: its gains were on the battlefields it
  was drawn from, units.md);
  pinning from the medium band was tried and not kept (no modern side gained, medieval storms
  lost); planning again when a plan fails was tried and not kept (5 sides better, 7 worse);
  feints and scouting were measured first (a planner that sees everything, and Godinot's feint at
  Albuera) and not built: units.md; the planner work pauses here); ladders only where the GM or a battlefield marks them (the Great Redan's ladder parties put them down into its deep ditch: units.md, *A deep ditch*). It does
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
  it is marked by battlefield where a source gives one. On 12 runs of the 50 battlefields, planner off, 490 of 600 runs now match the battle as
  fought (Mojkovac and Topolčani added; reliability, 423 to 422; a bayonet front against horse,
  Albuera 7 to 12, Lundy's Lane 1 to 0; a closing volley before a charge home, both Redans +1;
  Cassino's sangars, the Monastery 0 to 3; trenches against shellfire at a fifth of lying, after
  Evans, and Snipe's six-pounders with no HE round, 431 to 435: Snipe 0 to 3, Babuna 6 to 10, the
  Monastery 3 to 6, Pork Chop 10 to 12, Mojkovac 11 to 12, but Tumbledown 8 to 3 and 73 Easting 4
  to 0; project doc "snipe-study"; proof armour takes no harm, a T-72's frontal hit neither
  immobilising an M1A1 nor putting its gun out, 435 to 443: 73 Easting 0 to 8; a cornered unit surrenders only to as many men as it has, 443
  to 449: Tumbledown 3 to 6, Dornach 7 to 10, Chipyong-ni 10 to 12, Agincourt and Mogadishu -1; plans, Snipe's evening
  German tanks pinning from range, 449 to 452: Snipe 3 to 6; plans for 73 Easting, Goose Green, Mons and the June Redan,
  452 to 462: 73 Easting 8 to 11, Goose Green 1 to 3, Mons 10 to 12, the June Redan 7 to 10; Jacob's Ford's storming
  column as four parties a breach wide, 462 to 470: Jacob's Ford 0 to 8; the Germans' posts on the massif held
  in May, 470 to 474: the Poles 0 to 4; Badajoz and Burgos added; held up at a gap in works a formed unit
  narrows further, 489 to 488 of 600: Aljubarrota 10 to 11, Jacob's Ford 8 to 6, Sidon's wall fought for but its
  attackers still losing under 1%; the gap rule's floor of 3 hexes, 488 to 490: Jacob's Ford 6 to 8). Still behind: Snipe 6 of 12 (the evening Italian tanks
  have no plan: the account names only the Germans drawing back; not traced since); Tumbledown 6 of 12, Left Flank walking
  into contact upright in the dark and broken at once by a handful at its flank (the flank check
  counts three men as a flanking force); Lundy's Lane 0, studied (project doc "lundys-lane-study"):
  Ripley's brigade stops 140 m off the guns and trades fire ("a shooter never charges"); made to
  storm them, it breaks 7 men down to the per-man rule for losing the exchange, and capping that
  rule by share cost Agincourt more than it gained. A closing volley before a charge home is
  now in (missile.closing_volley), but with the storm order it still gives 1 of 12: Ripley's
  brigade still loses the melee by the per-man rule. A planned charge (3 November 2026): `envelop` with
  `charge: true`, and Lundy's Lane's plan sends Ripley's brigade round below the crest and at the
  guns. Ripley now takes the guns (traced: about 155) and holds the crest against Hercules Scott's
  column for some 75 exchanges, then breaks (about 230) and is cut down in the rout: 0 to 1 of 12,
  American losses 58% to 63% (about 31% in 1814). Holding the crest once taken, looked at
  (3 November 2026): letting an attacker on the objective it took count as holding (morale.posture)
  changed nothing (12 runs: 1 of 12, the same runs): posture needs a bunker, cover to lie in or
  works, and the crest is open ground, for the British on it too. Ripley holds some 70 exchanges
  under Hercules Scott's fire, falls past a quarter down (900 to 626), checks every exchange and
  breaks at 228. What held it in 1814 is not on the map: the dark at point blank, and the American guns
  brought up among the captured British ones. (An earlier note here had the captured guns turned on
  their owners: no source says so; corrected.) Closed with no change (asked and answered). The
  American guns (3 November 2026): Hindman's six guns (Biddle's and Ritchie's companies) come up
  on the crest once the British guns are taken (a phase on `when: {broken}`, new; Wikipedia,
  HistoryNet). Traced: shot to pieces by Hercules Scott's column within 20 exchanges; Ripley holds
  some 20 exchanges longer. Still 1 of 12 in 12 local runs (asked and answered: kept as sourced).
- **Self-play against the battles as fought, first review** (`docs/selfplay-review.md`). Every
  battlefield was played with the commander on both sides and set against what happened; what has
  been changed since, and what was measured and not built, is in the review. To do, from the
  review and its traces:
  - 73 Easting: the fight at the crest is now the plan's (11 of 12); the troop still loses about 8%
    against none in fact;
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
  - the American rush on the guns at Lundy's Lane (the guns still hold);
  - Point 593: the paratroops now hold sangars and bunkers (the Monastery 0 to 3 of 12); May's
    counter-attacks are on the map with strengths of our own (none sourced); with the posts held,
    the Poles are thrown off in 4 of 12. The sourced Polish withdrawals (Kresowa 13:10, the 1st
    Battalion 15:00, Anders's order at 14:00) are not on the map: a shaken unit does not obey a
    withdraw order, and most are shaken by then;
  - Goose Green (3 of 12 with its plan: the trench platoons break, but the Argentine machine-gun
    nest, 10 men, holds the crest, while 2 Para's companies flee at about a quarter to a third
    down, the constant morale drain; 1 of 12 once the officers were named, since the plan left D
    Company free and the commander sent it over the open grass to the trenches at first light,
    where Neame went down and it broke in 11 of 12 runs; D now waits with A and B until the noon
    phase, as Wikipedia has it "temporarily halted" between them (4 November 2026): 1 to 7 of 12,
    no other field moved. Holding Jones's headquarters until about 10:00 as well, an estimate,
    gave 4 of 12 over 12 local runs and was left out), Keating (traced: not the bounds;
    and the Americans retaking the outpost, researched but with no clock times in the sources) and
    Wanat (no single fix; within the runs' spread);
  - Hue: the Marines' rockets (3.5-inch, LAW, 106), recoilless rifles and gas (no sourced counts).
    Traced 4 November 2026 (3 of 12): the North Vietnamese mortars are not the cause (2 tubes: 2 of
    12; none: 3, the Marine losses unchanged at 26%); the 4-6 February field's 3,301 exchanges were
    cut at self_play.most (1,200), 20 hours in, so the Marines had to take the headquarters two days
    early, their companies checking morale every minute of it and failing at 10-30% down. The field
    is now 6 February alone, 09:50 (H Company halted before the headquarters, 2/5's chronology) to
    the flag a little past 14:00 (Nolan), 256 exchanges, with the hospital drawn west of the
    headquarters (the order the Marines came to them; drawn the other way, G Company's rout ran past
    the headquarters' garrison and was cut to pieces). It did not move Hue (2 of 12 over 12 local
    runs, Marine losses 31% against a few dozen in the sources): H Company storms a bunkered
    garrison nothing has suppressed, loses a quarter to a third and flees, the tanks never breaking
    it. The sources credit an 81 mm mission with E-8 gas for silencing the weapons and getting H
    into the compound, and there is no gas rule: next;
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
- **Grozny, traced 4 November 2026 (4 of 12).** After dark the Chechens knew of no Russian unit
  all night: the sight rule sees into a building only at its edge, and the 1st Battalion's middle
  and front ends were inside the station, so it was never seen, lit or not; the Chechen attackers
  stood at the objective's edge. An attacking side now knows where the enemy on its objective
  stands (commander.objective). The station is also lit all battle by the burning train and oil
  tank car of the Novaya Gazeta account (lit; where and the radii ours). 12 local runs: 4 to 8 of
  12 (7 without the light); full benchmark 4 to 8. Across every field a net 15 more runs as fought: Hue 5 to 8, the Cassino Poles 4 to 7, Babuna, Burgos, Ciudad Rodrigo, Mogadishu and the Monastery up 2, Chipyong and Keating up 1; Badajoz and Tumbledown down 2, Goose Green, Snipe and Topolčani down 1. Checked on 24 fresh seeds (13-36) with and without the rule: Badajoz 18 and 16 British wins, Tumbledown 8 and 10, so both drops are the dice's spread, not the rule (4 November 2026). The battalion now breaks within about half an hour, where it held the
  station into the next evening: the fight is short, not overnight. Six fields run past
  self_play.most (1,200): Bougainville (ends 4,171), Cassino town (10,801), Dak To (5,131),
  Grozny (1,531), Pork Chop (1,496) and X-Ray (1,556). Looked at 4 November 2026: in the five
  besides Grozny the result as fought is settled within the first 1,200 exchanges (Bougainville,
  Dak To and Pork Chop 12 of 12, X-Ray 11, Cassino town 12 of 12 locally under report.py's own count, though every run ends with one side gone, well before the cap, rather than in the stalemate), so they are left as they are, the
  cut documented in each field's units.md entry and by self_play.most; Grozny's breakout at
  1,531 is still past it (its fight is too short as it stands, above).
- **Grozny's short fight, traced 4 November 2026.** The 4 Chechen mortar tubes decide it, and no
  source supports them: the maker gives none, and neither the Novaya Gazeta account nor Russian
  Wikipedia's (which has fire from upper floors at vehicles that could not manoeuvre in the narrow
  streets) mentions mortars at the station. Through the roof they put about 34 men down in the first
  quarter hour, keep the battalion pinned and hit Khmelevsky; the Chechen fighters close, Klupov
  falls and the battalion breaks within half an hour (Chechens 8 of 12). Without them the Chechen
  attack on the station is beaten (Russians 8 of 12, 12 local runs). Neither is the history, in
  which the battalion held all night and was destroyed breaking out on 1 January (past
  self_play.most). Left as it is, by choice; a sourced account of what struck the battalion in the
  station overnight (Oliker's RAND study, Grau) would settle the mortars.
- **Wanat, traced 4 November 2026 (5 of 12).** In the losing runs the fighters took Topside and the
  run stopped at exchange 244, three after the second relief force (3rd Platoon, A Company and the
  scouts) came on at the map's south edge, more than 10 hexes from the post, so the post counted as
  secured. Holding the objective now ends a run only once the last phase is self_play.after_phases
  old, as the run's length already allowed. Full benchmark: Wanat 5 to 9, the June Redan 11 to 12,
  no field down. Wanat's American losses rose from 54% to 69%, against about 40% in the account (9
  killed and 27 wounded of about a hundred): the relief forces now fight, and lose men, where the
  run used to end.
- **Wanat's American losses, traced 4 November 2026** (69% against about 40% in the account, after
  the held stop above). The Afghan platoon on the base's west side (24 men; the account has 4
  wounded) breaks in the first minutes and, a broken unit running straight back from its facing,
  runs east across the base past the post into the fighters on the slopes: gone in 9 of 12 runs (as
  Hue's G Company before that map was redrawn). Two rout rules were measured and not built (branch
  rout-away): running straight away from the nearest enemy, net -10 on the benchmark (Wanat's
  losses 45%, but the Cassino Poles 7 to 3, Badajoz, the Monastery and Grozny down 2); running
  straight back unless that takes the unit nearer the nearest enemy, net -5 (Wanat 10 of 12 at 55%,
  but the Poles 7 to 4, the Monastery down 2: on a flipped seed the German paratroops on Point 593,
  breaking, turned from the Poles behind them, were cut down to the last man, and the Poles held
  the point at the end). Next: the Afghan platoon's position and facing from the Army's study
  (Combat Studies Institute, Wanat: Combat Action in Afghanistan, 2008), which no source reached
  gave (Wikipedia: 24 Afghans, 4 wounded; neither it nor Foreign Policy places them); the study
  was not reachable from here.
- **Cassino town, traced 4 November 2026.** Every run ended with the paratroops gone inside the
  first hour or two (German losses 66-91%), the week's stalemate never played: the barrage struck
  their ranks in the open rubble (only the middle of each front row was a cellar). Cellars under
  every hex they stand on stretched it only to about 110 exchanges: a bunker left its men 50% of
  shellfire's struck % (no `shell` of its own), worse than a trench's 20%. Bunkers at shell 10 cost
  9 runs as fought on the benchmark (Tumbledown 7 to 0: the Argentine crags all but shell-proof;
  Hue, the Poles and Goose Green down), so the cellars are their own hex work (works.yaml cellar:
  as a bunker, shell 10, an estimate; in assault.works), used only at Cassino town. 12 local runs:
  every run now ends with the New Zealanders holding Castle Hill at exchange 331, the paratroops
  about half down (35-58%), as fought. Full benchmark: only Cassino town moves (German losses 79% to 50%; still scored 12 of 12).
- **The Cassino Poles, traced 4 November 2026 (7 of 12).** In the runs the Poles win they still
  hold Point 593 at the end, and the German counter-attack parties (I./FJR 3's two from 569, the
  14th Company in the evening) mostly never fight: they come on with their phases but, on the
  holding side, have no order to go for 593. Measured on 12 local runs, none better than 7 of 12
  (branch poles-counterattacks, not merged): a German plan sending each party at 593 by an
  envelopment when its phase brings it on (6 of 12: the I./FJR 3 parties went in piecemeal, 30
  men against a Polish battalion, and were destroyed, or stood untouched); with a plan's
  envelopment whose last leg the enemy blocks counting as attacking (6 of 12: without it the
  route counted as blocked by the Poles round 593 and the unit, handed back to its holding
  stance, went to ground and stood there to the end). Still not found: why the 14th Company
  (80 men) and, in some runs, both I./FJR 3 parties still end untouched with the stance switch in.
- **Snipe, traced 4 November 2026 (5 of 12; British losses 42%, the account 72 killed and
  wounded of about 300).** Two blows. At about 07:30 (exchange 77) the long-gunned Panzers from
  the south come up on the carriers in the open middle of the hollow and knock out 21 of them in
  five exchanges, 640 to 760 m off (the account's first carrier losses come just before noon). So
  at 10:00 no carriers go out at the Bersaglieri, who cross the open almost untouched (200 to
  about 165-190: the six-pounders and riflemen hardly hurt them) and reach A Company's guns, which
  the overrun rule takes at once (19 crew). Then the 17:00 counter-attack breaks A Company's
  riflemen within four exchanges and the north-west guns after them. Measured and not built
  (branch snipe-panzers): a plan sending the long-gunned Panzers at 47th RTR, as the account has
  them ambush the 24th Armoured Brigade, made it worse, 2 of 12. Why the Bersaglieri cross unhurt
  (5 November 2026): the riflemen spent their rounds early, some 40 volleys at 400-600 m at men
  lying in the open they barely saw (seen 0.05-0.1), and were low by exchange 302. Fire discipline
  (`ammunition.hold_hidden`, a unit's `holds_fire`) is now on the three rifle companies: they fire
  only at men they see. Full benchmark: still 5 of 12, British losses 42% to 38%, the Axis's 18%
  to 30%; no other field moved. Measured and not built: the same hold for every unit (Snipe 10 of
  12 locally, but 21 runs lost as fought across the benchmark), and in the long band only (worse);
  Snipe's gain there came from the Axis infantry holding fire too, which no source gives. The
  07:30 carriers (5 November 2026): the hollow was flat open ground, and the long-gunned Panzers
  coming up from the south saw the carriers parked in its middle 740 m off, the only British
  vehicles in reach, and knocked out 16 of 22 in five exchanges, into their flank. The hollow's low
  middle is now drawn inside a narrow ring of slope (the rules have no low ground; its size is ours),
  dead ground from the flat outside: the Panzers fire at C Company's guns and 41st RTR instead, as
  the account has them go for 24th Armoured Brigade. Snipe 5 to 6 of 12 (12 runs, the benchmark's
  seeds; only Snipe's stamp moved), British losses 38% to 27% (the account 72 of about 300, 24%),
  the Axis's 30% to 27%. The 10:30 carriers (5 November 2026): the dozen Italian tanks and the
  Germans on their right, on the western ridge 590-660 m off, put every round into the carriers
  (a main gun took the nearest vehicle first) while A and C Companies' six-pounders knocked them
  out. Threat first is now the rule: a main gun takes first an enemy that fired at it the exchange
  before and could knock it out (`threat_by`), then vehicles, then the rest. The carriers come
  through 10:30 with 20 of 22. Full benchmark: Snipe 6 to 8 of 12 before the tank-crew table, 9 to
  10 with it (British losses 16% to 19%; the account 24%); no other field moved either time. Still
  left: the carriers never go out at the Bersaglieri, who break on their own; the evening attack.
- **Marks dropped at load, fixed 5 November 2026.** A field unit's `masks` and `holds_fire` were
  not copied onto the playing unit (battle.make_unit's list, makeUnit in the page), so Hue's
  Marines fought unmasked from the first gas cut. With them copied, Hue is unchanged (8 of 12,
  the same losses): the Marines were not in their own gas.
- **Tear gas, first cut** (`indirect.gas`, the `e8` kind; 4 November 2026). A CS launcher lays a
  cloud that thins and drifts as smoke does; unmasked men in it fire nothing and check Nerve or fall
  back out of it, masked men fire less (a unit's `masks`). On Hue's 6 February field: 2 to 5 of 12
  (full benchmark; Marine losses 31% to 24%, North Vietnamese 60% to 67%), no other field moved. Still left out: gas grenades thrown by the stormers, CS mortar rounds, gas
  drifting back on unmasked friends calling the launcher off, and masks on any other battlefield.
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
  - on the Great Redan battlefields, the French attack on the Malakhov (the siege guns: the
    British batteries were silent during both assaults, so they stay off; the Russian guns in
    the work, a battery either side on 18 June and the Barrack Battery on 8 September are on
    the map: 31 October 2026);
  - a deep ditch that needs ladders: done (units.md, *A deep ditch*), with the cost without
    ladders our reading, as no figures were found for how much slower it was without them.
- **Sieges and ladders: to look at** (asked 29 October 2026). Gathered from the notes above and
  below; not yet studied as one subject.
  - **Ladders** work as escalade over a wall, palisade or barred gate (units.md, *Escalade*), and
    go down into a deep ditch (*A deep ditch*: the Great Redan, both battlefields; 30 October 2026).
    Badajoz 1812, the breaches and the castle, is a battlefield (a first cut: the town falls in 5 of
    12, by the castle, as it did, but the stormers wait at the ditch rather than dying in the breaches,
    so the losses are the wrong way round: units.md). Second cut (1 November 2026): fires light the breaches, the sword blades are chevaux de frise, escalade gains a footing, the castle is the objective; the breaches hold and the castle falls in 2 of 12. Still open: the brigades never come into the fight, so Allied losses are far too low (9% against nearly half). Surveyed (claude/sieges-ladders-survey.md in
    the project): still to do, what is behind a
    breach (a drop, a retrenchment, a mine: San Sebastián, Badajoz; Jacob's Ford's burning timber
    wall), and a siege phase on the travel map. The siege guns on the Redans: done (31 October
    2026). Ladders too short: done (31 October 2026: `ladders: short`, units.md *Escalade*, and
    the hornwork of San Miguel at Burgos as a battlefield, a first cut). Building it found that
    men touching across a wall no one fights over neither fought nor shot; they now shoot, with
    no cover at the foot of a wall against men on top of it (units.md, *Who shoots*).
  - **Siege defences** (1 November 2026): done. Spare loaded muskets, things thrown down and a
    sprung mine (units.md, *Siege defences*), on Badajoz's breaches. They change little there (Allied
    losses 30% without, 29-33% with): the loss gap is how long the stormers stay at the breaches
    (storming parties break after a few losses, the brigades wait behind them; Napier counts some
    forty attacks), not what is thrown at them. Traced the same day: an 8-wide brigade could not
    pass the 5-wide flooded way before the Trinidad, and stormers stood short of the sword blades
    trading fire. Fixed: half-brigades 4 wide (data), and storming now also goes for a target at or
    a hex behind a work that blocks hand to hand (`units.at_works`); Allied losses 35% to 40%,
    nothing else moved. Re-forming broken stormers: done for Badajoz only (`reform: true`; on every
    battlefield it cost 31 of 576 runs as fought, units.md *Broken, re-forming*). Still open:
    half-brigades queued behind others.
  - **Enemy inside a work, behind its defenders** (found at Burgos, 31 October 2026): done (31
    October 2026) without a new morale rule. The light companies' gorge attack is the battlefield's
    plan (an envelopment), and bayonet-armed units that have gone round on a plan charge a flank or
    rear at any odds; the existing rear-attack rules then break the half of the 34th they strike.
  - **Deep columns at Badajoz's castle** (1 November 2026): traced further, it was not turn cost.
    The brigade turned toward the flank guns 30 hexes off behind the walls (a battery scores high as
    a threat), and inside the outwork a 5-wide, 7-deep column had no room to turn to face the
    garrison. Fixed in data: the 3rd Division's brigades in halves of about 625; the castle falls in
    4 of 12 (from 1). A unit on a route turning toward a far target: measured and not built (1
    November 2026). The rule (a unit whose route is blocked goes for the enemy across its way, not
    the best-scoring one elsewhere) changed nothing on any of the 50 battlefields, to three
    decimals (run 41361333394): after the split the 3rd Division's halves target the garrison
    themselves, and no other battlefield has the case. Branch route-blocker, not merged.
  - **The siege before the storm** is off every field map. Jacob's Ford's map starts at the
    storm (its mine, the outer wall and the days before are not played); the Redan's battlefields
    leave out the British siege guns, which were silent during both assaults.
  - **Siege phase, first cut** (2 November 2026): done on the travel map (travel.md, *Sieges*): a
    fortress place, investment, a breach clock counted in days of siege work, and no storm offered
    until the breach is practicable; Jacob's Ford's castle (4 days). Second cut (2 November 2026):
    fortress stores, and terms (summoned; answered by players or rolled; honours of war, or no
    quarter in the storm if refused after the breach). Third cut (2 November 2026): sorties (fought,
    then marked: a success undoes a day of work) and relief (unbesieged, the garrison repairs a day
    a day). Fourth cut (2 November 2026): disease in the siege lines (investing counts as a camp
    from the investment, poor hygiene with none made) and the unburied dead (flux and typhoid near a
    battle for two weeks until buried). Badajoz 1812 (2 November 2026): a second map on the Albuera
    ground, 16 March to the storm, the town a fortress of 21 days. Mines and countermines (2 November
    2026): a fortress broken by a mine is fired when dug (50% the wall comes down, else redig), and
    a garrison may countermine (15% a day to find it, a day lost); Jacob's Ford's castle is mined.
    The storm won and the sack (2 November 2026): the GM marks the storm won; the place changes
    hands, the garrison is taken, and where the era allows the stormers sack it for three days (halted,
    desertion and straggling doubled, the named men's loot rolled in the roller). Burgos 1812 (2
    November 2026): a third map, Celada to Briviesca, 19 September 1812; the castle is mined (10
    days, redig 5), Souham's relief at Briviesca. Ciudad Rodrigo 1812 (2 November 2026): a fourth map, the Águeda to
    Salamanca, 8 January 1812; the town broken by the guns in 11 days; Marmont off the map. The Ciudad
    Rodrigo battlefield (2 November 2026): the great and lesser breaches, with two commander rules
    it needed (hacking through works men can open by hand; turning to face an enemy touching only a
    flank). Columns filing
    through a gap (2 November 2026): a unit's ranks behind its front may lie across a wall and file
    after it. Guns overrun (2 November 2026): a battery or anti-tank guns
    touched hand to hand by as many enemy as its crews is overrun (Ciudad Rodrigo 4 to 10 of 12).
    Ciudad Rodrigo at its sourced breach widths (2 November 2026): with guns
    overrun the columns no longer stall inside. Re-forming with a leader (2 November 2026): on any
    battlefield, a broken unit whose leader is up re-forms (Nerve −20 plus his bonus). Leaders from
    the accounts (2 November 2026): Badajoz, Ciudad Rodrigo and Burgos name their leaders, each a
    leader hero of his unit (heroes.field_leaders); Badajoz's French losses 33% to 43% (1812: about
    47%), Burgos 10 to 9 of 12, the total 494 to 493. A field leader's rank bonus (3 November 2026):
    left at 12, as the rule already gives it (3 a step up the era's ladder, at most 12: an ensign is
    four steps up, so every officer is at the cap); asked and answered. Leaders on Albuera, Cowpens, Lundy's Lane and both
    Redans (3 November 2026): 38 named, from the orders of battle; as fought 493 to 494 of 588.
    Leaders on Bull Run, Lützen, Crécy, Dornach and
    Jacob's Ford (3 November 2026): 46 named; as fought 494 to 496. Held back at Agincourt, Towton
    and Aljubarrota (asked and answered): with their lords on, the losers' battles held together
    (7 to 2, 12 to 7, 12 to 9 of 12; without the losers' lords alone they came back to 7, 11, 11).
    Lords on great medieval battles, looked at (3 November 2026): with the lords on, each part of
    the rule turned off in turn (12 runs each, wins as fought): Towton 7, 10 without leaders
    re-forming, 9 without the bonus; Aljubarrota 9, 10, 10; Agincourt 2, 3, 1, and 5 with both
    off (7 with no leaders). Re-forming is most of it at Towton and Aljubarrota; Agincourt stays
    low whatever is off, within the runs' spread. The +22 and re-forming rest on Napoleonic
    sources and nothing found sizes a medieval lord's effect, so the three stay without leaders
    (asked and answered); closed. Leaders on 26 battlefields from Fetterman to
    Keating (3 November 2026): 99 commissioned officers from the accounts, at most two to a unit;
    as fought 496 to 496 (Tumbledown 6 to 9, X-Ray, Hue and Cisterna up 2; Wanat 8 to 5, Mons,
    Goose Green and Grozny down 2). None named yet on Babuna, Topolčani, the three Cassino fields,
    Bougainville and Heartbreak Ridge. Reinöhl at Mojkovac (3 November 2026): not killed there (promoted
    Feldmarschalleutnant in 1918, died in Prague that September; his Maria Theresa cross in 1922,
    after his death); the maker, the book and the phase note are corrected. Albuera's length (3 November 2026): `ends: 150` from the
    accounts (the Spaniards' hour and a half, Hoghton's half hour, the Fusiliers' half hour);
    Colborne's brigade is now ridden down as in 1811, Allied losses 19% to 23%, French 26% to 27%.
    The jam behind a broken unit (3 November 2026): `rout.through` 3 to 6, so Girard's division runs
    back through Gazan's and Werlé's; and Albuera's plan brings Cole on against the French left at
    91 (Oman). Albuera's French losses 27% to 40% (Soult's 5,936 to Oman's 7,900 are 29% to 38% of
    the French on the map), the Allies' 23% (about 27% in 1811); every other battlefield within its
    spread (Agincourt 7 to 9, Babuna 10 to 9, Chipyong-ni 12 to 11; 496 of 588 as before). Passage of
    lines (3 November 2026): a plan's `relieve` task (commander.plans.relieve: 3 exchanges, ours);
    at Albuera Hoghton's brigade relieves Zayas at 61. Only Albuera changed: Allied losses 23% to
    22%, French 40% to 43%. Hoghton's fight is still not the bloodbath of 1811 (about two thirds
    of his men down): Gazan's division breaks soon after Hoghton comes into line. Looked at
    (3 November 2026; 12 runs each): Hoghton loses 3-5% and Gazan 17-19%. Gazan's column of 4,000
    fires about 600 muskets against Hoghton's 1,400, and is shot at by Zayas, Cole and what is left
    of Colborne too; the 20 French guns stay 600 m back firing round shot, mostly at Zayas. Brought
    up within canister range they changed nothing for Hoghton (3%; they fired at Zayas and
    Colborne) and French losses rose to 47%. In 1811 the British were struck "mainly by grape-shot
    from their guns ... at close range" (britishbattles.com). Nothing found sizes a column's fire or
    the guns' share, so closed with no change (asked and answered). Still to do: Burgos's later
    storms.
  - **Wound tables:** the Crimean siege table is the only siege table (the Siege warfare tables
    item above).
  - To start: list the sieges and storms the game already touches (the two Redans, Jacob's Ford,
    Visby's walls, Cassino town, the towns of the travel map), what each needs that the rules lack,
    and the sources for ladders against ditches and banks.
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
  own; Kurdish and Persian are new tongues with estimated shares. The storming column goes in as
  four parties a breach wide (8 of 12 in self-play): as one column nine ranks deep it never got
  through. Still left out: units move as rigid blocks, so a deep unit cannot file through a gap
  narrower than its depth (a movement rule to study).
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
  desert tank-crew wound table: Chute's 1942 Eighth Army report on tank casualties (every casualty of
  one regiment by crew position, injury and cause; about 30% flash burns; 15-25% hit after bailing
  out) lies in an archive not reached. Knocked-out crews now roll on Wright's NW Europe 1944-45
  table (35% burnt inside vehicles, near Chute's 30%), so the desert is played as Normandy; men
  hit after bailing out are not counted. With it the commander's Snipe moves (24 seeds: British
  win 18 of 24 against 13 of 24 before, British losses about 18% against 30%; the Axis side is
  gone in 9 of 12 runs against 4): a struck crewman is now down more often (70% against 58%) and
  killed less often (5% against 7%). A lead for the self-play review, not tuned here.
  In self-play the battalion does not hold (0 of 3: every British unit gone by about 10:30, 40% of
  its men down to the Axis 14%; in fact 72 of under 300 hit and some 37 tanks and SP guns burnt
  out): the first use of anti-tank guns on a battlefield, a lead for the self-play review, not
  tuned here.
- **The tank-crew table, two follow-ups for later.** (1) *Korea.* Only the Second World War's
  tables carry `crew_table` today; the Korean tables (owens-korea, korea-1950-53-hospitalized) could point at
  tank-crews-nwe-1944-45 too, since the tanks and the armour-piercing shot were of the same
  generation (Shermans, Centurions and T-34/85s), but no Korean tank-crew source has been found and
  it would be a stretch, so it waits for one or for a decision to accept the stretch. (2) *Crews hit
  after bailing out.* The rest of a knocked-out crew bail out unhurt and the rules never take them
  on afterwards; Chute puts 15-25% of crews hit after bailing out, and Wright's Operation
  Veritable report (RAMC/1783/2) found 40% of 80 tank-crew casualties hit outside the tank, over
  a third of them out to brew up. Wright 1946 Table 52 has the regions for men outside (S.A.
  outside 5 / 11 / 14 / 17, multiple 10; H.E. outside 18 / 11 / 21 / 31, multiple 27) and for the
  partly exposed (head out of the hatch; S.A. 15 / 2 / 6 / 1). A rule would strike the bailed-out
  men on the battle table as small-arms or shellfire on the open ground round the wreck, and the
  partly exposed commander on the head line. Figures in project doc claude/tank-wounds-research.
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

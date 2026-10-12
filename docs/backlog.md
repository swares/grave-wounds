# Backlog

Known gaps and deferred work, so they are not lost. Each entry says what happens now, why
it falls short, and one way to fix it. Open design decisions (stop-check calibration, how
much the book leans on the roller, disease sets for later eras) are tracked in the
checklist at the end of [design.md](design.md), not here.

When an item is done, delete it here and note it in the pull request that closes it.

## Deferred work

- **A rule book.** The printed tables carry a summary of each rule, but there is no rule
  book to read through: how to play, the turn, the roller, the field map, the travel map,
  camps and disease, the team builder, with examples. With the tables, or as its own book.
- **An AI game master in the online app (to consider).** An option for an AI to run the
  other side or the whole table: narrate, set up fights from the travel map, move and order
  the enemy's units on the field map, roll and explain. Open questions: which model and where
  it runs (a key the player supplies, or a hosted service), what it may change in the saved
  game, and how the player overrules it.

- **Works and ground on the field map.** Turning a unit in place pays nothing for the ground
  its ends sweep over, a unit's flanks and rear rows pay no ground on the move (only its
  front row), and high ground's edge in shooting is all or nothing (no slopes). Tall
  buildings are one storey high as far as the rules go: no floors, no fighting room to room,
  no seeing over the rooftops from them. See [units.md](units.md).
- **Heroes on the field map.** His sickness does not lower his attack and defence there
  (the GM can lower them by hand), his wounds' impairments (a useless arm, dazed) are left
  to the roller, and there is no first aid during the battle: he bleeds until it is over.
- **Indirect fire, simplified.** Batteries stay off the map, with no ground of their own:
  counter-battery fire finds a located battery wherever it is, its crews' wounds are counted
  but not named, and a displaced battery reappears unlocated with no new position to plot.
  A barrage's fire plan has one direction and one lift for the whole plan.
- **The travel clock, simplified.** The clock watches for meetings every quarter hour, so
  two fast forces passing in open country within one quarter hour can miss each other; and
  meetings are only between the forces' hexes (no scouting reach, no seeing a dust cloud).
- **Campaign and battle maps for the other campaigns.** Sidon (1253), Visby (1361),
  Agincourt (1415), Towton (1461), Lützen (1632), Albuera (1811), Cowpens (1781), Lundy's
  Lane (1814), First Bull Run (1861), Fort Phil Kearny (1866-67, with two battlefields), Mons
  (1914), Hill 700 on Bougainville (1944), Anzio and Cisterna (1944), Osan (1950), Chipyong-ni
  (1951), the Ia Drang (1965), Mogadishu (1993), Wanat (2008), Cassino (1944, three battlefields), the Chosin Reservoir (1950), Kapyong (1951), Heartbreak Ridge (1951), Pork Chop Hill (1953), Hue (1968), Khe Sanh (1968), Dak To (1967), Hamburger Hill (1969), Goose Green (1982), Grozny (1995), Fallujah (2004) and COP Keating (2009) have both a campaign map and a battlefield. The rest of Italy, the Gulf War (1991) and Northern Ireland
  still play on the generic valley and open ground (the unit rules for them are in: machine
  guns, extended order, artillery and mortars on call, suppression). Each needs the same work: a spec for `tools/maps/campaign_lib.mjs` (places,
  rivers and roads drawn through public-domain facts) and one for `field_lib.mjs` (the
  battlefield and its armies).
- **Night, second cut.** Muzzle flashes, night vision, fixed lines, slower moves and losing
  direction are in. Night vision is all or nothing by kit: there are no early image
  intensifiers (Vietnam's Starlight scope), no thermal sights on vehicles, and no
  goggles for the other side. A fixed line is laid on one hex, with no traverse limits or
  final protective fire called by flare. A lost unit only turns, and never strays onto
  another path or into its friends. The moon is a simple model, good to an hour or so.
- **Air support, first cut.** Aircraft are called like batteries. There is no fire at them
  (no aircraft lost to ground fire), no forward air controller or marking rounds, and no
  direction to a strafing run or a napalm strip: every attack is a round burst like a shell.
- **Landing by air, first cut.** Helicopters are not on the map: a lift lands or is waved
  off, and a hot zone costs men, but the helicopters themselves cannot be shot down, the
  lift has no fixed number of aircraft or turnaround time, and nothing is flown out (the
  wounded, or a unit lifted away). The GM places a downed helicopter by hand.
- **Cold, first cut.** Frostbite is a sickness on the force's track (and a named man's), not a
  wound on a body part, and cold-weather clothing, warming tents and fires are only the camp's
  shelter. In battle, only automatic weapons jam; mortars, grenades and vehicles do not freeze.
- **Vehicles, first cut.** No facing armour (flank and rear shots), no hull or turret hits, no
  immobilised or damaged vehicles, no infantry riding in carriers or on tanks, no anti-tank guns
  or bazookas but the RPG (`anti_armour`), no mines, no fuel or ammunition, and the crews who
  bail out simply leave the fight. Tanks see as well as men do. Infantry fighting vehicles (the
  BMP at Grozny, the Bradley at Fallujah) play as armoured carriers, without their guns or missiles.
- **Fire at hidden men, first cut.** Men gone to ground, in bunkers or in buildings are now hit
  at 10% of aimed shots (machine guns 5%), and dug-in men hold better. Osan, left alone, lasts
  about an hour where the real fight took two and a half; the rest of that time went in the
  North Koreans moving round the flanks, which the static test does not play. Worth a second
  look once Osan has been played through by hand.
- **Guns, still simplified.** A battery splits into at most one section, and its canister
  at a charge is counted at the end of the exchange like all fire, so it does not thin the
  blows the charge strikes that minute. The Thirty Years' War still borrows the Peninsula's
  gun wounds: no 1618-48 artillery wound counts were found.
- **Character generation, beyond the first cut.** The medieval tables are a first draft for
  a team playtest. Its characteristics now count in the roller (Agility, Endurance,
  Strength, Presence), and Leechcraft, Fieldcraft, Watch and Stealth work outside a fight.
  Followers have one-line stat blocks, and the gunpowder eras (1618-1876) and the world wars
  (1914-18, 1939-45) have their own tables. Korea and later, and women, are their own
  entries below.
- **Team tables for Korea and later.** The team builder has seven eras, ending with the
  Second World War. The maps now run from Korea to Afghanistan, but a team for them has to be
  made from the Second World War tables or by hand, with the wrong kit (no flak vest, no M16,
  no Interceptor), the wrong careers (no draft and twelve-month tour, no Rangers or Paras) and
  the wrong events. One way to fix it: tables for Korea (1950-53), Vietnam (1965-73) and the
  later wars (1982-2010s), each with its origins, careers, events and kit drawn from the armour
  kits the maps already use.
- **Women under arms.** Every name list is men's and every sheet says "he", though women
  served under arms in several eras: Soviet snipers, machine gunners and medics in 1941-45,
  and American and British soldiers and medics in Iraq and Afghanistan, for two. One way to
  fix it: a women's name list for each era where they served, a choice (or a roll, at the
  era's real share) of man or woman, pronouns on the sheets, and careers open to them as the
  records show for that era and army.

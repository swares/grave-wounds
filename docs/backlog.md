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
  on the pages, not in the book. It has no index or page numbers in print.
- **The enemy commander, beyond the first cut.** A scripted commander moves one side on the
  field map (attacking or holding, by its units' quality; Undo puts its move back). It knows
  only what its units see, remembering last sightings for a few exchanges, and looks once
  at the start of each move. It leaves batteries, fire support, air controllers,
  vehicles' riders, fixed lines, reserves and works to the GM. Its units pick their targets
  one by one (nearest, or hurt, shaken and dangerous for better troops), and it has no plan
  beyond each unit's next move: no scouting, feints or holding a reserve.
  It does not play the travel map. Later, by the choice made: an optional narrator, using
  a model with a key the player supplies, to explain its orders in prose.

- **Works and ground on the field map.** Height has three steps (flat, slope, high) and no
  contour lines or dead ground behind a crest. Tall buildings give a view and a height, but
  not separate floors: there is no fighting room to room or stair by stair, and men upstairs
  are not safer from shells. Scrub and orchards thin aimed fire and block sight past 3 hexes,
  but calling fire has no roll for them to cost (only the block), and the roller's 2-yard
  battle map does not thin sight at all (its woods and brush only give cover). There is no
  seeing through a building's open windows.
- **Heroes on the field map.** First aid comes from the unit's best Leechcraft or its
  medics, with tourniquets and (before 1914) cautery. A lamed hero slows his unit until he
  is carried back or left behind. Bearers carry him to his side's aid post across the map
  (or off it, with none), walking wounded go back alone, and a hero left lying is picked up
  by a friendly unit or found by an enemy one. Still left out: parties go on a straight line
  over any ground (water and woods included) and only shellfire can catch them, not aimed
  fire; the rank and file have no aid post (their wounded are reckoned after the battle);
  an aid post cannot be moved once the battle starts; prisoners have no exchange, ransom or
  escape; and there is no two-handed great sword among the weapons, so no sword is barred
  to a one-armed hero.
- **Indirect fire, simplified.** A battery placed off the map stands straight out from the
  edge nearest where it was placed, not anywhere behind it. Its crews' wounds are counted
  but not named. Counter-battery fire does not need to see a placed battery: it
  finds it by flash and sound once located, wherever it stands within range.
- **The travel clock, simplified.** Meetings are only between the forces' hexes: no
  scouting reach, and no seeing a dust cloud or campfires from further off.
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
  direction are in. Night-vision devices (Starlight scope, goggles, thermal sight) are a
  unit's whole: a Starlight scope stands for the few rifles that had one, and there are no
  infra-red searchlights (the 1950s-60s active sights) or devices that wash out in a flare's
  light. A fixed line is laid on one hex, with no traverse limits or
  final protective fire called by flare. A lost unit only turns, and never strays onto
  another path or into its friends. The moon is a simple model, good to an hour or so.
- **Air support, second cut.** Ground fire brings aircraft down and forward air controllers
  talk them on. Still left out: anti-aircraft guns and missiles (only machine guns, rockets
  and rifles fire at them), marking rounds and smoke, a damaged aircraft that limps home, and
  direction to a strafing run or a napalm strip: every attack is a round burst like a shell.
- **Landing by air, first cut.** Helicopters are not on the map: a lift lands or is waved
  off, and a hot zone costs men, but the helicopters themselves cannot be shot down, the
  lift has no fixed number of aircraft or turnaround time, and nothing is flown out (the
  wounded, or a unit lifted away). The GM places a downed helicopter by hand.
- **Cold, first cut.** Frostbite is a sickness on the force's track (and a named man's), not a
  wound on a body part, and cold-weather clothing, warming tents and fires are only the camp's
  shelter. In battle, only automatic weapons jam; mortars, grenades and vehicles do not freeze.
- **Vehicles, second cut.** Flank and rear shots, immobilised vehicles and guns put out of
  action, riders and the bazooka, recoilless rifle and guided missile are in. Still left out:
  hull and turret hits, tank riders ("desant") and riders firing from the vehicle, anti-tank
  guns as batteries, mines, fuel and ammunition, and vehicles' night sights. Crews who bail
  out simply leave the fight. A guided missile's long range only helps in clear weather and
  light, as aimed fire does.
- **Fire at hidden men, first cut.** Men gone to ground, in bunkers or in buildings are now hit
  at 10% of aimed shots (machine guns 5%), and dug-in men hold better. Osan, left alone, lasts
  about an hour where the real fight took two and a half; the rest of that time went in the
  North Koreans moving round the flanks, which the static test does not play. Worth a second
  look once Osan has been played through by hand.
- **Guns, still simplified.** The Thirty Years' War still borrows the Peninsula's gun wounds,
  because no 1618-48 artillery wound counts were found. Sections share the battery's rounds
  in order rather than each carrying its own.
- **Character generation, beyond the first cut.** The medieval tables are a first draft for
  a team playtest. Its characteristics now count in the roller (Agility, Endurance,
  Strength, Presence), and Leechcraft, Fieldcraft, Watch and Stealth work outside a fight.
  Followers have one-line stat blocks, and the gunpowder eras (1618-1876) and the world wars
  (1914-18, 1939-45), Korea, Vietnam and the later wars (1982-2014) have their own tables.
- **Women under arms, first cut.** Women serve in the Civil War (disguised), the Soviet
  Union of 1941-45, Vietnam (the ARVN, the North and the Viet Cong) and the later wars (the US,
  Britain and Russia), chosen or rolled at the army's share. Still left out: the earlier eras
  (women in medieval sieges, the Revolution's and 1812's few, Russia's women's battalions of
  1917 and Flora Sandes in Serbia), careers outside the fighting units (nurses, auxiliaries,
  anti-aircraft gunners, pilots, the Female Engagement Teams of Afghanistan), the Plains
  nations' women who fought, and shares by career rather than by army. The Viet Cong's and the
  North's women have no reliable share, so they are chosen, never rolled.

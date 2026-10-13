# Night and the air {#night}

## Fighting in the dark {#dark}

The light limits how far anyone can see to aim or to call fire, as in [Light](#light): on a
moonlit night {{n_moon}}, on a dark night {{n_dark}}. The weather's own limit still applies,
and whichever is shorter counts. The dark also slows a march and turns men round:

{{table:dark}}

- **Losing direction.** Each unit that moved in the dark may lose its way when its side's
  move ends. Its chance is the light's, adjusted by its quality: {{n_lost}}. A lost unit
  ends a point off its line and cannot move next exchange, though it can turn.
- **Muzzle flashes.** A unit that fires when the light limits sight to less than
  {{n_flash_under}} shows where it is. Through the next exchange, the hexes it fired from can
  be aimed at, and fire called on, from up to {{n_flash}} away.
- **Flares.** A flare lights the ground within {{n_flare}} for {{n_lasts}} exchanges, and
  illumination rounds from mortars and guns light far more. A lit hex is seen as by day.
- **Night vision.** From the 1960s, units can carry devices that see further in the dark:

{{table:nvd}}

- **Fixed lines.** Before dark a machine gun can be laid on a fixed line. In the dark, with
  no target it can see, it fires blind down the line at an enemy within {{n_fixed_width}}
  hex of it, at −{{n_fixed}}%.
- **The enemy commander** knows only what its units see, so at night it waits for the
  enemy to come close or to fire.

## Aircraft {#aircraft}

Fighter-bombers and helicopter gunships are called like batteries; each "tube" is an
aircraft. Fire can be called only where one of the side's units can see it fall.

{{table:air}}

- **Weather.** Aircraft do not fly in {{a_grounded}}, and fighter-bombers do not fly at
  night. A mission called then waits until the weather clears.
- **Ground fire.** After each attack run, every aircraft that attacked can be brought down
  by the enemy within {{a_reach}} of the aim. Its chance is {{a_mg}}% for each machine gun
  served there, {{a_rocket}}% for each unit with rockets, and {{a_rifles}}% for every 100
  men with other firearms. Gunships fly low and slow, so they count it
  ×{{a_gs_exposed}}. The chance is at most {{a_cap}}%.
- **Air controllers.** A unit can be given a forward air controller. When he can see the
  aim, the attack scatters half as far. Without one, aircraft will not attack within
  {{a_danger}} of their own men; the mission waits until it can.

## Landing by air {#landing}

From Vietnam on, units can come in by helicopter to a **landing zone**. At the end of each
exchange up to {{h_lift}} men land at each zone, on it or the nearest spot within
{{h_zone}} hexes, and they can move the next exchange.

- **Waved off.** No one lands while an enemy unit stands within {{h_blocked}} hexes of the
  zone.
- **A hot zone.** If any enemy unit could shoot at the zone, each man landing is struck at
  {{h_hot}}% and wounded as by shellfire.
- **A downed helicopter** gives the men in its hex cover and is slow ground to cross.

!!! gm "For the GM"
    Night evens the odds against a stronger side, and its fire support and aircraft
    count for less in the dark. A defender with fixed lines, flares and a plan for
    illumination can still hold.

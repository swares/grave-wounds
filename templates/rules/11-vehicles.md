# Vehicles {#vehicles}

On the field map, in wars with machine guns or later, tanks, infantry fighting vehicles and
armoured carriers fight as units, one vehicle to a hex. The unit's men are its crews.

{{table:vehicles}}

- **Moving.** Vehicles cross open and high ground at a hex for a hex, and rough ground,
  slopes and woods for more. They cannot enter marsh, buildings, rubble or water, so in a
  town they keep to the streets.
- **Their machine guns** fire as a machine-gun team's, about one gun to a vehicle.
- **Main guns** fire each exchange at the nearest enemy in range, in sight and in front,
  enemy vehicles first, with a clear line of fire.
- **Armour.** Small arms cannot hurt a vehicle, and men armed only with them do not shoot
  at one. No one fights a vehicle hand to hand.

## Knocking them out {#knocking-out}

Rocket teams fire a round for every {{v_rocket_per}} men each exchange, and missile teams
one for every {{v_atgm_per}}. Every round is aimed, and range, cover and the weather count
as for shots at men. A hit knocks the vehicle out at:

{{table:armour}}

- **Where it is hit.** A hit into the flank counts ×{{v_flank}}, and into the rear
  ×{{v_rear}}, to 100% at most. Which it is depends on where the shooter stands.
- **Damage short of that.** A hit that does not knock the vehicle out immobilises it at
  {{v_immobile}}%, or else puts its main gun out at {{v_gun_out}}%. Immobilised vehicles
  can still turn. Their crews can abandon them and leave the fight unhurt.
- **Shells and bombs** bursting in a vehicle's hex knock it out at the kind's own chance: a
  heavy howitzer's {{i_how_knock}}%, a fighter-bomber's {{v_fb_knock}}%. Light armour is
  {{v_shell_light}} times as likely to go.
- **Knocked out.** Its crew are out of the fight. Each is struck at {{v_crew_struck}}% and
  wounded as by shellfire; the rest bail out.

## Riders {#riders}

Infantry fighting vehicles and carriers carry men. A foot unit beside them can **mount**
if all its men fit and neither unit is in contact. Riders move with the vehicles. They do
not fight, shoot or check morale until they **dismount** beside them. When a carrier is
knocked out, each of its riders is struck at {{v_riders_struck}}%, as by shellfire.

!!! gm "For the GM"
    Armour is a problem the infantry must solve, not a fight it can win with rifles. Give
    the side without tanks rockets, ground the tanks cannot cross, or the dark.

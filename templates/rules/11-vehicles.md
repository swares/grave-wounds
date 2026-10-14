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
- **Armour.** Small arms cannot hurt an armoured vehicle, and men armed only with them do
  not shoot at one. Trucks and gun tractors are **soft-skinned**: rifles and machine guns
  shoot at them too, every shot aimed, and each hit knocks one out at the chance below. No
  one fights a vehicle hand to hand.

## Knocking them out {#knocking-out}

Rocket teams fire a round for every {{v_rocket_per}} men each exchange, and missile teams
one for every {{v_atgm_per}}. Every round is aimed, and range, cover and the weather count
as for shots at men. A hit knocks the vehicle out at:

{{table:armour}}

- **Where it is hit.** A hit into the flank counts ×{{v_flank}}, and into the rear
  ×{{v_rear}}, to 100% at most. Which it is depends on where the shooter stands.
- **Damage short of that.** A hit that does not knock the vehicle out strikes the turret at
  {{v_turret}}%, else the hull.
  - On the turret it puts the main gun out at {{v_t_gun}}%, and immobilises the vehicle at
    only {{v_t_imm}}%.
  - On the hull it immobilises the vehicle at {{v_h_imm}}%, and puts the gun out at
    {{v_h_gun}}%.

  Immobilised vehicles can still turn. Their crews can abandon them and leave the fight
  unhurt.
- **Shells and bombs** bursting in a vehicle's hex knock it out at the kind's own chance: a
  heavy howitzer's {{i_how_knock}}%, a fighter-bomber's {{v_fb_knock}}%. Light armour is
  {{v_shell_light}} times as likely to go, soft-skinned vehicles {{v_shell_soft}} times.
- **Knocked out.** Its crew are out of the fight. Each is struck at {{v_crew_struck}}% and
  wounded as by shellfire; the rest bail out.

## Anti-tank guns {#at-guns}

In the Second World War and Korea, a unit can be **anti-tank guns**: towed guns such as
the British 6-pounder, the American 57 mm, the German Pak 38 and 40, the Soviet and North
Korean 45 mm and the Japanese 47 mm.

- **Crews.** Each gun has {{at_crew}} men. A gun fires while one of its crew is up, and its
  crews manhandle it {{at_move}} hexes.
- **Fire.** Each gun fires {{at_rate}} round an exchange, as a tank's main gun does. Out to
  {{at_range}}, it hits a vehicle at {{at_hit}}% (close, mid and full range), and the hit
  then knocks the vehicle out as a main gun's would. At men, its high explosive bursts as a
  tank's round does.
- **Towing.** Gun tractors and trucks tow a gun each, the crews riding. Hooked up beside
  them, the guns move with the tractors and do not fire; unhooked, they fire from the next
  exchange.
- **Rounds.** Each gun brings {{at_rounds}} rounds. A gun out of them is resupplied as a
  battery is: an exchange out of contact, neither moving nor firing.
- **Shields.** Anti-tank and anti-aircraft guns have shields: small arms fired at them from
  in front lose {{at_shield}}%. Shields do nothing against shells or fire from the flank or
  rear.
- **Vulnerable.** Otherwise its crews are men: rifles, machine guns and shells strike them,
  and hand to hand they fight with bayonets.
- **Emplaced.** Before the battle the GM can dig in any gun unit (anti-tank guns,
  anti-aircraft guns, machine guns or a battery). While it stands it counts as gone to
  ground, −{{at_ground}}% and hidden, but it cannot move all battle, though it can turn. A
  unit that breaks leaves its pits.
- **The enemy commander** tows its anti-tank guns forward and unhooks them in reach (see
  [the enemy commander](#commander)).

## Minefields {#mines}

From 1939, the GM can paint minefields before the battle, marked or hidden. A hidden field
shows on the map only once something has gone into it. A unit that moves into minefield
hexes sets them off before the exchange's shooting. The ground it crossed is reckoned on a
straight line from where its move began.

{{table:mines}}

- **Men.** A man struck rolls a wound as one hit by a mine, at {{m_attack}}%. Mine wounds
  fall mostly on the feet and legs.
- **Vehicles.** A vehicle struck is knocked out at {{m_heavy}}% (heavy armour) or
  {{m_light}}% (light). Otherwise a track is blown off and it is immobilised.
- **Sappers.** In set-up the GM can mark a foot unit as sappers. On its own side's move,
  before it moves and out of contact, it can start to **lay** mines of any kind or to **lift**
  them. While it works it neither moves nor fires. Moving, turning, breaking or coming into
  contact stops the work.
  - Laying takes {{m_lay}} exchanges. Then the row of hexes just ahead of its front, as wide
    as its front, is a hidden minefield. Hexes where a unit stands are left clear.
  - Lifting takes {{m_clear}} exchanges. Then the minefield hexes in that row that its side
    knows of are lifted: a lane.
  - The enemy commander sets its own sappers to work (see [the enemy commander](#commander)).
  - A side knows the mines its own sappers laid: its commander steers round them, and they do
    not strike its own men.

## Riders {#riders}

Infantry fighting vehicles, carriers and lorries carry men, and tanks carry {{v_rides}} men on
each hull. A foot unit beside them can **mount**
if all its men fit and neither unit is in contact. Riders move with the vehicles. Men in an infantry fighting vehicle shoot through its ports
({{v_ports}} of them) and men on a tank's hull shoot from it ({{v_hull}}), at their own weapon's
target; otherwise riders do
not fight, shoot or check morale until they **dismount** beside them. When a carrier is
knocked out, each of its riders is struck at {{v_riders_struck}}%, as by shellfire. Lorries
are soft-skinned: a rifle or machine-gun hit that does not knock one out strikes a man aboard.
Men riding on a tank's hull are in the open: small arms shoot at the tanks for them, and each
hit strikes a rider; shells bursting near the tanks strike them as men in the open.

!!! gm "For the GM"
    Armour is a problem the infantry must solve, not a fight it can win with rifles. Give
    the side without tanks rockets, anti-tank guns, mines, ground the tanks cannot cross,
    or the dark.

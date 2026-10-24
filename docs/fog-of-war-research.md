# Fog of war on the travel map: how far a force sees the enemy

The travel map's fog of war decides which enemy forces a side's players see online, and where it
last saw them. Its first cut counted sight in hexes with placeholder numbers. This note looks at
what period sources and the game's own data say, and sets the numbers now in `data/terrain.yaml`
(`sight`). Researched October 2026.

## The scale problem first

The campaign maps' hexes are not one size. In the built travel data, 23 maps have 1 km hexes, 15 have
0.5 km, 2 have 5 km (Agincourt 1415, Serbia 1915), and 1 has 0.25 km (Mogadishu 1993). A rule
counted in hexes ("foot sees 2 hexes") meant 500 m at Mogadishu and 10 km at Agincourt. **Sight is
now in kilometres**, and each map's hex size converts it.

## What the sources say

**Seeing troops with the naked eye.** A 19th-century artillery officer's guide to judging distance
gives (in yards):

| Distance | What may be distinguished |
|---|---|
| about 1,300 yd (1.2 km) | infantry from cavalry, with good eyesight |
| about 1,000 yd (0.9 km) | a single figure |
| about 700 yd | his head, as a round ball |
| about 500 yd | the face as a light spot; limbs, uniform and firelocks |
| 200 to 250 yd | details of body and uniform |

The page does not name the manual or its year ([Kriegsspiel.org](https://kriegsspielorg.wordpress.com/distances-at-which-troops-may-be-distinguished/)).
A body of troops is a much larger target than one figure: a column of a few thousand men is
about a kilometre of road, and an army of 10,000 about five miles ([A Collection of Unmitigated
Pedantry](https://acoup.blog/2019/10/06/new-acquisitions-how-fast-do-armies-move/)). So a force is
made out well beyond the 0.9 to 1.2 km of the table. On level ground, though, the horizon caps it:
about 3.57 times the square root of the eye's height in metres gives about 4.7 km from a man's eye
(1.7 m), and somewhat more from a rider's or for a tall column or its dust. Ground that is not
level, haze, woods and buildings cut this well short.

**Cavalry screens and outposts.** In 1806 the French light cavalry ranged up to "150 kilometers in
advance of the advanced guard", while an advance guard far from the enemy was "at most 12
kilometers" ahead of its corps. The Prussian cavalry kept close to its infantry. Even so, Napoleon
did not know where the Russian army was, and contact came from a clash at Bromberg ([The Napoleon
Series, *Lessons on 1807*](https://www.napoleon-series.org/military-info/battles-campaigns/lessons-on-1807-maneuvers-of-eylau-and-friedland/)).
Screens worked over a wide area to the flanks and rear as well as the front; their reach depended
on where the main body was, not on a fixed distance ([Screening (tactical)](https://en.wikipedia.org/wiki/Screening_(tactical))).

**The dark.** A US Army course on limited visibility: on a clear night the naked eye makes out the
lie of the land to about 400 m, and with a full moon it spots a moving man at about 240 m (700 m
with binoculars). It gives no distances for fog, rain or snow, only that they limit observation
([US Army, *Limited visibility techniques*](https://www.globalsecurity.org/military/library/policy/army/accp/in0202/le2m.htm)).

**Dust.** Moving cavalry raised distinct swirling dust and infantry broad clouds, and commanders
read it, for example at Chickamauga in 1863. But that comes from a modern forum's paraphrase of a
modern history, with no distance given ([Civil War Talk](https://civilwartalk.com/threads/dust-in-the-distance-approach-of-infantry-or-cavalry.213067/)).
It is not used here.

**The game's own weather.** `data/weather.yaml` already gives, for each condition, how far a man
can see to aim, in 2 m battle hexes: fog 25 (50 m), blizzard 15 (30 m), storm 50 (100 m), heavy rain
and snow 75 (150 m), heavy snow 40 (80 m), rain 150 (300 m). The travel rule uses those, scaled up
for a body of troops.

## The numbers, and how they follow

| | Value | From |
|---|---|---|
| Foot, clear day | 3 km | Beyond the 0.9 to 1.2 km at which figures are told apart, since a force is a big target; under the 4.7 km horizon from the ground, which folds of ground and haze cut. A judgment between the two. |
| Mounted, clear day | 8 km | Patrols and vedettes out ahead, within the advance guard's 12 km. Not the 150 km strategic sweeps: those are reports gathered over days, outside a sight rule. |
| Wagons, clear day | 2 km | Train guards look to the road, not out. A judgment. |
| In weather | 5 × the weather's aiming distance | Fog 250 m, storm 500 m, heavy rain 750 m, rain 1.5 km. **The factor 5 is a judgment**: a body of troops against one man to aim at. No source gives travel-scale figures. |
| Dusk | half | A judgment. |
| Moonlit | 0.5 km | A moving man at 240 m by full moon, so a body of troops somewhat further. |
| Dark night | 0.2 km | Under the 400 m at which the land itself is made out on a clear night. |
| Contact | 1 km, always | Outposts and pickets find an enemy this close in any weather, light or cover. **A judgment**: no source above gives an outpost line's distance. |
| Woods, villages, towns | seen only within contact | A force inside is out of sight until outposts are on it. |

A side sees what any of its forces sees, as reports pass along the side. That is a simplification:
reports took time.

## What it leaves out

- **Campfires at night.** A camped army's fires were seen from far off. I found no distance worth
  using, so the dark limits a camp's visibility as it does a marching column's.
- **Dust by day in dry weather.** No sourced distance. It would extend sight of a marching force.
- **Height.** A force on a hill sees further, and one in a valley less. The rule does not look at
  ground height.
- **Optics and aircraft.** Telescopes and field glasses (from the 18th and 19th centuries) and
  observation aircraft (from 1914) see much further. The 20th-century maps get the same naked-eye
  numbers, which is too little for them. A per-period factor is the obvious next step.
- **Scouting as an order.** Patrols, spies and deserters sent out, and false or stale reports
  beyond the last sighting.
- **The delay of reports.** A side's whole knowledge is shared at once.

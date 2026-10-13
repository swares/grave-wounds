# Team builder: character generation

Each player runs a team of four to six. The first member leads, and when he falls another
steps up. A whole team should take about twenty minutes to make at the table, or one click
on the team builder page, `dist/team.html`. The tables are in `data/teams/` (one file an
era) and in the printed tables (*Team generation*). Every table, event and trait is written for
this game. The names are common period names.

The first table set covers the medieval era, c.1250-1460, the era of the Sidon, Visby,
Agincourt and Towton battlefields. The team comes from one of four regions:

| Region | Wound table | Kit and weapons |
| --- | --- | --- |
| Latin East (c.1250) | Sidon 1253 | mail hauberks, gambesons, crossbows |
| Gotland and the Baltic (c.1360) | Visby 1361 | Gotland levy and better kits, Danish men-at-arms |
| England (c.1415-1460) | Towton 1461 | jacks and sallets, brigandines, longbows, bills |
| France (c.1415) | Towton 1461 (the nearest records) | full plate, brigandines, jacks |

## Five steps

**1. Characteristics.** Strength, Agility, Endurance, Wits, Nerve and Presence. Either roll
3d6 x 5 for each in order (15 to 90), or take the fixed array 70, 60, 55, 50, 45, 35 and
place it, highest first, in the order his career prefers. On the page, a fixed-array
character's characteristics can be swapped: click one, then another.

**2. Origin.** d100 on the origin table (20 origins, 5 each): where he comes from, a skill
(+15), a trait and the drawback that goes with it. A trait or drawback is +/-10 to a
characteristic or +/-15 to a skill: the ploughman's son has a strong back and cannot read a
word; the novice who left the cloister knows his herbs and faints at the sight of blood.

**3. Career terms.** The leader serves three terms, the others one or two. Each term:

- his career's main skill rises, +15 the first term and +10 after;
- its second skill rises +5;
- d100 on the career's table gives an event and the skill it taught (+15). An event he has
  already had moves to the next row down.

He is 16, plus 4 a term. Nobody dies in generation. There are twelve careers:

| Career | Main | Second |
| --- | --- | --- |
| Man-at-arms | Blade | Parry |
| Archer | Bow | Dodge |
| Crossbowman | Crossbow | Dodge |
| Spearman or billman | Polearm | Parry |
| Mounted sergeant | Ride | Parry |
| Mercenary | Axe and mace | Parry |
| Sailor | Seamanship | Dodge |
| Clerk or priest | Letters | Persuade |
| Barber-surgeon | Leechcraft | Craft |
| Forester or huntsman | Fieldcraft | Stealth |
| Servant or groom | Ride | Watch |
| Merchant | Persuade | Letters |

The steps are set so a fighter's attack with his own weapon comes out about where the
field map's unit qualities sit. One term gives about a green soldier's 40%, two a
regular's 50%, three a veteran's 60%. Defence comes out near theirs (25, 35, 45).
Averaged over 400 characters each, a man-at-arms reaches 43, 52 and 63% after one, two and
three terms, with defence 33, 40 and 48%.

**4. Old wounds.** A term can leave an old wound in two ways: its event is marked * (a
siege, a broken line, a rout), or d100 comes up at or under the career's old-wound
chance (25% a term for a man-at-arms or a mercenary, 3% for a clerk). The wound's location
is rolled on the region's wound table for the weapon that usually hurt men of that trade.
That table is the same one the roller uses, so a Towton man's old wounds fall where
Towton's did. Then d100:

- 01-70: a healed scar, drawn on his figure;
- 71-00: a lasting hurt, 5 off the characteristic its place governs: Wits for the head,
  Presence for the face, Strength for the arms, Agility for the legs, Endurance for the body.

Veterans carry them. Most three-term soldiers have at least one, as the healed wounds on the
Towton and Sidon skeletons suggest.

**5. Skills and kit.** Each skill starts at a characteristic divided by 2, 3, 4 or 5
(rounded down; the printed table gives each), plus what he gained, at most 90. His
**attack** is the skill his weapon is fought with (Blade for a sword or dagger, Polearm for a
spear, bill or poleaxe, and so on). His **defence** is the better of Parry and Dodge. His
**Nerve** is the characteristic, used by the roller's stop checks and morale. Kit and weapon
come with his first career and his region.

## Teams

| Team | Members (terms) | Followers (quality) |
| --- | --- | --- |
| A lord's retinue | man-at-arms (3), archer (2), archer (1), spearman (1), barber-surgeon (1), servant (1) | 8 archers, 4 spearmen, 2 servants |
| A free company | mercenary (3), mercenary (2), crossbowman (2), archer (1), spearman (1) | 6 mercenaries, 4 crossbowmen, 2 archers (hardened) |
| A garrison patrol | mounted sergeant (3), crossbowman (2), crossbowman (1), spearman (1), clerk (1) | 4 crossbowmen, 4 spearmen, 2 mounted sergeants |
| A farmers' muster | spearman (3), spearman (1), spearman (1), archer (1), forester (1) | 10 spearmen, 4 archers (raw) |
| A pilgrims' escort | man-at-arms (3), mounted sergeant (2), crossbowman (1), clerk (1), barber-surgeon (1) | 3 mounted sergeants, 3 crossbowmen, 2 servants |
| A merchant's company | merchant (3), sailor (2), crossbowman (1), servant (1) | 4 sailors, 2 crossbowmen, 2 servants |

*Your own team* on the page picks four to six careers and their terms, and no followers
until you add them.

## The gunpowder eras, the world wars and after

Nine more eras use the same five steps, with their own skills, origins, careers, events,
regions, teams and followers (`data/teams/thirty_years.yaml`, `horse_musket.yaml`,
`civil_war.yaml`, `plains_nations.yaml`, `wwi.yaml`, `wwii.yaml`, `korea.yaml`, `vietnam.yaml`
and `modern.yaml`). Pick one with **Era** on the page, or `--era` on the command line. Each
region takes its war's wound table, for old wounds and for the roller.

| Era | Regions (wound table) | Fighting skills | Careers |
| --- | --- | --- | --- |
| Thirty Years' War (1618-1648) | the Swedish army; the Imperial army and the Catholic League (Thirty Years' War) | Musket, Pistol, Blade, Pike | musketeer, pikeman, cuirassier, harquebusier, dragoon, sergeant, field surgeon, sutler, chaplain |
| Horse and musket (1775-1815) | the Continental Army and the British in America (Revolution); the British and the French in the Peninsula (Peninsular War); the United States (1812) | Musket, Rifle, Pistol, Blade, Bayonet, Gunnery | line infantryman, rifleman, dragoon or hussar, artilleryman, sergeant, officer, surgeon's mate, scout, sailor or marine, sutler |
| Civil War and frontier (1861-1876) | the Union, the Confederacy, the US Army on the frontier (all the Civil War table) | Rifle, Pistol, Blade, Bayonet, Gunnery | infantryman, sharpshooter, cavalry trooper, artilleryman, sergeant, officer, surgeon or hospital steward, scout, teamster |
| Plains nations (1860-1877) | the Lakota; the Cheyenne and Arapaho (the Army surgeons' arrow report, with Civil War gunshots) | Bow, Lance, Club and knife, Gun | warrior with bow and shield, warrior with lance and shield, warrior with a gun, scout, leader of war parties, healer, herder of the camp's horses |
| First World War (1914-1918) | the British Empire, France, Germany, the United States (1917-18) (all the First World War table) | Rifle, Pistol, Machine gun, Bombing, Gunnery, Bayonet, Trench weapons | rifleman, machine gunner, bomber, sniper or observer, sapper or tunneller, stretcher-bearer or orderly, signaller or runner, corporal or sergeant, junior officer, gunner or trench mortarman |
| Second World War (1939-1945) | the United States in Europe, the British Commonwealth, Germany, the Soviet Union (the Owens WWII table); US Marines and Army in the Pacific, Japan (the Bougainville table) | Rifle, SMG and pistol, Machine gun, Grenade, Gunnery, Bayonet, Close combat | rifleman, machine gunner, grenadier or anti-tank man, sniper or scout, combat engineer, medic, radio operator, corporal or sergeant, junior officer, paratrooper or commando, tank crewman |
| Korean War (1950-1953) | US Army and Marines 1950-51, the US Army on the outpost line 1952-53, the Commonwealth, the Republic of Korea Army, the Chinese People's Volunteers, the Korean People's Army (all the Korean War hospital table) | Rifle, SMG and pistol, Machine gun, Grenade, Gunnery, Bayonet, Close combat | rifleman, machine gunner or BAR man, rocket or recoilless gunner, mortarman, sniper or scout, combat engineer, aidman or corpsman, radio operator or wireman, squad leader, platoon leader, tank crewman |
| Vietnam War (1965-1973) | the US Army, the US Marines, Australians and New Zealanders, the ARVN, the North Vietnamese army, the Viet Cong (all the Vietnam hospital table) | Rifle, SMG and pistol, Machine gun, Grenade and rocket, Gunnery, Bayonet, Close combat | rifleman, machine gunner, grenadier or RPG gunner, point man or scout, combat engineer or sapper, tunnel rat or tunnel fighter, mortarman, medic or corpsman, radio operator, squad leader, platoon leader |
| The Falklands to Afghanistan (1982-2014) | the British and Argentines in the Falklands (Falklands table), US forces in the Gulf 1991 (Gulf War table), the Rangers in Mogadishu 1993 (Somalia table), the Russians and Chechens 1994-96 (Chechnya table), the US, the British and the insurgents in Iraq and Afghanistan (OIF/OEF table) | Rifle, Pistol, Machine gun, Grenade and rocket, Gunnery, Bayonet, Close combat | rifleman, machine gunner, grenadier or anti-tank gunner, marksman or sniper, combat engineer or bomb searcher, combat medic, signaller, military police or convoy gunner, armoured vehicle crewman, section leader, platoon leader |

Brawl, Parry, Dodge and the skills outside a fight (Leechcraft, Fieldcraft, Watch, Stealth
and the rest) carry over; Bow, Crossbow, Axe and Sling stay medieval. Gunnery is the
artillerymen's skill. The wound tables have no pike wounds, so the pike rolls on the Visby
melee table as a long spear (reach 3, no shield, more thrusts to the face and chest); a
pikeman fights with it at his Pike skill, his sabre second. On the frontier, gunshots roll on
the Civil War table, as the arrow-wound records have none; the frontier infantry carry the
Springfield breech-loader of 1866 (Rifle), the Civil War's Sharps and Spencer carbines' kin.

The Plains nations' tables are written from plain ethnographic and historical fact: the
buffalo and the horse, raids on the Crow and the Shoshone for horses and honours, counting
coup, scouts sent ahead of a camp, and from 1866 the fighting along the Bozeman Trail. Their
names are in English translation, built from common elements of the period's names, and
are not meant to name anyone. Warriors with bow or lance carry the rawhide shield and fight
mounted on the field map; their old wounds are arrow wounds, from the wars between the
nations. Their kits: cuirassiers,
harquebusiers and pikemen in the 1630s armours; dragoons with helmets and the French with
cuirasses; everyone else unarmoured.

The world wars: a term is a year of the war, not four, so a soldier of three terms is about 21.
Everyone wears the steel helmet (in general use from 1915-16). Signals (telephone, lamp,
runner and radio) and, in the Second World War, Drive (trucks and tanks) are new skills
outside a fight; a raid's clubs, knives and entrenching tools are fought with Trench weapons
(Close combat in 1939-45). The Second World War's regions roll on their theatre's table:
Europe and Russia on the Owens WWII table, the Pacific on Bougainville. There are no vehicle
rules yet, so a tank crew fights as men on foot with pistols and submachine guns. The names
are common period names; the events are ours, written from plain fact about trench and
field service.

Korea and after: armour follows the region and the year, as on the battlefields: a steel
helmet for the Americans of 1950-51, the Commonwealth and the ROK; the M1952 flak vest on the
outpost line of 1952-53; the nylon and Doron vests in Vietnam (the Army's and the Marines');
PASGT in 1991, the Ranger Body Armor in Mogadishu, plate armour in Iraq and Afghanistan (the
British Osprey drawn as the Interceptor); no armour for the Chinese, the North Koreans, the
Vietnamese communists, the Chechens and the insurgents. Rocket launchers and recoilless rifles
are fought with Gunnery in Korea; from Vietnam on, the RPG with Grenade and rocket, and an
RPG gunner of the Viet Cong, the North's army, the Chechens or the insurgents carries one.
Chinese, Korean and Vietnamese names are written family name first. A term is a year.

## Women under arms

A region's `women` block opens careers to women where the records show they served under
arms; elsewhere `no_women` says why not (nurses and auxiliaries served, but not in these
careers). On the page, **Women** rolls each member of a template team (and each follower) at
the army's share; in **Your own team** each member is a man, a woman or a roll, and a career
closed to women in that army is greyed out with the reason. A roll is d10000 at or under the
share x 100 (shares are given to two places), taken before the characteristics, and only for a
career open to women; a career closed to them, or an army with no reliable share, rolls a man.
A woman takes the women's name lists, has no beard, rolls on the shared origins and her own
(`who: f`; `who: m` rows are men's only), and her sheet's events and traits say *she* and *her*.

| Era and army | Share | Careers open | Source |
| --- | --- | --- | --- |
| Civil War: the Union, the Confederacy | 0.02%, 0.03% | infantryman, sharpshooter, trooper, artilleryman, scout, teamster: enlisted disguised as men, under men's names | DeAnne Blanton, *Prologue* (National Archives, 1993): roughly 750 women, as many as 250 Confederates; the share is our arithmetic |
| Second World War: the Soviet Union | 3% | rifleman, machine gunner, sniper, medic, radio operator, sergeant, officer, tank crewman | Over 800,000 women, over 3% of the forces (Air University Review, 1982); 2,484 women snipers |
| Vietnam: the ARVN, the North's army, the Viet Cong | not known: chosen, never rolled | ARVN medic; the North's rifleman, scout, sapper, medic; the Viet Cong's rifleman, scout, sapper, medic, radio operator, squad leader, platoon leader | Women in the Vietnam War (Wikipedia, with its sources) |
| US forces in the Gulf, 1991 | 7% | medic, signaller, military police | GAO NSIAD-93-93: about 41,000 women, some 7% of those deployed |
| Russian forces in Chechnya | 10% | medic | Smirnov (2002): almost 10% of the Russian forces by 1999 |
| US forces in Iraq and Afghanistan | 11.4% | medic, signaller, military police, section leader, platoon leader | CRS R42075: 11.4% of those deployed in February 2013 |
| British forces in Iraq and Afghanistan | 8.3% | the same | MoD manning report, 1 October 2012: 8.3% of the Army |

The share is the women among that army's soldiers, not among those in the career, so a roll is
a rough guide: the GM may prefer to choose. Ground close combat opened to women in the US in
2016 and in Britain in 2016-18, after these wars.

## Followers

A big team's other men get no sheet, only a line: a career (for his kit and weapon, by
region), a name, and a quality rolled on d100, which gives his attack, defence and Nerve.
They are the field map's unit qualities. All are design estimates.

| Quality | Attack | Defence | Nerve |
| --- | --- | --- | --- |
| Green | 40% | 25% | 35 |
| Regular | 50% | 35% | 50 |
| Veteran | 60% | 45% | 65 |

| Quality table | Green | Regular | Veteran |
| --- | --- | --- | --- |
| Default | 01-30 | 31-80 | 81-00 |
| Hardened (a free company) | 01-15 | 16-60 | 61-00 |
| Raw (a farmers' muster) | 01-55 | 56-90 | 91-00 |

For example: *John Archer, archer, regular: longbow 50%, defence 35%, Nerve 50; jack and
sallet.* A follower has no characteristics or skills: in the roller he counts 50 in each.

On the page, **Followers** lists how many of each career come with the team; **−** and
**+** change them, and **Add** brings in another career. **Roll the team** rolls them with
the team, and **Reroll the followers** rolls them again. Their lines print below the sheets.

- **Send to the roller** brings the followers too, each as a fighter on the team's side.
  His card says "Follower" with his career and quality. His quality's attack and defence
  fill the Strike panel whatever weapon he holds, and his Nerve is the quality's.
- **Send to the field map** makes one unit of each career's followers, at the quality most
  of them have (a tie goes to the better), in open order for bows and crossbows and close
  order for the rest, mounted for mounted sergeants. Followers of a healing career go with
  the biggest unit as its medics instead (see [units.md](units.md), *Heroes*). The team goes with them as heroes, each
  with his own career's unit, or else the biggest. The field map offers to add them before
  the battle starts, on the side of that name if it has one, else its first side. Heroes
  sent this way are not the roller's fighters, so their wounds stay on the field map: to
  carry wounds back to the roller, send the team to the roller and add its men as heroes
  from there.

## On the page and in the roller

**Roll the team** makes the whole team, and each sheet has **Reroll him** (or **her**). The names can be
edited. **Print the sheets** prints them, two across. **Send to the roller** hands the team
to the wound roller, which offers to add them to its fighters on the side named. If the
roller has no fighters yet, it switches to the region's wound table.

There, a character from the team builder carries his sheet: his card shows his career, age,
characteristics, skills, defence and old wounds, with the scars on his figure. When he
attacks, his attack % with the weapon in hand fills the Strike panel; when he defends, his
defence does. The GM can still change either. His Nerve comes from the sheet. Old wounds do
not bleed or count as wounds there; their lasting hurts are already in his characteristics.

`python3 -m gravewounds team --region england --template retinue` prints a team and its
followers on the command line. `--array` uses the fixed array, `--women roll` rolls each member and follower at the army's share, and `--seed N` gives repeatable dice. The page
and the Python rules make the same team from the same dice.

His characteristics also count in the roller: Agility for initiative, Endurance for his Blood
and for disease, Strength for how soon he tires hand to hand in his kit, and a leader's
Presence for his side's morale (see [combat.md](combat.md), *Characteristics in the fight*).
Each sheet's **In a fight** line gives the numbers.

Four skills work outside a fight. **Leechcraft** rolls first aid in the roller and, with a
named man on the travel map, helps his force's sick and wounded recover; **Fieldcraft**
forages fresh food on the march; **Watch** makes his force harder to surprise, and
**Stealth** makes the force he attacks with likelier to surprise its enemy (see
[combat.md](combat.md), [travel.md](travel.md) and [works.md](works.md), *Surprise*).

Not yet done (see the backlog): women in the earlier eras (the medieval, gunpowder and First
World War tables have no women blocks yet), and careers for women outside the fighting units
(nurses, auxiliaries, anti-aircraft gunners, pilots).

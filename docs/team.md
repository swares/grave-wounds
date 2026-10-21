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

**Money.** A **Day** is a common soldier's day's pay in his army's coin: 6d for an English
archer in 1415, 12 kreuzer in 1630, $13 a month (43¢) for a Union private, $1,588 a month
($53) for an American soldier in 2008. Each character starts with 30 Days saved for each
career term (`data/money.yaml`), and the downtime action "earn money" pays 1 Day for each day
worked. His issued kit and weapon are free; the sheet shows what they are worth in Days.

The purse is kept as an account: a character's `ledger` lists what he has earned and spent
since he was made, in signed Days, and his purse is his starting Days plus the ledger
(`gravewounds/money.py` purse, earn, spend). In the team builder each sheet shows the account
under the money line: a term worked in the Find work panel pays into it, and he can buy from
the era's price list (pay rows aside; a range at its middle, in his own army's Day) or pay any
sum for anything else. He cannot spend more than his purse holds, and an entry taken back
cannot leave it short. Purses show to the quarter Day.

**One purse on every page.** The account is kept in the browser under `gravewounds-purses`,
one entry for each character (his purse id, `pid`): his name, era, army, terms, starting Days
and ledger (`templates/purse.js`). The team builder writes it whenever it saves and takes back
what other pages changed when it is opened or comes back into view; a character sent to the
wound roller carries his `pid`, his card shows his purse, and putting him **With** a force on
the travel map carries it there. Spending, earning and keep on any page change the same
account.

**Keep.** A soldier with his army is fed by it; a man who is not pays his keep from his purse:
a day's food, and a night's bed where there is one. Each era's equipment file names the price
rows for both (`keep: {food: {row, times}, bed: {row}}`, `times` for a per-meal row; an army may
have its own under `regions`), worked out in his army's Days (`money.keep_days`). Each day's
food is paid before its bed (`money.pay_keep`): a day he cannot pay for food he goes hungry, a
night he cannot pay for a bed he sleeps rough. A job term charges keep for each day worked,
with a bed only in a town, city, village or on the road, unless the job is `board: true` (his
army's service, or wages paid with board or keep: `jobs.keep_for`). `python3 -m gravewounds
work` shows the keep with `--region` and `--purse`.

**Losses and replacements.** `data/replacements/<era>.yaml` gives each era's ways of filling a
gap (`gravewounds/replace.py`): `assigned` (the army's system: armies, careers, the terms a
replacement usually came with, a wait in days), `hire` (men the team can engage: careers,
terms low-high, a cost in Days and more per term, places), and `effects` (what becomes of a
lost man's purse: `share`, `heirs` or `lost`, by army). Each row has a source, or `approx: true`.
In the team builder, **Lost…** on a sheet takes a man off the team with a reason; a man the
travel map records as dead of wounds or disease, or the field map as killed or taken prisoner,
comes off by himself (through his shared purse). The Losses panel settles his purse (the era's
practice offered first; a share is split equally among the survivors, in their ledgers), then
offers the replacements: roll a new man of the same career and terms, an assigned man
(the GM's choice of career where the system allows several; his wait is rolled and shown on
his sheet), or a hire where the team is (the place in Find work), paid from the purse of the
member the GM names. `templates/team.js` repeats `options`, `hire_cost`, `effects` and `settle`.

Prices live in `data/equipment/<era>.yaml`, one file to an era, like the team tables:

- **currencies:** each coin, its units (or a decimal coin), its Day in its smallest unit, and
  a `coin` family. Prices are whole numbers of the smallest unit (farthings for pounds,
  shillings and pence; kreuzer; cents), so nothing is lost to rounding, and Days are worked
  out, never stored.
- **currency:** which coin each army was paid in. An army with no known pay (the Plains
  nations, who traded in robes; the Confederacy, whose dollar collapsed) shows its purse in
  Days only.
- **items:** a name, a category, a price or a low-high range, and a source, or `approx: true`
  for an estimate. A row's `kit` or `weapon` names the armour kits and weapons it prices (a
  kit may be several rows: a brigandine and a sallet); `regions` limits it to some armies.

Seen from an army whose coin is of the same family, a price is counted in that army's Day: an
AK-47 costs an insurgent paid $10 a day more Days than it costs an American soldier. Kit with
no price (machine guns, artillery, most enemy armies' kit) is shown as "part not priced".
The prices, their sources and the gaps are set out in the project doc "Grave Wounds: money and
price lists by period book".

**Jobs.** Earning money can be a job: `data/jobs/<era>.yaml` lists the work a soldier or
adventurer could take between fights in each era (a routier's contract, a Feldscher's post, a
Kansas Pacific buffalo hunter, a KBR convoy driver). Each job has a skill and the least of it
needed to be hired, pay in quarter Days for each day worked (or with `lump`, a sum for the
whole contract, `per` a horse, a robe or a body), a term (a day, a week, a month, or a contract
of so many days), the kinds of place it is found (town, city, village, camp, road, frontier,
sea), who may take it (anyone, or some of the era's careers), a risk, a hook, and the period
wage with its source, or `approx: true`. Each file ends with a d10 trouble table.

The team picks from the jobs where it is. A term takes one check on the job's skill: at or
under, full pay; over, half; 96 or more and over, nothing (`data/money.yaml` work). A job with
a risk takes one d100 a term too; at or under the risk, trouble, a d10 on the era's table, or
the hook. `gravewounds/jobs.py` has the rules, the team builder's Find work panel repeats them
(`templates/team.js`, the same dice in the same order), and `python3 -m gravewounds work --era
wwi --place camp` lists the jobs going, or with `--job` and `--skill` works one term. The
printed tables carry every era's jobs and trouble, the rule book the medieval ones.

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

Ten more eras use the same five steps, with their own skills, origins, careers, events,
regions, teams and followers (`data/teams/thirty_years.yaml`, `horse_musket.yaml`, `crimea.yaml`,
`civil_war.yaml`, `plains_nations.yaml`, `wwi.yaml`, `wwii.yaml`, `korea.yaml`, `vietnam.yaml`
and `modern.yaml`). Pick one with **Era** on the page, or `--era` on the command line. Each
region takes its war's wound table, for old wounds and for the roller.

| Era | Regions (wound table) | Fighting skills | Careers |
| --- | --- | --- | --- |
| Thirty Years' War (1618-1648) | the Swedish army; the Imperial army and the Catholic League (Thirty Years' War) | Musket, Pistol, Blade, Pike | musketeer, pikeman, cuirassier, harquebusier, dragoon, sergeant, field surgeon, sutler, chaplain |
| Horse and musket (1775-1815) | the Continental Army and the British in America (Revolution); the British and the French in the Peninsula (Peninsular War); the United States (1812) | Musket, Rifle, Pistol, Blade, Bayonet, Gunnery | line infantryman, rifleman, dragoon or hussar, artilleryman, sergeant, officer, surgeon's mate, scout, sailor or marine, sutler |
| Crimean War (1854-1856) | the British, the French Army of the East, the Russians at Sevastopol (all the Crimean all-hits table) | Musket, Pistol, Blade, Bayonet, Gunnery | line infantryman, rifleman (chasseur or Zouave), light cavalryman, artilleryman, sailor serving guns ashore, sapper or miner, sergeant, officer, surgeon or orderly, cantinière or canteen-keeper |
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
Springfield breech-loader of 1866 (Rifle), the Civil War's Sharps and Spencer carbines' kin. In the Crimea one Musket skill covers both the smoothbore musket most Russian
infantry still carried and the British and French rifle-musket, fired by the same drill;
sailors serve guns ashore with Gunnery, as the British Naval Brigade and the Russian Black Sea
sailors did in the siege.

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
| Crimean War: the French | not known: chosen, never rolled | cantinière (with her regiment, openly as a woman) | Vivandière (Military Wiki): Napoleon III doubled the cantinières in 1854; they served with their regiments in every campaign of the Second Empire, the Crimea included |
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

## Rank, pay and loot

`data/ranks.yaml` (rules in `gravewounds/ranks.py`, repeated in `templates/team.js` as `rkStart`,
`rkPay`, `rkWage`, `rkPromote`, `rkLoot`, `rkStanding`, `rkWealth`). Figures and their sources
are in the project doc "promotion-loot-research"; `approx: true` marks estimates.

- **Ladders.** Each era's ranks, lowest first, with pay as a multiple of a private's (other
  armies' by region in `pay_by`), least years in the rank below, the Command check's difficulty,
  a literacy bar (`letters`) or penalty (`unlettered`), `deed_only` (a medieval knighting), and
  prize `shares`. `start` puts careers higher (sergeants, officers); `career_pay` multiplies
  (horse twice the foot in the Thirty Years' War; sutlers and cantinières 0).
- **Promotion** at End of season, vacancy by vacancy from the top: the eligible men one rank
  below, most days in rank first, roll Command (+20 and no wait for a deed) until one succeeds;
  his old rank then falls vacant. A lost man's rank falls vacant by itself; the GM opens others
  with + and −, sets any man's rank (a reduction resets his days in rank), and ticks deeds.
- **Pay.** The travel map counts each night a named man's force is fed by its army (`army` in
  the experience store), or owed when its pay is in arrears. End of season pays days × pay ×
  `kept` into his purse and adds the arrears to his debt, paid when the GM presses Pay owed.
- **Loot** (*After the fight*): the field, a sack, plunder after the sack is called off, prize
  money (the Napoleonic wars), a ransom (medieval, Thirty Years' War), or a raid for horses (the
  Plains). Finds are one d100 table in Days for every era (estimates set against Waterloo's
  prize, Hagendorf's Magdeburg sale and the Seringapatam armlets); the era's `keep` takes the
  captain's third or the hospital's tenth; forbidden loot, or a trophy past the era's `cap`,
  risks the provost (his Watch against the man's Stealth; caught, it is lost; on the provost's
  critical or the man's fumble, the era's punishment). Winnings go into his purse.
- **From the fight** (`templates/roller.html`, *After the fight* under Casualties; the rules are
  shared in `templates/ranks.js`). The roller counts each fighter's **downs** (an enemy put down
  by a wound he applied) and suggests a deed for two or more, or the enemy's leader; **Mark
  deeds** sends the ticked men's deeds to the experience store (`deed`), which the team builder
  takes up as the deed tick (+20, the wait waived). A Plains man's blow that lands in close
  combat counts **coup** on that enemy if he is among the first three to strike (3, 2, 1
  honours: `honours` in the store). The winner is the one side still standing, or the side the
  GM names, or (heroes back from the field map) whether each hero's side held the field. The
  winners still up roll **loot** by their era's rules, every one or one the GM picks (a ransom
  is usually one man's); Days go straight into their purses, horses into the store (`horses`,
  each also an honour). A new fight (from the travel map, or Reset count) clears the marks.
- **Honours** (the Plains nations): coups 3, 2 and 1 for the first, second and third to strike,
  a horse taken 1, a horse given away 1; standing and wealth tiers (Ewers: under 6 horses poor,
  40 or more wealthy).

## Skill checks

`data/checks.yaml` (rules in `gravewounds/checks.py`, repeated in `templates/team.js`:
`skillCheck`, `opposedCheck`, `haggle`, `checkUses`). The one roll gets a **difficulty** (Easy
+20, Ordinary, Hard −20, Very hard −40), a **critical** at 10% of the chance and a **fumble**
on a failed 96+ (the fight's and the jobs' figures). **Opposed**: both roll, the resisting side
at Ordinary; the man acting must beat them (success over failure, critical over success, else
the wider margin); a tie or two failures goes to the side resisting. The other side counts as
50 without a sheet.

`uses` lists what each skill and characteristic does out of a fight, each with its usual
difficulty, who resists it (`against`: a skill or characteristic, and the value to use), and
its success, failure and fumble; an era is offered only the uses whose skill it has. The
difficulties and effects are design choices; the notes on period practice (passes, billeting,
articles of war) are general and carry no figures.

The team builder's **Skill checks** panel: pick a man and a use (it fills in the skill, the
difficulty and the other side's value), or any skill or characteristic, and roll. A skill
check that succeeds, or wins, ticks the skill for experience; a characteristic is not ticked.
**Haggle** beside Buy rolls his Persuade against the seller's 50: a tenth off if he wins (a
quarter on a critical, to the quarter Day, never under ¼), the list price if not, and no sale
on a fumble; winning ticks Persuade.

## Strain

`data/stress.yaml` (rules in `gravewounds/stress.py`, repeated in `templates/ranks.js`: `stAdd`,
`stRest`, `stTreat`, `stRelieve`, and `xpStress` for the shared store; research in the project
doc "stress-research"). Each man's Strain, Toll (0.4 of every Strain point), state and whether he
has broken down before are kept in the experience store by purse id. Adding Strain checks each
multiple of 10 the total passes: d100 at or under Nerve + 115 − the multiple (−10 after a
breakdown; 99-00 always fail); a failure rolls d10 + margin/10 on the results (shaken, strained,
exhaustion, severe; the worst holds). Sources: the roller (a wound +2, a bad one +3; a team-builder
comrade down +4; the leader down +3; and once a side has won, the fight +2 and heavy losses +3
where a quarter of his side is down), the travel map (each day a force is **In the line**, +1; a
day camped out of it, rest) and the team builder's **Strain** panel (the GM's sources; Rest a
day; treatment with the unit, forward from 1916, in the rear, sent home or on furlough before
1914, each with return-to-duty odds by state; rotation home for Korea, Vietnam and later;
homecoming for the Plains nations; a lasting-effect note once the Toll reaches his Nerve or he has
broken down). In the roller, shaken and strained cost attack and Nerve (for stop and morale
checks) and a breakdown takes him out of the fight. Calibrated by simulation: Nerve 50, 30 days in
the line and 3 out, breaks down at a median 81 days (Appel: 88); 12 in and 4 out, twice as long.

## Loads

Each sheet's **Loads** line gives what his era's fighting order, marching order and full kit weigh
with his armour and any **extra** kg the GM writes there (what he has bought or picked up; it
goes with him to the roller and the travel map), and the band each puts him in for his body weight
and Strength (see
[travel.md](travel.md), *Loads*).

## Age

`data/ageing.yaml` (rules in `gravewounds/ageing.py`, repeated in `templates/team.js`:
`agSteps`, `agAddWear`, `agWornOut`; research in the project doc "ageing-research").
`steps` takes every 4 years from `aged_to` to `age`: the band of the middle year (plus 2 years for
each 4 Wear) gives the dice each of Strength, Agility, Endurance and Wits loses (Endurance twice,
the worse, from 6 Wear); maturity adds 1 to Presence and Nerve to 40 and Wits to 45 (cap 5 each)
from 20; Wear rises 1. Changes go into `stat_mods`, so skills fall with their characteristics.
`make_character` ages a new man through his terms (the last dice taken; so a 3-term man of 28
has some maturity and 3 Wear, but no decline yet). At End of season, a season with 30 or more
hard nights (counted on the travel map: short of food, a night harder than the shelter, sick or
wounded) or the GM's **Hard season** tick adds 1 Wear; the terms served age him; and each term
from 35 (or 8 Wear) rolls the Worn Out check (3 × Wear + 2 × (age − 35) − (End − 50) ÷ 2, scaled
by the term's years ÷ 4; from 40, End under 30 or any of Str/Agi/End under 25 at once). A worn-out
man's row offers **Discharge him** (lost: sent home) or **Keep him on**. Tuned by simulation: a
line private serving from 16 is worn out by 40 about half the time, by 44 three times in four.
A man made before ageing starts from his age then (`aged_to`).

## Experience

**Training** (`data/training.yaml`, rules in `gravewounds/training.py`, repeated in
`templates/ranks.js`: `trMasters`, `trTeammateOk`, `trWeek`, `trDrill`). On the team builder's
Experience panel: a pupil, a skill and a teacher, from the masters for hire where the team is
(Find work's place; `masters`: skill, fee a week, places; skill `master_skill`, 60) or a
teammate `teammate_gap` (20) or more better. The teacher's Ordinary check ticks the pupil's
skill; the fee and the week's keep (as a job without board) come from the pupil's purse. On the
travel map, on each week's last day a force fed by its army that spent `drill.camped_days` (4)
or more days not marching drills: the best Command among its named men (or `nco`, 50) rolls,
and a success ticks each able named man's weapon skill (`drill` on his record: the skill his
weapon is fought with, set by the roller). The riding fee is from 1879 London; the rest are
estimates.

`data/experience.yaml` (rules in `gravewounds/experience.py`, repeated as `xpSeason` in
`templates/team.js`). A skill used well is **ticked** in a store the three pages share,
`gravewounds-xp`, kept by purse id (`templates/xp.js`):

- the team builder: a job term whose check succeeds ticks the job's skill (illegal jobs too; a
  failed or fumbled check, or a job with no check, ticks nothing), and its days count as
  served unless fumbled (a job with no check counts none);
- the roller: a hit ticks the skill his weapon is fought with (`skill_by` on his sheet), a
  parry or dodge that works ticks his defence skill (`defence_by`, the better of the two), and
  first aid that works ticks the Leechcraft of the man who gave it;
- the travel map: Fieldcraft that forages fresh food, the best Leechcraft with a force that has
  sick or wounded on the week's last day, Stealth when the attack surprises and Watch when it
  does not; and each night with a force is a day served for each named man.

The team builder's **Experience** panel lists each member's ticks and days toward a term.
**End of season** (the GM calls it; about 91 days) rolls d100 for each ticked skill in the
era's skill order: over the skill, it rises 1d3 (to the cap). The days served are then added to
his count, and each term of days (the era's `age.per_term` years of 365 days: 1,460 in most
eras, 365 for Korea) gives `term_main` to his career's main skill, `term_second` to its second,
and the years of age; the sheet shows "(+1 served)". His `terms`, and so his starting purse,
stay as rolled. The new sheet goes into the store with a stamp, and the roller swaps it in when
it next looks (focus, or the store changing); the travel map's copy of his skills is updated at
once. The Python rules and the page give the same result from the same dice.

Not ticked yet: the field map's battles (its heroes come back to the roller, which does not
count their fight), and a term served does not roll the career's event table or its wound
chance.

Not yet done (see the backlog): women in the earlier eras (the medieval, gunpowder and First
World War tables have no women blocks yet), and careers for women outside the fighting units
(nurses, auxiliaries, anti-aircraft gunners, pilots).

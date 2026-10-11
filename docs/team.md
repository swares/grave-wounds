# Team builder: character generation

Each player runs a team of four to six. The first member leads, and when he falls another
steps up. A whole team should take about twenty minutes to make at the table, or one click
on the team builder page, `dist/team.html`. The tables are in `data/teams/medieval.yaml`
and in the printed tables (*Team generation*). Every table, event and trait is written for
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

| Team | Members (terms) |
| --- | --- |
| A lord's retinue | man-at-arms (3), archer (2), archer (1), spearman (1), barber-surgeon (1), servant (1) |
| A free company | mercenary (3), mercenary (2), crossbowman (2), archer (1), spearman (1) |
| A garrison patrol | mounted sergeant (3), crossbowman (2), crossbowman (1), spearman (1), clerk (1) |
| A farmers' muster | spearman (3), spearman (1), spearman (1), archer (1), forester (1) |
| A pilgrims' escort | man-at-arms (3), mounted sergeant (2), crossbowman (1), clerk (1), barber-surgeon (1) |
| A merchant's company | merchant (3), sailor (2), crossbowman (1), servant (1) |

*Your own team* on the page picks four to six careers and their terms.

## On the page and in the roller

**Roll the team** makes the whole team, and each sheet has **Reroll him**. The names can be
edited. **Print the sheets** prints them, two across. **Send to the roller** hands the team
to the wound roller, which offers to add them to its fighters on the side named. If the
roller has no fighters yet, it switches to the region's wound table.

There, a character from the team builder carries his sheet: his card shows his career, age,
characteristics, skills, defence and old wounds, with the scars on his figure. When he
attacks, his attack % with the weapon in hand fills the Strike panel; when he defends, his
defence does. The GM can still change either. His Nerve comes from the sheet. Old wounds do
not bleed or count as wounds there; their lasting hurts are already in his characteristics.

`python3 -m gravewounds team --region england --template retinue` prints a team on the
command line. `--array` uses the fixed array and `--seed N` gives repeatable dice. The page
and the Python rules make the same team from the same dice.

His characteristics also count in the roller: Agility for initiative, Endurance for his Blood
and for disease, Strength for how soon he tires hand to hand in his kit, and a leader's
Presence for his side's morale (see [combat.md](combat.md), *Characteristics in the fight*).
Each sheet's **In a fight** line gives the numbers.

Not yet done (see the backlog): tables for the other eras, skills outside a fight
(Leechcraft for first aid, Fieldcraft and Watch on the travel map) and followers.

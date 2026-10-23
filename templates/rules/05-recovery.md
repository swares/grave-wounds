# Recovery {#recovery}

After the fight come the days that decide who lives. Wounds, sickness and fever all move
on one **track** of five steps, and each step weakens a man in the next fight:

{{table:track}}

## Into camp {#camp}

Each wound goes onto the track at the step its severity gives (light **mending**, serious
**serious**, critical **grave**), or worse if its clock is short: a wound that would kill in
hours or minutes starts at **grave**. In camp the bleeding stops, and each night he gets
back {{blood_night}} Blood.

On the [wound roller](roller.html), put him **With** his force on the
[travel map](travel.html) and press **To camp**; the travel map's nights then run his
wounds with the force's own wounded.

## The recovery check {#check}

Once every {{wound_every}} days, each wound makes a **recovery check**: d100 against his
**Endurance**, adjusted:

{{table:recovery}}

- Succeed by {{big}} or more: **two steps** better.
- Succeed: one step better.
- Fail: it holds; at **deadly**, he dies.
- Fail by {{big}} or more: one step **worse**.

A player character may spend a fate point to roll a failed check again, or a wound-fever roll
that went against him ([Lethality](#lethality)).

A wound that reaches *healed* leaves a scar on his sheet and figure.

## Wound fever {#fever}

{{fever_lo}} to {{fever_hi}} days after the fight, each wound turns septic or it does not:
{{fever_low}}% for a wound with a low risk of infection, {{fever_medium}}% medium,
{{fever_high}}% high; +{{fever_nocamp}} with no camp, −{{fever_quarters}} in quarters, less a
leech's bonus. A septic wound is **wound fever**: a step worse, checked every night, and the
check is harder by {{fever_harder}}. Before antibiotics, this is what killed the men who
survived the battle.

!!! example "The retinue: the camp"
    The retinue carries {{ex.arch_first}} to its camp. His wound goes onto the track at
    **{{ex.k_start}}**. A few nights on, its risk of fever is {{ex.k_fever}}% (medium,
    less {{ex.k_bonus}} for {{ex.leech}}'s Leechcraft). The GM rolls {{ex.k_froll}}: it stays
    clean.

    At the end of the week he checks: Endurance {{ex.k_end}}, a camp (+0), resting
    (+{{rest}}), a leech (+{{ex.k_bonus}}) and a battle wound (+{{wound_easier}}) make
    **{{ex.k_target}}**. He rolls {{ex.k_r1}}, a success by {{ex.k_m1}}: one step better,
    **mending**. A week later he rolls {{ex.k_r2}}, a success by {{ex.k_m2}}: **healed**,
    with a scar on his right thigh. His Blood came back in his first nights in camp, and
    the retinue marches on with its archer.

!!! gm "For the GM"
    The track is where the campaign's hard choices are made. March on, and every check is
    {{marched}}; camp in the open, and fever is likelier; stay in a filthy camp, and the
    flux comes. The travel map counts all of it for whole
    forces; the players only have to decide.

## Strain {#strain}

Fighting wears on a man's mind as well as his body. **Strain** builds from what he goes through:

{{table:strain}}

A day in the line, a fight or an extreme day is changed by how he stands with his comrades,
summed: {{table:strain_mods}}

and {{st_toll}}% of every point also goes into his **Toll**, which only going home lowers. Each
time Strain and Toll together pass {{st_every}}, 20, 30 and on, he rolls d100: at or under his
Nerve + {{st_base}} − that total, he holds; a man who has broken down before rolls 10 less. If he
fails, he rolls d10, adding 1 for each 10 he failed by: 1-4 **shaken** (−10 to attack and Nerve
until a day's rest), 5-7 **strained** (−20 until treated), 8-9 **broken down** (out of the fight
until treated), 10 or more **severely** (out, and to be sent back). Each era has its own words for
these: nostalgia in the Napoleonic and Civil wars, shell shock in 1914-18, combat exhaustion in
1944.

A day out of the line, camped, takes {{st_rest}} Strain off. A man who breaks down is treated
where he is, near the front or in the rear; the nearer and the sooner, the likelier he goes back
to duty:

{{table:treatment}}

Except treatment with his unit, he is away from the force for those days: the travel map counts
them off, and he comes back to it when they are done. If the team's leader is killed, each of his
men takes the Strain of it ({{st_leader}}), twice that if he was a trusted leader (Command
{{st_trusted}} or more): a design estimate, since no study measured it.

Korea, Vietnam and the later wars rotated men home at the end of a tour: Strain gone, the Toll
cut to a quarter. For the Plains nations, a homecoming that welcomes and honours a man halves it.
A man who ends a campaign with his Toll at or above his Nerve, or who broke down, may carry a
lasting effect: the GM notes it as part of who he is (sleeping badly, starting at noises, drinking,
grief), never as a penalty.

!!! gm "For the GM"
    These rules follow the US Army's figures of 1944: a man of ordinary Nerve in a rifle company
    lasted about 80 to 90 days of combat, and nearly every man had broken down by 200 to 240 days;
    British units, rested every twelve days, lasted about twice as long. Breaking down was not
    weakness: it came to almost everyone who stayed in the line long enough. Handle it with the
    respect the men who lived it deserve.


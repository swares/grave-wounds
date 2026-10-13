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

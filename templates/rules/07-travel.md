# The march and the camp {#travel}

Between battles the team marches, camps and sickens. The [travel map](travel.html) moves
forces across a map of hexes, usually 0.6 mile (1 km) across, on one clock for everyone.

## Marching {#marching}

A force marches at its kind's road speed:

{{table:speeds}}

Other ground takes longer; a step from one hex to the next costs the average of the two:

{{table:terrain}}

The march starts {{t_start}} hour after sunrise and stops {{t_stop}} hour before sunset, up to
{{t_hours}} hours a day: a short winter day is a short march. Mud and snow slow it (next
chapter), and a flooded ford cannot be crossed. These speeds are for a small, fit band; a
large army's column made less ground a day.

**The clock.** Every force on a map keeps the same time, and it moves on only when the GM
moves it: an hour, to nightfall, or until something happens. **Orders** say whether a force
marches on its route or halts. When forces of different sides come within {{t_within}} hex of
each other, the clock stops and both halt: the fight can be set up, on the roller's battle
map or the field map, or they can be given new orders.

## Camps {#camps}

At the end of the march a force makes camp:

{{table:camps}}

Digging takes the work of the camp's ditches, banks, palisades and stakes, laid out as the
battle map would lay them, divided among the men ({{t_share}} of them work at once; the rest
guard and cook). Camp work can use what is left of the marching day and then {{t_evening}}
evening hours; beyond that it runs on into the next day.

**Surprise.** When a fight is set up from the travel map, the defenders may be caught
unawares: {{s_base}}%, plus the camp's figure above ({{s_none}} more with no camp at all),
+{{s_dark}} in the dark, +{{s_fog}} in fog, plus the attackers' best Stealth ÷ {{s_per}}, less the
defenders' best Watch ÷ {{s_per}}, and never under {{s_lo}}% or over {{s_hi}}%. Surprised men
cannot attack or move in the first round.

## Finding work {#work}

Between fights a man may hire himself out. Where the team is (a town, city, village, camp, the
road, the frontier or at sea) decides which jobs are on offer; he may take any of them that his
career allows and his skill reaches (the least skill to be hired). Pay is in Days for each day
worked, or a sum for the whole contract, a horse or a body.

A job is worked in **terms**: a day, a week ({{w_week}} days), a month ({{w_month}} days) or a
contract of so many days. Each term he makes **one check** on the job's skill. At or under it,
he is paid in full; over it, {{w_fail}} of the pay; {{w_fumble}} or more and over, a fumble,
and nothing. A job with no skill pays in full.

A job with a **risk** takes one d100 a term as well: at or under the risk, trouble. The GM uses
the job's hook, or rolls a d10 on the era's trouble table. Jobs marked † are against the law,
and their trouble is the law's.

**Keep.** A soldier with his army is fed by it. A man who is not (off on his own, on leave, or
working for someone else) pays his **keep** from his purse each day: a day's food
({{keep_food}} for an English archer), and a bed ({{keep_bed}}) where there is one to be had,
in a town, city or village or at an inn on the road. A job marked *fed* feeds him while he works:
his army's own service, or wages paid with board. A day he cannot pay for his food he goes
hungry: it counts as a day without fresh food, and tires him a step. A night he cannot pay for
a bed he sleeps rough. The medieval jobs:

{{table:jobs}}

{{table:job_trouble}}

The other {{w_eras}} eras' jobs are in the printed tables and the team builder.

## Sickness {#sickness}

Before antibiotics, disease emptied armies faster than battle. Once a week every well man
may catch what the camp breeds, at a chance set by its **hygiene** (a bivouac is poor,
quarters good, other camps fair), by staying four weeks or more in one place, by the
ground (marsh, a town) and by the week's weather:

{{table:diseases}}

A case climbs to its peak after it shows, then gets better or worse each night on the
track of [Recovery](#recovery), with rest, a camp and shelter helping, and marching, cold
wet nights and filth hurting. Survivors of typhus and plague cannot catch it again; ague comes
back in marsh country.

- **What it costs.** Men at **{{d_unfit}}** or worse cannot dig, fight or march on their own;
  at **{{d_carried}}** or worse they are carried on litters. A force carrying litters marches at
  {{d_march}}%, or {{d_short}}% with fewer than {{d_bearers}} fit men a litter.
- **Scurvy.** After {{sc_weeks}} weeks without fresh food (fruit, greens, fresh meat, onions),
  each week every well man may fall ill: {{sc_chance}}% the first week, {{sc_per}} more each week
  after, against his Endurance. Fresh food heals it {{sc_heal}} steps a week. A scurvied man's
  old wounds open again.
- **Frostbite.** On a night of {{fb_below_f}} °F ({{fb_below}} °C) or colder, men without
  enough shelter may be frostbitten, a sickness on the same track.

!!! example "The retinue: on the road"
    The retinue marches north on foot: {{t_foot_day}} a day on the road when the days are long,
    less in March, when Towton was fought, and less again in the snow that fell that day. It
    makes a watched camp each night, with a sentry roster and fires; no tools are needed. In
    a fair camp, moving on every day, the flux is the only real danger; were it to sit
    in a filthy siege camp for a month, typhus would come for it.

!!! gm "For the GM"
    The travel map counts all of this for whole forces, and runs each named character's own
    case with his own Endurance when you put him **With** a force from the roller. Your job
    is the choices: how hard to march, where to camp, whether to wait for the sick.

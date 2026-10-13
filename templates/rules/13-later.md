# A later war: the squad {#later}

The medieval chapters followed one retinue. This chapter follows a US Army rifle squad
in Vietnam through one night, with the same rules and, where dice are rolled, the dice
given. The [team builder](team.html) made the squad.

!!! example "The squad"
    The team builder rolls {{lx.squad}}. **{{lx.lead}}** leads it: {{lx.lead_terms}} terms,
    each a year of the war, so he is {{lx.lead_age}}, with Command {{lx.lead_cmd}}. Its
    machine gunner is **{{lx.mg}}**, {{lx.mg_terms}} terms, who fires the gun at
    **{{lx.mg_skill}}%** but defends at only {{lx.mg_def}}%. Its grenadier is
    **{{lx.gren}}**, and its medic is **{{lx.medic}}**, Leechcraft {{lx.medic_skill}}.
    {{lx.followers}} riflemen follow them. Their kit: {{lx.kit}}.

## On the field map {#later-field}

!!! example "The squad: an ambush in the dark"
    The squad lies in extended order beside a trail on a dark night, gone to ground. No
    one can see to aim past {{n_dark}}. Shots at the squad lose {{x_ground}}% for going to
    ground, and only {{x_seen}}% of the aimed ones find a man to aim at.

    An enemy column comes down the trail. When the squad's gun opens fire, its muzzle
    flashes give it away: the enemy can now aim at its hex from up to {{n_flash}}. The
    sergeant calls the company's mortars for illumination. It lands this exchange and
    lights the trail as by day for {{n_lasts}} exchanges, so his riflemen can aim.

## In the roller {#later-roller}

The heroes' wounds are rolled in full, as in [the fight](#fight).

!!! example "The squad: the gun"
    An enemy rifleman, a regular, fires his AK at {{lx.mg_first}} at {{lx.k_attack}}% and
    rolls **{{lx.k_roll}}**: a margin of {{lx.k_margin}}. Against a bullet, an arm takes a
    margin of {{lx.k_band}} or more to be serious, so this one is **{{lx.k_sev}}**.
    {{lx.mg_first}} dodges at {{lx.mg_def}}% and rolls {{lx.k_droll}}: no.

    The round strikes his **{{lx.k_loc}}**, where his vest does not reach. It bleeds
    {{lx.k_bleed}}, pain {{lx.k_pain}}, and the arm is hurt. The wound carries shock, so he
    makes a stop check: Nerve {{lx.k_nerve}}, less {{lx.k_pain}} steps of pain, gives
    **{{lx.k_target}}**. He rolls {{lx.k_sroll}} and {{lx.k_passed}}: he fights on.

    But the {{lx.k_weapon}} takes both hands. With an arm hurt he cannot fire it, as in
    [Wounds](#penalties), so he can only defend. At {{lx.k_per}} Blood a round, his
    {{lx.k_blood}} Blood lasts {{lx.k_rounds}} rounds.

!!! example "The squad: the grenade"
    A grenade bursts beside {{lx.gren_first}}. The thrower's margin is {{lx.r_margin}}
    (he rolled {{lx.r_roll}}). A fragment in the body is serious from a margin of
    {{lx.r_band}}, so this is **{{lx.r_sev}}**, in his **{{lx.r_loc}}**. But his vest, a
    {{lx.r_vest}}, takes {{lx.r_steps}} steps off a fragment: it is **{{lx.r_after}}**.
    Against a rifle round the same vest takes {{lx.r_rifle}}.

!!! example "The squad: the medic"
    In a quiet moment {{lx.medic_first}} crawls to the gun. He binds {{lx.mg_first}}'s arm
    at his Leechcraft {{lx.medic_skill}} and rolls {{lx.m_roll}}: he {{lx.m_done}}, taking
    the bleeding down {{lx.m_steps}} steps to **{{lx.m_after}}**. The arm is still hurt
    (−{{lx.m_impair}}% to his attack with it), so another man takes the gun.

    At dawn the squad carries him back. His wound goes onto the track as in
    [Recovery](#recovery).

!!! gm "For the GM"
    In a later war the heroes are the few men whose names the players know in a fight of
    hundreds. Keep the field map for the shape of the night and the roller for the
    moments that matter: a gunner hit, a medic crawling out, a vest that held.

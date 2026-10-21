# Making a team {#team}

A team is four to six characters with a shared history: a lord's retinue, a free company, a
patrol. The first character leads it, and when he falls another steps up. The
[team builder](team.html) makes a whole team in one click, or one character at a time, from
the tables of {{eras}} eras; the [printed tables](tables.pdf) hold the same tables for the
table top. This chapter uses the medieval tables (c.1250–1460). The other eras follow the
same five steps with their own careers, skills and kit ([Other wars](#eras)).

## The five steps {#five-steps}

**1. Characteristics.** Roll 3d6 × 5 for each characteristic in order ({{stat_lo}} to 90), or
take the fixed array {{array}} and place it, highest first, where the character's career
wants it most.

**2. Origin.** Roll d100 on the origin table ({{origins}} origins). It says where he comes
from, gives one skill +{{origin_gain}}, and a **trait** and a **drawback** that go together: a
characteristic ±10 or a skill ±15.

**3. Career terms.** The leader serves three terms, the others one or two. In each term:

- his career's main skill rises, +{{first_term}} in the first term and +{{term_main}} after;
- its second skill rises +{{term_second}};
- d100 on the career's table gives an **event**, and the skill it taught rises
  +{{event_gain}}. An event he has had already moves to the next row down.

He starts at {{age_start}} and is {{age_term}} years older for each term. Nobody dies while being
made. The {{careers}} medieval careers:

{{table:careers}}

**4. Old wounds.** A term marked * on its table (a siege, a broken line, a rout) leaves an
old wound, and so does a d100 at or under the career's wound chance. Its place is rolled on
the region's own wound table, the same one the roller uses. Then d100: up to
{{scar_upto}}, a healed scar; above, a **lasting hurt**, {{lasting}} off the characteristic
that place governs (Wits for the head, Presence for the face, Strength for the arms,
Agility for the legs, Endurance for the body).

**5. Skills and kit.** Each skill starts at a characteristic divided by 2, 3, 4 or 5
(rounded down), plus what he gained, to {{skill_max}} at most. His kit and weapon come with
his first career and his region.

**Money.** A **Day** is a common soldier's day's pay in his army's coin: {{day_coin}} for an
English archer. Each character starts with **{{purse_days}} Days** saved for each career term,
so a leader of three terms has {{purse_three}} Days ({{purse_three_coin}}). His issued kit and
weapon cost him nothing; the team builder shows what they are worth in Days. In camp, a man who
spends a day of rest earning money gets **{{earn_days}} Day** for it; one who takes a job does
better or worse by the job ([Finding work](#work)).

!!! example "The retinue: {{ex.arch}}"
    The team builder rolls a lord's retinue from England: {{ex.lead}}, a man-at-arms, leads
    it. Its senior archer is **{{ex.arch}}**, {{ex.a_terms}} terms, age {{ex.a_age}}:
    Strength {{ex.a_str}}, Agility {{ex.a_agi}}, Endurance {{ex.a_end}}, Wits {{ex.a_wits}},
    Nerve {{ex.a_nerve}}, Presence {{ex.a_pres}}. He was {{ex.a_origin}} ({{ex.a_trait}};
    {{ex.a_drawback}}), and in his terms he {{ex.a_events}}. His skills that matter here:
    {{ex.a_skills}}. He fights with the longbow at **{{ex.a_bow}}%**, and his defence is
    **{{ex.a_def}}%**.

    His Endurance is low, and it shows in a fight: his **Blood** is {{ex.a_blood}}, not the
    usual {{blood_pool}} (next chapter). With Agility {{ex.a_agi}} he rolls
    **d{{init_die}} + {{ex.a_init}}** for initiative.

## Followers {#followers}

A big team's other men get no sheet, only a line: a career, a name and a **quality**,
rolled on d100. The quality gives their attack, defence and Nerve (the table in
[How to play](#characteristics)). Some teams roll on a better or worse table:

{{table:fq}}

!!! gm "For the GM"
    Followers are what make a team feel like a household or a company, and they are who
    dies first. Name them; the players will remember them. On the [field map](field.html)
    they fight as units around the team, who go with them as **heroes**.

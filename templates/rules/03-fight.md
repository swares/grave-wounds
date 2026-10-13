# The fight {#fight}

A fight runs in **rounds** of 6 seconds. Each round every fighter who can act takes one
turn, in order of initiative; then the round ends, the wounded bleed and the sides check
their nerve. Most fights last a minute or two: one side breaks long before it is all down.

The [wound roller](roller.html) runs all of this: pick an attacker and a defender, roll the
hit, apply it, and press **Next fighter** and **Next round**. Its battle map is a grid of
hexes about {{hex_yd}} yards ({{hex_m}} m) across.

## A fighter's turn {#turn}

1. **Initiative.** At the start of the fight each fighter rolls d{{init_die}} + Agility ÷
   {{init_per}} (rounded down), and they act from highest to lowest. A fighter who is down,
   out of the fight, or on a side that has broken does not act.
2. **Move or stay.** He may stay, **advance** up to {{advance}} hexes and still attack, or
   **run** up to {{run}} hexes and not attack. He may pass through friends but not stop on
   them. Leaving an enemy's side by more than one step gives that enemy a free attack.
3. **Attack.** Roll d100 against his attack, less his wound penalties and any range
   penalty. Equal or under hits, and the **margin** is how far under. A roll at or under a
   tenth of the chance is a **critical**: it cannot be defended.
4. **Defence.** The defender may roll d100 against his defence (Parry or Dodge), less his
   own penalties. Equal or under, the blow misses.
5. **Where it lands.** Roll d100 on the era's hit-location table for the place, and on the
   weapon's table for how it wounds: a cut, a thrust (pierce), a crushing blow, a bullet.
6. **How bad.** The margin sets the severity: under {{band_serious}} **light**, from
   {{band_serious}} **serious**, from {{band_critical}} (or on a critical) **critical**.
   Firearms have their own bands for the body and the limbs. A hit by a margin of
   {{graze}} or less, if it is not a critical, only **grazes**: its bleeding and pain are
   a step less, and it calls for no stop check.
7. **Armour.** The armour on that place lowers the severity a step at a time against that
   kind of blow, if its coverage roll says the blow met it. Some weapons are made to beat
   armour: a war bow's heavy arrows go through mail and a jack as if they were not there.
8. **The wound.** Look up the wound for the place, the kind of blow and the severity, and
   write it down. Its effects are in [the next chapter](#wounds).
9. **The stop check.** A {{stop_sev}} wound that carries **shock** (most do; many limb wounds
   do not) calls for a d100 against the wounded man's **Nerve**, less his pain and blood-loss
   penalties, and {{crit_stop}} more for a critical wound:

{{table:stop}}

A worse result replaces a milder one, and the round it happens in is the first of its
rounds. This is what ends real fights: men stop, sit down, crawl away, long before they
die.

!!! example "The retinue: the arrow"
    On the road to Towton the retinue meets a band of Lancastrian billmen, regulars. It is
    {{ex.arch}}'s turn, and the nearest billman is in short range. He shoots at
    {{ex.a_bow}}% and rolls **{{ex.s_roll}}**: a hit by a margin of {{ex.s_margin}},
    **{{ex.s_sev}}**. The billman tries to dodge at {{ex.s_def}}% and rolls {{ex.s_droll}}:
    no. The arrow strikes his **{{ex.s_loc}}**, a thrust. His jack would take the wound
    down {{ex.s_raw}} step, but the war bow's arrows ignore it, so it stays
    **{{ex.s_after}}**: bleeding {{ex.s_bleed}}, pain {{ex.s_pain}}, short of breath, and it
    would kill in {{ex.s_lethal}} untreated. It carries shock, so he makes a stop check:
    Nerve {{ex.s_nerve}}, less {{ex.s_pain}} steps of pain, gives **{{ex.s_target}}**. He
    rolls {{ex.s_sroll}}, failing by {{ex.s_by}}: he can **{{ex.s_state}}** for
    {{ex.s_rounds}} rounds.

!!! example "The retinue: the bill"
    The billmen close. One reaches {{ex.arch_first}} and swings at {{ex.c_attack}}%, rolling
    **{{ex.c_roll}}**: a margin of {{ex.c_margin}}, **{{ex.c_sev}}**. {{ex.arch_first}} dodges
    at {{ex.a_def}}% and rolls {{ex.c_droll}}. The bill opens his **{{ex.c_loc}}**, a cut,
    where his jack does not reach. The wound bleeds **{{ex.c_bleed}}** (arterial), pain
    {{ex.c_pain}}, and the leg is hurt. It {{ex.c_shock}} carry shock, so there is no stop
    check, and he fights on. But at {{ex.c_per}} Blood a round, his {{ex.a_blood}} Blood will be
    gone in {{ex.c_rounds_dead}} rounds. The next chapter is about what that means.

## The end of the round {#round-end}

- **Bleeding.** Every wounded fighter loses Blood at his wounds' rate (next chapter).
- **Results wear off.** Defend only and stunned count down a round.
- **Pain.** A fighter whose pain is above the cap ({{pain_cap}} steps, −{{pain_cap_pct}}%)
  makes a stop check every round, as for a serious wound.
- **Morale.** A side with {{morale_trigger}} or more of its fighters down rolls d100 against
  the best Nerve among those still up (its leader's, if he is up): +{{leader_present}} while a
  leader is up, and (Presence − 50) ÷ {{presence_per}} more for him; −{{leader_down}} if a
  leader is down; −{{heavy_losses}} once {{morale_heavy}} of the side is down. Over the
  target, the side breaks: it runs or surrenders.

!!! gm "For the GM"
    The roller asks for the stop check and the morale roll when they are due, and you can
    type your own dice into it. Remember that most enemies want to live too: a side that
    breaks runs, and a man who is down asks for quarter. A fight is usually decided in a
    minute.

## Wounds and movement {#wounds-moving}

A leg wound halves a fighter's move (advance {{ex.c_adv}}, run {{ex.c_run}}). A man who
has collapsed or cannot stand crawls {{crawl}} hex. A winded man cannot run, and a
stunned or out man cannot move at all. The [printed tables](tables.pdf) and the roller's
battle map have the rest: ground, height, cover, works and weather.

# Wounds {#wounds}

A wound is written down as what it does. Each one has five things, and they add up across
all of a fighter's wounds:

- **Bleeding**, from B0 (none) to B3 (arterial).
- **Pain**, from P0 to P3.
- **Impairments**: what the wound stops the body doing.
- **Shock, fracture or severed**: shock calls for the stop check; a fracture is a bone
  that needs setting; a severed part is gone.
- **The clock**: how long it would take to kill him untreated, from *none* through days,
  hours, minutes and rounds to *instant*.

## Blood {#blood}

Every fighter has a **Blood** pool: {{blood_pool}}, plus (Endurance − 50) ÷ {{blood_per}},
rounded down ({{blood_lo}} at Endurance 15, {{blood_hi}} at 95). A player character's pool is
multiplied by the [lethality](#lethality) setting. Each wound bleeds away
Blood at its rate:

{{table:bleed}}

As Blood falls, so does the fighter:

{{table:blood}}

Bleeding is what kills quickly. A man with an arterial wound has a few rounds; a man with a
heavy one has a few minutes; slow bleeding gives his friends time.

## Penalties {#penalties}

A wounded fighter fights worse. Add up:

- **Pain**: −{{pain_step}}% to attack and defence for each step, counted to {{pain_cap}}
  steps at most (and above that, a stop check every round).
- **Blood lost**: the table above.
- **Impairments**, each counted once however many wounds cause it. An arm's impairment
  counts against his **weapon arm** (his weapon hand's side) or his **shield arm** (the
  other):

{{table:impair}}

Attack and defence penalties are each capped at −{{cap}}%. A fighter with no usable hand
cannot hold a weapon. A fighter with **either** arm hurt (an arm wound, a lost grip, a
useless hand or arm) cannot attack with a two-handed weapon (bows, crossbows, long guns,
bills, halberds, pikes and poleaxes): he can only defend until he takes up something he can use in
one hand.

## First aid {#first-aid}

A wound can be treated three ways (on the roller, the buttons on the casualty's card).
How long it takes, and whether anyone can reach him under fire, is the GM's call:

- **Bind**: pressure and a bandage, one step less bleeding.
- **Tourniquet**: an arm or a leg only; the bleeding stops. Left on for hours, the limb is
  lost.
- **Cauterise**: the bleeding stops, at one more step of pain.

If anyone on his side comes from the team builder, the best **Leechcraft** among them still
standing rolls d100 for each treatment. Success: a bind stops {{bind_skilled}} steps instead
of one, and cautery adds no pain. Failure: nothing happens, and it can be tried again next
turn. A side with no sheets binds without rolling.

!!! example "The retinue: the tourniquet"
    {{ex.arch_first}}'s thigh bleeds {{ex.c_per}} Blood a round. The best Leechcraft in the
    retinue is {{ex.leech_who}}: {{ex.leech_skill}}.
    He drags {{ex.arch_first}} back and tries a tourniquet; he rolls 41, over his
    {{ex.leech_skill}}, and the strap slips. He tries again the next round and rolls 19: it
    holds, and the bleeding stops. Two rounds of bleeding have left {{ex.arch_first}} **{{ex.c_left}}** of
    {{ex.c_blood}} Blood: {{ex.c_th}}.

    His wound penalties now: pain {{ex.c_pain}} and the Blood he lost give
    **−{{ex.c_patt}}% to attack**; his hurt leg adds to his defence, **−{{ex.c_pdef}}%**. He
    moves at half pace. He is out of this fight in all but name, and alive.

!!! gm "For the GM"
    The clock is a guide to the story, not a timer to run down: a wound *fatal in hours* is
    one that needs a surgeon tonight, not one that kills on the stroke of the hour. Blood is
    what the rules count. A man who reaches no Blood is unconscious and dying; what happens
    next is first aid, luck, and the camp.

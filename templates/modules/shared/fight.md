<!-- page -->
# The fight {#fight}

A round is 6 seconds. Every fighter gets one turn, highest **initiative** first. Each man rolls once at the
start: d{{init_die}} + Agility ÷ {{init_per}}, rounded down.

**The one roll.** Roll d100. Equal to or under the number succeeds, and how far under is the **margin**. A roll
at or under a tenth of the number is a **critical**.

**On his turn**

1. **Move.** Stay, **advance** up to {{advance}} hexes and still attack, or **run** up to {{run}} and not attack.
   Walking away from an enemy beside you gives him a free attack.
2. **Attack.** d100 against Attack, less your penalties. You may first declare an **aim** at a zone, at a gap in
   the armour, or both. Each costs {{aim_cost}} of your margin on a hit, and is free on a critical.
3. **Defence.** The defender rolls d100 against Defence, less his penalties. Success turns the blow. A critical
   can't be defended.
4. **Where it lands.** d100 on *Where it lands*, under the attacker's weapon. {{pt_blow_note}}
5. **How bad.** Margin under {{band_serious}}: **light**. {{band_serious}} or more: **serious**. {{band_critical}}
   or more, or a critical: **critical**. A margin of {{graze}} or less only **grazes**, unless it is a
   critical: a step less bleeding and pain, and no stop check.
6. **Armour.** Armour lowers the severity by steps. See *Where it lands*.
7. **The wound.** Read it from *What it does* and write it on the sheet.
8. **Stop check.** A serious or critical wound marked **S** needs d100 against the wounded man's Nerve, less his
   pain and blood penalties, and {{crit_stop}} more for a critical. Players' men add their setting's bonus.

{{table:stop}}

**End of the round.** Everyone bleeds. Then a side with {{morale_trigger}} or more of its men down, or whose leader went down this round, rolls d100 against
the best Nerve among those still up: +{{leader_present}} while a leader is up, −{{leader_down}} if he is down, −{{heavy_losses}} once
{{morale_heavy}} of the side is down. Over the target, the side breaks: it runs or surrenders.

**Lethality.** Standard: Blood ×1.5, +20 to Nerve on stop checks, and one **fate** point, which lowers a wound a
step, or rerolls a stop check, recovery or fever roll. Gritty: Blood ×1, no bonus, no fate.

